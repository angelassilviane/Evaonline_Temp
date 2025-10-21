# 🔍 AUDITORIA: FASES 3, 4 e 5 - Processamento, Cache e PostgreSQL

## 📍 Estrutura de Pastas Auditada

```
backend/core/
├── data_processing/         ← FASE 3 (Processamento e Fusão)
├── data_results/            ← Resultados (Estatísticas, Tabelas, Gráficos)
├── eto_calculation/         ← Cálculo de ETo
└── map_results/             ← Visualização de Mapas
```

---

## 📊 FASE 3: PROCESSAMENTO E FUSÃO DE DADOS

### 📁 `backend/core/data_processing/`

#### 1️⃣ **data_preprocessing.py** (240 linhas)

**Status: ✅ FUNCIONAL, MAS PRECISA ATUALIZAR PARA OPEN-METEO**

**Funções Principais:**
- `data_initial_validate()` - Valida dados com limites físicos (Xavier et al. 2016, 2022)
- `detect_outliers_iqr()` - Detecção de outliers via IQR
- `data_impute()` - Imputação por interpolação linear
- `preprocessing()` - Pipeline completo (validação → outlier → imputação)

**Colunas Esperadas (NASA POWER):**
```
T2M_MAX, T2M_MIN, T2M, RH2M, WS2M, ALLSKY_SFC_SW_DWN, PRECTOTCORR
```

**⚠️ PROBLEMA IDENTIFICADO:**
- Espera 7 colunas NASA POWER
- **Open-Meteo fornece 13 colunas**, incluindo:
  - `temperature_2m_mean`, `precipitation_sum`, `wind_speed_10m_max`, `wind_speed_10m_mean`
  - `shortwave_radiation_sum`, `relative_humidity_2m_max/mean/min`
  - `daylight_duration`, `sunshine_duration`
  - **`et0_fao_evapotranspiration`** (pré-calculado!)

**Limites de Validação (Física):**
```
T2M_MAX: [-30, 50]°C
T2M_MIN: [-30, 50]°C
T2M: [-30, 50]°C
RH2M: [0, 100]%
WS2M: [0, 100] m/s
PRECTOTCORR: [0, 450] mm
ALLSKY_SFC_SW_DWN: [0.03*Ra, Ra] MJ/m²/dia
```

**Cache Redis:**
- TTL: 24 horas
- Armazena DataFrame serializado com pickle
- Chave: `preprocess_{date_inicio}_{date_fim}_{lat}_{lng}`

---

#### 2️⃣ **data_fusion.py** (250 linhas)

**Status: ⚠️ CRÍTICO - LICENSE VALIDATION BLOQUEADO**

**Validação de Licenças:**
```python
blocked_sources = {
    "openmeteo": "Open-Meteo (CC-BY-NC 4.0)",
    "openmeteo_forecast": "Open-Meteo Forecast (CC-BY-NC 4.0)",
    "openmeteo_archive": "Open-Meteo Archive (CC-BY-NC 4.0)"
}
```

❌ **BLOQUEADO: Open-Meteo com CC-BY-NC 4.0 (não-comercial)**

**Licenças Permitidas:**
- ✅ NASA POWER (Domínio Público)
- ✅ MET Norway (CC-BY 4.0 - comercial)
- ✅ NWS/NOAA (Domínio Público)

**Método de Fusão:**
- Filtro de Kalman Ensemble (ExFKE)
- Ensemble Size: 50
- Inflation Factor: 1.02
- KNNImputer: k=5 vizinhos

**Colunas Requeridas:**
```
T2M_MAX, T2M_MIN, T2M, RH2M, WS2M, ALLSKY_SFC_SW_DWN, PRECTOTCORR
```

**⚠️ DECISÃO NECESSÁRIA:**
1. **REMOVER validação de licença** (se usar Open-Meteo comercialmente)
2. **USAR apenas fontes CC0/CC-BY** para fusão

---

#### 3️⃣ **data_download.py** (300 linhas)

**Status: ✅ FUNCIONAL, ADAPTADO PARA OPENMETEO**

**Fonte de Dados Suportadas:**
- `"nasa_power"` - Dados históricos
- `"data fusion"` - Fusão de múltiplas fontes

**Validações:**
- Coordenadas: -90 ≤ lat ≤ 90, -180 ≤ lon ≤ 180
- Data: formato YYYY-MM-DD
- Período: 1-366 dias
- Data futura não permitida para dados históricos

