# 🚀 PLANO DE AÇÃO - FASES 3, 4 e 5

## FASE 3: Processar e Fusionar Dados ✅ IN-PROGRESS

### 3.1 Corrigir Licença Open-Meteo em `data_fusion.py` ⚠️ CRÍTICO
**Status**: BLOQUEADOR encontrado
**Problema**: Arquivo `data_fusion.py` linhas 47-72 bloqueia Open-Meteo com "CC-BY-NC 4.0"
**Realidade**: Open-Meteo é CC BY 4.0 (SEM restrição não-comercial) + AGPLv3 compatível

**Ação**:
1. Remover bloqueio de Open-Meteo do `data_fusion.py`
2. Adicionar validação de **atribuição obrigatória** (CC BY 4.0)
3. Documentar compatibilidade com AGPLv3

**Arquivos a atualizar**:
- `backend/core/data_processing/data_fusion.py` (remover bloqueio Open-Meteo)
- `backend/core/data_processing/data_download.py` (adicionar suporte Open-Meteo)
- `backend/core/data_processing/data_preprocessing.py` (adaptarocolunas)

---

### 3.2 Atualizar `data_download.py` para Open-Meteo
**Status**: Pendente
**Objetivo**: Integrar clientes Open-Meteo no download

**Mudanças**:
```python
# Adicionar imports
from backend.api.services.openmeteo_client import (
    OpenMeteoArchiveClient,
    OpenMeteoForecastClient,
)
from backend.api.services.climate_factory import ClimateClientFactory

# Expandir valid_sources
valid_sources = [
    "nasa_power",
    "openmeteo_archive",      # NEW
    "openmeteo_forecast",     # NEW
    "met_norway",             # NEW
    "nws",                    # NEW
    "data fusion",
]

# Adicionar lógica para cada fonte
if source.lower() == "openmeteo_archive":
    client = ClimateClientFactory.create_openmeteo_archive()
    df = client.get_daily_data(lat, lon, start_date, end_date)
    
if source.lower() == "openmeteo_forecast":
    client = ClimateClientFactory.create_openmeteo_forecast()
    df = client.get_daily_forecast(lat, lon, days=...)
```

---

### 3.3 Atualizar `data_preprocessing.py` para 13 Variáveis ETo
**Status**: Pendente
**Objetivo**: Expandir validação para as 13 variáveis do Open-Meteo

**Mapeamento de Colunas**:

| Open-Meteo | Legacy (NASA) | ETo Uso |
|-----------|--------------|---------|
| `temperature_2m_max` | `T2M_MAX` | ✓ Temperatura máxima |
| `temperature_2m_min` | `T2M_MIN` | ✓ Temperatura mínima |
| `temperature_2m_mean` | `T2M` | ✓ Temperatura média |
| `precipitation_sum` | `PRECTOTCORR` | ✓ Precipitação |
| `wind_speed_10m_max` | `WS2M_MAX` | ✓ Vento máximo |
| `wind_speed_10m_mean` | `WS2M` | ✓ Vento médio |
| `shortwave_radiation_sum` | `ALLSKY_SFC_SW_DWN` | ✓ Radiação solar |
| `relative_humidity_2m_max` | `RH2M_MAX` | ✓ Umidade máxima |
| `relative_humidity_2m_mean` | `RH2M` | ✓ Umidade média |
| `relative_humidity_2m_min` | `RH2M_MIN` | ✓ Umidade mínima |
| `daylight_duration` | - | ✓ Duração dia |
| `sunshine_duration` | - | ✓ Duração sol |
| `et0_fao_evapotranspiration` | - | ✓ **ETo pronto** |

**Mudanças**:
1. Normalizar nomes de colunas ao carregar dados
2. Adicionar validação para 13 variáveis
3. Manter compatibilidade com dados legados (NASA)

---

### 3.4 Criar/Atualizar `data_fusion.py` com 5 Fontes
**Status**: Pendente
**Objetivo**: Fusionar dados de múltiplas fontes com qualidade

**Estratégia de Fusão**:
1. **Prioridade por fonte** (em ordem):
   - Open-Meteo Archive (30+ anos, confiável)
   - NASA POWER (42+ anos, global)
   - MET Norway (Europa, alta resolução)
   - NWS (USA, tempo real)
   - Open-Meteo Forecast (16 dias à frente)

2. **Kalman Ensemble Filter**:
   - Combinar múltiplas fontes
   - Tratar missing values (KNN imputer)
   - Correção de bias entre fontes

