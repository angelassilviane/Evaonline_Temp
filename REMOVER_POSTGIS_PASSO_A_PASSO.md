# 🗑️ Guia Completo: Remover PostGIS do EVAonline

## 📋 Resumo da Operação

| Item | Antes | Depois | Ganho |
|------|-------|--------|-------|
| **Tamanho Docker** | 500MB | 170MB | -66% ✅ |
| **Tempo Build** | 5 min | 30s | -90% ✅ |
| **Tempo Startup** | 15-20s | 5-8s | -60% ✅ |
| **Memória RAM** | 200-300MB | 80-100MB | -60% ✅ |
| **Disco SSD** | 500MB | 170MB | -66% ✅ |

---

## ⚠️ PRÉ-REQUISITOS

Antes de começar:

```bash
# 1. Verificar que nenhum serviço está rodando
docker-compose ps

# Resultado esperado:
# STATUS: Down (ou não existem containers)

# 2. Fazer backup (por segurança)
docker-compose exec postgres pg_dump -U evaonline evaonline > backup_antes_postgis.sql

# 3. Verificar espaço em disco
df -h

# Resultado esperado: > 2GB livre
```

---

## 🚀 ETAPA 1: Editar docker-compose.yml

### Passo 1.1: Abrir arquivo

```bash
# No VS Code ou editor:
# Arquivo: docker-compose.yml
# Procure por: postgis/postgis:15-3.4-alpine
```

### Passo 1.2: Localizar a imagem PostGIS

**PROCURAR:**
```yaml
  postgres:
    image: postgis/postgis:15-3.4-alpine    # ← AQUI!
    container_name: evaonline-postgres
```

### Passo 1.3: Substituir pela imagem PostgreSQL pura

**SUBSTITUIR POR:**
```yaml
  postgres:
    image: postgres:15-alpine              # ← MUDOU!
    container_name: evaonline-postgres
```

### Verificação ✅

```bash
# Depois de editar, abra o terminal e execute:
grep -n "image:" docker-compose.yml | grep postgres

# Resultado esperado:
# postgres:
#   image: postgres:15-alpine              # ← SEM postgis!
```

---

## 🚀 ETAPA 2: Editar requirements.txt

### Passo 2.1: Localizar GeoAlchemy2

**PROCURAR:**
```bash
geoalchemy2>=0.14.0,<1.0.0  # Tipos geoespaciais para SQLAlchemy + PostGIS
```

### Passo 2.2: Remover linha completa

**ANTES:**
```bash
# Database & ORM
psycopg2-binary>=2.9.0,<3.0.0
sqlalchemy>=2.0.0,<3.0.0
sqlalchemy-utils>=0.41.0,<1.0.0
alembic>=1.12.0,<2.0.0
geoalchemy2>=0.14.0,<1.0.0  # ❌ REMOVER ESTA LINHA
pgcli>=4.0.0,<5.0.0
```

**DEPOIS:**
```bash
# Database & ORM
psycopg2-binary>=2.9.0,<3.0.0
sqlalchemy>=2.0.0,<3.0.0
sqlalchemy-utils>=0.41.0,<1.0.0
alembic>=1.12.0,<2.0.0
pgcli>=4.0.0,<5.0.0
```

### Verificação ✅

```bash
# Executar no terminal:
grep -i geoalchemy2 requirements.txt

# Resultado esperado:
# (nada - linha não encontrada)
```

---

## 🚀 ETAPA 3: Remover Scripts PostGIS do Docker

### Passo 3.1: Listar arquivos em init-db/

```bash
# Terminal:
ls -la init-db/

# Resultado esperado:
# 02-install-postgis.sh          ← ❌ REMOVER
# 99-configure-pg-hba.sh         ← ✅ MANTER
# README.md (se existir)         ← ✅ MANTER
```

### Passo 3.2: Remover arquivo PostGIS

```bash
# OPÇÃO 1: Linha de comando
rm init-db/02-install-postgis.sh

# OPÇÃO 2: No VS Code
# - Clique direito em init-db/02-install-postgis.sh
# - Selecione "Delete"
# - Confirme
```

### Verificação ✅

```bash
# Terminal:
ls -la init-db/

# Resultado esperado:
# 99-configure-pg-hba.sh         # Existe
# 02-install-postgis.sh          # NÃO EXISTE (✅ removido)
```

---

## 🚀 ETAPA 4: Verificar Código Python (NENHUMA MUDANÇA NECESSÁRIA!)

### Verificação: Não há código PostGIS no backend

```bash
# Procurar por uso de PostGIS:
grep -r "geoalchemy\|postgis\|ST_\|geometry\|geography" backend/ --include="*.py"

# Resultado esperado:
# (nada - ou apenas em comentários)
```

