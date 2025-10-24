# 🐳 ARQUITETURA DOCKER - Explicação Completa

---

## ❓ SUAS DÚVIDAS RESPONDIDAS

### 1️⃣ **Portainer faz falta?**

```
✅ SIM, Portainer é importante para:
   • Gerenciar containers via interface web
   • Monitorar recursos em tempo real
   • Deploy sem linha de comando
   • Perfeito para times não-técnicos

MAS: É OPCIONAL em desenvolvimento
      É RECOMENDADO em produção
```

### 2️⃣ **As imagens vêm "sozinhas" do DockerHub?**

```
NÃO! Cada imagem no DockerHub é INDEPENDENTE:

postgresql:15-alpine é APENAS PostgreSQL
   └─ Vem com: sistema de arquivos, postgresql binário, libs
   └─ NÃO vem com: Redis, Grafana, ou qualquer outra coisa

redis:7-alpine é APENAS Redis
   └─ Vem com: sistema de arquivos, redis binário
   └─ NÃO vem com: PostgreSQL, ou qualquer outra coisa

Portainer é APENAS Portainer
   └─ Vem com: Node.js, aplicação Portainer
   └─ NÃO vem com: PostgreSQL, Redis, ou qualquer outra coisa

🎯 CADA CONTAINER = 1 PROCESSO/SERVIÇO
   São COMUNICADOS via NETWORK, não "empacotados juntos"
```

### 3️⃣ **Então como "empacotamos tudo"?**

```
❌ ERRADO - Tentar colocar tudo em 1 container:
   evaonline-all
   ├─ PostgreSQL (processo)
   ├─ Redis (processo)
   ├─ API FastAPI (processo)
   ├─ Celery Worker (processo)
   ├─ Prometheus (processo)
   ├─ Grafana (processo)
   └─ PgAdmin (processo)
   
   PROBLEMAS:
   • Difícil de escalar (não posso rodar 3 workers)
   • Difícil de debugar (logs misturados)
   • PostgreSQL cai, tudo cai
   • Contra boas práticas Docker

✅ CORRETO - Usar Docker Compose:
   docker-compose.yml orquestra tudo
   ├─ postgres (1 container)
   ├─ redis (1 container)
   ├─ api (1 container)
   ├─ celery-worker (N containers)
   ├─ celery-beat (1 container)
   ├─ flower (1 container)
   ├─ prometheus (1 container)
   ├─ grafana (1 container)
   └─ pgadmin (1 container)
   
   VANTAGENS:
   • Posso rodar: docker-compose up -d
   • Posso fazer scale: docker-compose up -d --scale celery-worker=3
   • Logs separados: docker logs evaonline-api
   • Reinicia independente: docker restart evaonline-postgres
```

---

## 🏗️ ARQUITETURA CORRETA

### Como NÃO Pensar (Container Monolítico):

```
❌ ERRADO:

USER (DockerHub) → docker pull evaonline-api
                 → 1 GIGANTIC image (5GB)
                 → docker run evaonline-api
                 → 1 container com TUDO rodar juntar
```

### Como REALMENTE Funciona (Container Orquestrado):

```
✅ CORRETO:

USER (Git) → clona projeto
           → cd evaonline
           → docker-compose up

docker-compose.yml
├─ Carrega postgresql:15-alpine (já existe no DockerHub)
├─ Carrega redis:7-alpine (já existe no DockerHub)
├─ Faz BUILD de evaonline-runtime (criamos o Dockerfile)
├─ Faz BUILD de evaonline-runtime (MESMA imagem, diferentes ENV vars)
├─ Cria network "evaonline_default" para containers se comunicarem
└─ Inicia cada container independentemente

RESULTADO: 9 containers rodando, comunicados via network Docker
```

---

## 📦 O QUE ENVIAMOS AO DOCKERHUB

### Opção A: Apenas a Imagem da Aplicação

