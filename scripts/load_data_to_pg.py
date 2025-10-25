import json
import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import JSON, Column, DateTime, Float, Index, Integer, String, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tenacity import retry, stop_after_attempt, wait_fixed  # pip install tenacity para retry

# Carrega .env
load_dotenv('.env')  # Ou .env.production

# Configs do BD (de .env)
PG_USER = os.getenv('POSTGRES_USER', 'evaonline')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '123456')
PG_HOST = os.getenv('POSTGRES_HOST', 'postgres')
PG_PORT = os.getenv('POSTGRES_PORT', '5432')
PG_DB = os.getenv('POSTGRES_DB', 'evaonline')

DB_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

logger.add("load_data.log", rotation="1 day", level="INFO")  # Log em arquivo

# ===========================================
# DEFINIÇÃO DE TABELAS (SQLAlchemy ORM)
# ===========================================
class CitiesSummary(Base):
    __tablename__ = 'cities_summary'
    city = Column(String, primary_key=True)
    region = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    alt = Column(Float)
    total_records = Column(Integer)
    data_period = Column(String)
    variables = Column(JSON)
    completeness = Column(Float)
    eto_mean = Column(Float)
    eto_std = Column(Float)
    eto_max = Column(Float)
    eto_min = Column(Float)
    eto_p99 = Column(Float)
    eto_p01 = Column(Float)

class AnnualNormals(Base):
    __tablename__ = 'annual_normals'
    id = Column(Integer, primary_key=True, autoincrement=True)
    city = Column(String)
    period = Column(String)
    eto_normal_mm_day = Column(Float)
    precip_normal_mm_year = Column(Float)
    valid_years = Column(Integer)
    completeness = Column(Float)
    __table_args__ = (Index('idx_city_period', 'city', 'period'),)

class ExtremesAnalysis(Base):
    __tablename__ = 'extremes_analysis'
    id = Column(Integer, primary_key=True, autoincrement=True)
    city = Column(String)
    total_days = Column(Integer)
    eto_high_extremes_count = Column(Integer)
    eto_low_extremes_count = Column(Integer)
    eto_total_extremes = Column(Integer)
    eto_extreme_frequency = Column(Float)
    eto_max_value = Column(Float)
    eto_min_value = Column(Float)
    eto_high_extremes_years = Column(JSON)  # Lista de anos
    eto_low_extremes_years = Column(JSON)
    precip_extremes_count = Column(Integer)
    precip_extreme_frequency = Column(Float)
    precip_max_value = Column(Float)
    precip_dry_spell_max = Column(String)
    precip_wet_spell_max = Column(String)
    __table_args__ = (Index('idx_city_extremes', 'city'),)

class CityReports(Base):
    __tablename__ = 'city_reports'
    city = Column(String, primary_key=True)
    report_data = Column(JSON)  # JSON completo do report_*.json
    loaded_at = Column(DateTime, default=datetime.utcnow)

class GenerationMetadata(Base):
    __tablename__ = 'generation_metadata'
    id = Column(Integer, primary_key=True, autoincrement=True)
    generation_date = Column(DateTime)
    total_cities = Column(Integer)
    reference_period_start = Column(String)
    reference_period_end = Column(String)
    reference_period_key = Column(String)
    methodologies = Column(JSON)
    summary_statistics = Column(JSON)
    loaded_at = Column(DateTime, default=datetime.utcnow)

# Cria tabelas se não existirem (com retry para conexão)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def create_tables():
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tabelas criadas/verificadas no PostgreSQL")

create_tables()

# ===========================================
# FUNÇÃO PARA CARREGAR CSVs (Otimizada com chunks e multi)
# ===========================================
def load_csv_to_table(csv_path, table_class, if_exists='append'):
    """Carrega CSV para tabela SQLAlchemy com otimizações."""
    try:
        start_time = time.time()
        df = pd.read_csv(csv_path)
        df.to_sql(
            table_class.__tablename__, 
            engine, 
            if_exists=if_exists, 
            index=False,
            chunksize=1000,      # Bulk em chunks
            method='multi'       # Inserts nativos do PG (rápido)
        )
        elapsed = time.time() - start_time
        logger.info(f"✅ CSV '{csv_path.name}' carregado em '{table_class.__tablename__}' ({len(df)} linhas) em {elapsed:.2f}s")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar {csv_path}: {e}")

