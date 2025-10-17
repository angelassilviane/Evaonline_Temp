# Plano: Base de Dados Mundial de Localizações para ETo em Tempo Real

## 🎯 Objetivo Corrigido

Criar uma base de dados persistente (PostgreSQL) com localizações das principais cidades do mundo contendo:
- ✅ **Latitude** (float)
- ✅ **Longitude** (float)
- ✅ **Elevação** (float, em metros)
- ✅ **Timezone** (string, ex: "GMT+9.0")
- ✅ **Data Source** (string, ex: "Data Fusion", "NASA POWER")

**ETo é calculado em tempo real** (não armazenado) usando:
- Dados climáticos atuais (APIs: NASA POWER, MET Norway, NWS USA)
- Fusão de dados quando múltiplas fontes disponíveis
- Localização (lat, lon, elevação) do PostgreSQL

**Resultado**: 
- ✅ Reduzir requisições de elevação à Open-Meteo em ~95%
- ✅ ETo sempre disponível no mapa (calculado on-demand)
- ✅ Marcadores visuais com ETo em tempo real

---

## 📊 Estrutura de Dados Simplificada

### Tabela: `world_locations`

```sql
CREATE TABLE world_locations (
    id SERIAL PRIMARY KEY,
    
    -- Identificação
    location_name VARCHAR(255) NOT NULL,  -- "Nagoya, Aichi, JPN"
    city VARCHAR(100),                    -- "Nagoya"
    region VARCHAR(100),                  -- "Aichi"
    country VARCHAR(100) NOT NULL,        -- "Japan"
    country_code CHAR(3) NOT NULL,        -- "JPN"
    
    -- Coordenadas geográficas (dados estáticos)
    latitude FLOAT NOT NULL,              -- 35.2
    longitude FLOAT NOT NULL,             -- 137.0
    
    -- Elevação (dados estáticos - Open-Meteo)
    elevation_m FLOAT NOT NULL,           -- 51.0
    
    -- Timezone (dados estáticos)
    timezone VARCHAR(50),                 -- "GMT+9.0" ou "Asia/Tokyo"
    
    -- Fonte de dados climáticos preferencial
    preferred_climate_source VARCHAR(50), -- "Data Fusion", "NASA POWER", etc.
    
    -- Controle
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices para performance
    CONSTRAINT unique_coordinates UNIQUE (latitude, longitude)
);

-- Índices geoespaciais
CREATE INDEX idx_world_locations_coords ON world_locations (latitude, longitude);
CREATE INDEX idx_world_locations_country ON world_locations (country_code);
```

**⚠️ IMPORTANTE**: 
- **ETo NÃO é armazenado** na tabela
- **ETo é calculado em tempo real** quando o marcador é clicado
- Apenas dados geográficos estáticos são armazenados

---

## 🤖 Script de Coleta Automática de Dados

### Fase 1: Script Python para Baixar Elevações (2-3 dias)

**Objetivo**: Baixar automaticamente lat, lon, elevação das principais cidades do mundo usando Open-Meteo Elevation API.

**Limites Open-Meteo**:
```
✅ 10.000 chamadas/dia
✅ 5.000 chamadas/hora
✅ 600 chamadas/minuto
```

**Estratégia**: Baixar ~5000 cidades em 1 dia com rate limiting inteligente.

#### Script: `scripts/download_world_elevations.py`