```
O QUE SUBIMOS:
   evaonline/evaonline-runtime:latest (600MB)
   └─ Contém: Python + deps + código

O QUE NÃO SUBIMOS (puxamos do DockerHub oficial):
   library/postgresql:15-alpine (390MB)
   library/redis:7-alpine (60MB)
   library/prometheus (150MB)
   library/grafana (200MB)
   dpage/pgadmin4 (100MB)
   library/nginx:alpine (10MB)

COMO O USUÁRIO USA:
   git clone https://github.com/seu-usuario/evaonline.git
   cd evaonline
   docker-compose up

docker-compose.yml automaticamente:
   1. Faz PULL das imagens oficiais do DockerHub
   2. Faz BUILD de evaonline-runtime (do Dockerfile local)
   3. Orquestra tudo via network Docker
```

### Opção B: Stack Completo Pré-packaged (Para Production)

```
Se quisermos distribuir TUDO junto (não é comum):

O QUE CRIAMOS: evaonline-stack:latest (2.5GB)
   ├─ postgresql:15-alpine (390MB)
   ├─ redis:7-alpine (60MB)
   ├─ prometheus:latest (150MB)
   ├─ grafana:latest (200MB)
   ├─ pgadmin4:latest (100MB)
   ├─ nginx:alpine (10MB)
   ├─ evaonline-api (600MB)
   └─ docker-compose.yml pré-configurado

COMO O USUÁRIO USA:
   docker pull evaonline/evaonline-stack:latest
   docker-compose -f evaonline-stack.yml up

MAS PROBLEMAS:
   • Imagem gigante (2.5GB)
   • Difícil de atualizar (tem que rebuildar tudo)
   • Não segue boas práticas Docker
   • NÃO É RECOMENDADO
```

---

## 🎯 ESTRUTURA ATUAL (A QUE VAMOS FAZER)

### O Arquivo que O Usuário Recebe:

```
repositório (GitHub)
│
├─ Dockerfile ← Descreve como BUILD evaonline-runtime
├─ docker-compose.yml ← Orquestra os containers
├─ entrypoint.sh ← Script que executa baseado em SERVICE env var
│
├─ requirements/
│  ├─ base.txt (deps gerais)
│  ├─ production.txt (deps production)
│  └─ development.txt (deps dev)
│
├─ backend/
├─ frontend/
├─ config/
└─ ... (resto do projeto)
```

### O Que Acontece Quando o Usuário Faz `docker-compose up`:

```
PASSO 1: docker-compose lê docker-compose.yml

PASSO 2: Faz PULL das imagens base (se não existem):
   ✅ docker pull postgres:15-alpine
   ✅ docker pull redis:7-alpine
   ✅ docker pull prometheus:latest
   ✅ docker pull grafana:latest
   ✅ docker pull dpage/pgadmin4:latest
   ✅ docker pull nginx:alpine
   (Estas já existem prontas no DockerHub oficial)

PASSO 3: Faz BUILD da imagem customizada:
   ✅ docker build -t evaonline-runtime:latest .
   (Usa Dockerfile local + requirements + código)

PASSO 4: Cria NETWORK para comunicação:
   ✅ docker network create evaonline_default

PASSO 5: Inicia cada container:
   ✅ docker run postgres:15-alpine → evaonline-postgres
   ✅ docker run redis:7-alpine → evaonline-redis
   ✅ docker run evaonline-runtime (SERVICE=api) → evaonline-api
   ✅ docker run evaonline-runtime (SERVICE=worker) → evaonline-celery-worker
   ✅ docker run evaonline-runtime (SERVICE=beat) → evaonline-celery-beat
   ✅ docker run evaonline-runtime (SERVICE=flower) → evaonline-flower
   ✅ docker run prometheus:latest → evaonline-prometheus
   ✅ docker run grafana:latest → evaonline-grafana
   ✅ docker run dpage/pgadmin4:latest → evaonline-pgadmin
   (Opcional: portainer, nginx, etc)

PASSO 6: Containers se comunicam:
   evaonline-api:8000 <→ evaonline-postgres:5432
   evaonline-api:8000 <→ evaonline-redis:6379
   evaonline-celery-worker:* <→ evaonline-redis:6379
   ... (tudo communicando via network interna Docker)
```