3. **Quality Assurance**:
   - Validar ranges físicos
   - Detectar outliers
   - Documentar origem dos dados

---

### 3.5 Integrar com `eto_calculation.py`
**Status**: Pendente
**Objetivo**: ETo calculation recebe dados fusionados

**Fluxo**:
```
Open-Meteo APIs (5 fontes)
    ↓
data_download.py (carregar dados)
    ↓
data_preprocessing.py (validar 13 variáveis)
    ↓
data_fusion.py (fusionar + Kalman)
    ↓
eto_calculation.py (calcular ETo FAO-56)
    ↓
results (graphs, tables, statistics)
```

---

### 3.6 Adicionar Atribuição CC BY 4.0
**Status**: Pendente
**Objetivo**: Conformidade legal obrigatória

**Implementação**:
1. Adicionar classe `ClimatDataAttribution`
2. Rastrear origem de cada valor
3. Exibir atribuição no frontend:
   - "Weather data by Open-Meteo.com" (CC BY 4.0)
   - "NASA POWER Data (Public Domain)"
   - Etc.

---

### 3.7 Testes End-to-End
**Status**: Pendente
**Objetivo**: Validar fluxo completo

**Testes**:
- ✅ `test_data_download_openmeteo.py` - Baixar dados
- ✅ `test_data_preprocessing_13vars.py` - Validar variáveis
- ✅ `test_data_fusion_5sources.py` - Fusionar dados
- ✅ `test_eto_calculation_integrated.py` - Calcular ETo completo
- ✅ `test_attribution_compliance.py` - Verificar atribuição

---

## FASE 4: Cache em Redis ⏳ NOT STARTED

### 4.1 Criar `climate_data_cache.py`
**Status**: Pendente
**Objetivo**: Cache robusto com Redis para dados climáticos

**Features**:
- Cachear resposta de cada fonte
- TTL específico por tipo:
  - Archive: 30 dias (dados não mudam)
  - Forecast: 6 horas (dados mudam frequentemente)
  - NASA: 2 dias (atualiza a cada 2-7 dias)
  - MET: 24 horas (real-time)
  - NWS: 12 horas (real-time)
  
**Cache Keys**:
```python
# Archive (30d)
cache:climate:archive:lat={lat}:lon={lon}:start={start}:end={end} → TTL=2592000

# Forecast (6h)
cache:climate:forecast:lat={lat}:lon={lon}:days={days} → TTL=21600

# NASA (2d)
cache:climate:nasa:lat={lat}:lon={lon}:start={start}:end={end} → TTL=172800

# Fusion result (12h)
cache:climate:fusion:lat={lat}:lon={lon}:start={start}:end={end} → TTL=43200

# ETo result (7d)
cache:climate:eto:lat={lat}:lon={lon}:start={start}:end={end} → TTL=604800
```

### 4.2 Integrar Cache em `data_download.py`
**Status**: Pendente
**Objetivo**: Reutilizar dados em cache quando possível

**Lógica**:
1. Verificar cache antes de chamar API
2. Se miss: buscar da API
3. Se hit: retornar do cache (+ log)
4. Salvar resposta no cache

### 4.3 Integrar Cache em `data_fusion.py`
**Status**: Pendente
**Objetivo**: Cachear resultado de fusão

### 4.4 Integrar Cache em `eto_calculation.py`
**Status**: Pendente
**Objetivo**: Cachear cálculo de ETo

---

## FASE 5: Armazenamento PostgreSQL ⏳ NOT STARTED

### 5.1 Criar Schema PostgreSQL
**Status**: Pendente
**Objetivo**: Tabelas persistentes para histórico

**Tabelas**:

#### `climate_data`
```sql
CREATE TABLE climate_data (
    id BIGSERIAL PRIMARY KEY,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    date DATE NOT NULL,
    
    -- Fonte
    source VARCHAR(50) NOT NULL,  -- 'openmeteo_archive', 'nasa_power', etc
    
    -- 13 Variáveis ETo
    temperature_2m_max FLOAT,
    temperature_2m_min FLOAT,
    temperature_2m_mean FLOAT,
    precipitation_sum FLOAT,
    wind_speed_10m_max FLOAT,
    wind_speed_10m_mean FLOAT,
    shortwave_radiation_sum FLOAT,
    relative_humidity_2m_max FLOAT,
    relative_humidity_2m_mean FLOAT,
    relative_humidity_2m_min FLOAT,
    daylight_duration FLOAT,
    sunshine_duration FLOAT,
    et0_fao_evapotranspiration FLOAT,
    
    -- Quality
    quality_flag VARCHAR(20) DEFAULT 'good',  -- 'good', 'interpolated', 'gap_filled'
    data_confidence FLOAT,  -- 0-100%
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    
    CONSTRAINT unique_location_date_source UNIQUE (latitude, longitude, date, source),
    CONSTRAINT valid_latitude CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT valid_longitude CHECK (longitude >= -180 AND longitude <= 180),
);

CREATE INDEX idx_climate_location_date ON climate_data(latitude, longitude, date);
CREATE INDEX idx_climate_source ON climate_data(source);
CREATE INDEX idx_climate_date ON climate_data(date);
```

