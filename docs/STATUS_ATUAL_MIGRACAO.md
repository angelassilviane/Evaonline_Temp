# 📊 Status Atual da Migração Assíncrona - 14 Out 2025

## ✅ Completado Hoje

### **1. Limpeza de Código Legado**
- ✅ `nasapower.py.deprecated` deletado
- ✅ Pasta `backend/api/services/` organizada
- ✅ `.gitignore` atualizado com seção async migration

### **2. Fase 1: HTTP Clients - 100% COMPLETA** 🎉
- ✅ Todos os clientes HTTP usam `httpx` (async)
- ✅ `openmeteo.py` migrado → `elevation_api.py`
- ✅ API de Elevação atualizada com docs oficiais (Copernicus DEM 90m)
- ✅ 3 imports atualizados
- ✅ Wrapper síncrono temporário criado

**Documentação**: `docs/PHASE1_HTTP_CLIENTS_COMPLETED.md`

---

## 🎯 Próximas Fases - Roadmap

### **Opção A: Continuar Migração Async** (Técnico)

#### **Fase 2: Cache Layer** - 3 dias 🟡 MÉDIO
**Objetivo**: Migrar Redis de síncrono para `aioredis` (async)

**Arquivos alvo**:
1. `backend/infrastructure/cache/celery_tasks.py` (3 Celery tasks)
2. `backend/infrastructure/cache/climate_tasks.py` (3 Celery tasks)

**Passos**:
1. Criar `backend/infrastructure/cache/async_cache.py`
2. Implementar interface async: `get()`, `set()`, `delete()`
3. Migrar tasks gradualmente
4. Benchmarks performance

**Benefícios**:
- Cache não bloqueante
- Melhor performance I/O
- Preparação para Fase 3

---

#### **Fase 3: Data Processing** - 5 dias 🟡 MÉDIO
**Objetivo**: Migrar pipeline de processamento de dados

**Arquivos alvo**:
1. `backend/core/data_processing/data_download.py`
2. `backend/core/data_processing/data_fusion.py`
3. `backend/core/data_processing/data_preprocessing.py`

**Mudança principal**:
```python
# ANTES
@shared_task
def download_weather_data(...):
    adapter = NASAPowerSyncAdapter()  # Usa bridge
    data = adapter.get_daily_data_sync(...)

# DEPOIS
async def download_weather_data_async(...):
    client = NASAPowerClient()  # Direto, sem adapter!
    data = await client.get_daily_data(...)
```

**Benefícios**:
- Remover `nasa_power_sync_adapter.py` (não precisa mais!)
- Pipeline 100% async
- ETo calculations mais rápidos

---

#### **Fase 4: Database** - 7 dias 🔴 DIFÍCIL
**Objetivo**: Migrar de `psycopg2` (sync) para `asyncpg` (async)

**Impacto**: ALTO (toda leitura/escrita DB)

**Passos**:
1. Instalar `asyncpg`
2. Criar `backend/database/async_connection.py`
3. Migrar queries gradualmente
4. Testar cada endpoint

---

#### **Fase 5: Celery → FastAPI/Dramatiq** - 7 dias 🔴 DIFÍCIL
**Objetivo**: Substituir Celery por solução async

**Opção A: FastAPI BackgroundTasks** (simples)
```python
@router.post("/eto/calculate")
async def calculate_eto(background_tasks: BackgroundTasks):
    background_tasks.add_task(download_weather_data_async, ...)
    return {"status": "processing"}
```

**Opção B: Dramatiq** (avançado)
- Retry automático
- Dead letter queue
- Priorização de tasks

---

### **Opção B: Completar Mapa Mundial** (Funcionalidade)

#### **Passo 4: Seleção Geográfica** - 1 dia 🟢 FÁCIL
**Objetivo**: Detectar fontes disponíveis por localização

**Arquivo principal**:
- `backend/api/services/climate_source_manager.py`