**Retorna:**
```
DataFrame com 7 colunas:
T2M_MAX, T2M_MIN, T2M, RH2M, WS2M, ALLSKY_SFC_SW_DWN, PRECTOTCORR
```

**Usa:**
- `NASAPowerSyncAdapter()` - Novo cliente síncrono
- Converte records para DataFrame

---

### 🔄 Pipeline Atual (data_download → preprocessing → eto_calculation)

```
Open-Meteo (13 vars)
    ↓
data_download() → Converte para 7 vars (T2M, RH2M, WS2M, etc)
    ↓
preprocessing() → Validação + Outliers + Imputação
    ↓
eto_calculation() → Calcula ETo com 7 vars
    ↓
Resultado: DataFrame com ETo calculada
```

---

## 🧮 FASE 4: CACHE EM REDIS

### 📊 Status Atual

**Implementado em:**
- ✅ `data_preprocessing.py` - Cache para dados pré-processados
  - TTL: 24 horas
  - Serialização: pickle
  - Chave: `preprocess_{start}_{end}_{lat}_{lng}`

**Não Implementado:**
- ❌ `data_fusion.py` - Sem cache
- ❌ `eto_calculation.py` - Sem cache
- ❌ Open-Meteo Archive/Forecast - Cache local requests_cache (não Redis)

### 💾 Estratégia de Cache Proposta

| Fonte | TTL | Tipo | Razão |
|-------|-----|------|-------|
| NASA POWER | 2 dias | Redis | Histórico, mudanças raras |
| Open-Meteo Archive | 30 dias | Redis | Histórico (1950+), não muda |
| Open-Meteo Forecast | 6 horas | Redis | Previsão, muda frequentemente |
| MET Norway | 24 horas | Redis | Previsão, real-time |
| NWS USA | 12 horas | Redis | Previsão, atualiza 2x/dia |
| Pré-processados | 24 horas | Redis | Dados validados |
| Fusão | 12 horas | Redis | Dados combinados |

### 📝 Chaves Redis Propostas

```
# Dados brutos
climate:nasa_power:{lat}:{lng}:{start_date}:{end_date}
climate:openmeteo_archive:{lat}:{lng}:{start_date}:{end_date}
climate:openmeteo_forecast:{lat}:{lng}:{days}
climate:met_norway:{lat}:{lng}:{start_date}:{end_date}
climate:nws:{lat}:{lng}:{start_date}:{end_date}

# Dados processados
preprocess:{lat}:{lng}:{start_date}:{end_date}
fusion:{lat}:{lng}:{start_date}:{end_date}:fusion_{n_sources}

# Metadados
climate:metadata:{source}:{timestamp}
```

---

## 💾 FASE 5: ARMAZENAMENTO POSTGRESQL

### 📋 Tabelas Necessárias

#### 1. **climate_data** - Dados meteorológicos

```sql
CREATE TABLE climate_data (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL,          -- FK para locations
    date DATE NOT NULL,
    source VARCHAR(50) NOT NULL,           -- nasa_power, openmeteo_archive, etc
    
    -- Variáveis climáticas (13 do Open-Meteo)
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
    
    -- ET0 calculada
    et0_fao_evapotranspiration FLOAT,
    
    -- Metadados
    quality_flag VARCHAR(20),              -- 'good', 'fair', 'poor'
    data_source VARCHAR(100),              -- NASA POWER v2.1, Open-Meteo Archive, etc
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(location_id, date, source)
);

-- Índices
CREATE INDEX idx_climate_location_date ON climate_data(location_id, date);
CREATE INDEX idx_climate_source ON climate_data(source);
CREATE INDEX idx_climate_created ON climate_data(created_at);
```

#### 2. **eto_results** - Resultados de ETo

```sql
CREATE TABLE eto_results (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL,          -- FK para locations
    calculation_date DATE NOT NULL,
    
    -- Período de análise
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    period_days INTEGER,
    
    -- Resultados
    eto_sum FLOAT,                         -- ETo acumulada no período
    eto_mean FLOAT,                        -- ETo média
    eto_max FLOAT,                         -- ETo máxima
    eto_min FLOAT,                         -- ETo mínima
    eto_std_dev FLOAT,                     -- Desvio padrão
    
    -- Variáveis
    temp_mean FLOAT,
    humidity_mean FLOAT,
    wind_speed_mean FLOAT,
    radiation_sum FLOAT,
    precipitation_sum FLOAT,
    
    -- Metadados
    method VARCHAR(50),                    -- 'fao56_penman_monteith', etc
    data_sources VARCHAR(200),             -- Lista de fontes usadas
    data_quality VARCHAR(20),              -- 'excellent', 'good', 'fair', 'poor'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(location_id, start_date, end_date)
);

-- Índices
CREATE INDEX idx_eto_location_date ON eto_results(location_id, calculation_date);
CREATE INDEX idx_eto_period ON eto_results(start_date, end_date);
CREATE INDEX idx_eto_created ON eto_results(created_at);
```

