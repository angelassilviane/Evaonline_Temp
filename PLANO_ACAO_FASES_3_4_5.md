# 🚀 PLANO DE AÇÃO: FASES 3, 4 e 5

## 📋 Visão Geral

```
FASE 3: Adaptação do Pipeline (data_preprocessing.py, data_fusion.py, eto_calculation.py)
   ↓
FASE 4: Cache em Redis com TTL per-source
   ↓
FASE 5: Persistência em PostgreSQL (climate_data, eto_results, locations)
```

---

## 🎯 FASE 3: PROCESSAMENTO E FUSÃO

### ⚠️ PROBLEMA CRÍTICO IDENTIFICADO

**Open-Meteo retorna 13 variáveis:**
```
1. temperature_2m_max
2. temperature_2m_min
3. temperature_2m_mean
4. precipitation_sum
5. wind_speed_10m_max
6. wind_speed_10m_mean
7. shortwave_radiation_sum
8. relative_humidity_2m_max
9. relative_humidity_2m_mean
10. relative_humidity_2m_min
11. daylight_duration
12. sunshine_duration
13. et0_fao_evapotranspiration ← JÁ CALCULADO!
```

**Código atual espera apenas 7 (NASA POWER):**
```python
# data_preprocessing.py (linha ~100)
limits = {
    "T2M_MAX": (-30, 50),
    "T2M_MIN": (-30, 50),
    "T2M": (-30, 50),
    "RH2M": (0, 100),
    "WS2M": (0, 100),
    "PRECTOTCORR": (0, 450),
}
```

### ✅ ESTRATÉGIA: Suporte Multi-Fonte

**Nova estratégia:**
```python
# Mapear diferentes fontes para coluna padrão
SOURCE_MAPPINGS = {
    "nasa_power": {
        "T2M_MAX": "T2M_MAX",
        "temperature_2m_max": "T2M_MAX",
    },
    "openmeteo": {
        "temperature_2m_max": "T2M_MAX",
        "temperature_2m_min": "T2M_MIN",
        "temperature_2m_mean": "T2M",
        "precipitation_sum": "PRECTOTCORR",
        "wind_speed_10m_max": "WS2M_MAX",
        "wind_speed_10m_mean": "WS2M",
        "shortwave_radiation_sum": "ALLSKY_SFC_SW_DWN",
        "relative_humidity_2m_mean": "RH2M",
    }
}
```

### 📝 Tarefas FASE 3

#### T3.1: Atualizar `data_preprocessing.py`
**Objetivo:** Aceitar 13 variáveis do Open-Meteo

**Ações:**
- [ ] Adicionar função `normalize_columns()` para mapear diferentes fontes
- [ ] Expandir limites de validação para incluir novas variáveis
  - `wind_speed_10m_max`: [0, 100] m/s
  - `wind_speed_10m_mean`: [0, 100] m/s
  - `relative_humidity_*`: [0, 100]%
  - `daylight_duration`: [0, 86400] segundos
  - `sunshine_duration`: [0, 86400] segundos
  - `et0_fao_evapotranspiration`: [0, 15] mm/dia
- [ ] Testar com dados Open-Meteo reais
- [ ] Documentar schema esperado

**Exemplo de código:**
```python
def normalize_columns(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Mapeia colunas de diferentes fontes para padrão interno."""
    if source == "openmeteo":
        mapping = {
            "temperature_2m_max": "T2M_MAX",
            "temperature_2m_min": "T2M_MIN",
            "temperature_2m_mean": "T2M",
            # ... etc
        }
        return df.rename(columns=mapping)
    return df
```

---

#### T3.2: Resolver Licença Open-Meteo em `data_fusion.py`
**Objetivo:** Permitir uso de Open-Meteo (ou decidir por alternativa)

**Opção A: Remover Bloqueio** (se usar comercialmente)
```python
# REMOVER:
blocked_sources = {
    "openmeteo": "Open-Meteo (CC-BY-NC 4.0)",
    ...
}

# ADICIONAR:
logger.warning("Open-Meteo CC0 (https://open-meteo.com/) - sem restrições comerciais")
```

