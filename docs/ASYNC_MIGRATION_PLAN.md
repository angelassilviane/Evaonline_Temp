# 🚀 Plano de Migração para Arquitetura Assíncrona

**Data**: 14 de outubro de 2025  
**Status**: 📋 Planejamento  
**Objetivo**: Migrar codebase de síncrono (Celery) para assíncrono puro

---

## 🎯 Visão Geral

### Por que Migrar?

✅ **Performance**: Async não bloqueia threads, melhor para I/O-bound  
✅ **Escalabilidade**: Suporta milhares de conexões simultâneas  
✅ **Modernização**: Stack moderna (httpx, asyncpg, aioredis)  
✅ **Custos**: Menos recursos computacionais  
✅ **Manutenibilidade**: Código mais limpo e testável

### Estado Atual

```
❌ Celery (síncrono) → Redis → PostgreSQL (psycopg2)
❌ requests (bloqueante)
✅ httpx (já em nasa_power_client.py)
⚠️ Adapter bridge (nasa_power_sync_adapter.py)
```

### Estado Desejado

```
✅ FastAPI (async/await nativo)
✅ httpx (non-blocking HTTP)
✅ asyncpg (async PostgreSQL)
✅ aioredis (async Redis)
✅ Background tasks (FastAPI nativo ou Dramatiq)
```

---

## 📊 Análise de Complexidade

### 🟢 FÁCIL - Migração Rápida (1-2 dias)

#### 1. **Clientes HTTP Externos** ✅ **PRIORIDADE ALTA**
- ✅ `nasa_power_client.py` - Já async!
- ⚠️ `met_norway_client.py` - Verificar se usa requests
- ⚠️ `nws_client.py` - Verificar se usa requests
- ⚠️ `openmeteo.py` - Verificar get_openmeteo_elevation()

**Ação**: Converter requests → httpx async

**Benefício**: Requisições HTTP não bloqueiam mais

---

### 🟡 MÉDIO - Migração Cuidadosa (3-5 dias)

#### 2. **Camada de Cache** ⚠️ **CRÍTICO**
- ❌ `backend/infrastructure/cache/celery_tasks.py` - 3 Celery tasks
- ❌ `backend/infrastructure/cache/climate_tasks.py` - 3 Celery tasks
- ✅ Redis client pode usar `aioredis`

**Desafio**: Cache é usado por toda aplicação

**Estratégia**:
1. Criar `async_cache.py` com aioredis
2. Manter `celery_tasks.py` temporariamente (bridge)
3. Migrar consumidores gradualmente
4. Deprecar Celery tasks após 100% migrado

#### 3. **Data Processing** ⚠️ **CORE BUSINESS**
- ❌ `backend/core/data_processing/data_download.py` - @shared_task
- ❌ `backend/core/data_processing/data_fusion.py` - Pode ter Celery
- ❌ `backend/core/data_processing/data_preprocessing.py` - Pode ter Celery

**Desafio**: ETo calculations dependem desses módulos

**Estratégia**:
1. Converter funções para async
2. Usar `nasa_power_client.py` diretamente (remover adapter)
3. Testar com dados reais (44 dias validados)
4. Manter interface síncrona via FastAPI BackgroundTasks

---

### 🔴 DIFÍCIL - Migração Complexa (1-2 semanas)

#### 4. **PostgreSQL Connection** 🔥 **INFRAESTRUTURA**
- ❌ Usa `psycopg2` (síncrono)
- ✅ Migrar para `asyncpg` (async nativo)

**Desafio**: Toda leitura/escrita DB afetada

**Arquivos afetados**:
```
backend/database/connection.py
backend/api/routes/*.py (queries)
backend/core/eto_calculation/*.py (queries)
```

**Estratégia**:
1. Instalar `asyncpg`
2. Criar `async_db.py` com connection pool
3. Converter queries gradualmente
4. Testar cada endpoint após migração
5. Manter psycopg2 em bridge temporário

#### 5. **Celery Worker** 🔥 **SUBSTITUIÇÃO COMPLETA**
- ❌ Celery (arquitetura síncrona)
- ✅ Substituir por: **FastAPI BackgroundTasks** (simples) ou **Dramatiq** (avançado)

**Desafio**: Todas as tasks precisam migrar

**Celery Tasks identificadas**:
```python
# backend/core/data_processing/data_download.py
@shared_task
def download_weather_data(...)

# backend/infrastructure/cache/celery_tasks.py
@shared_task
def cache_warmup(...)
@shared_task
def cache_stats(...)

# backend/infrastructure/cache/climate_tasks.py
@shared_task
def prefetch_climate_data(...)
@shared_task
def cleanup_old_cache(...)
@shared_task
def generate_cache_stats(...)
```