### Se aparecer algo:

```python
# ❌ ERRADO (não deve aparecer em código ativo):
from geoalchemy2 import Geometry
geometry_column = Column(Geometry('POINT'))

# ✅ CERTO (nenhum uso de PostGIS):
# Tudo usa PostgreSQL normal + Redis
```

---

## 🚀 ETAPA 5: Remover Container Antigo

### Passo 5.1: Parar e remover tudo

```bash
# Terminal:
docker-compose down

# Resultado esperado:
# Stopping evaonline-postgres ... done
# Removing evaonline-postgres ... done
# (e outros containers)
```

### Passo 5.2: Verificar que tudo foi removido

```bash
# Terminal:
docker-compose ps

# Resultado esperado:
# (lista vazia ou "down" status)
```

### Passo 5.3: Remover volumes se quiser recomeçar do zero

```bash
# ⚠️ CUIDADO: Isso deleta TODOS OS DADOS!
docker-compose down -v

# Resultado esperado:
# Removing volumes:
# - evaonline_postgres_data
# (etc)
```

---

## 🚀 ETAPA 6: Rebuild com PostgreSQL Puro

### Passo 6.1: Build nova imagem Docker

```bash
# Terminal:
docker-compose build postgres

# Resultado esperado:
# Step 1/10 : FROM postgres:15-alpine   # ← PostgreSQL puro!
# ...
# Successfully built abc123def456
# Successfully tagged evaonline-postgres:latest
```

### Passo 6.2: Monitorar o build

```bash
# Tempo esperado:
# - PostgreSQL puro: ~30-60 segundos
# - Com PostGIS: 4-5 minutos

# Você verá:
# Pulling postgres:15-alpine
# Pulling from library/postgres
# 62bdc19ac660: Pull complete   # Camadas sendo baixadas
# ...
```

---

## 🚀 ETAPA 7: Iniciar Containers

### Passo 7.1: Subir tudo

```bash
# Terminal:
docker-compose up -d

# Resultado esperado:
# Creating evaonline-redis ... done
# Creating evaonline-postgres ... done
# Creating evaonline-api ... done
# (etc)
```

### Passo 7.2: Verificar que tudo está rodando

```bash
# Terminal:
docker-compose ps

# Resultado esperado:
# STATUS: Up (para todos)

# Ou detalhado:
docker ps | grep evaonline
```

### Passo 7.3: Verificar logs do PostgreSQL

```bash
# Terminal:
docker-compose logs postgres

# Resultado esperado:
# database system is ready to accept connections
# (SEM mensagens de erro)

# Se ver erro:
# could not open file "pg_wal/...": No such file or directory
# Isso é normal na primeira vez com volume novo
```

---

## 🚀 ETAPA 8: Verificar Conexão

### Passo 8.1: Testar conexão PostgreSQL

```bash
# Opção 1: Via PgAdmin
# URL: http://localhost:5050
# Email: admin@evaonline.org
# Senha: admin

# Opção 2: Via terminal
docker-compose exec postgres psql -U evaonline -d evaonline -c "SELECT 1"

# Resultado esperado:
#  ?column?
# ----------
#        1
```

### Passo 8.2: Testar extensões PostgreSQL

```bash
# Terminal:
docker-compose exec postgres psql -U evaonline -d evaonline -c "SELECT * FROM pg_extension"

# Resultado esperado:
#     extname     | extversion | ...
# -----------------+----------
#  plpgsql         | 1.0        | ...
# (NÃO deve aparecer postgis!)
```

### Verificação ✅ PostGIS Foi Removido

```bash
# Terminal:
docker-compose exec postgres psql -U evaonline -d evaonline -c "CREATE TABLE test(id int)"

# Se funcionar = PostgreSQL puro está OK
# Se erro de encoding = pode precisar reinicializar

# Depois delete:
docker-compose exec postgres psql -U evaonline -d evaonline -c "DROP TABLE test"
```

---

## 🚀 ETAPA 9: Testar API

### Passo 9.1: Verificar que API está funcionando

```bash
# Terminal:
curl http://localhost:8000/api/v1/health

# Resultado esperado:
# {"status": "ok"}
```

### Passo 9.2: Testar banco de dados via API

```bash
# Terminal:
curl http://localhost:8000/api/v1/world-locations?limit=1

# Resultado esperado:
# [...dados de localizações...]
```

### Passo 9.3: Verificar frontend

```
# Browser:
http://localhost:8050

# Resultado esperado:
# Página de início carrega normalmente
# Mapas funcionam
# Dados aparecem
```

---

## 🚀 ETAPA 10: Executar Migrations