---

## 📊 TAMANHOS REAIS

### O Que O Usuário Faz Download:

```
git clone → ~500MB (apenas código-fonte)
   ├─ Dockerfile
   ├─ docker-compose.yml
   ├─ código-fonte
   └─ requirements

NÃO faz download das imagens (não estão em git!)
```

### O Que Docker Faz Download:

```
docker-compose up → Faz PULL automático

✅ postgresql:15-alpine → 390MB (primeira vez)
✅ redis:7-alpine → 60MB (primeira vez)
✅ prometheus:latest → 150MB (primeira vez)
✅ grafana:latest → 200MB (primeira vez)
✅ dpage/pgadmin4:latest → 100MB (primeira vez)
✅ nginx:alpine → 10MB (primeira vez)
✅ BUILD evaonline-runtime → 600MB (primeira vez)

PRIMEIRA EXECUÇÃO: ~1.5GB download
EXECUTAÇÕES SEGUINTES: Apenas novos/atualizados

IMPORTANTE: Estas imagens são COMPARTILHADAS entre projetos!
Se você tiver outro projeto que usa postgresql:15-alpine,
reutiliza a mesma imagem (não baixa de novo)
```

---

## 🚀 O QUE SUBIMOS AO DOCKERHUB

```
evaonline/evaonline-runtime:latest (600MB)

Quando user faz:
   docker pull evaonline/evaonline-runtime:latest

Ele recebe APENAS:
   • Python 3.10-slim
   • requirements/production.txt instalados
   • código-fonte do projeto
   • entrypoint.sh

ELE NÃO RECEBE (porque não estão aqui, estão oficiais):
   • PostgreSQL
   • Redis
   • Prometheus
   • Grafana
   • etc

PARA USAR NOSSA IMAGEM:
   # Opção 1: Com docker-compose (recomendado)
   git clone ... && docker-compose up

   # Opção 2: Apenas nossa imagem
   docker pull evaonline/evaonline-runtime:latest
   docker run evaonline/evaonline-runtime:latest
   (Mas precisa ter PostgreSQL/Redis rodando em outro lugar)
```

---

## ✅ RESPOSTA RESUMIDA ÀS SUAS DÚVIDAS

### Pergunta 1: "Portainer está faltando?"

```
✅ SIM, deve estar no docker-compose.yml
   image: portainer/portainer-ce:latest

PERFIL:
   profiles:
     - development
   (opcional, só em desenvolvimento)
```

### Pergunta 2: "Quando puxamos do DockerHub, vem tudo junto?"

```
❌ NÃO! Cada imagem é independente

postgresql:15-alpine = APENAS PostgreSQL
redis:7-alpine = APENAS Redis
etc

Docker Compose é que ORQUESTRA para funcionarem juntos
(via network interna, volumes compartilhados, env vars, etc)
```

### Pergunta 3: "Deveria ser evaonline-api com tudo empacotado?"

```
❌ NÃO, estrutura correta é:

docker-compose.yml
├─ postgresql:15-alpine (imagem oficial)
├─ redis:7-alpine (imagem oficial)
├─ prometheus:latest (imagem oficial)
├─ grafana:latest (imagem oficial)
├─ pgadmin4:latest (imagem oficial)
├─ nginx:alpine (imagem oficial)
├─ portainer:latest (imagem oficial - OPCIONAL)
└─ evaonline-runtime:latest (NOSSA imagem, buildada)
   ├─ api (SERVICE=api)
   ├─ worker (SERVICE=worker)
   ├─ beat (SERVICE=beat)
   └─ flower (SERVICE=flower)

USUÁRIO FAZ:
   git clone https://github.com/seu-usuario/evaonline.git
   cd evaonline
   docker-compose up

PRONTO! Tudo rodando!

(Não precisa saber de Docker, não precisa dar
 docker pull postgresql, docker run redis, etc)
```

