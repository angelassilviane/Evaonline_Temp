"""
Script para adicionar elevações ao worldcities.csv.
USA A MESMA LÓGICA DO DOCKER (httpx + Open-Meteo).

Uso:
    python scripts/add_elevation_batch.py --batch 9500
"""
import argparse
import csv
import logging
import time
from datetime import datetime
from pathlib import Path

import httpx

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ElevationDownloader:
    """Downloader de elevações usando Open-Meteo (mesma lógica do Docker)."""
    
    def __init__(self):
        self.url = "https://api.open-meteo.com/v1/elevation"
        self.requests_made = 0
        self.errors = 0
        self.delay_seconds = 0.11  # 9 req/s = 540/min (safe for 600/min)
        
        # Usar httpx.Client (síncrono, igual ao Docker)
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True
        )
    
    def get_elevation(self, lat: float, lon: float, location_name: str = "") -> float:
        """
        Busca elevação usando Open-Meteo API (EXATAMENTE como no Docker).
        
        Returns:
            Elevação em metros (0.0 se erro)
        """
        try:
            # Fazer requisição (mesma lógica do elevation_api.py)
            response = self.client.get(
                self.url,
                params={
                    "latitude": lat,
                    "longitude": lon
                }
            )
            response.raise_for_status()
            
            # Extrair elevação
            data = response.json()
            elevation_list = data.get("elevation", [])
            
            if elevation_list and len(elevation_list) > 0:
                elevation = elevation_list[0]
                
                if elevation is not None:
                    self.requests_made += 1
                    
                    # Rate limiting
                    time.sleep(self.delay_seconds)
                    
                    return float(elevation)
            
            logger.warning(f"⚠️ Sem dados de elevação para {location_name}")
            self.errors += 1
            return 0.0
            
        except httpx.TimeoutException:
            logger.error(f"❌ Timeout: {location_name}")
            self.errors += 1
            return 0.0
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP Error {e.response.status_code}: {location_name}")
            self.errors += 1
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ Erro em {location_name}: {e}")
            self.errors += 1
            return 0.0
    
    def close(self):
        """Fechar client HTTP."""
        self.client.close()


