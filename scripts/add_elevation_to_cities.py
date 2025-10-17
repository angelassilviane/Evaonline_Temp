"""
Script para adicionar elevações ao worldcities.csv usando Open-Meteo API.

Lê o CSV existente (city, lat, long, country, sigla) e adiciona coluna 'elevation'.
Respeita rate limiting Open-Meteo: 10k/dia, 5k/hora, 600/min.

Uso:
    python scripts/add_elevation_to_cities.py --batch 9500
"""
import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ElevationDownloader:
    """
    Baixa elevações usando Open-Meteo API com rate limiting.
    Fallback para Open-Elevation se Open-Meteo falhar.
    """
    
    def __init__(self):
        # Open-Meteo (Principal)
        self.openmeteo_url = "https://api.open-meteo.com/v1/elevation"
        
        # Open-Elevation (Backup)
        self.openelevation_url = "https://api.open-elevation.com/api/v1/lookup"
        
        # Estatísticas
        self.requests_made = 0
        self.openmeteo_requests = 0
        self.openelevation_requests = 0
        self.errors = 0
        
        # Rate limiting Open-Meteo
        self.delay_seconds = 0.11  # ~9 req/s = 540/min (seguro para 600/min)
        
        # Limites diários
        self.daily_limit = 9500  # Margem de segurança (10k limite)
    
    def get_elevation_openmeteo(
        self,
        lat: float,
        lon: float
    ) -> Optional[float]:
        """
        Busca elevação usando Open-Meteo API com retry.
        
        Returns:
            Elevação em metros ou None se erro
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    self.openmeteo_url,
                    params={"latitude": lat, "longitude": lon},
                    timeout=30  # Aumentado para 30s
                )
                response.raise_for_status()
                
                data = response.json()
                elevation = data.get("elevation", [None])[0]
                
                if elevation is not None:
                    self.openmeteo_requests += 1
                    return float(elevation)
                
                return None
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    logger.warning(f"⏱️ Timeout na tentativa {attempt+1}/{max_retries}, tentando novamente...")
                    time.sleep(2)
                    continue
                logger.error(f"❌ Timeout após {max_retries} tentativas")
                return None
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Erro na tentativa {attempt+1}/{max_retries}: {e}")
                    time.sleep(2)
                    continue
                logger.debug(f"Open-Meteo error for {lat}, {lon}: {e}")
            return None
    
    def get_elevation_openelevation(
        self,
        lat: float,
        lon: float
    ) -> Optional[float]:
        """
        Busca elevação usando Open-Elevation API (backup).
        
        Returns:
            Elevação em metros ou None se erro
        """
        try:
            response = requests.post(
                self.openelevation_url,
                json={"locations": [{"latitude": lat, "longitude": lon}]},
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if results:
                elevation = results[0].get("elevation")
                if elevation is not None:
                    self.openelevation_requests += 1
                    return float(elevation)
            
            return None
            
        except Exception as e:
            logger.debug(f"Open-Elevation error for {lat}, {lon}: {e}")
            return None
    
    def get_elevation(
        self,
        lat: float,
        lon: float,
        city_name: str = ""
    ) -> float:
        """
        Busca elevação com fallback automático.
        
        Tenta Open-Meteo primeiro, depois Open-Elevation se falhar.
        
        Args:
            lat: Latitude
            lon: Longitude
            city_name: Nome da cidade (para logs)
            
        Returns:
            Elevação em metros (0.0 se erro)
        """
        # 1. Tentar Open-Meteo (principal)
        elevation = self.get_elevation_openmeteo(lat, lon)
        
        if elevation is not None:
            self.requests_made += 1
            time.sleep(self.delay_seconds)  # Rate limiting
            return elevation
        
        # 2. Fallback: Open-Elevation
        logger.warning(
            f"Open-Meteo failed for {city_name} ({lat}, {lon}), "
            f"trying Open-Elevation..."
        )
        
        elevation = self.get_elevation_openelevation(lat, lon)
        
        if elevation is not None:
            self.requests_made += 1
            time.sleep(self.delay_seconds)  # Moderação
            return elevation
        
        # 3. Ambas falharam
        self.errors += 1
        logger.error(
            f"❌ Both APIs failed for {city_name} ({lat}, {lon})"
        )
        return 0.0
    
    def print_statistics(self):
        """Imprime estatísticas do processamento."""
        logger.info("\n" + "="*60)
        logger.info("📊 ESTATÍSTICAS DE PROCESSAMENTO")
        logger.info("="*60)
        logger.info(f"Total de requisições: {self.requests_made}")
        logger.info(f"  - Open-Meteo: {self.openmeteo_requests}")
        logger.info(f"  - Open-Elevation: {self.openelevation_requests}")
        logger.info(f"Erros: {self.errors}")
        logger.info("="*60 + "\n")


def add_elevation_to_csv(
    input_csv: str,
    output_csv: str,
    max_cities: int = 9500,
    skip_existing: bool = True
):
    """
    Adiciona coluna 'elevation' ao CSV de cidades.
    
    Args:
        input_csv: Caminho do worldcities.csv original
        output_csv: Caminho do CSV de saída (com elevation)
        max_cities: Número máximo de cidades a processar
        skip_existing: Se True, pula cidades que já têm elevação no output
    """
    downloader = ElevationDownloader()
    processed = 0
    skipped = 0
    
    # Verificar se output já existe (para continuar de onde parou)
    existing_cities = set()
    if skip_existing and Path(output_csv).exists():
        logger.info(f"📂 Output já existe. Carregando cidades já processadas...")
        with open(output_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Criar chave única: "city|country"
                key = f"{row['city']}|{row['country']}"
                existing_cities.add(key)
        logger.info(f"✅ {len(existing_cities)} cidades já processadas")
    
    # Modo de abertura do output
    output_mode = 'a' if skip_existing and existing_cities else 'w'
    write_header = output_mode == 'w'
    
    start_time = datetime.now()
    
    with open(input_csv, 'r', encoding='utf-8') as f_in, \
         open(output_csv, output_mode, encoding='utf-8', newline='') as f_out:
        
        reader = csv.DictReader(f_in)
        
        # Campos de saída (adicionar 'elevation')
        fieldnames = ['city', 'lat', 'lng', 'country', 'sigla', 'elevation']
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        
        if write_header:
            writer.writeheader()
        
        for row in reader:
            # Verificar limite de processamento
            if processed >= max_cities:
                logger.info(f"✋ Limite de {max_cities} cidades atingido")
                break
            
            # Verificar limite diário API
            if downloader.requests_made >= downloader.daily_limit:
                logger.warning(
                    f"⚠️ Limite diário de {downloader.daily_limit} "
                    f"requisições atingido!"
                )
                break
            
            city = row['city']
            country = row['country']
            city_key = f"{city}|{country}"
            
            # Pular se já processada
            if city_key in existing_cities:
                skipped += 1
                continue
            
            # Extrair coordenadas
            try:
                lat = float(row['lat'])
                lon = float(row['lng'])
            except ValueError:
                logger.error(
                    f"❌ Coordenadas inválidas para {city}, {country}"
                )
                continue
            
            # Buscar elevação
            elevation = downloader.get_elevation(lat, lon, f"{city}, {country}")
            
            # Escrever linha com elevação
            output_row = {
                'city': city,
                'lat': lat,
                'lng': lon,
                'country': country,
                'sigla': row.get('sigla', ''),
                'elevation': round(elevation, 1)  # 1 casa decimal
            }
            writer.writerow(output_row)
            
            processed += 1
            
            # Log a cada 100 cidades
            if processed % 100 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = processed / elapsed if elapsed > 0 else 0
                eta_seconds = (max_cities - processed) / rate if rate > 0 else 0
                eta_minutes = eta_seconds / 60
                
                logger.info(
                    f"✅ Processadas: {processed}/{max_cities} "
                    f"({processed/max_cities*100:.1f}%) | "
                    f"Taxa: {rate:.1f} cidades/s | "
                    f"ETA: {eta_minutes:.1f} min | "
                    f"Requisições: {downloader.requests_made}"
                )
    
    # Estatísticas finais
    elapsed_total = (datetime.now() - start_time).total_seconds()
    
    logger.info("\n" + "="*60)
    logger.info("🎉 PROCESSAMENTO CONCLUÍDO!")
    logger.info("="*60)
    logger.info(f"Cidades processadas: {processed}")
    logger.info(f"Cidades puladas (já existentes): {skipped}")
    logger.info(f"Tempo total: {elapsed_total/60:.1f} minutos")
    logger.info(f"Taxa média: {processed/elapsed_total:.2f} cidades/segundo")
    logger.info("="*60 + "\n")
    
    downloader.print_statistics()
    
    logger.info(f"📁 Output salvo em: {output_csv}")


def check_progress(output_csv: str, total_cities: int = 48060):
    """
    Verifica progresso do processamento.
    
    Args:
        output_csv: Caminho do CSV de saída
        total_cities: Total de cidades no input
    """
    if not Path(output_csv).exists():
        logger.info("❌ Arquivo de output não existe ainda")
        return
    
    with open(output_csv, 'r', encoding='utf-8') as f:
        # Contar linhas (excluir cabeçalho)
        processed = sum(1 for _ in f) - 1
    
    percentage = (processed / total_cities) * 100
    remaining = total_cities - processed
    
    logger.info("\n" + "="*60)
    logger.info("📊 PROGRESSO")
    logger.info("="*60)
    logger.info(f"Processadas: {processed:,} / {total_cities:,}")
    logger.info(f"Percentual: {percentage:.2f}%")
    logger.info(f"Restantes: {remaining:,}")
    logger.info("="*60 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Adiciona elevações ao worldcities.csv'
    )
    parser.add_argument(
        '--input',
        default='data/csv/worldcities.csv',
        help='Caminho do CSV de entrada'
    )
    parser.add_argument(
        '--output',
        default='data/csv/worldcities_with_elevation.csv',
        help='Caminho do CSV de saída'
    )
    parser.add_argument(
        '--batch',
        type=int,
        default=9500,
        help='Número de cidades a processar neste lote (default: 9500)'
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
        help='Apenas verificar progresso (não processa)'
    )
    
    args = parser.parse_args()
    
    # Verificar progresso
    if args.check_progress:
        check_progress(args.output)
    else:
        # Processar
        logger.info("🚀 Iniciando processamento...")
        logger.info(f"📂 Input: {args.input}")
        logger.info(f"📁 Output: {args.output}")
        logger.info(f"📊 Lote: {args.batch} cidades")
        
        if args.continue_processing:
            logger.info("♻️ Modo: Continuar processamento")
        else:
            logger.info("🆕 Modo: Novo processamento")
        
        input_path = Path(args.input)
        if not input_path.exists():
            logger.error(f"❌ Arquivo de entrada não encontrado: {args.input}")
            exit(1)
        
        add_elevation_to_csv(
            args.input,
            args.output,
            max_cities=args.batch,
            skip_existing=args.continue_processing
        )