**Estratégia - Opção A (Simples)**:
```python
# FastAPI BackgroundTasks (para tasks leves)
from fastapi import BackgroundTasks

@router.post("/eto/calculate")
async def calculate_eto(background_tasks: BackgroundTasks):
    background_tasks.add_task(download_weather_data_async, ...)
    return {"status": "processing"}
```

**Estratégia - Opção B (Avançado)**:
```python
# Dramatiq (para tasks pesadas, substitui Celery)
import dramatiq

@dramatiq.actor
async def download_weather_data_async(...):
    # Async task processing
    pass
```

---

## 🗺️ Roadmap de Migração

### **Fase 1: Preparação** (1 dia)
✅ Análise completa (este documento)  
⏳ Instalar dependências async:
```bash
pip install asyncpg aioredis httpx
# Opcional: pip install dramatiq (se escolher Opção B)
```
⏳ Criar branch `async-migration`  
⏳ Setup ambiente de teste

---

### **Fase 2: HTTP Clients** (2 dias) 🟢 FÁCIL → ✅ **COMPLETA** (<1 dia)

#### Dia 1: Migrar clientes REST
- [x] ✅ Verificar `met_norway_client.py` (já usa httpx!)
- [x] ✅ Verificar `nws_client.py` (já usa httpx!)
- [x] ✅ Verificar `nasa_power_client.py` (já usa httpx!)
- [x] ✅ Nenhuma conversão necessária!

#### Dia 2: OpenMeteo elevation
- [x] ✅ Converter `openmeteo.py` → `elevation_api.py` (httpx async)
- [x] ✅ Criar wrapper síncrono temporário para compatibilidade
- [x] ✅ Atualizar importações (3 arquivos: eto_routes.py, app.py, test_infrastructure_integration.py)
- [x] ✅ Atualizar `.gitignore` com seção async migration
- [x] ✅ Documentação completa (PHASE1_HTTP_CLIENTS_COMPLETED.md)

**Validação**: ✅ Todos os HTTP clients async, zero bloqueio

**Documentação**: `docs/PHASE1_HTTP_CLIENTS_COMPLETED.md`

---

### **Fase 3: Cache Layer** (3 dias) 🟡 MÉDIO

#### Dia 1: Novo cache async
- [ ] Criar `backend/infrastructure/cache/async_cache.py`
- [ ] Implementar com `aioredis`
- [ ] Interface: `async def get()`, `async def set()`, `async def delete()`

#### Dia 2: Migrar climate_tasks
- [ ] Converter `prefetch_climate_data` → async
- [ ] Converter `cleanup_old_cache` → async
- [ ] Converter `generate_cache_stats` → async

#### Dia 3: Testes e validação
- [ ] Testar cache hit/miss
- [ ] Validar TTL e expiração
- [ ] Benchmark performance (antes vs depois)

**Validação**: Cache 100% async, sem degradação

---

### **Fase 4: Data Processing** (5 dias) 🟡 MÉDIO

#### Dia 1-2: download_weather_data
- [ ] Criar `async def download_weather_data_async()`
- [ ] Usar `NASAPowerClient` diretamente (remover adapter)
- [ ] Converter DataFrame processing para async
- [ ] Testes com 44 dias de dados validados

#### Dia 3: data_fusion
- [ ] Analisar dependências Celery
- [ ] Converter para async
- [ ] Testes de fusão multi-fonte

#### Dia 4: data_preprocessing
- [ ] Converter para async
- [ ] Validar pipeline completo

#### Dia 5: Integração ETo
- [ ] Testar cálculo ETo com dados async
- [ ] Validar resultados vs baseline

**Validação**: Pipeline completo async, resultados idênticos

---

### **Fase 5: Database** (1 semana) 🔴 DIFÍCIL

#### Dia 1-2: Setup asyncpg
- [ ] Instalar `asyncpg`
- [ ] Criar `backend/database/async_connection.py`
- [ ] Connection pool config
- [ ] Health check async

#### Dia 3-4: Migrar queries críticas
- [ ] Identificar queries mais usadas
- [ ] Converter para asyncpg syntax
- [ ] Testar com dados reais
- [ ] Rollback plan

#### Dia 5-7: Migrar rotas API
- [ ] `eto_routes.py` → async queries
- [ ] `climate_sources_routes.py` → async queries
- [ ] `system_routes.py` → async queries
- [ ] Testes de integração

**Validação**: DB 100% async, performance melhorada

---

### **Fase 6: Celery → FastAPI/Dramatiq** (1 semana) 🔴 DIFÍCIL