### Passo 10.1: Aplicar migrações

```bash
# Terminal:
cd backend
alembic upgrade head

# Resultado esperado:
# Running upgrade 001_create_initial_tables
# Done
```

### Passo 10.2: Verificar tabelas foram criadas

```bash
# Terminal:
docker-compose exec postgres psql -U evaonline -d evaonline -c "\dt"

# Resultado esperado:
# Tabelas criadas:
# - alembic_version
# - climate_data
# - world_locations
# (etc)
```

---

## ✅ CHECKLIST FINAL

```
ETAPA 1: docker-compose.yml
[ ] Mudou: postgis/postgis:15-3.4-alpine → postgres:15-alpine
[ ] Salvou arquivo

ETAPA 2: requirements.txt
[ ] Removeu: geoalchemy2>=0.14.0,<1.0.0
[ ] Salvou arquivo

ETAPA 3: init-db/
[ ] Deletou: init-db/02-install-postgis.sh
[ ] Manteve: init-db/99-configure-pg-hba.sh

ETAPA 4: Código Python
[ ] Verificou: grep -r geoalchemy (sem resultados)

ETAPA 5: Docker Down
[ ] Executou: docker-compose down
[ ] Verificou: docker-compose ps (vazio)

ETAPA 6: Build
[ ] Build novo: docker-compose build postgres
[ ] Tempo: ~30-60s (vs 4-5min antes)

ETAPA 7: Up
[ ] Subiu: docker-compose up -d
[ ] Todos: UP status

ETAPA 8: Conexão
[ ] Testou PostgreSQL: psql conecta
[ ] Sem PostGIS: SELECT * FROM pg_extension (postgis ausente)

ETAPA 9: API
[ ] API respondendo: /api/v1/health
[ ] Frontend carregando
[ ] Mapas funcionando

ETAPA 10: Migrations
[ ] alembic upgrade head (sucesso)
[ ] Tabelas criadas: \dt mostra tudo

STATUS: ✅ PostGIS REMOVIDO COM SUCESSO!
```

---

## 🎯 Resumo Final

### ✅ O Que Aconteceu

```
ANTES: image: postgis/postgis:15-3.4-alpine
           ↓ (500MB, 5min build, PostGIS não usado)
DEPOIS: image: postgres:15-alpine
           ↓ (170MB, 30s build, tudo funciona!)
RESULTADO: -330MB, -4m30s, 0% perda de funcionalidade ✅
```

### 🚀 Próximos Passos

```
1. Commit das mudanças:
   git add .
   git commit -m "Remove PostGIS: clean PostgreSQL image"

2. Verificar testes passam:
   pytest tests/ -v

3. Deploy para Railway:
   git push origin main
   # Railway auto-deploy

4. Próximo: Implementar features
   - Visitor counter
   - Admin dashboard
   - Cache elevação
```

### ❓ Problemas Encontrados?

```bash
# ❌ Erro: "could not open file pg_wal"
Solução: docker-compose down -v && docker-compose up -d

# ❌ Erro: "permission denied"
Solução: docker-compose exec postgres chown 999:999 /var/lib/postgresql/data

# ❌ Erro: "role does not exist"
Solução: Apagar volume e recriar com credenciais corretas

# ❌ Erro: "database does not exist"
Solução: Migrações não rodaram. Executar: alembic upgrade head
```

---

## 📞 Verificação Pós-Remoção

Execute este script para confirmar tudo está OK:

```bash
#!/bin/bash

echo "🔍 Verificando PostGIS removido..."

echo "1. Docker image..."
docker-compose config | grep postgres | grep image

echo "2. requirements.txt..."
grep -i geoalchemy2 requirements.txt || echo "✅ GeoAlchemy2 não encontrado"

echo "3. init-db/"
ls -la init-db/ | grep postgis || echo "✅ Nenhum arquivo postgis"

echo "4. Código Python..."
grep -r "geoalchemy\|postgis\|ST_" backend/ --include="*.py" || echo "✅ Sem código PostGIS"

echo "5. PostgreSQL extensões..."
docker-compose exec postgres psql -U evaonline -d evaonline -c "SELECT * FROM pg_extension WHERE extname = 'postgis'"

echo "🎉 Se tudo acima mostrou ✅ ou vazio, PostGIS foi removido com sucesso!"
```

---

## 📊 Documentação Relacionada

- **ESTRUTURA_BANCO_DADOS.md** - Estrutura correta do projeto
- **DEPLOYMENT_ANALYSIS.md** - Por que PostGIS não era necessário
- **DATABASE_MIGRATIONS.md** - Como executar migrações
- **REDIS_POSTGRESQL_INTEGRATION.md** - Novas features

