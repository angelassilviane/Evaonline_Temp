# 🧪 GUIA DE TESTES - EVAonline

**Data:** 14 de Janeiro de 2025  
**Versão:** 1.0

---

## 📋 Índice

1. [Testes de Integração Docker](#1-testes-de-integração-docker)
2. [Teste Completo da Stack](#2-teste-completo-da-stack)
3. [Testes de API](#3-testes-de-api)
4. [Testes de Performance](#4-testes-de-performance)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. 🐳 Testes de Integração Docker

### 1.1 Preparação

```powershell
# Garantir que .env está configurado
if (!(Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "⚠️  Configure o arquivo .env antes de continuar!" -ForegroundColor Yellow
    notepad .env
}

# Parar containers existentes
docker-compose down -v
```

### 1.2 Iniciar Serviços Básicos

```powershell
# Iniciar apenas PostgreSQL e Redis
docker-compose up -d postgres redis

# Aguardar serviços ficarem healthy
Write-Host "⏳ Aguardando serviços iniciarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar status
docker-compose ps
```

**Resultado esperado:**
```
NAME                 STATUS
evaonline-postgres   Up (healthy)
evaonline-redis      Up (healthy)
```

### 1.3 Testar PostgreSQL

```powershell
# Teste 1: Conectar ao PostgreSQL
docker-compose exec postgres psql -U evaonline -d evaonline -c "SELECT version();"

# Teste 2: Verificar extensão PostGIS
docker-compose exec postgres psql -U evaonline -d evaonline -c "SELECT PostGIS_version();"

# Teste 3: Criar tabela de teste
docker-compose exec postgres psql -U evaonline -d evaonline -c @"
CREATE TABLE IF NOT EXISTS test_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    location GEOGRAPHY(POINT, 4326)
);
INSERT INTO test_table (name, location) 
VALUES ('Test Location', ST_GeogFromText('POINT(-47.9292 -15.7801)'));
SELECT * FROM test_table;
"@

# Teste 4: Limpar
docker-compose exec postgres psql -U evaonline -d evaonline -c "DROP TABLE IF EXISTS test_table;"
```

**Resultado esperado:**
- ✅ Versão do PostgreSQL exibida
- ✅ Versão do PostGIS exibida (ex: 3.4)
- ✅ Tabela criada e consultada com sucesso
- ✅ Dados geográficos armazenados corretamente

### 1.4 Testar Redis

```powershell
# Teste 1: PING
docker-compose exec redis redis-cli -a evaonline PING

# Teste 2: SET/GET
docker-compose exec redis redis-cli -a evaonline SET test_key "test_value"
docker-compose exec redis redis-cli -a evaonline GET test_key

# Teste 3: Hash
docker-compose exec redis redis-cli -a evaonline HSET test_hash field1 value1 field2 value2
docker-compose exec redis redis-cli -a evaonline HGETALL test_hash

# Teste 4: Lista
docker-compose exec redis redis-cli -a evaonline RPUSH test_list item1 item2 item3
docker-compose exec redis redis-cli -a evaonline LRANGE test_list 0 -1

# Teste 5: Limpar
docker-compose exec redis redis-cli -a evaonline DEL test_key test_hash test_list
```

**Resultado esperado:**
- ✅ PONG recebido
- ✅ Valor armazenado e recuperado
- ✅ Hash criado e consultado
- ✅ Lista criada e consultada
- ✅ Chaves deletadas

### 1.5 Rodar Testes de Integração Python

```powershell
# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# Configurar variáveis de ambiente
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DB = "evaonline"
$env:POSTGRES_USER = "evaonline"
$env:POSTGRES_PASSWORD = "evaonline"
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"
$env:REDIS_PASSWORD = "evaonline"

# Rodar testes de integração
pytest tests/integration/test_docker_services.py -v

# Ou rodar todos os testes de integração
pytest -m integration -v
```

**Resultado esperado:**
```
tests/integration/test_docker_services.py::TestPostgreSQLConnection::test_database_connection PASSED
tests/integration/test_docker_services.py::TestPostgreSQLConnection::test_database_version PASSED
tests/integration/test_docker_services.py::TestPostgreSQLConnection::test_postgis_extension PASSED
tests/integration/test_docker_services.py::TestRedisConnection::test_redis_connection PASSED
tests/integration/test_docker_services.py::TestRedisConnection::test_redis_set_get PASSED
...
✅ Todos os serviços Docker estão funcionando!
```

---

## 2. 🚀 Teste Completo da Stack

### 2.1 Iniciar Stack Completa

```powershell
# Profile de desenvolvimento
docker-compose --profile development up -d

# Aguardar todos os serviços iniciarem
Start-Sleep -Seconds 20

# Verificar status
docker-compose ps
```

**Serviços esperados:**
- ✅ postgres (healthy)
- ✅ redis (healthy)
- ✅ api (running)
- ✅ celery-worker (running)
- ✅ dash (running)

### 2.2 Verificar Logs

```powershell
# Ver logs de todos os serviços
docker-compose logs

# Ver logs específicos
docker-compose logs api
docker-compose logs celery-worker
docker-compose logs dash

# Seguir logs em tempo real
docker-compose logs -f api
```

### 2.3 Testar Endpoints

```powershell
# Teste 1: Health Check API
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -Method Get

# Teste 2: Health Check Dash
Invoke-WebRequest -Uri "http://localhost:8050" -Method Get

# Teste 3: API Info (se disponível)
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/info" -Method Get
```

**Resultados esperados:**
```json
// Health API
{
  "status": "healthy",
  "service": "evaonline-api",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}

// Health Dash
StatusCode: 200
```

### 2.4 Testar Celery

```powershell
# Ver workers ativos
docker-compose exec celery-worker celery -A backend.infrastructure.celery.app inspect active

# Ver tarefas registradas
docker-compose exec celery-worker celery -A backend.infrastructure.celery.app inspect registered

# Ver estatísticas
docker-compose exec celery-worker celery -A backend.infrastructure.celery.app inspect stats
```

---

## 3. 🌐 Testes de API

### 3.1 Testes Manuais com cURL/Invoke-RestMethod

```powershell
# Teste 1: GET endpoint
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/geo/data?lat=-15.7801&lon=-47.9292" -Method Get

# Teste 2: POST endpoint (exemplo ETo)
$body = @{
    date = "2025-01-14"
    latitude = -15.7801
    altitude = 1000.0
    tmax = 30.0
    tmin = 20.0
    radiation = 20.0
    wind_speed = 2.0
    humidity_max = 80.0
    humidity_min = 40.0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/eto/calculate" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

### 3.2 Testes Automatizados

```powershell
# Rodar testes de API
pytest tests/api/ -v

# Com marcador específico
pytest -m api -v

# Com coverage
pytest tests/api/ --cov=backend.api --cov-report=html -v
```

### 3.3 Teste de Carga (Opcional)

Se tiver `locust` instalado:

```powershell
# Instalar locust
pip install locust

# Criar arquivo locustfile.py (exemplo básico)
@"
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def health_check(self):
        self.client.get("/api/v1/health")
    
    @task(3)
    def get_geo_data(self):
        self.client.get("/api/v1/geo/data?lat=-15.7801&lon=-47.9292")
"@ | Out-File -FilePath locustfile.py

# Rodar teste de carga
locust -f locustfile.py --host=http://localhost:8000
```

Acesse http://localhost:8089 para interface web.

---

## 4. 📊 Testes de Performance

### 4.1 Benchmark de Database

```powershell
# Teste de inserção em massa
docker-compose exec postgres psql -U evaonline -d evaonline -c @"
CREATE TABLE IF NOT EXISTS benchmark_test (
    id SERIAL PRIMARY KEY,
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Inserir 10000 registros
INSERT INTO benchmark_test (data)
SELECT jsonb_build_object('value', i, 'timestamp', now())
FROM generate_series(1, 10000) AS i;

-- Medir tempo de consulta
\timing on
SELECT COUNT(*) FROM benchmark_test;
SELECT * FROM benchmark_test WHERE data->>'value' = '5000';
\timing off

DROP TABLE benchmark_test;
"@
```

### 4.2 Benchmark de Redis

```powershell
# Redis benchmark integrado
docker-compose exec redis redis-benchmark -a evaonline -t set,get -n 10000 -q
```

**Resultado esperado:**
```
SET: X requests per second
GET: Y requests per second
```

### 4.3 Pytest Benchmark

```powershell
# Instalar pytest-benchmark
pip install pytest-benchmark

# Rodar benchmarks
pytest tests/ --benchmark-only

# Com comparação
pytest tests/ --benchmark-autosave

# Comparar com runs anteriores
pytest tests/ --benchmark-compare
```

---

## 5. 🔧 Troubleshooting

### 5.1 Container não inicia

```powershell
# Ver logs detalhados
docker-compose logs <service_name>

# Verificar configuração
docker-compose config

# Reconstruir imagem
docker-compose build --no-cache <service_name>

# Remover volumes órfãos
docker volume prune
```

### 5.2 Erro de conexão ao PostgreSQL

```powershell
# Verificar se está rodando
docker-compose ps postgres

# Verificar logs
docker-compose logs postgres

# Testar conexão manualmente
docker-compose exec postgres pg_isready -U evaonline

# Verificar variáveis de ambiente
docker-compose exec postgres env | grep POSTGRES
```

### 5.3 Erro de conexão ao Redis

```powershell
# Verificar se está rodando
docker-compose ps redis

# Verificar logs
docker-compose logs redis

# Testar conexão
docker-compose exec redis redis-cli -a evaonline PING

# Ver configuração
docker-compose exec redis redis-cli -a evaonline CONFIG GET *
```

### 5.4 API não responde

```powershell
# Verificar logs
docker-compose logs api

# Verificar se está ouvindo na porta
netstat -ano | findstr :8000

# Entrar no container
docker-compose exec api sh

# Testar dentro do container
docker-compose exec api curl http://localhost:8000/api/v1/health
```

### 5.5 Testes falhando

```powershell
# Limpar cache
pytest --cache-clear

# Limpar __pycache__
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall

# Rodar com verbose extremo
pytest -vvv --tb=long
```

---

## 📝 Checklist de Testes

Use este checklist antes de fazer deploy ou PR:

### Testes Básicos
- [ ] PostgreSQL conecta e responde
- [ ] PostGIS está disponível
- [ ] Redis conecta e responde
- [ ] API responde em http://localhost:8000
- [ ] Dash responde em http://localhost:8050

### Testes de Integração
- [ ] `pytest -m integration` passa
- [ ] `pytest -m database` passa
- [ ] `pytest -m redis` passa

### Testes de API
- [ ] `pytest -m api` passa
- [ ] Health check retorna 200
- [ ] Endpoints principais funcionam

### Testes de Código
- [ ] `black --check backend/ tests/` passa
- [ ] `isort --check backend/ tests/` passa
- [ ] `flake8 backend/ tests/` passa
- [ ] `mypy backend/` não tem erros críticos

### Docker
- [ ] `docker-compose up -d` funciona
- [ ] Todos os containers ficam healthy
- [ ] Logs não mostram erros críticos
- [ ] Rebuild funciona (`docker-compose build`)

### Coverage
- [ ] Coverage > 80% (meta)
- [ ] Relatório HTML gerado (`htmlcov/`)
- [ ] Nenhuma área crítica sem cobertura

---

## 🎉 Conclusão

Se todos os testes passaram, seu ambiente está **100% funcional**! 🚀

**Próximos passos:**
1. Implementar funcionalidades do mapa mundial
2. Adicionar mais testes unitários
3. Melhorar coverage para >80%
4. Deploy em ambiente de staging

---

**Mantenedor:** Ângela Cunha Soares  
**Email:** angelassilviane@gmail.com