**Opção B: Usar Apenas CC0** (mais seguro)
```python
# Usar apenas:
- NASA POWER (domínio público)
- MET Norway (CC-BY 4.0)
- NWS (domínio público)

# Não usar em fusão:
- Open-Meteo (apenas para visualização no mapa)
```

**Decisão:** ⏳ **Qual opção você prefere?**

---

#### T3.3: Integrar Open-Meteo em `data_download.py`
**Objetivo:** Download via Open-Meteo junto com NASA POWER

**Ações:**
- [ ] Adicionar `source="openmeteo_archive"` e `source="openmeteo_forecast"`
- [ ] Integrar `OpenMeteoArchiveClient` e `OpenMeteoForecastClient`
- [ ] Converter DataFrame Open-Meteo para formato interno (7 colunas)
- [ ] Testar download para Brasília

**Código exemplo:**
```python
elif source == "openmeteo_archive":
    client = OpenMeteoArchiveClient()
    df = client.get_daily_data(lat, lon, start_date, end_date)
    # Selecionar 7 colunas principais
    df = df[["T2M_MAX", "T2M_MIN", "T2M", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR"]]
```

---

#### T3.4: Testes End-to-End
**Objetivo:** Pipeline completo funcionando com Open-Meteo

**Testes:**
- [ ] Download Open-Meteo Archive (Brasília, set 2024)
- [ ] Pré-processamento (validação + outliers + imputação)
- [ ] Cálculo ETo
- [ ] Verificar se ETo calculated ≈ ET0 pré-calculado

**Teste de Regressão:**
```python
# Brasília, set 2024
lat, lon = -15.7939, -47.8828
df_archive = client_archive.get_daily_data(lat, lon, 
    start_date=datetime(2024, 9, 1),
    end_date=datetime(2024, 9, 30)
)
# ETo pré-calculado deve estar em coluna "et0_fao_evapotranspiration"
# Nosso cálculo deve ser semelhante
```

---

## 💾 FASE 4: CACHE EM REDIS

### 📊 Estratégia de Cache

**TTL por Fonte:**
```
NASA POWER              → 2 dias (histórico, mudanças raras)
Open-Meteo Archive     → 30 dias (1950+, nunca muda)
Open-Meteo Forecast    → 6 horas (previsão muda frequentemente)
MET Norway             → 24 horas (previsão, real-time)
NWS USA                → 12 horas (previsão, atualiza 2x/dia)
Pré-processados        → 24 horas (dados validados)
Fusão de dados         → 12 horas (dados combinados)
```

### 📝 Tarefas FASE 4

#### T4.1: Criar Wrapper Redis para Dados Climáticos
**Objetivo:** Centralizar cache de dados meteorológicos

**Arquivo:** `backend/infrastructure/cache/climate_data_cache.py`

**Funcionalidades:**
- Cache key generation (source + location + date)
- TTL management per source
- Serialization (JSON para leitura, pickle para performance)
- TTL renewal

**Código esquema:**
```python
class ClimateDataCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttls = {
            "nasa_power": 2 * 24 * 3600,  # 2 dias
            "openmeteo_archive": 30 * 24 * 3600,  # 30 dias
            "openmeteo_forecast": 6 * 3600,  # 6 horas
        }
    
    def get_key(self, source: str, lat: float, lon: float, start: date, end: date) -> str:
        """Gera chave consistente."""
        return f"climate:{source}:{lat:.4f}:{lon:.4f}:{start}:{end}"
    
    def get(self, source: str, lat: float, lon: float, start: date, end: date) -> Optional[pd.DataFrame]:
        """Recupera dados do cache."""
        key = self.get_key(source, lat, lon, start, end)
        data = self.redis.get(key)
        if data:
            return pd.read_json(data)
        return None
    
    def set(self, source: str, lat: float, lon: float, start: date, end: date, df: pd.DataFrame):
        """Armazena dados no cache."""
        key = self.get_key(source, lat, lon, start, end)
        ttl = self.ttls.get(source, 24 * 3600)  # Default: 24h
        self.redis.setex(key, ttl, df.to_json())
```

#### T4.2: Integrar Cache em `data_download.py`
**Objetivo:** Verificar cache antes de download

