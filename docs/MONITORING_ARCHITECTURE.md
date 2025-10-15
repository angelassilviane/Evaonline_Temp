# 🏗️ Arquitetura de Monitoramento EVAonline

```
┌─────────────────────────────────────────────────────────────────┐
│                        USUÁRIOS FINAIS                          │
│  👤 Gestores  👤 Stakeholders  👤 Pesquisadores  👤 Público    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP (Read-Only)
                         ▼
            ┌────────────────────────┐
            │   🎨 GRAFANA (3000)   │
            │  Dashboard Simplificado│
            │  ✅ Status Sistema     │
            │  ⏱️  Tempo Resposta    │
            │  📊 Consultas Hoje     │
            │  ⚡ Cache Performance  │
            └────────────┬───────────┘
                         │
                         │ PromQL Queries
                         ▼
            ┌────────────────────────┐
            │ 📊 PROMETHEUS (9090)  │
            │  Time-Series Database  │
            │  Coleta métricas a     │
            │  cada 15 segundos      │
            └─────┬──────────────────┘
                  │
        ┌─────────┼─────────┬──────────────┐
        │         │         │              │
        │ /metrics│/metrics │/metrics      │/metrics
        ▼         ▼         ▼              ▼
    ┌───────┐ ┌──────┐ ┌────────┐    ┌─────────┐
    │ API   │ │REDIS │ │POSTGRES│    │ CELERY  │
    │ :8000 │ │ :6379│ │  :5432 │    │ Worker  │
    └───────┘ └──────┘ └────────┘    └─────────┘
        │
        │ Requests
        ▼
┌──────────────────┐
│  USUÁRIOS API    │
│  🔧 Desenvolvedores│
└──────────────────┘

═══════════════════════════════════════════════════════════════

                    FLUXO DE MÉTRICAS

1️⃣  API recebe request
    └─> Incrementa contador: api_requests_total
    └─> Registra latência: api_request_duration_seconds
    └─> Cache hit/miss: cache_hits_total / cache_misses_total

2️⃣  Prometheus faz scraping a cada 15s
    └─> GET http://api:8000/metrics
    └─> Armazena em time-series database

3️⃣  Grafana executa queries PromQL
    └─> Busca dados do Prometheus
    └─> Renderiza dashboards visuais
    └─> Atualiza a cada 30s

4️⃣  Alertas são disparados (se configurado)
    └─> Slack / Email / PagerDuty
    └─> Baseado em thresholds (ex: error rate > 5%)

═══════════════════════════════════════════════════════════════

                  DASHBOARDS DISPONÍVEIS

┌─────────────────────────────────────────────────────────────┐
│  📊 "EVAonline - Visão do Usuário" (PÚBLICO)               │
├─────────────────────────────────────────────────────────────┤
│  ✅ Status Online/Offline                                   │
│  ⏱️  Tempo de Resposta Médio (P50)                         │
│  📈 Consultas nas Últimas 24h                               │
│  ⚡ Taxa de Cache Hit (%)                                   │
│  🌍 Distribuição Geográfica                                 │
│  💡 Economia de Tempo (cache)                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🔧 "EVAonline Application Metrics" (DEVOPS)               │
├─────────────────────────────────────────────────────────────┤
│  📊 API Requests per Second                                 │
│  ⏱️  Response Time (P50, P95, P99)                         │
│  💾 Cache Performance (hits/misses)                         │
│  ⚠️  Error Rate (4xx, 5xx)                                  │
│  🖥️  System Resources (CPU, RAM, Disk)                     │
│  🔄 Celery Tasks (pending/running/failed)                   │
└─────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════

                    MÉTRICAS COLETADAS

📊 API Metrics (FastAPI):
   ├─ http_requests_total (Counter)
   ├─ http_request_duration_seconds (Histogram)
   ├─ api_active_requests (Gauge)
   ├─ cache_hits_total (Counter)
   ├─ cache_misses_total (Counter)
   └─ popular_data_accesses (Counter)

💾 Redis Metrics:
   ├─ redis_connected_clients
   ├─ redis_memory_used_bytes
   └─ redis_commands_processed_total

🗄️  PostgreSQL Metrics:
   ├─ pg_up
   ├─ pg_connections_active
   ├─ pg_queries_duration_seconds
   └─ pg_database_size_bytes

🔄 Celery Metrics:
   ├─ celery_tasks_total (by state: pending/running/success/failure)
   ├─ celery_task_duration_seconds
   └─ celery_workers_active

═══════════════════════════════════════════════════════════════

                    NÍVEIS DE ACESSO

┌─────────────┬──────────────┬─────────────┬──────────────────┐
│  Ferramenta │    URL       │   Acesso    │    Usuário       │
├─────────────┼──────────────┼─────────────┼──────────────────┤
│  Grafana    │  :3000       │  Anônimo    │  👥 Todos       │
│  (Viewer)   │              │  Read-Only  │                  │
├─────────────┼──────────────┼─────────────┼──────────────────┤
│  Grafana    │  :3000/login │  admin/     │  🔧 DevOps      │
│  (Admin)    │              │  admin      │  Admin           │
├─────────────┼──────────────┼─────────────┼──────────────────┤
│  Prometheus │  :9090       │  Aberto     │  🔧 Devs        │
│             │              │             │  DevOps          │
├─────────────┼──────────────┼─────────────┼──────────────────┤
│  Swagger    │  :8000/      │  Aberto     │  🔧 Devs        │
│  Docs       │  api/v1/docs │             │                  │
├─────────────┼──────────────┼─────────────┼──────────────────┤
│  /metrics   │  :8000/      │  Aberto     │  🔧 Devs        │
│             │  metrics     │             │  Prometheus      │
└─────────────┴──────────────┴─────────────┴──────────────────┘

═══════════════════════════════════════════════════════════════

                    ALERTAS CONFIGURADOS

⚠️  High Error Rate (Critical)
    Condição: error_rate > 5% por 5 minutos
    Ação: Notificar DevOps via Slack
    
⏱️  High Latency (Warning)
    Condição: P95 > 2 segundos por 10 minutos
    Ação: Email para equipe de backend
    
💾 Low Cache Hit Rate (Warning)
    Condição: cache_hit_rate < 70% por 15 minutos
    Ação: Notificar via Slack
    
🔴 Service Down (Critical)
    Condição: up == 0
    Ação: PagerDuty + SMS para on-call

═══════════════════════════════════════════════════════════════

                    RETENÇÃO DE DADOS

📅 Prometheus:
   ├─ Raw data: 15 dias
   ├─ Agregações 5min: 30 dias
   └─ Agregações 1h: 90 dias

📅 Grafana:
   ├─ Dashboards: Persistente (grafana_data volume)
   └─ Snapshots: Opcional (API ou plugin)

═══════════════════════════════════════════════════════════════

                    PRÓXIMOS PASSOS

✅ Implementado:
   ├─ Prometheus coletando métricas
   ├─ Grafana com 2 dashboards
   ├─ Acesso anônimo (read-only)
   └─ API expondo /metrics

📋 Sugerido:
   ├─ Configurar alertas (Slack/Email)
   ├─ Adicionar Redis Exporter
   ├─ Adicionar PostgreSQL Exporter
   ├─ Configurar backup de dashboards
   ├─ Implementar rate limiting por IP
   └─ Adicionar autenticação OAuth (prod)

═══════════════════════════════════════════════════════════════
