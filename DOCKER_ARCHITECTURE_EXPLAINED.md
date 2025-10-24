# 🐳 ARQUITETURA DOCKER - EVAonline

## 📊 Problema Atual

```
❌ IMAGENS ATUAIS (4 imagens, 2.09GB cada):
   - evaonline (generic runtime)
   - evaonline_temp-celery-worker (2.09GB)
   - evaonline_temp-celery-beat (2.09GB)
   - evaonline_temp-flower (2.09GB)

❌ IMAGENS FALTANDO:
   - PostgreSQL 15-alpine (390MB) - database
   - Redis 7-alpine (60MB) - cache/broker
   - Nginx (Alpine) (~10MB) - reverse proxy
   - Prometheus (~150MB) - monitoring
   - Grafana (~200MB) - dashboards
   - PgAdmin (~100MB) - DB admin
   - Portainer (~200MB) - container management

TOTAL ESPERADO: ~2.1GB
TOTAL ATUAL: 8.36GB (4x 2.09GB)
PROBLEMA: Imagens muito grandes + duplicadas
```

---

## ✅ SOLUÇÃO: Arquitetura Correta

### 1️⃣ **Imagens Base (FROM DockerHub)**
```
Estas são OFICIAIS e otimizadas (não buildamos):

✅ PostgreSQL 15-alpine     (390MB) - PUXAR do DockerHub
✅ Redis 7-alpine           (60MB)  - PUXAR do DockerHub
✅ Nginx Alpine             (~10MB) - PUXAR do DockerHub
✅ Python 3.10-slim         (Base para build)
✅ Prometheus               (~150MB)
✅ Grafana                  (~200MB)
✅ PgAdmin 4                (~100MB)
✅ Portainer                (~200MB)
```

### 2️⃣ **Imagens Customizadas (BUILDAMOS)**
```
Apenas 1 imagem principal, usada por todos os serviços:

📦 evaonline-runtime:latest (500-700MB)
   ├─ Base: Python 3.10-slim
   ├─ Requirements: requirements/production.txt
   ├─ Entrypoint: scripts/entrypoint.sh
   └─ Serviços que usam:
      • evaonline-api (service: api)
      • evaonline-celery-worker (service: celery-worker)
      • evaonline-celery-beat (service: celery-beat)
      • evaonline-flower (service: flower)

🎯 DIFERENÇA: 
   - Mesma imagem base
   - Diferentes ENTRYPOINT (definido em docker-compose)
   - Diferentes ENV variables (SERVICE=api|worker|beat|flower)
```

---

## 🏗️ Estrutura Docker Proposta

### docker-compose.yml CORRETO:

```yaml
version: '3.9'

services:
  # ============================================================================
  # TIER 1: DATA LAYER (Base infrastructure)
  # ============================================================================
  
  redis:
    image: redis:7-alpine          # ← PUXAR (60MB)
    container_name: evaonline-redis
    ports: ["6379:6379"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  postgres:
    image: postgres:15-alpine      # ← PUXAR (390MB)
    container_name: evaonline-postgres
    environment:
      POSTGRES_USER: evaonline
      POSTGRES_PASSWORD: 123456
      POSTGRES_DB: evaonline
    ports: ["5432:5432"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U evaonline"]

  # ============================================================================
  # TIER 2: APPLICATION LAYER (Nossa aplicação)
  # ============================================================================
  
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    image: evaonline-runtime:latest    # ← BUILD (600MB)
    container_name: evaonline-api
    environment:
      - SERVICE=api                    # ← Determina qual serviço rodar
      - DATABASE_URL=postgresql://evaonline:123456@postgres:5432/evaonline
      - REDIS_URL=redis://redis:6379/0
    ports: ["8000:8000"]
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    restart: unless-stopped

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    image: evaonline-runtime:latest    # ← MESMA IMAGEM
    container_name: evaonline-celery-worker
    environment:
      - SERVICE=worker                 # ← Diferentes env vars
      - DATABASE_URL=postgresql://evaonline:123456@postgres:5432/evaonline
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://:evaonline@redis:6379/0
    depends_on:
      - redis
      - postgres
    restart: unless-stopped

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    image: evaonline-runtime:latest    # ← MESMA IMAGEM
    container_name: evaonline-celery-beat
    environment:
      - SERVICE=beat                   # ← Diferentes env vars
      - DATABASE_URL=postgresql://evaonline:123456@postgres:5432/evaonline
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://:evaonline@redis:6379/0
    depends_on:
      - celery-worker
    restart: unless-stopped

  flower:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    image: evaonline-runtime:latest    # ← MESMA IMAGEM
    container_name: evaonline-flower
    environment:
      - SERVICE=flower                 # ← Diferentes env vars
    ports: ["5555:5555"]
    depends_on:
      - celery-worker
    restart: unless-stopped

  # ============================================================================
  # TIER 3: MONITORING LAYER (Opcional)
  # ============================================================================
  
  prometheus:
    image: prom/prometheus:latest      # ← PUXAR (~150MB)
    container_name: evaonline-prometheus
    ports: ["9090:9090"]
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest      # ← PUXAR (~200MB)
    container_name: evaonline-grafana
    ports: ["3000:3000"]
    restart: unless-stopped

  pgadmin:
    image: dpage/pgadmin4:latest       # ← PUXAR (~100MB)
    container_name: evaonline-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@evaonline.org
      PGADMIN_DEFAULT_PASSWORD: admin
    ports: ["5050:80"]
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

## 📊 Comparação de Tamanhos

### ❌ ATUALMENTE (ERRADO):
```
evaonline                  2.09GB
evaonline_temp-celery-worker    2.09GB
evaonline_temp-celery-beat      2.09GB
evaonline_temp-flower           2.09GB
────────────────────────────────
TOTAL 4 IMAGENS:         8.36GB ❌❌❌
```

### ✅ PROPOSTO (CORRETO):
```
evaonline-runtime:latest      600MB  (BUILD uma vez)
postgresql:15-alpine          390MB  (PUXAR)
redis:7-alpine                 60MB  (PUXAR)
prometheus:latest             150MB  (PUXAR)
grafana:latest                200MB  (PUXAR)
pgadmin4:latest               100MB  (PUXAR)
nginx:alpine                   10MB  (PUXAR)
────────────────────────────────────
TOTAL 7 IMAGENS:           ~1.51GB ✅✅✅