# ===========================================
# FUNÇÃO PARA CARREGAR JSONs de Cidades (Batch Upsert)
# ===========================================
def load_city_reports(cities_folder):
    """Loop nos JSONs de cities/ e insere em batch com upsert."""
    cities_path = Path(cities_folder)
    batch_size = 10  # Batch para performance
    inserted = 0
    batch = []
    start_time = time.time()
    
    for json_file in cities_path.glob('report_*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extrai city do filename
            city = json_file.stem.replace('report_', '')
            batch.append({
                'city': city,
                'report_data': data,
                'loaded_at': datetime.utcnow()
            })
            
            # Batch insert a cada N arquivos
            if len(batch) >= batch_size:
                insert_batch(batch)
                batch = []
                inserted += len(batch)
        except Exception as e:
            logger.error(f"❌ Erro ao processar {json_file}: {e}")
    
    # Insere batch final
    if batch:
        insert_batch(batch)
        inserted += len(batch)
    
    elapsed = time.time() - start_time
    logger.info(f"📊 Total de relatórios de cidades carregados: {inserted} em {elapsed:.2f}s")

def insert_batch(batch):
    """Insere batch com upsert (ON CONFLICT)."""
    with SessionLocal() as db:
        try:
            # Upsert: INSERT ... ON CONFLICT DO UPDATE
            db.execute(
                text("""
                    INSERT INTO city_reports (city, report_data, loaded_at) 
                    VALUES (:city, :report_data::jsonb, :loaded_at) 
                    ON CONFLICT (city) DO UPDATE SET 
                        report_data = EXCLUDED.report_data, 
                        loaded_at = EXCLUDED.loaded_at
                """),
                batch
            )
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erro no batch insert: {e}")
            # Fallback: Insere um a um
            for item in batch:
                try:
                    existing = db.query(CityReports).filter_by(city=item['city']).first()
                    if existing:
                        existing.report_data = item['report_data']
                        existing.loaded_at = item['loaded_at']
                    else:
                        new_report = CityReports(**item)
                        db.add(new_report)
                    db.commit()
                except Exception as e2:
                    logger.error(f"❌ Fallback erro para {item['city']}: {e2}")

# ===========================================
# FUNÇÃO PARA CARREGAR Metadata Global
# ===========================================
def load_metadata(metadata_path):
    """Carrega generation_metadata.json em tabela."""
    try:
        start_time = time.time()
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with SessionLocal() as db:
            # Limpa e insere (ou upsert se múltiplos)
            db.execute(text("DELETE FROM generation_metadata"))
            
            new_meta = GenerationMetadata(
                generation_date=datetime.fromisoformat(data['generation_date'].replace('Z', '+00:00')),
                total_cities=data['total_cities'],
                reference_period_start=data['reference_period'][0],
                reference_period_end=data['reference_period'][1],
                reference_period_key=data['reference_period_key'],
                methodologies=json.dumps(data['methodologies']),
                summary_statistics=json.dumps(data['summary_statistics'])
            )
            db.add(new_meta)
            db.commit()
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Metadata global carregado de '{metadata_path.name}' em {elapsed:.2f}s")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar metadata: {e}")

# ===========================================
# EXECUÇÃO PRINCIPAL
# ===========================================
if __name__ == "__main__":
    logger.info("🚀 Iniciando carga de dados para PostgreSQL...")
    start_total = time.time()
    
    # Caminhos ajustados para sua estrutura (reports/cities e reports/summary)
    base_path = Path(__file__).parent.parent  # Assuma scripts/ na raiz; ajuste se necessário
    cities_folder = base_path / 'reports' / 'cities'  # reports/cities com report_*.json
    csv_folder = base_path / 'reports' / 'summary'     # reports/summary com CSVs
    
    # Verifica existência
    if not cities_folder.exists():
        logger.error(f"❌ Pasta {cities_folder} não encontrada!")
        exit(1)
    if not csv_folder.exists():
        logger.error(f"❌ Pasta {csv_folder} não encontrada!")
        exit(1)
    
    # Carrega CSVs (otimizado)
    load_csv_to_table(csv_folder / 'annual_normals_comparison.csv', AnnualNormals)
    load_csv_to_table(csv_folder / 'cities_summary.csv', CitiesSummary)
    load_csv_to_table(csv_folder / 'extremes_analysis.csv', ExtremesAnalysis)
    
    # Carrega JSONs de cidades
    load_city_reports(cities_folder)
    
    # Carrega metadata global (assuma em summary)
    load_metadata(csv_folder / 'generation_metadata.json')
    
    elapsed_total = time.time() - start_total
    logger.info(f"✅ Carga completa! Tempo total: {elapsed_total:.2f}s. Verifique logs para detalhes.")