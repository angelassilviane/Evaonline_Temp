# 📦 Requirements - EVAonline

Este diretório contém as dependências Python do projeto organizadas em **3 níveis**:

## 📋 Estrutura

```
requirements/
├── base.txt          ← Pacotes COMUNS (50 pacotes, ~400MB)
├── production.txt    ← Base + Production (60 pacotes, ~500MB)
├── development.txt   ← Base + Production + Dev (100 pacotes, ~700MB)
└── README.md         ← Este arquivo
```

---

## 🎯 Quando Usar

### 1️⃣ **Ambiente de Produção (Docker)**
```bash
# Docker (na imagem final)
pip install -r requirements/production.txt

# Resultado: ~500MB de dependências
# ✅ Mínimo necessário
# ✅ Sem ferramentas de desenvolvimento
# ✅ Sem testes, linters, profilers
```

**Tamanho Docker**: ~600-700MB (imagem final)

---

### 2️⃣ **Desenvolvimento Local**
```bash
# Seu computador (desenvolvimento)
pip install -r requirements/development.txt

# Resultado: ~700MB de dependências  
# ✅ Tudo para programar
# ✅ Testes (pytest)
# ✅ Linters (flake8, pylint, ruff)
# ✅ Formatters (black, isort)
# ✅ Debugging (ipdb, ipython)
# ✅ Profilers (py-spy, memory-profiler)
# ✅ Documentação (mkdocs)
```

---

### 3️⃣ **CI/CD Pipeline**
```bash
# Em pipelines de teste/build
pip install -r requirements/development.txt

# Roda:
# - Testes (pytest)
# - Linting (flake8, pylint, ruff)
# - Type checking (mypy)
# - Security (bandit, safety)
# - Coverage reports
```

---

## 📊 Comparação

| Aspecto | Base | Production | Development |
|---------|------|------------|-------------|
| **Pacotes** | 50 | ~60 | ~100 |
| **Tamanho** | ~400MB | ~500MB | ~700MB |
| **Produção** | ✅ | ✅ | ✅ |
| **Desenvolvimento** | ❌ | ❌ | ✅ |
| **Testes** | ❌ | ❌ | ✅ |
| **Linters** | ❌ | ❌ | ✅ |
| **Documentação** | ❌ | ❌ | ✅ |

---

## 🚀 Instalação Rápida

### Primeira Vez
```bash
# 1. Criar venv
python -m venv .venv

# 2. Ativar venv
.\.venv\Scripts\Activate.ps1    # Windows PowerShell
# ou
source .venv/bin/activate       # Linux/Mac

# 3. Instalar (escolha uma):

# Para desenvolvimento (RECOMENDADO)
pip install -r requirements/development.txt

# Ou para produção apenas
pip install -r requirements/production.txt
```

### Atualizar Dependências
```bash
# Se arquivo base.txt mudou
pip install --upgrade -r requirements/base.txt

# Se arquivo production.txt mudou
pip install --upgrade -r requirements/production.txt

# Se arquivo development.txt mudou
pip install --upgrade -r requirements/development.txt
```

---

## 📝 Significado dos Arquivos

### `base.txt` - Pacotes Essenciais
**Incluem:**
- FastAPI + Uvicorn (web framework)
- PostgreSQL + SQLAlchemy (database)
- Redis + Celery (caching/async)
- Pandas + NumPy + SciPy (data processing)
- Dash + Plotly (dashboard)
- GeoPandas (geospatial)
- Climate APIs (openmeteo)

**NÃO incluem:**
- Testes
- Linters
- Profilers
- Documentação

### `production.txt` - Adiciona Production-Specific
**Inclui todo base.txt +:**
- MyPy (type checking em CI/CD)
- Bandit + Safety (security scanning)
- Flask-Caching
- Prometheus exporters
- Email validation

**NÃO inclui:**
- Testes
- Linters
- Debugging tools
- Documentação

### `development.txt` - Adiciona Everything
**Inclui todo production.txt +:**
- Pytest + plugins (testes)
- Black + Isort + Autopep8 (formatters)
- Flake8 + Pylint + Ruff (linters)
- MyPy types (type checking)
- IPython + IPDb (debugging)
- Profilers (py-spy, memory-profiler)
- Mkdocs (documentação)

---

## ✅ Checklist de Instalação

### Após instalar dependências, valide:

```bash
# 1. Verificar Python
python --version
# Esperado: Python 3.10+

# 2. Verificar venv
which python  # Linux/Mac
# ou
Get-Command python  # Windows

# 3. Testar imports principais
python -c "import fastapi, sqlalchemy, pandas, dash; print('✅ OK')"

# 4. Testar CLI
pytest --version
black --version
flake8 --version

# 5. Listar pacotes instalados
pip list | wc -l  # Linux/Mac
# ou
(pip list | Measure-Object -Line).Lines  # Windows
```

---

## 🔄 Mantendo Atualizado

### Adicionar novo package
```bash
# 1. Decida se é:
#    - Common (base.txt)
#    - Production-specific (production.txt)
#    - Development-only (development.txt)

# 2. Adicione a seção correta:
#    Manutenha as seções comentadas
#    Use version pinning: package>=X.Y.Z,<X.(Y+1).0

# 3. Reinstale:
pip install -r requirements/development.txt

# 4. Teste:
python -c "import new_package; print('✅')"
```

### Remover package
```bash
# 1. Remova do arquivo correto
# 2. Limpe venv:
pip uninstall package_name

# 3. Reinstale:
pip install -r requirements/development.txt
```

---

## 🐳 Dockerfile Integration

```dockerfile
# Production build
FROM python:3.10-slim
COPY requirements/production.txt .
RUN pip install -r production.txt

# Development build
FROM python:3.10-slim
COPY requirements/production.txt .
COPY requirements/development.txt .
RUN pip install -r development.txt
```

---

## 📊 Histórico de Mudanças

**2025-10-22**: Criação da estrutura requirements/ 3-tier
- Separado de 159 pacotes monolíticos em 3 arquivos lógicos
- ~60% redução em imagem Docker (production)
- Melhor manutenibilidade

---

## ❓ FAQ

### P: Por que 3 arquivos e não 1?
R: Porque:
- Docker production não precisa de pytest, linters, profilers
- Development local precisa de tudo
- CI/CD reutiliza production.txt

### P: Posso usar apenas base.txt?
R: Sim! Mas faltarão ferramentas importantes como pytest, black, flake8.

### P: Como saber se um package vai em qual arquivo?
R: Regra simples:
- **Base**: Usado em produção? SIM → base.txt
- **Production**: Apenas produção? SIM → production.txt
- **Development**: Apenas dev/test? SIM → development.txt

### P: Preciso reinstalar tudo se editar um arquivo?
R: Não! Apenas rode novamente:
```bash
pip install -r requirements/development.txt
```

---

**Última atualização**: 2025-10-22  
**Documentação**: v1.0  
**Status**: ✅ Pronto para uso