```python
"""
Script para baixar elevações das principais cidades do mundo.
Usa Open-Meteo Elevation API com rate limiting respeitando os termos.
"""
import time
import csv
import requests
from typing import List, Dict
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElevationDownloader:
    """
    Baixa elevações de cidades usando Open-Meteo API com rate limiting.
    
    Rate Limits Open-Meteo (não-comercial):
    - 10,000 requests/day
    - 5,000 requests/hour
    - 600 requests/minute
    """
    
    def __init__(self):
        self.api_url = "https://api.open-meteo.com/v1/elevation"
        self.requests_made = 0
        self.requests_limit_per_day = 9500  # Margem de segurança
        self.delay_seconds = 0.15  # 6-7 req/s = 400/min (seguro)
    
    def get_elevation(self, lat: float, lon: float) -> float:
        """
        Busca elevação para coordenadas.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Elevação em metros (float)
        """
        try:
            response = requests.get(
                self.api_url,
                params={"latitude": lat, "longitude": lon},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            elevation = data.get("elevation", [None])[0]
            
            if elevation is None:
                logger.warning(f"No elevation data for {lat}, {lon}")
                return 0.0
            
            self.requests_made += 1
            
            # Rate limiting: aguardar entre requisições
            time.sleep(self.delay_seconds)
            
            return float(elevation)
            
        except Exception as e:
            logger.error(f"Error fetching elevation for {lat}, {lon}: {e}")
            return 0.0
    
    def download_from_cities_list(
        self,
        input_csv: str,
        output_csv: str,
        max_cities: int = 5000
    ):
        """
        Baixa elevações de uma lista de cidades.
        
        Input CSV deve ter colunas: location_name, city, country, country_code, latitude, longitude
        Output CSV terá: todas as colunas acima + elevation_m, timezone
        
        Args:
            input_csv: Caminho do CSV de entrada (sem elevação)
            output_csv: Caminho do CSV de saída (com elevação)
            max_cities: Número máximo de cidades a processar
        """
        processed = 0
        
        with open(input_csv, 'r', encoding='utf-8') as f_in, \
             open(output_csv, 'w', encoding='utf-8', newline='') as f_out:
            
            reader = csv.DictReader(f_in)
            
            # Campos de saída
            fieldnames = reader.fieldnames + ['elevation_m', 'timezone']
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                if processed >= max_cities:
                    logger.info(f"Reached max cities limit: {max_cities}")
                    break
                
                if self.requests_made >= self.requests_limit_per_day:
                    logger.warning("Daily rate limit reached!")
                    break
                
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                
                # Buscar elevação
                elevation = self.get_elevation(lat, lon)
                
                # Adicionar dados
                row['elevation_m'] = elevation
                row['timezone'] = self.estimate_timezone(lon)  # Aproximado
                
                writer.writerow(row)
                processed += 1
                
                if processed % 100 == 0:
                    logger.info(
                        f"✅ Processed {processed} cities "
                        f"({self.requests_made} requests made)"
                    )
        
        logger.info(f"🎉 Done! Processed {processed} cities")
        logger.info(f"📊 Total requests: {self.requests_made}")
    
    def estimate_timezone(self, longitude: float) -> str:
        """
        Estima timezone baseado na longitude (aproximado).
        Para timezone preciso, usar API como timezonefinder.
        
        Args:
            longitude: Longitude (-180 a 180)
            
        Returns:
            Timezone string (ex: "GMT+9.0")
        """
        # Cada 15° de longitude ≈ 1 hora de diferença
        offset_hours = round(longitude / 15)
        
        if offset_hours >= 0:
            return f"GMT+{offset_hours}.0"
        else:
            return f"GMT{offset_hours}.0"


def create_cities_input_csv(output_path: str):
    """
    Cria CSV de entrada com principais cidades do mundo.
    
    Fonte sugerida: 
    - Natural Earth Data: https://www.naturalearthdata.com/downloads/10m-cultural-vectors/
    - SimpleMaps: https://simplemaps.com/data/world-cities (Free version: 41k cities)
    - GeoNames: http://download.geonames.org/export/dump/ (cities15000.txt)
    
    Para este exemplo, vou criar um CSV de amostra.
    """
    sample_cities = [
        {
            "location_name": "Tokyo, Kanto, JPN",
            "city": "Tokyo",
            "region": "Kanto",
            "country": "Japan",
            "country_code": "JPN",
            "latitude": 35.6762,
            "longitude": 139.6503
        },
        {
            "location_name": "New York, NY, USA",
            "city": "New York",
            "region": "New York",
            "country": "United States",
            "country_code": "USA",
            "latitude": 40.7128,
            "longitude": -74.0060
        },
        {
            "location_name": "São Paulo, SP, BRA",
            "city": "São Paulo",
            "region": "São Paulo",
            "country": "Brazil",
            "country_code": "BRA",
            "latitude": -23.5505,
            "longitude": -46.6333
        },
        # Adicionar mais cidades aqui...
    ]
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = [
            "location_name", "city", "region", "country",
            "country_code", "latitude", "longitude"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_cities)
    
    logger.info(f"✅ Created sample cities CSV: {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Download elevations for world cities'
    )
    parser.add_argument(
        '--input',
        default='data/cities_input.csv',
        help='Input CSV with cities (without elevation)'
    )
    parser.add_argument(
        '--output',
        default='data/cities_with_elevation.csv',
        help='Output CSV with cities (with elevation)'
    )
    parser.add_argument(
        '--max-cities',
        type=int,
        default=5000,
        help='Maximum number of cities to process'
    )
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='Create sample input CSV'
    )
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_cities_input_csv(args.input)
    
    downloader = ElevationDownloader()
    downloader.download_from_cities_list(
        args.input,
        args.output,
        args.max_cities
    )
```