def add_elevation_to_csv(
    input_csv: Path,
    output_csv: Path,
    max_cities: int = 9500,
    skip_existing: bool = False
):
    """
    Adiciona coluna 'elevation' ao CSV de cidades.
    
    Args:
        input_csv: Caminho do CSV de entrada (city, lat, lng, country, sigla)
        output_csv: Caminho do CSV de saída (adiciona elevation)
        max_cities: Número máximo de cidades a processar
        skip_existing: Se True, pula cidades já processadas (modo continue)
    """
    downloader = ElevationDownloader()
    
    try:
        logger.info("🚀 Iniciando processamento...")
        logger.info(f"📂 Input: {input_csv}")
        logger.info(f"📁 Output: {output_csv}")
        logger.info(f"📊 Lote: {max_cities} cidades")
        
        # Verificar se output já existe (modo continue)
        existing_cities = set()
        
        if skip_existing and output_csv.exists():
            logger.info("🔄 Modo: Continuar de onde parou")
            logger.info("📂 Carregando cidades já processadas...")
            
            with open(output_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = f"{row['city']}|{row['country']}"
                    existing_cities.add(key)
            
            logger.info(f"✅ {len(existing_cities)} cidades já processadas")
        else:
            logger.info("🆕 Modo: Novo processamento")
        
        # Modo de abertura do output
        output_mode = 'a' if skip_existing and existing_cities else 'w'
        write_header = output_mode == 'w'
        
        start_time = datetime.now()
        processed = 0
        skipped = 0
        
        with open(input_csv, 'r', encoding='utf-8') as f_in, \
             open(output_csv, output_mode, encoding='utf-8', newline='') as f_out:
            
            reader = csv.DictReader(f_in)
            
            # Campos de saída
            fieldnames = ['city', 'lat', 'lng', 'country', 'sigla', 'elevation']
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            
            if write_header:
                writer.writeheader()
            
            for row in reader:
                # Verificar limite de processamento
                if processed >= max_cities:
                    logger.info(f"✋ Limite de {max_cities} cidades atingido")
                    break
                
                city = row['city']
                country = row['country']
                
                # Verificar se já foi processada
                key = f"{city}|{country}"
                if key in existing_cities:
                    skipped += 1
                    continue
                
                # Extrair coordenadas
                try:
                    lat = float(row['lat'])
                    lon = float(row['lng'])
                except (ValueError, KeyError) as e:
                    logger.error(f"❌ Coordenadas inválidas: {city}, {country} - {e}")
                    continue
                
                # Buscar elevação
                elevation = downloader.get_elevation(lat, lon, f"{city}, {country}")
                
                # Escrever linha com elevação
                output_row = {
                    'city': city,
                    'lat': lat,
                    'lng': lon,
                    'country': country,
                    'sigla': row['sigla'],
                    'elevation': elevation
                }
                writer.writerow(output_row)
                
                processed += 1
                
                # Log de progresso a cada 100 cidades
                if processed % 100 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = processed / elapsed if elapsed > 0 else 0
                    eta_seconds = (max_cities - processed) / rate if rate > 0 else 0
                    eta_minutes = eta_seconds / 60
                    
                    logger.info(
                        f"✅ {processed}/{max_cities} ({100*processed/max_cities:.1f}%) "
                        f"| Taxa: {rate:.1f} cidades/s "
                        f"| ETA: {eta_minutes:.1f} min "
                        f"| Requisições: {downloader.requests_made}"
                    )
        
        # Estatísticas finais
        total_time = (datetime.now() - start_time).total_seconds()
        total_minutes = total_time / 60
        
        logger.info("\n" + "="*60)
        logger.info("🎉 PROCESSAMENTO CONCLUÍDO!")
        logger.info("="*60)
        logger.info(f"Cidades processadas: {processed}")
        logger.info(f"Cidades puladas (já existentes): {skipped}")
        logger.info(f"Tempo total: {total_minutes:.1f} minutos")
        
        if total_time > 0:
            avg_rate = processed / total_time
            logger.info(f"Taxa média: {avg_rate:.2f} cidades/segundo")
        
        logger.info("="*60)
        logger.info("\n" + "="*60)
        logger.info("📊 ESTATÍSTICAS")
        logger.info("="*60)
        logger.info(f"Total de requisições: {downloader.requests_made}")
        logger.info(f"Erros: {downloader.errors}")
        logger.info("="*60)
        logger.info(f"\n📁 Output salvo em: {output_csv}")
    
    finally:
        # Garantir que o client seja fechado
        downloader.close()


def check_progress(output_csv: Path, total_cities: int = 48060):
    """Verifica progresso do processamento."""
    
    if not output_csv.exists():
        logger.info("📊 PROGRESSO")
        logger.info("="*60)
        logger.info("Nenhuma cidade processada ainda.")
        logger.info("="*60)
        return
    
    with open(output_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        processed = sum(1 for _ in reader)
    
    percentage = 100 * processed / total_cities
    remaining = total_cities - processed
    
    logger.info("\n" + "="*60)
    logger.info("📊 PROGRESSO")
    logger.info("="*60)
    logger.info(f"Processadas: {processed:,} / {total_cities:,}")
    logger.info(f"Percentual: {percentage:.2f}%")
    logger.info(f"Restantes: {remaining:,}")
    logger.info("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Adicionar elevações ao worldcities.csv (Open-Meteo API)"
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/csv/worldcities.csv',
        help='Caminho do CSV de entrada'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/csv/worldcities_with_elevation.csv',
        help='Caminho do CSV de saída'
    )
    parser.add_argument(
        '--batch',
        type=int,
        default=9500,
        help='Número máximo de cidades a processar (padrão: 9500)'
    )
    parser.add_argument(
        '--continue',
        dest='continue_processing',
        action='store_true',
        help='Continuar de onde parou (pula cidades já processadas)'
    )
    parser.add_argument(
        '--check-progress',
        action='store_true',
        help='Apenas verificar progresso (não processar)'
    )
    
    args = parser.parse_args()
    
    input_csv = Path(args.input)
    output_csv = Path(args.output)
    
    # Verificar progresso
    if args.check_progress:
        check_progress(output_csv)
        return
    
    # Validar input
    if not input_csv.exists():
        logger.error(f"❌ Arquivo não encontrado: {input_csv}")
        return
    
    # Processar
    add_elevation_to_csv(
        input_csv=input_csv,
        output_csv=output_csv,
        max_cities=args.batch,
        skip_existing=args.continue_processing
    )


if __name__ == "__main__":
    main()
