# 📐 ARQUITETURA COMPLETA: Open-Meteo → ETo → PostgreSQL

## 🔄 Fluxo de Dados Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          5 FONTES DE DADOS CLIMÁTICOS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  🌍 NASA POWER (Global)        ☀️ Open-Meteo Archive (Global, 1950+)       │
│     Domínio Público            CC0 - Sem restrições                        │
│     Delay: 2-7 dias            Delay: Nenhum                              │
│                                                                               │
│  🔮 Open-Meteo Forecast (Global)  🇪🇺 MET Norway (Europa)                  │
│     CC0 - Sem restrições          CC-BY 4.0                                │
│     Previsão: 16 dias             Real-time, Alta qualidade               │
│                                                                               │
│  🇺🇸 NWS USA (USA Continental)                                               │
│     Domínio Público                                                         │
│     Real-time, 2x/dia                                                       │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓↓↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 1: DOWNLOAD (backend/api/services/)              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────┐     ┌──────────────────────────┐                     │
│  │ nasa_power_      │     │ openmeteo_client.py      │                     │
│  │ client.py        │     │ ├─ Archive (13 vars)     │                     │
│  │ (321 lines)      │     │ └─ Forecast (13 vars)    │                     │
│  └──────┬───────────┘     └──────────┬───────────────┘                     │
│         │                            │                                      │
│         ▼                            ▼                                      │
│  7 variáveis:                13 variáveis:                                 │
│  T2M_MAX, T2M_MIN           temperature_2m_max/min/mean                   │
│  T2M, RH2M, WS2M            precipitation_sum                              │
│  ALLSKY_SFC_SW_DWN          wind_speed_10m_max/mean                        │
│  PRECTOTCORR                shortwave_radiation_sum                        │
│                              relative_humidity_2m_max/mean/min             │
│                              daylight_duration                              │
│                              sunshine_duration                              │
│                              ✨ et0_fao_evapotranspiration (JÁ CALC)      │
│                                                                               │
│  ┌────────────────────────────────────────────────────────┐                │
│  │ climate_factory.py - Factory Pattern                   │                │
│  │ ├─ create_nasa_power()                                │                │
│  │ ├─ create_openmeteo_archive()                         │                │
│  │ ├─ create_openmeteo_forecast()                        │                │
│  │ ├─ create_met_norway()                                │                │
│  │ └─ create_nws()                                       │                │
│  └────────────────────────────────────────────────────────┘                │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓↓↓
┌─────────────────────────────────────────────────────────────────────────────┐
│         PHASE 2: CACHE (backend/infrastructure/cache/)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────┐                   │
│  │ Redis Cache (climate_data_cache.py)                 │                   │
│  ├─────────────────────────────────────────────────────┤                   │
│  │                                                      │                   │
│  │ Keys:                          TTL:                 │                   │
│  │ climate:nasa_power:{lat}:{lon}:{date}  → 2 dias   │                   │
│  │ climate:openmeteo_archive:{...}        → 30 dias  │                   │
│  │ climate:openmeteo_forecast:{...}       → 6 horas  │                   │
│  │ climate:met_norway:{...}               → 24 horas │                   │
│  │ climate:nws:{...}                      → 12 horas │                   │
│  │ preprocess:{lat}:{lon}:{date}          → 24 horas │                   │
│  │ fusion:{lat}:{lon}:{date}              → 12 horas │                   │
│  │                                                      │                   │
│  └─────────────────────────────────────────────────────┘                   │
│                                                                               │
│  Hit Rate: ~80% para requisições repetidas                                  │
│  Storage: ~100MB para ano inteiro (10 locais)                              │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓↓↓
┌─────────────────────────────────────────────────────────────────────────────┐
│    PHASE 3: PROCESSING (backend/core/data_processing/)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────────────────────────────────────────┐                │
│  │ data_download.py                                       │                │
│  │ ├─ Valida coordenadas e datas                         │                │
│  │ ├─ Faz download de múltiplas fontes                   │                │
│  │ ├─ Verifica cache antes                               │                │
│  │ └─ Normaliza colunas para padrão interno (7 vars)    │                │
│  └────────────────────────────────────────────────────────┘                │
│           ↓                                                                  │
│  ┌────────────────────────────────────────────────────────┐                │
│  │ data_preprocessing.py (updated)                        │                │
│  │ ├─ Valida com limites físicos (Xavier et al)          │                │
│  │ ├─ Detecta outliers (IQR method)                       │                │
│  │ ├─ Imputa dados faltantes (interpolação linear)       │                │
│  │ └─ Suporta múltiplas fontes/formatos                  │                │
│  └────────────────────────────────────────────────────────┘                │
│           ↓                                                                  │
│  ┌────────────────────────────────────────────────────────┐                │
│  │ data_fusion.py (Kalman Ensemble)                       │                │
│  │ ├─ Combina múltiplas fontes                           │                │
│  │ ├─ Ensemble Size: 50                                  │                │
│  │ ├─ Valida licenças ✅ (NASA POWER, MET, NWS)         │                │
│  │ └─ Retorna estado analisado                           │                │
│  └────────────────────────────────────────────────────────┘                │
│                                                                               │
│  Input:   DataFrame 7 colunas (T2M_MAX, T2M_MIN, ...)                      │
│  Output:  DataFrame processado, validado e fusionado                       │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓↓↓
┌─────────────────────────────────────────────────────────────────────────────┐
│     PHASE 4: CALCULATION (backend/core/eto_calculation/)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────────────────────────────────────────┐                │
│  │ eto_calculation.py                                     │                │
│  │ ├─ Implementa FAO-56 Penman-Monteith                  │                │
│  │ ├─ Calcula Ra (radiação extraterrestre)               │                │
│  │ ├─ Calcula pressão de saturação de vapor              │                │
│  │ ├─ Calcula défice de pressão de vapor                 │                │
│  │ ├─ Calcula radiação líquida (Rn)                      │                │
│  │ └─ Retorna ETo (mm/dia)                               │                │
│  └────────────────────────────────────────────────────────┘                │
│                                                                               │
│  Inputs:                          Outputs:                                 │
│  - Dados validados (7 vars)        - ETo calculado (mm/dia)               │
│  - Elevação (m)                    - Intervalo de confiança               │
│  - Latitude (°)                    - Qualidade dos dados                   │
│                                                                               │
│  Validação:                                                                 │
│  ETo_calculated ≈ ET0_openmeteo (para dados Open-Meteo)                    │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓↓↓
┌─────────────────────────────────────────────────────────────────────────────┐
│       PHASE 5: STORAGE (backend/database/)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────┐                                  │
│  │ PostgreSQL (15-alpine)               │                                  │
│  ├──────────────────────────────────────┤                                  │
│  │                                      │                                  │
│  │  📋 locations (337 cidades MATOPIBA) │                                  │
│  │  ├─ id, name, lat, lon, elevation   │                                  │
│  │  └─ state, city, region             │                                  │
│  │                                      │                                  │
│  │  📊 climate_data (histórico)         │                                  │
│  │  ├─ location_id (FK)                 │                                  │
│  │  ├─ date, source                     │                                  │
│  │  ├─ 13 variáveis climáticas         │                                  │
│  │  ├─ et0_fao_evapotranspiration      │                                  │
│  │  └─ quality_flag                     │                                  │
│  │     Índices: (location, date), source │                                 │
│  │     TTL: 1-2 anos de dados           │                                  │
│  │                                      │                                  │
│  │  📈 eto_results (agregado)           │                                  │
│  │  ├─ location_id (FK)                 │                                  │
│  │  ├─ start_date, end_date             │                                  │
│  │  ├─ eto_sum, eto_mean, eto_max      │                                  │
│  │  ├─ estatísticas (std_dev, etc)     │                                  │
│  │  └─ data_quality, method             │                                  │
│  │     Índices: (location, date), period │                                 │
│  │     TTL: 5 anos (histórico)          │                                  │
│  │                                      │                                  │
│  └──────────────────────────────────────┘                                  │
│                                                                               │
│  climate_repository.py (DAL)                                                │
│  ├─ insert_climate_data()                                                   │
│  ├─ insert_eto_result()                                                     │
│  ├─ get_climate_data()                                                      │
│  └─ get_eto_results()                                                       │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓↓↓
┌─────────────────────────────────────────────────────────────────────────────┐
│       PHASE 6: VISUALIZATION (frontend/)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌───────────────────────────────────────────────────────┐                 │
│  │ Dash Dashboard (app.py)                               │                 │
│  ├───────────────────────────────────────────────────────┤                 │
│  │                                                        │                 │
│  │ Mapas:                                                 │                 │
│  │ ├─ Mapa interativo MATOPIBA (337 cidades)            │                 │
│  │ ├─ Heat map de densidade                              │                 │
│  │ └─ Limites de estados (Brasil)                        │                 │
│  │                                                        │                 │
│  │ Gráficos:                                              │                 │
│  │ ├─ ETo vs Temperatura (barras + linhas)              │                 │
│  │ ├─ ETo vs Radiação (dual axis)                       │                 │
│  │ ├─ Precipitação acumulada                             │                 │
│  │ └─ Série temporal com desvio padrão                   │                 │
│  │                                                        │                 │
│  │ Tabelas:                                               │                 │
│  │ ├─ Dados diários (date, temp, humidity, ETo)        │                 │
│  │ ├─ Estatísticas descritivas                           │                 │
│  │ ├─ Teste de normalidade (Shapiro-Wilk)              │                 │
│  │ └─ Matriz de correlação                               │                 │
│  │                                                        │                 │
│  │ Exportação:                                            │                 │
│  │ ├─ CSV                                                 │                 │
│  │ ├─ Excel                                               │                 │
│  │ └─ PDF (relatório)                                    │                 │
│  │                                                        │                 │
│  └───────────────────────────────────────────────────────┘                 │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Tabela Resumida de Fluxos