ECONOMIA: 6.85GB (82% menos!)
```

---

## 🔧 Como Funciona o Entrypoint

### Estrutura de Múltiplos Serviços com 1 Imagem:

```
evaonline-runtime:latest
    ├─ entrypoint.sh (script que detecta SERVICE)
    ├─ backend/ (código da API)
    ├─ frontend/ (código do Dash)
    └─ requirements/ (dependências)

entrypoint.sh:
    if [ "$SERVICE" = "api" ]; then
        uvicorn backend.main:app ...
    elif [ "$SERVICE" = "worker" ]; then
        celery -A backend.core.celery_config worker ...
    elif [ "$SERVICE" = "beat" ]; then
        celery -A backend.core.celery_config beat ...
    elif [ "$SERVICE" = "flower" ]; then
        celery -A backend.core.celery_config flower ...
    fi
```

---

## 📋 Plano de Ação

### PASSO 1: Atualizar docker-compose.yml
✅ Usar MESMA imagem para todos
✅ Mudar para imagens base oficiais

### PASSO 2: Verificar entrypoint.sh
✅ Conferir se detecta $SERVICE
✅ Adaptar comandos para cada serviço

### PASSO 3: Build UMA ÚNICA VEZ
```bash
docker build -t evaonline-runtime:latest .
```

### PASSO 4: Puxar imagens base
```bash
docker pull postgres:15-alpine
docker pull redis:7-alpine
docker pull prometheus:latest
docker pull grafana:latest
docker pull dpage/pgadmin4:latest
```

### PASSO 5: Rodar tudo
```bash
docker-compose up -d
```

---

## 🎯 Tamanhos Esperados Finais

```
✅ evaonline-runtime:latest    ~600MB (BUILD 1x)
✅ postgresql:15-alpine        ~390MB (PUXAR)
✅ redis:7-alpine              ~60MB  (PUXAR)
✅ prometheus:latest           ~150MB (PUXAR)
✅ grafana:latest              ~200MB (PUXAR)
✅ pgadmin4:latest             ~100MB (PUXAR)

TOTAL COM TODOS RODANDO: ~1.5GB em disco
ESPAÇO EM MEMÓRIA: ~300MB (cores + services)
```

---

## ✅ Checklist

- [ ] Atualizar docker-compose.yml com nova estrutura
- [ ] Verificar entrypoint.sh funciona com SERVICE env var
- [ ] Fazer build: `docker build -t evaonline-runtime:latest .`
- [ ] Puxar imagens base: `docker pull ...`
- [ ] Validar: `docker-compose config`
- [ ] Rodar: `docker-compose up -d`
- [ ] Verificar logs: `docker logs evaonline-api`
- [ ] Testar API: `curl http://localhost:8000/health`
- [ ] Testar DB: `psql -h localhost -U evaonline -d evaonline`
- [ ] Dashboard Celery: `http://localhost:5555`

