# 🚀 GUIA DE INÍCIO RÁPIDO - EVAonline

**Última atualização:** 14 de Janeiro de 2025

---

## 📋 Pré-requisitos

- Python 3.10+
- Docker Desktop
- Git
- PostgreSQL 15+ (ou via Docker)
- Redis 7+ (ou via Docker)

---

## 🎯 Setup Rápido (5 minutos)

### 1️⃣ Clonar e Configurar

```powershell
# Clonar repositório
git clone https://github.com/angelassilviane/Evaonline_Temp.git
cd Evaonline_Temp

# Criar e ativar ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependências (produção + desenvolvimento)
pip install --upgrade pip
pip install -r requirements.txt

# Configurar pre-commit hooks
pre-commit install
```

### 2️⃣ Configurar Ambiente

```powershell
# Copiar arquivo de exemplo
Copy-Item .env.example .env

# Editar .env com suas configurações
notepad .env
```

**Configurações mínimas necessárias:**
```ini
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=evaonline
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha_aqui

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Secret
SECRET_KEY=sua-chave-secreta-min-32-caracteres
```

### 3️⃣ Iniciar Serviços Docker

```powershell
# Iniciar PostgreSQL + Redis
docker-compose up -d postgres redis

# Verificar se estão rodando
docker-compose ps
```

### 4️⃣ Configurar Banco de Dados

```powershell
# Criar banco de dados (se necessário)
# Ver: database/init_alembic.py

# Rodar migrações
alembic upgrade head
```

### 5️⃣ Rodar Testes

```powershell
# Rodar todos os testes
pytest

# Ou usar o script interativo
.\scripts\run_tests.ps1
```

---

## 🐳 Opção: Tudo no Docker

Se preferir rodar tudo no Docker:

```powershell
# Build da imagem
docker build -t evaonline:dev --target development .

# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Acessar aplicação
# FastAPI: http://localhost:8000
# Dash: http://localhost:8050
# Grafana: http://localhost:3000
```

---

## 📝 Comandos Úteis

### Desenvolvimento

```powershell
# Formatar código
black backend/ tests/

# Organizar imports
isort backend/ tests/

# Linting
flake8 backend/ tests/

# Type checking
mypy backend/

# Rodar pre-commit em todos os arquivos
pre-commit run --all-files
```

### Testes

```powershell
# Testes unitários
pytest -m unit

# Testes de integração
pytest -m integration

# Testes com coverage
pytest --cov=backend --cov-report=html

# Abrir relatório de coverage
start htmlcov/index.html
```

### Docker

```powershell
# Ver logs de um serviço
docker-compose logs -f backend

# Reiniciar serviço
docker-compose restart backend

# Parar todos os serviços
docker-compose down

# Parar e remover volumes
docker-compose down -v

# Rebuild imagem
docker-compose build --no-cache backend
```

### Database

```powershell
# Conectar ao PostgreSQL
docker-compose exec postgres psql -U postgres -d evaonline

# Criar migration
alembic revision --autogenerate -m "Description"

# Aplicar migrations
alembic upgrade head

# Reverter última migration
alembic downgrade -1
```

### Redis

```powershell
# Conectar ao Redis
docker-compose exec redis redis-cli

# Ver todas as chaves
docker-compose exec redis redis-cli KEYS '*'

# Limpar todos os dados
docker-compose exec redis redis-cli FLUSHALL
```

### Celery

```powershell
# Iniciar worker
celery -A backend.infrastructure.celery.app worker --loglevel=info

# Ver tarefas ativas
celery -A backend.infrastructure.celery.app inspect active

# Ver workers registrados
celery -A backend.infrastructure.celery.app inspect registered
```

---

## 🔍 Verificar Instalação

Execute estes comandos para verificar se tudo está funcionando:

```powershell
# 1. Verificar versão Python
python --version  # Deve ser 3.10+

# 2. Verificar dependências instaladas
pip list

# 3. Verificar serviços Docker
docker-compose ps

# 4. Rodar smoke tests
pytest -m smoke -v

# 5. Verificar health da API
curl http://localhost:8000/api/v1/health
```

**Resultado esperado:**
```json
{
  "status": "healthy",
  "service": "evaonline",
  "version": "1.0.0"
}
```

---

## 🛠️ Troubleshooting

### Problema: Erro ao instalar dependências

**Solução:**
```powershell
# Atualizar pip
python -m pip install --upgrade pip setuptools wheel

# Instalar com verbose
pip install -r requirements.txt -v
```

### Problema: Docker não inicia

**Solução:**
```powershell
# Ver logs detalhados
docker-compose logs

# Remover containers antigos
docker-compose down -v
docker-compose up -d
```

### Problema: Erro de conexão com PostgreSQL

**Solução:**
```powershell
# Verificar se PostgreSQL está rodando
docker-compose ps postgres

# Verificar logs
docker-compose logs postgres

# Testar conexão
docker-compose exec postgres psql -U postgres -c "SELECT 1"
```

### Problema: Erro de conexão com Redis

**Solução:**
```powershell
# Verificar se Redis está rodando
docker-compose ps redis

# Testar conexão
docker-compose exec redis redis-cli PING
```

### Problema: Testes falhando

**Solução:**
```powershell
# Limpar cache
pytest --cache-clear

# Reinstalar dependências de teste
pip install pytest pytest-cov pytest-asyncio -U

# Rodar com verbose
pytest -vv
```

---

## 📚 Próximos Passos

Após o setup, consulte:

1. **[IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md)** - Resumo de todas as melhorias
2. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Estrutura do projeto
3. **[API.md](api/API.md)** - Documentação da API
4. **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Como contribuir

---

## 🆘 Ajuda

- **Documentação:** [docs/](.)
- **Issues:** [GitHub Issues](https://github.com/angelassilviane/Evaonline_Temp/issues)
- **Email:** angelassilviane@gmail.com

---

## ✅ Checklist de Verificação

Use este checklist para confirmar que tudo está funcionando:

- [ ] Python 3.10+ instalado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas (`requirements.txt`)
- [ ] Pre-commit hooks configurados
- [ ] Arquivo `.env` criado e configurado
- [ ] Docker Desktop rodando
- [ ] PostgreSQL iniciado e conectando
- [ ] Redis iniciado e conectando
- [ ] Migrations aplicadas
- [ ] Testes passando (`pytest`)
- [ ] API respondendo em http://localhost:8000
- [ ] Dashboard respondendo em http://localhost:8050

**Se todos os itens estiverem marcados, você está pronto para desenvolver! 🎉**