| Fase | Componente | Input | Output | Cache | Armazenamento |
|------|-----------|-------|--------|-------|---------------|
| 1 | NASA POWER Client | (lat, lon, date) | DataFrame 7 cols | Redis 2d | ❌ |
| 1 | Open-Meteo Client | (lat, lon, date) | DataFrame 13 cols | Redis 30d | ❌ |
| 2 | Cache Manager | DataFrame | DataFrame cached | Redis | - |
| 3 | Preprocessing | DataFrame | Validated/Imputed | Redis 24h | ❌ |
| 3 | Fusion | List[DataFrame] | Merged DataFrame | Redis 12h | ❌ |
| 4 | ETo Calculation | DataFrame | DataFrame + ETo | Redis 24h | PostgreSQL |
| 5 | Repository | DataFrame | Persisted | - | PostgreSQL ✅ |
| 6 | Dashboard | PostgreSQL | Visualization | Memory | Frontend |

---

## 🔗 Dependências Entre Fases

```
FASE 1 (Download)
    ↓
    └─→ FASE 2 (Cache) ✅ CONCLUÍDO
    
        ↓
        └─→ FASE 3 (Preprocessing/Fusion) ⏳ COMEÇANDO
                ↓
                └─→ FASE 4 (ETo Calculation) ⏳ SERÁ ADAPTADO
                        ↓
                        └─→ FASE 5 (PostgreSQL) ⏳ SERÁ CRIADO
                                ↓
                                └─→ FASE 6 (Visualization) ✅ JÁ EXISTE
```