#### Opção A: FastAPI BackgroundTasks (Recomendado para início)

**Dia 1-2**: Migrar tasks leves
```python
# backend/api/routes/eto_routes.py
from fastapi import BackgroundTasks

@router.post("/eto/calculate")
async def calculate_eto(background_tasks: BackgroundTasks, ...):
    background_tasks.add_task(
        download_weather_data_async,
        data_source, data_inicial, data_final, longitude, latitude
    )
    return {"status": "processing", "task_id": str(uuid4())}
```

**Dia 3-4**: Status tracking
- [ ] Implementar task status (Redis)
- [ ] Endpoint `/tasks/{task_id}/status`
- [ ] Webhook/SSE para notificações

**Dia 5-7**: Testes de carga
- [ ] Simular 100 requisições simultâneas
- [ ] Validar sem deadlock
- [ ] Benchmark vs Celery

#### Opção B: Dramatiq (Se precisar de features avançadas)

**Dia 1-3**: Setup Dramatiq
```python
# backend/infrastructure/tasks/dramatiq_config.py
import dramatiq
from dramatiq.brokers.redis import RedisBroker

broker = RedisBroker(url="redis://redis:6379/1")
dramatiq.set_broker(broker)

# backend/core/data_processing/async_data_download.py
@dramatiq.actor
async def download_weather_data_async(...):
    # Async processing
    pass
```

**Dia 4-5**: Migrar todas tasks
- [ ] download_weather_data
- [ ] prefetch_climate_data
- [ ] cleanup_old_cache
- [ ] generate_cache_stats

**Dia 6-7**: Testes e validação
- [ ] Task retries
- [ ] Error handling
- [ ] Dead letter queue
- [ ] Monitoring

**Validação**: Zero dependência de Celery

---

### **Fase 7: Cleanup** (2 dias)

#### Dia 1: Remover código legado
- [ ] Deletar `nasa_power_sync_adapter.py` (não precisa mais!)
- [ ] Deletar `backend/infrastructure/celery/celery_config.py`
- [ ] Deletar todas `@shared_task`
- [ ] Atualizar `requirements.txt` (remover celery)

#### Dia 2: Documentação
- [ ] Atualizar README.md
- [ ] Documentar arquitetura async
- [ ] Guia de migração para futuros devs
- [ ] Performance benchmarks

---

## 📈 Métricas de Sucesso

### Performance

| Métrica | Antes (Sync) | Meta (Async) |
|---------|--------------|--------------|
| **Requisições/seg** | ~100 | **>1000** |
| **Latência p95** | 500ms | **<100ms** |
| **Memória** | 512MB | **<256MB** |
| **Conexões simultâneas** | 50 | **>500** |
| **CPU idle** | 20% | **>50%** |

### Funcional

- [ ] ✅ Todos os testes passando (35/36 → 36/36)
- [ ] ✅ Cálculo ETo idêntico (validado)
- [ ] ✅ Cache funcionando (hit rate >80%)
- [ ] ✅ NASA POWER 100% match (validado)
- [ ] ✅ Zero downtime deployment

---

## ⚠️ Riscos e Mitigações

### Risco 1: Breaking Changes
**Impacto**: Alto  
**Probabilidade**: Média  
**Mitigação**: 
- Testes extensivos em cada fase
- Branch separada (async-migration)
- Rollback plan com Docker tags
- Feature flags para toggle sync/async

### Risco 2: Performance Degradation
**Impacto**: Alto  
**Probabilidade**: Baixa  
**Mitigação**:
- Benchmarks antes/depois
- Load testing (Locust)
- Monitoring contínuo (Prometheus)
- Canary deployment (10% → 50% → 100%)

### Risco 3: Database Connection Pool
**Impacto**: Médio  
**Probabilidade**: Média  
**Mitigação**:
- asyncpg pool size tuning
- Connection health checks
- Graceful degradation
- Circuit breaker pattern

### Risco 4: Learning Curve
**Impacto**: Baixo  
**Probabilidade**: Alta  
**Mitigação**:
- Documentação detalhada
- Pair programming
- Code reviews
- Async/await workshop

---

## 🛠️ Ferramentas e Dependências

### Novas Dependências

```toml
# pyproject.toml ou requirements.txt

# Async HTTP
httpx = "^0.27.0"

# Async PostgreSQL
asyncpg = "^0.29.0"

# Async Redis
aioredis = "^2.0.1"

# Task Queue (Opção B)
dramatiq[redis] = "^1.17.0"  # Opcional

# Testing
pytest-asyncio = "^0.23.0"
pytest-aiohttp = "^1.0.5"

# Monitoring
opentelemetry-instrumentation-asyncpg = "^0.43b0"
```

