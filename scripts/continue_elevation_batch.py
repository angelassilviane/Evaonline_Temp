"""
Script para continuar processamento após rate limit.
Pula cidades já processadas e continua de onde parou.

USO: Executar às 19:20 (após 1 hora do início)
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
    """Downloader com tratamento de rate limit."""
    
    def __init__(self):
        self.url = "https://api.open-meteo.com/v1/elevation"
        self.requests_made = 0
        self.errors = 0
        self.rate_limit_errors = 0
        self.delay_seconds = 0.11  # 9 req/s
        
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True
        )
    
    def get_elevation(self, lat: float, lon: float, location_name: str = "") -> float:
        """Busca elevação com tratamento de rate limit."""
        try:
            response = self.client.get(
                self.url,
                params={"latitude": lat, "longitude": lon}
            )
            
            # Tratar rate limit especificamente
            if response.status_code == 429:
                logger.warning(f"⏱️ Rate limit atingido em: {location_name}")
                self.rate_limit_errors += 1
                return 0.0
            
            response.raise_for_status()
            
            data = response.json()
            elevation_list = data.get("elevation", [])
            
            if elevation_list and len(elevation_list) > 0:
                elevation = elevation_list[0]
                
                if elevation is not None:
                    self.requests_made += 1
                    time.sleep(self.delay_seconds)
                    return float(elevation)
            
            logger.warning(f"⚠️ Sem dados: {location_name}")
            self.errors += 1
            return 0.0
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error(f"❌ Rate Limit: {location_name}")
                self.rate_limit_errors += 1
            else:
                logger.error(f"❌ HTTP {e.response.status_code}: {location_name}")
                self.errors += 1
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ Erro em {location_name}: {e}")
            self.errors += 1
            return 0.0
    
    def close(self):
        """Fechar client."""
        self.client.close()


def continue_processing(
    input_csv: Path,
    output_csv: Path,
    max_cities: int = 5000
):
    """Continua processamento após rate limit."""
    
    downloader = ElevationDownloader()
    
    try:
        logger.info("🔄 Continuando processamento após rate limit...")
        logger.info(f"📂 Input: {input_csv}")
        logger.info(f"📁 Output: {output_csv}")
        logger.info(f"📊 Máximo: {max_cities} cidades")
        
        # Carregar cidades já processadas
        processed_cities = {}
        
        with open(output_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row['city']}|{row['country']}"
                processed_cities[key] = float(row['elevation'])
        
        logger.info(f"✅ {len(processed_cities)} cidades já processadas")
        
        # Identificar cidades com elevação = 0.0 (rate limit)
        cities_to_reprocess = {
            k: v for k, v in processed_cities.items() if v == 0.0
        }
        
        logger.info(f"⚠️ {len(cities_to_reprocess)} cidades com elevação zerada (rate limit)")
        
        # Reprocessar todas as linhas
        start_time = datetime.now()
        processed = 0
        updated = 0
        
        # Ler todo o CSV novamente
        temp_data = []
        
        with open(output_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            for row in reader:
                city = row['city']
                country = row['country']
                key = f"{city}|{country}"
                elevation = float(row['elevation'])
                
                # Se elevação é 0.0, tentar buscar novamente
                if elevation == 0.0 and processed < max_cities:
                    try:
                        lat = float(row['lat'])
                        lon = float(row['lng'])
                        
                        new_elevation = downloader.get_elevation(
                            lat, lon, f"{city}, {country}"
                        )
                        
                        if new_elevation > 0.0:
                            row['elevation'] = new_elevation
                            updated += 1
                            logger.info(f"✅ Atualizado: {city}, {country} = {new_elevation}m")
                        
                        processed += 1
                        
                        # Log a cada 100
                        if processed % 100 == 0:
                            elapsed = (datetime.now() - start_time).total_seconds()
                            rate = processed / elapsed if elapsed > 0 else 0
                            eta_seconds = (max_cities - processed) / rate if rate > 0 else 0
                            eta_minutes = eta_seconds / 60
                            
                            logger.info(
                                f"🔄 {processed}/{max_cities} ({100*processed/max_cities:.1f}%) "
                                f"| Taxa: {rate:.1f}/s | ETA: {eta_minutes:.1f} min "
                                f"| Atualizados: {updated}"
                            )
                        
                        # Se atingir rate limit novamente, parar
                        if downloader.rate_limit_errors > 10:
                            logger.warning("⏱️ Rate limit atingido novamente! Parando...")
                            break
                    
                    except (ValueError, KeyError) as e:
                        logger.error(f"❌ Erro em {city}, {country}: {e}")
                
                temp_data.append(row)
        
        # Reescrever arquivo com dados atualizados
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(temp_data)
        
        # Estatísticas
        total_time = (datetime.now() - start_time).total_seconds()
        total_minutes = total_time / 60
        
        logger.info("\n" + "="*60)
        logger.info("🎉 PROCESSAMENTO CONCLUÍDO!")
        logger.info("="*60)
        logger.info(f"Cidades processadas: {processed}")
        logger.info(f"Cidades atualizadas: {updated}")
        logger.info(f"Tempo total: {total_minutes:.1f} minutos")
        logger.info(f"Rate limit errors: {downloader.rate_limit_errors}")
        logger.info("="*60)
    
    finally:
        downloader.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Continuar processamento após rate limit"
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/csv/worldcities.csv',
        help='CSV de entrada'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/csv/worldcities_with_elevation.csv',
        help='CSV de saída (será atualizado)'
    )
    parser.add_argument(
        '--batch',
        type=int,
        default=5000,
        help='Máximo de cidades a processar (padrão: 5000)'
    )
    
    args = parser.parse_args()
    
    input_csv = Path(args.input)
    output_csv = Path(args.output)
    
    if not output_csv.exists():
        logger.error(f"❌ Arquivo não encontrado: {output_csv}")
        exit(1)
    
    continue_processing(
        input_csv=input_csv,
        output_csv=output_csv,
        max_cities=args.batch
    )