**Uso:**

```bash
# 1. Criar CSV de amostra
python scripts/download_world_elevations.py --create-sample

# 2. Baixar elevações (5000 cidades ≈ 12-15 minutos)
python scripts/download_world_elevations.py \
    --input data/cities_input.csv \
    --output data/cities_with_elevation.csv \
    --max-cities 5000

# 3. Importar para PostgreSQL
python backend/database/scripts/import_world_locations.py \
    data/cities_with_elevation.csv
```

**Estimativa de Tempo**:
```
5000 cidades × 0.15s delay = 750 segundos = ~12-15 minutos
```

---

## 🗺️ Fontes de Dados de Cidades (Input)

### Opção 1: SimpleMaps World Cities (Recomendado)
- **URL**: https://simplemaps.com/data/world-cities
- **Versão Free**: 41,000 cidades
- **Dados**: city, country, lat, lon, population
- **Formato**: CSV
- **Licença**: Creative Commons

### Opção 2: GeoNames Cities15000
- **URL**: http://download.geonames.org/export/dump/cities15000.zip
- **Cidades**: ~25,000 (população >15,000)
- **Dados**: name, country, lat, lon, timezone, population
- **Formato**: TXT (tab-separated)
- **Licença**: Creative Commons

### Opção 3: Natural Earth Data
- **URL**: https://www.naturalearthdata.com/downloads/10m-cultural-vectors/
- **Dataset**: Populated Places (10m)
- **Cidades**: ~7,500
- **Formato**: Shapefile/CSV
- **Licença**: Public Domain

**Recomendação**: Usar **SimpleMaps** (41k cidades) ou **GeoNames** (25k).

---

## 📊 Fluxo de ETo em Tempo Real

### Quando Usuário Clica no Marcador:

```python
1. Frontend envia: lat, lon (do marcador)
   ↓
2. Backend busca no PostgreSQL:
   - location_name, elevation_m, timezone, preferred_climate_source
   ↓
3. Backend busca dados climáticos em tempo real:
   - Se preferred_climate_source = "Data Fusion":
     → Chama múltiplas APIs (NASA + MET/NWS)
     → Fusão Kalman Filter
   - Senão:
     → Chama API específica (NASA POWER ou MET ou NWS)
   ↓
4. Backend calcula ETo (Penman-Monteith):
   - Usa: temp, humidity, wind, radiation (APIs)
   - Usa: elevation_m, lat (PostgreSQL)
   ↓
5. Backend retorna JSON:
   {
     "location_name": "Nagoya, Aichi, JPN",
     "latitude": 35.2,
     "longitude": 137.0,
     "elevation_m": 51.0,
     "timezone": "GMT+9.0",
     "data_source": "Data Fusion",
     "eto_mm_day": 4.3,  ← CALCULADO EM TEMPO REAL
     "climate_data": {
       "temperature_c": 25.5,
       "humidity_percent": 65,
       "wind_speed_ms": 2.3,
       ...
     }
   }
   ↓
6. Frontend exibe no popup do marcador
```

**⚠️ IMPORTANTE**: 
- ETo é **recalculado a cada clique**
- Dados climáticos são **sempre atuais** (tempo real)
- Apenas lat, lon, elevação vêm do cache (PostgreSQL)

---

## 🎨 Frontend: Marcadores com ETo em Tempo Real

### Componente: `frontend/components/world_eto_markers.py`