#### 3. **locations** - Coordenadas e metadados

```sql
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    elevation FLOAT,
    state VARCHAR(50),
    city VARCHAR(100),
    region VARCHAR(100),                   -- MATOPIBA, SEMIÁRIDO, etc
    
    -- Cobertura de dados
    data_available_since DATE,
    has_nasa_power BOOLEAN DEFAULT FALSE,
    has_openmeteo BOOLEAN DEFAULT FALSE,
    has_met_norway BOOLEAN DEFAULT FALSE,
    has_nws BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(latitude, longitude)
);

CREATE INDEX idx_location_name ON locations(name);
CREATE INDEX idx_location_coords ON locations(latitude, longitude);
CREATE INDEX idx_location_region ON locations(region);
```

### 📊 Relações entre Tabelas

```
locations (1)
    ↓ (1:N)
climate_data (N)
    
locations (1)
    ↓ (1:N)
eto_results (N)
```

### 🔄 Fluxo de Dados para PostgreSQL

```
Open-Meteo Archive/Forecast
    ↓
openmeteo_client.py
    ↓
DataFrame (13 colunas)
    ↓
data_preprocessing.py
    ↓
climate_data (INSERT/UPDATE)
    ↓
eto_calculation.py
    ↓
eto_results (INSERT/UPDATE)
```

---

## 🎯 Resumo das Ações Necessárias

### FASE 3: Processamento e Fusão

| Ação | Status | Esforço |
|------|--------|---------|
| Adaptar `data_preprocessing.py` para 13 variáveis Open-Meteo | ⏳ Pendente | Baixo |
| Atualizar `data_fusion.py` - resolver questão de licença Open-Meteo | ⏳ Pendente | Médio |
| Integrar Open-Meteo clients em `data_download.py` | ⏳ Pendente | Médio |
| Testes de pré-processamento com dados Open-Meteo | ⏳ Pendente | Médio |

### FASE 4: Cache em Redis

| Ação | Status | Esforço |
|------|--------|---------|
| Criar wrapper Redis para Open-Meteo | ⏳ Pendente | Médio |
| Implementar estratégia de TTL por fonte | ⏳ Pendente | Baixo |
| Integrar cache em `data_fusion.py` | ⏳ Pendente | Baixo |
| Integrar cache em `eto_calculation.py` | ⏳ Pendente | Baixo |
| Testes de cache hit/miss | ⏳ Pendente | Baixo |

### FASE 5: PostgreSQL

| Ação | Status | Esforço |
|------|--------|---------|
| Criar tabelas `climate_data` e `eto_results` | ⏳ Pendente | Baixo |
| Criar tabela `locations` | ⏳ Pendente | Baixo |
| Implementar DAL (Data Access Layer) | ⏳ Pendente | Médio |
| Integrar DAL em `eto_calculation.py` | ⏳ Pendente | Médio |
| Criar índices e constraints | ⏳ Pendente | Baixo |
| Testes de I/O PostgreSQL | ⏳ Pendente | Médio |

---

## 🚀 Próximas Tarefas (Ordem Recomendada)

### 1. **Imediato** (FASE 3)
   - [ ] Atualizar `data_preprocessing.py` para aceitar 13 variáveis
   - [ ] Criar adaptador Open-Meteo para `data_download.py`
   - [ ] Testar pipeline completo com Open-Meteo

### 2. **Curto Prazo** (FASE 4)
   - [ ] Implementar cache Redis com TTL strategy
   - [ ] Criar utilities para serialização/desserialização
   - [ ] Integrar cache em toda pipeline

### 3. **Médio Prazo** (FASE 5)
   - [ ] Criar esquema PostgreSQL
   - [ ] Implementar DAL
   - [ ] Testes de persistência

---

## 📚 Referências

- **FAO-56 Penman-Monteith**: Allen et al. (1998) - Crop evapotranspiration
- **Xavier et al. (2016, 2022)**: Limites físicos para validação
- **Open-Meteo**: https://open-meteo.com/
- **NASA POWER**: https://power.larc.nasa.gov/