**Implementar**:
```python
def get_available_sources_for_location(
    self,
    lat: float,
    lon: float,
    exclude_non_commercial: bool = True
) -> Dict[str, Dict]:
    """
    Retorna fontes climáticas disponíveis para coordenadas.
    
    Lógica:
    1. Verifica bbox de cada fonte (NASA POWER, MET Norway, NWS)
    2. Filtra por licença (se exclude_non_commercial)
    3. Retorna dict com metadata de cada fonte disponível
    """
    available = {}
    
    # NASA POWER (global)
    available["nasa_power"] = {
        "name": "NASA POWER",
        "coverage": "Global",
        "license": "Public Domain"
    }
    
    # MET Norway (Europa: -25 a 45°E, 35 a 72°N)
    if self._is_point_covered(lat, lon, met_norway_bbox):
        available["met_norway"] = {...}
    
    # NWS (USA: -125 a -66°W, 24 a 49°N)
    if self._is_point_covered(lat, lon, nws_bbox):
        available["nws"] = {...}
    
    return available
```

**Frontend callbacks**:
1. `detect_available_sources` - Trigger no click do mapa
2. `render_climate_source_selector` - Atualiza checkboxes

**Testes**:
- Paris (48.86, 2.35): NASA POWER + MET Norway
- Brasília (-15.79, -47.88): NASA POWER only
- New York (40.71, -74.01): NASA POWER + NWS

**Benefícios**:
- ✅ Funcionalidade visível ao usuário
- ✅ Completa objetivo do Passo 4 (mapa mundial)
- ✅ Rápido (1 dia)

---

## 💡 Recomendação

### **Estratégia Híbrida: Fazer Ambas!**

#### **Esta Semana** (2-3 dias):
1. **Dia 1**: Implementar Seleção Geográfica (Opção B)
   - Backend: `get_available_sources_for_location()`
   - Frontend: callbacks de detecção
   - Testes com 3 localizações

2. **Dia 2-3**: Iniciar Fase 2 (Cache Layer)
   - Criar `async_cache.py`
   - Migrar 2-3 tasks simples
   - Testes de performance

#### **Próxima Semana** (5 dias):
3. **Dia 4-6**: Completar Fase 2 (Cache Layer)
4. **Dia 7-8**: Iniciar Fase 3 (Data Processing)

#### **Resultado**:
✅ Mapa mundial funcionando (objetivo original)  
✅ Migração async progredindo (objetivo técnico)  
✅ Entregas incrementais (valor contínuo)

---

## 📋 Decisão Necessária

**O que você prefere fazer AGORA?**

### **A) Seleção Geográfica** (1 dia, funcionalidade visível) 🗺️
```
✅ Completa Passo 4
✅ Usuário vê resultado imediato
✅ Rápido e baixo risco
```

### **B) Fase 2: Cache Layer** (3 dias, técnico) 🔧
```
✅ Continua migração async
✅ Melhora performance
✅ Preparação para Fase 3
```

### **C) Ambas em Paralelo** (2-3 dias) 🚀
```
✅ Melhor de ambos os mundos
✅ Entregas incrementais
✅ Progresso visível + técnico
```

---

## 📊 Métricas de Progresso

### **Migração Async**

| Fase | Status | Tempo | Progresso |
|------|--------|-------|-----------|
| Fase 1: HTTP Clients | ✅ Completa | <1 dia | **100%** |
| Fase 2: Cache Layer | ⏳ Pendente | 3 dias | 0% |
| Fase 3: Data Processing | ⏳ Pendente | 5 dias | 0% |
| Fase 4: Database | ⏳ Pendente | 7 dias | 0% |
| Fase 5: Celery → FastAPI | ⏳ Pendente | 7 dias | 0% |
| Fase 6: Cleanup | ⏳ Pendente | 2 dias | 0% |

**Total**: 14% completo (1/7 fases)

### **Mapa Mundial**

| Passo | Status | Progresso |
|-------|--------|-----------|
| 1. Infraestrutura | ✅ Completa | **100%** |
| 2. Docker Rebuild | ✅ Completa | **100%** |
| 3. Type Hints | ✅ Completa | **100%** |
| 4. Seleção Geográfica | ⏳ Pendente | 0% |

**Total**: 75% completo (3/4 passos)

---

## 🎯 Próxima Ação

**Aguardando sua decisão**:
- [ ] A) Seleção Geográfica (completar mapa mundial)
- [ ] B) Fase 2: Cache Layer (continuar async)
- [ ] C) Ambas em paralelo (recomendado)

**Estou pronto para começar quando você decidir!** 🚀