### Ferramentas de Desenvolvimento

```bash
# Load testing
pip install locust

# Profiling
pip install py-spy

# Async linting
pip install pylint-async
```

---

## 📚 Referências

### Documentação Oficial
- **FastAPI Async**: https://fastapi.tiangolo.com/async/
- **asyncpg**: https://magicstack.github.io/asyncpg/
- **aioredis**: https://aioredis.readthedocs.io/
- **Dramatiq**: https://dramatiq.io/
- **httpx**: https://www.python-httpx.org/async/

### Artigos e Guias
- [Async Python: The Complete Walkthrough](https://realpython.com/async-io-python/)
- [Migrating from Celery to Dramatiq](https://dramatiq.io/guide.html)
- [FastAPI BackgroundTasks vs Celery](https://fastapi.tiangolo.com/tutorial/background-tasks/)

---

## ✅ Checklist de Início

Antes de começar a migração:

- [ ] ✅ Backup completo do banco de dados
- [ ] ✅ Criar branch `async-migration`
- [ ] ✅ Setup ambiente de testes isolado
- [ ] ✅ Documentar estado atual (benchmarks)
- [ ] ✅ Comunicar equipe sobre mudanças
- [ ] ✅ Definir rollback strategy
- [ ] ⏳ Instalar dependências async
- [ ] ⏳ Revisar este plano com time
- [ ] ⏳ Estimar timeline (3-4 semanas)
- [ ] ⏳ Começar Fase 1!

---

## 🎯 Próximos Passos Imediatos

**Agora** (Hoje):
1. ✅ Deletar `nasapower.py.deprecated` - **CONCLUÍDO!**
2. ⏳ Revisar este plano
3. ⏳ Decidir: BackgroundTasks ou Dramatiq?
4. ⏳ Criar branch `async-migration`

**Amanhã** (Fase 2 - Dia 1):
1. Verificar `met_norway_client.py`
2. Verificar `nws_client.py`
3. Converter primeiro HTTP client para httpx

**Esta Semana** (Fase 2-3):
1. Completar migração HTTP clients
2. Iniciar cache async layer
3. Testes de integração

---

## 💬 Decisões Pendentes

### 1. Task Queue: BackgroundTasks vs Dramatiq?

**FastAPI BackgroundTasks** ✅ Recomendado:
- ✅ Simples e integrado
- ✅ Zero dependências extras
- ✅ Bom para tasks rápidas (<30s)
- ❌ Sem retry automático
- ❌ Sem priorização

**Dramatiq** 🚀 Avançado:
- ✅ Features completas (retry, DLQ, priorities)
- ✅ Substituição direta do Celery
- ✅ Melhor para tasks longas
- ❌ Dependência extra
- ❌ Mais complexo

**Recomendação**: Começar com BackgroundTasks, migrar para Dramatiq se necessário.

### 2. Migração: Big Bang vs Gradual?

**Big Bang** (3-4 semanas intensas):
- ✅ Mais rápido
- ❌ Maior risco
- ❌ Downtime necessário

**Gradual** (2-3 meses, 1 dia/semana): ✅ Recomendado
- ✅ Menor risco
- ✅ Zero downtime
- ✅ Aprendizado contínuo
- ❌ Bridge code temporário

**Recomendação**: Migração gradual, 1 fase por semana.

---

## 🏆 Resultado Final Esperado

**Arquitetura Completa Async**:
```
┌─────────────────────────────────────────────┐
│         FastAPI (async/await)               │
├─────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐        │
│  │ HTTP Routes  │  │ Background   │        │
│  │ (async def)  │  │ Tasks        │        │
│  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                 │
│  ┌──────▼──────────────────▼────────┐       │
│  │   Business Logic (async)         │       │
│  │   - nasa_power_client.py         │       │
│  │   - met_norway_client.py         │       │
│  │   - data_download (async)        │       │
│  │   - eto_calculation (async)      │       │
│  └──────┬───────────────────────────┘       │
│         │                                    │
│  ┌──────▼───────────────────────────┐       │
│  │   Infrastructure (async)         │       │
│  │   - asyncpg (PostgreSQL)         │       │
│  │   - aioredis (Cache)             │       │
│  │   - httpx (External APIs)        │       │
│  └──────────────────────────────────┘       │
└─────────────────────────────────────────────┘

Performance: >1000 req/s, <100ms latency
Scalability: >500 concurrent connections
Maintainability: Modern async/await patterns
```

---

**Status**: 🟢 **READY TO START**  
**Primeira ação**: Revisar este plano e decidir estratégia de task queue

