"""
Script para importar localizações mundiais do CSV para PostgreSQL.

Este script lê o arquivo worldcities_with_elevation.csv e importa
os dados para a tabela world_locations no banco de dados PostgreSQL.

Uso:
    python scripts/import_world_locations.py
    python scripts/import_world_locations.py --dry-run  # Apenas mostra preview
"""
import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List

# Adiciona o diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.database.connection import Base
from backend.database.models.world_locations import WorldLocation

# Configuração do banco de dados (Docker)
DATABASE_URL = (
    "postgresql://evaonline:123456@localhost:5432/evaonline"
)


def read_csv_file(csv_path: Path) -> List[Dict]:
    """
    Lê arquivo CSV e retorna lista de dicionários.

    Args:
        csv_path: Caminho do arquivo CSV

    Returns:
        List[Dict]: Lista com dados das cidades
    """
    cities = []

    logger.info(f"Lendo arquivo: {csv_path}")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            cities.append({
                'city': row['city'],
                'lat': float(row['lat']),
                'lon': float(row['lng']),  # CSV usa 'lng', DB usa 'lon'
                'country': row['country'],
                'country_code': row['sigla'],
                'elevation': float(row['elevation'])
            })

    logger.info(f"Total de cidades lidas: {len(cities):,}")
    return cities


def create_tables(engine):
    """
    Cria tabelas no banco de dados.

    Args:
        engine: Engine do SQLAlchemy
    """
    logger.info("Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tabelas criadas com sucesso!")