```python
"""
Marcadores de localizações com ETo calculado em tempo real.
"""
import requests
from dash import html
import dash_leaflet as dl


def create_eto_markers():
    """
    Cria marcadores para localizações com ETo em tempo real.
    """
    try:
        # Buscar localizações do PostgreSQL
        response = requests.get(
            "http://localhost:8000/api/locations?limit=5000",
            timeout=5
        )
        locations = response.json()
        
        # Criar marcadores
        markers = []
        for loc in locations:
            marker = dl.Marker(
                id={"type": "eto-marker", "index": loc["id"]},
                position=[loc["latitude"], loc["longitude"]],
                children=[
                    dl.Tooltip(f"{loc['location_name']} - Clique para ver ETo"),
                    dl.Popup(
                        id={"type": "eto-popup", "index": loc["id"]},
                        children=html.Div([
                            html.H6(loc["location_name"]),
                            html.P("Carregando ETo...", id={"type": "eto-content", "index": loc["id"]})
                        ])
                    )
                ],
                icon=dict(
                    iconUrl="/assets/images/marker_eto.png",
                    iconSize=[25, 35]
                )
            )
            markers.append(marker)
        
        return markers
        
    except Exception as e:
        print(f"Error loading ETo markers: {e}")
        return []


# Callback para calcular ETo quando marcador é clicado
@app.callback(
    Output({"type": "eto-content", "index": MATCH}, "children"),
    Input({"type": "eto-marker", "index": MATCH}, "n_clicks"),
    State({"type": "eto-marker", "index": MATCH}, "id"),
    prevent_initial_call=True
)
def calculate_eto_on_click(n_clicks, marker_id):
    """
    Calcula ETo em tempo real quando marcador é clicado.
    """
    if not n_clicks:
        return "Clique para calcular ETo"
    
    location_id = marker_id["index"]
    
    try:
        # Chamar backend para calcular ETo
        response = requests.get(
            f"http://localhost:8000/api/locations/{location_id}/eto",
            timeout=10
        )
        data = response.json()
        
        return html.Div([
            html.P([
                html.Strong("📍 Elevação: "),
                f"{data['elevation_m']}m"
            ]),
            html.P([
                html.Strong("🕒 Timezone: "),
                data['timezone']
            ]),
            html.Hr(),
            html.H5([
                html.Strong("💧 ETo: "),
                f"{data['eto_mm_day']:.2f} mm/dia"
            ], style={"color": "#2d5016"}),
            html.Hr(),
            html.P([
                html.Strong("🌡️ Temperatura: "),
                f"{data['climate_data']['temperature_c']:.1f}°C"
            ], style={"fontSize": "12px"}),
            html.P([
                html.Strong("💨 Vento: "),
                f"{data['climate_data']['wind_speed_ms']:.1f} m/s"
            ], style={"fontSize": "12px"}),
            html.P([
                html.Strong("📊 Fonte: "),
                data['data_source']
            ], style={"fontSize": "11px", "fontStyle": "italic"})
        ])
        
    except Exception as e:
        return html.P(f"❌ Erro ao calcular ETo: {e}", style={"color": "red"})
```

---

## ✅ Cronograma Atualizado

```
Semana 1: Setup e Coleta de Dados
- Dia 1: Criar modelo PostgreSQL (world_locations)
- Dia 2: Preparar CSV de entrada (SimpleMaps/GeoNames)
- Dia 3: Rodar script de download de elevações (5000 cidades)
- Dia 4: Importar dados para PostgreSQL

Semana 2: API Backend
- Dia 1: Endpoint GET /api/locations (listar)
- Dia 2: Endpoint GET /api/locations/{id}/eto (calcular ETo)
- Dia 3: Integrar fusão de dados climáticos

Semana 3: Frontend
- Dia 1-2: Marcadores no mapa
- Dia 3: Callback de clique + cálculo ETo
- Dia 4-5: Testes e ajustes de UX

Total: ~12 dias úteis
```

---

## 🎯 Próximos Passos

1. ✅ **Aprovação do plano** ← Você está aqui
2. Baixar dataset de cidades (SimpleMaps ou GeoNames)
3. Criar modelo PostgreSQL
4. Rodar script de coleta de elevações
5. Implementar backend
6. Integrar frontend

**Quer que eu comece pela Fase 1 (modelo PostgreSQL + script)?** 🚀