**Código:**
```python
# No início de download_weather_data()
cache = ClimateDataCache(redis_client)
cached_df = cache.get(data_source, latitude, longitude, 
    pd.to_datetime(data_inicial).date(),
    pd.to_datetime(data_final).date()
)

if cached_df is not None:
    logger.info(f"✅ Cache HIT: {data_source}")
    return cached_df, ["Loaded from cache"]

# ... fazer download ...

# No final
cache.set(data_source, latitude, longitude, start.date(), end.date(), weather_data)
```

#### T4.3: Integrar Cache em `data_fusion.py`
**Objetivo:** Cache para dados fusionados

#### T4.4: Integrar Cache em `eto_calculation.py`
**Objetivo:** Cache para resultados de ETo

---

## 📊 FASE 5: POSTGRESQL

### 📋 Schema de Banco de Dados

**Arquivo:** `alembic/versions/003_create_climate_tables.py` (nova migração)

### 📝 Tarefas FASE 5

#### T5.1: Criar Migração Alembic
**Objetivo:** Adicionar tabelas `climate_data`, `eto_results`, `locations`

**Ações:**
- [ ] Criar arquivo de migração
- [ ] Definir schemas (como em documento anterior)
- [ ] Criar índices
- [ ] Testar migração

#### T5.2: Implementar DAL (Data Access Layer)
**Objetivo:** Interface para I/O de dados

**Arquivo:** `backend/database/climate_repository.py`

**Métodos:**
```python
class ClimateRepository:
    def insert_climate_data(self, location_id, date, source, data_dict) -> int
    def insert_eto_result(self, location_id, period, data_dict) -> int
    def get_climate_data(self, location_id, start_date, end_date, source=None) -> pd.DataFrame
    def get_eto_results(self, location_id, start_date, end_date) -> pd.DataFrame
    def create_location(self, name, lat, lon, elevation, state, city) -> int
```

#### T5.3: Integrar DAL em Pipeline
**Objetivo:** Salvar resultados em PostgreSQL

**Fluxo:**
```
Open-Meteo Download
    ↓ (salva em climate_data)
cache (Redis)
    ↓
preprocessing
    ↓
eto_calculation
    ↓ (salva em eto_results)
visualização
```

#### T5.4: Testes de I/O
**Objetivo:** Validar leitura/escrita

---

## 📊 Timeline Estimada

| Fase | Tarefa | Esforço | Prazo |
|------|--------|---------|-------|
| 3 | T3.1: Atualizar data_preprocessing.py | 2h | Hoje |
| 3 | T3.2: Resolver licença Open-Meteo | 1h | Hoje |
| 3 | T3.3: Integrar Open-Meteo em data_download.py | 2h | Hoje |
| 3 | T3.4: Testes end-to-end | 1h | Hoje |
| 4 | T4.1: Cache wrapper | 2h | Amanhã |
| 4 | T4.2-4.4: Integração cache | 2h | Amanhã |
| 5 | T5.1: Migração Alembic | 1h | Amanhã |
| 5 | T5.2: DAL | 2h | Amanhã |
| 5 | T5.3: Integração DAL | 1h | Amanhã |
| 5 | T5.4: Testes | 1h | Amanhã |
| **Total** | | **15h** | **2-3 dias** |

---

## ❓ Decisões Pendentes

1. **Licença Open-Meteo**: Opção A (remover bloqueio) ou Opção B (não usar em fusão)?
2. **Estratégia de Armazenamento**: Guardar todas as 13 variáveis no PostgreSQL ou apenas 7?
3. **Modo MATOPIBA**: Especificar cidades/regiões ou aceitar qualquer coordenada?

---

## 🎯 Próximo Passo

**Quando pronto, executaremos:**

```bash
# FASE 3
1. Atualizar data_preprocessing.py
2. Resolver licença
3. Integrar Open-Meteo em data_download.py
4. Testar pipeline completo

# FASE 4
5. Criar cache wrapper
6. Integrar em toda pipeline

# FASE 5
7. Criar schema PostgreSQL
8. Implementar DAL
9. Salvar resultados em BD
```

**Qual tarefa você quer começar primeiro?**