def import_locations(
    cities: List[Dict],
    dry_run: bool = False
) -> None:
    """
    Importa localizações para o banco de dados.

    Args:
        cities: Lista de dicionários com dados das cidades
        dry_run: Se True, apenas mostra preview sem importar
    """
    if dry_run:
        logger.info("\n" + "="*80)
        logger.info("🔍 DRY RUN - Preview dos primeiros 10 registros:")
        logger.info("="*80)

        for i, city in enumerate(cities[:10], 1):
            logger.info(
                f"{i:2d}. {city['city']:25s} | "
                f"{city['country']:20s} | "
                f"({city['lat']:8.4f}, {city['lon']:9.4f}) | "
                f"Elev: {city['elevation']:6.1f}m"
            )

        logger.info("="*80)
        logger.info(f"Total de registros a importar: {len(cities):,}")
        logger.info("="*80)
        logger.info(
            "\n⚠️  Para executar a importação real, "
            "remova o parâmetro --dry-run\n"
        )
        return

    # Conexão com banco de dados
    logger.info("Conectando ao banco de dados...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Criar tabelas se não existirem
        create_tables(engine)

        # Limpar tabela existente
        logger.info("Limpando tabela world_locations...")
        session.query(WorldLocation).delete()
        session.commit()

        # Importar dados
        logger.info(f"Importando {len(cities):,} localizações...")

        batch_size = 500
        total_imported = 0

        for i in range(0, len(cities), batch_size):
            batch = cities[i:i + batch_size]

            locations = [
                WorldLocation(
                    location_name=city['city'],
                    country=city['country'],
                    country_code=city['country_code'],
                    lat=city['lat'],
                    lon=city['lon'],
                    elevation_m=city['elevation']
                )
                for city in batch
            ]

            session.add_all(locations)
            session.commit()

            total_imported += len(batch)
            progress = (total_imported / len(cities)) * 100

            logger.info(
                f"  Progresso: {total_imported:,}/{len(cities):,} "
                f"({progress:.1f}%)"
            )

        logger.info("\n" + "="*80)
        logger.info("✅ IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info("="*80)
        logger.info(f"Total importado: {total_imported:,} localizações")

        # Verificar estatísticas
        total_db = session.query(WorldLocation).count()
        logger.info(f"Total no banco: {total_db:,} registros")

        # Estatísticas de elevação
        logger.info("\n📊 ESTATÍSTICAS DE ELEVAÇÃO:")

        result = session.execute(text("""
            SELECT
                COUNT(*) as total,
                MIN(elevation_m) as min_elev,
                MAX(elevation_m) as max_elev,
                AVG(elevation_m) as avg_elev,
                COUNT(CASE WHEN elevation_m < 0 THEN 1 END) as negativas,
                COUNT(CASE WHEN elevation_m = 0 THEN 1 END) as zero,
                COUNT(CASE WHEN elevation_m > 0 AND elevation_m <= 10
                      THEN 1 END) as baixas,
                COUNT(CASE WHEN elevation_m > 10 AND elevation_m <= 100
                      THEN 1 END) as medias,
                COUNT(CASE WHEN elevation_m > 100 AND elevation_m <= 1000
                      THEN 1 END) as altas,
                COUNT(CASE WHEN elevation_m > 1000 THEN 1 END) as muito_altas
            FROM world_locations
        """))

        stats = result.fetchone()

        logger.info(f"   • Mínima: {stats.min_elev:.1f}m")
        logger.info(f"   • Máxima: {stats.max_elev:.1f}m")
        logger.info(f"   • Média: {stats.avg_elev:.1f}m")
        logger.info(f"\n📈 DISTRIBUIÇÃO:")
        logger.info(
            f"   • Negativas (abaixo do mar): {stats.negativas:,} "
            f"({100*stats.negativas/stats.total:.1f}%)"
        )
        logger.info(
            f"   • Nível do mar (0m): {stats.zero:,} "
            f"({100*stats.zero/stats.total:.1f}%)"
        )
        logger.info(
            f"   • Baixas (1-10m): {stats.baixas:,} "
            f"({100*stats.baixas/stats.total:.1f}%)"
        )
        logger.info(
            f"   • Médias (11-100m): {stats.medias:,} "
            f"({100*stats.medias/stats.total:.1f}%)"
        )
        logger.info(
            f"   • Altas (101-1000m): {stats.altas:,} "
            f"({100*stats.altas/stats.total:.1f}%)"
        )
        logger.info(
            f"   • Muito altas (>1000m): {stats.muito_altas:,} "
            f"({100*stats.muito_altas/stats.total:.1f}%)"
        )

        # Top 5 cidades mais altas
        logger.info("\n🏔️  TOP 5 CIDADES MAIS ALTAS:")
        highest = session.query(WorldLocation).order_by(
            WorldLocation.elevation_m.desc()
        ).limit(5).all()

        for i, loc in enumerate(highest, 1):
            logger.info(
                f"   {i}. {loc.location_name:20s} | "
                f"{loc.country:15s} | {loc.elevation_m:6.1f}m"
            )

        # Top 5 cidades mais baixas
        logger.info("\n🌊 TOP 5 CIDADES MAIS BAIXAS:")
        lowest = session.query(WorldLocation).order_by(
            WorldLocation.elevation_m.asc()
        ).limit(5).all()

        for i, loc in enumerate(lowest, 1):
            logger.info(
                f"   {i}. {loc.location_name:20s} | "
                f"{loc.country:15s} | {loc.elevation_m:6.1f}m"
            )

        logger.info("="*80 + "\n")

    except Exception as e:
        logger.error(f"❌ Erro durante importação: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Importa localizações mundiais do CSV para PostgreSQL"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Apenas mostra preview sem importar'
    )
    parser.add_argument(
        '--csv',
        type=str,
        default='data/csv/worldcities_with_elevation.csv',
        help='Caminho do arquivo CSV (default: data/csv/worldcities_with_elevation.csv)'
    )

    args = parser.parse_args()

    # Caminho do CSV
    csv_path = ROOT_DIR / args.csv

    if not csv_path.exists():
        logger.error(f"❌ Arquivo não encontrado: {csv_path}")
        sys.exit(1)

    # Ler CSV
    cities = read_csv_file(csv_path)

    # Importar
    import_locations(cities, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