---

## ✅ Checklist de Implementação

### FASE 3
- [ ] Atualizar `data_preprocessing.py` para 13 variáveis
- [ ] Resolver bloqueio de licença em `data_fusion.py`
- [ ] Integrar Open-Meteo em `data_download.py`
- [ ] Testes end-to-end

### FASE 4
- [ ] Criar `climate_data_cache.py`
- [ ] Integrar cache em `data_download.py`
- [ ] Integrar cache em `data_fusion.py`
- [ ] Integrar cache em `eto_calculation.py`

### FASE 5
- [ ] Criar migração Alembic (003_climate_tables.py)
- [ ] Implementar `climate_repository.py`
- [ ] Testar I/O PostgreSQL
- [ ] Integrar salvamento em pipeline

### FASE 6 (Já existe)
- [ ] Atualizar frontend para usar PostgreSQL
- [ ] Adicionar filtros (data, fonte, qualidade)
- [ ] Adicionar exportação

---

## 📚 Arquivos Importantes

**Criados (FASE 1-2):**
- ✅ `backend/api/services/openmeteo_client.py`
- ✅ `backend/api/services/openmeteo_archive_client.py`
- ✅ `backend/api/services/climate_factory.py` (atualizado)

**A Criar/Atualizar (FASE 3-5):**
- ⏳ `backend/core/data_processing/data_preprocessing.py`
- ⏳ `backend/core/data_processing/data_fusion.py`
- ⏳ `backend/core/data_processing/data_download.py`
- ⏳ `backend/infrastructure/cache/climate_data_cache.py`
- ⏳ `backend/database/climate_repository.py`
- ⏳ `alembic/versions/003_create_climate_tables.py`

---

## 🎯 Próximo Passo

**Começar FASE 3:** Atualizar `data_preprocessing.py` para aceitar 13 variáveis do Open-Meteo!