#### `eto_results`
```sql
CREATE TABLE eto_results (
    id BIGSERIAL PRIMARY KEY,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    date DATE NOT NULL,
    
    -- Dados de entrada
    climate_data_sources JSONB,  -- ['openmeteo_archive', 'nasa_power']
    
    -- ETo calculado
    eto_fao56 FLOAT NOT NULL,  -- mm/day
    eto_method VARCHAR(50),  -- 'fao56', 'hargreaves', etc
    
    -- Componentes
    radiation_component FLOAT,
    aerodynamic_component FLOAT,
    
    -- Quality
    model_confidence FLOAT,  -- 0-100%
    data_gaps_filled INTEGER,  -- número de valores interpolados
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    
    CONSTRAINT unique_location_date_eto UNIQUE (latitude, longitude, date),
    CONSTRAINT valid_latitude CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT valid_longitude CHECK (longitude >= -180 AND longitude <= 180),
);

CREATE INDEX idx_eto_location_date ON eto_results(latitude, longitude, date);
CREATE INDEX idx_eto_date ON eto_results(date);
```

### 5.2 Criar Migração Alembic
**Status**: Pendente
**Objetivo**: Versionamento do schema

**Arquivo**: `alembic/versions/003_create_climate_tables.py`

### 5.3 Implementar `climate_repository.py` (DAL)
**Status**: Pendente
**Objetivo**: Camada de acesso a dados

```python
class ClimateRepository:
    def save_climate_data(self, df: pd.DataFrame, source: str):
        """Salva dados climáticos no PostgreSQL"""
        
    def get_climate_data(self, lat, lon, start_date, end_date) -> pd.DataFrame:
        """Busca dados climáticos do PostgreSQL"""
        
    def save_eto_results(self, df: pd.DataFrame):
        """Salva resultados de ETo"""
        
    def get_eto_results(self, lat, lon, start_date, end_date) -> pd.DataFrame:
        """Busca resultados de ETo"""
```

### 5.4 Testes PostgreSQL
**Status**: Pendente
**Objetivo**: Validar I/O de dados

---

## 📋 Checklist de Implementação

### FASE 3
- [ ] Remover bloqueio Open-Meteo de `data_fusion.py`
- [ ] Adicionar suporte Open-Meteo em `data_download.py`
- [ ] Expandir validação de 13 variáveis em `data_preprocessing.py`
- [ ] Integrar Kalman Ensemble com 5 fontes
- [ ] Adicionar rastreamento de atribuição
- [ ] Testes E2E passando

### FASE 4
- [ ] `climate_data_cache.py` implementado
- [ ] Cache integrado em `data_download.py`
- [ ] Cache integrado em `data_fusion.py`
- [ ] Cache integrado em `eto_calculation.py`
- [ ] Redis funcionando com TTL correto

### FASE 5
- [ ] Schema PostgreSQL criado
- [ ] Migração Alembic (003)
- [ ] `climate_repository.py` implementado
- [ ] Testes de I/O passando
- [ ] Dados persistindo corretamente

---

## 🎯 Prioridade

**CRÍTICO** (Bloqueia tudo):
1. Remover bloqueio Open-Meteo (data_fusion.py)
2. Atualizar data_download.py (suporte Open-Meteo)
3. Validação de 13 variáveis (data_preprocessing.py)

**HIGH**:
4. Fusão com 5 fontes
5. Testes E2E

**MEDIUM**:
6. Cache Redis
7. PostgreSQL storage

---

## 📞 Coordenação com Componentes Existentes

✅ **Clientes de API**: Prontos (openmeteo_client.py, climate_factory.py)
✅ **ETo Calculation**: Pronto (eto_calculation.py)
✅ **Results**: Prontos (graphs, tables, statistics)
⏳ **Data Pipeline**: FASE 3 vai integrar tudo

---

**Próximo passo**: Começar com 3.1 - Remover bloqueio Open-Meteo!