---

## 📋 CHECKLIST FINAL

### O Que Guardamos em Git:
- ✅ Dockerfile (como BUILD a imagem)
- ✅ docker-compose.yml (como ORQUESTAR)
- ✅ entrypoint.sh (o que RODAR em cada container)
- ✅ requirements/ (dependências Python)
- ✅ Código-fonte (backend, frontend, config)

### O Que Guardamos no DockerHub (Nosso Registry):
- ✅ evaonline/evaonline-runtime:latest (600MB)
  - Contém: Python + deps + código compilado
  - Used by: 4 serviços (api, worker, beat, flower)

### O Que Puxamos do DockerHub Oficial:
- ✅ library/postgresql:15-alpine
- ✅ library/redis:7-alpine
- ✅ library/prometheus
- ✅ library/grafana
- ✅ dpage/pgadmin4
- ✅ library/nginx:alpine
- ✅ portainer/portainer-ce (OPCIONAL)

### O Que o Usuário Faz:
```bash
git clone https://github.com/seu-usuario/evaonline.git
cd evaonline
docker-compose up

# Prontinho! Tudo rodando em ~2 minutos
# Na primeira vez, faz download das imagens
# Nas seguintes, só usa o cache
```

---

## 🎯 RESUMO VISUAL

```
┌─────────────────────────────────────────────────────────┐
│                    USUÁRIO                              │
│                                                         │
│  $ docker-compose up                                    │
│                                                         │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌───────────┐ ┌──────────────────┐
│   Git Clone  │ │DockerHub  │ │ BUILD Local      │
│              │ │ Oficial   │ │                  │
│Dockerfile   │ │           │ │ evaonline-       │
│docker-      │ │ postgres  │ │ runtime:latest   │
│compose.yml  │ │ redis     │ │ (600MB)          │
│código       │ │ prometheus│ │                  │
│             │ │ grafana   │ │ Usa Dockerfile   │
│(~500MB)     │ │ pgadmin   │ │ + requirements   │
│             │ │ nginx     │ │                  │
│             │ │ portainer │ │                  │
│             │ │ (~1.1GB)  │ │                  │
└──────────────┘ └───────────┘ └──────────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  Docker Network (evaonline)  │
        │                              │
        │ ┌─────────────────────────┐  │
        │ │ postgres:5432           │  │
        │ └─────────────────────────┘  │
        │ ┌─────────────────────────┐  │
        │ │ redis:6379              │  │
        │ └─────────────────────────┘  │
        │ ┌─────────────────────────┐  │
        │ │ api:8000                │  │
        │ │ worker:*                │  │
        │ │ beat:*                  │  │
        │ │ flower:5555             │  │
        │ └─────────────────────────┘  │
        │ ┌─────────────────────────┐  │
        │ │ prometheus:9090         │  │
        │ │ grafana:3000            │  │
        │ │ pgadmin:5050            │  │
        │ │ portainer:9000          │  │
        │ └─────────────────────────┘  │
        └──────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   USER ACESSA                │
        │                              │
        │ http://localhost:8000 - API  │
        │ http://localhost:5555 - Flow │
        │ http://localhost:3000 - Graf │
        │ http://localhost:5050 - PgA  │
        │ http://localhost:9000 - Port │
        └──────────────────────────────┘
```

---

## 🚀 PRÓXIMOS PASSOS

1. **Atualizar docker-compose.yml** com estructura correta
2. **Verificar entrypoint.sh** funciona com SERVICE env var
3. **BUILD ÚNICA VEZ**: `docker build -t evaonline-runtime:latest .`
4. **PUXAR imagens base**: Docker faz automaticamente
5. **RODAR**: `docker-compose up -d`
6. **TESTAR**: `http://localhost:8000`
7. **PUBLICAR**: `docker push evaonline/evaonline-runtime:latest`

Entendido agora? Quer que a gente implemente isso passo a passo?
