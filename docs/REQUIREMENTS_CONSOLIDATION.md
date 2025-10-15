# 📦 Consolidação de Requirements

**Data:** 14 de Outubro de 2025

## 🎯 Mudança Realizada

Consolidamos `requirements.txt` e `requirements-dev.txt` em um **único arquivo** `requirements.txt`.

## ✅ Motivação

### Antes:
- ❌ Dois arquivos separados (`requirements.txt` + `requirements-dev.txt`)
- ❌ Confusão sobre qual instalar
- ❌ Risco de inconsistências entre ambientes
- ❌ Manutenção duplicada

### Depois:
- ✅ **Um único arquivo** com todas as dependências
- ✅ Instalação simples: `pip install -r requirements.txt`
- ✅ Sem duplicação ou referências circulares
- ✅ Mais fácil de manter

## 📋 Estrutura do requirements.txt

O arquivo consolidado contém **todas as dependências** organizadas por categoria:

```
requirements.txt (único arquivo)
├── Core Web Framework (FastAPI, Uvicorn, Pydantic)
├── Async & HTTP (aiohttp, httpx, httpie)
├── Database & ORM (PostgreSQL, SQLAlchemy, pgcli)
├── Caching & Message Broker (Redis, Celery)
├── Data Processing (Pandas, NumPy, Scikit-learn)
├── Geospatial (GeoPandas, Shapely, PyProj)
├── Dashboard & Web UI (Dash, Plotly, Flask)
├── API Clients (Requests, Requests-cache)
├── Data Formats (xarray, netCDF4)
├── Utilities (dateutil, pytz, loguru, tqdm)
├── Validation & Serialization
├── Security & Auth (detect-secrets, bandit, safety)
├── Testing Framework (pytest + extensões)
├── Code Quality & Formatters (black, isort, autopep8)
├── Linters (flake8, pylint, ruff)
├── Type Checking (mypy + types-*)
├── Pre-commit & Hooks
├── Documentation (mkdocs, mkdocs-material)
└── Debugging & Profiling (ipdb, ipython, py-spy)
```

## 🔧 Comandos Atualizados

### Instalação

```powershell
# Instalar TODAS as dependências (produção + desenvolvimento)
pip install -r requirements.txt

# Atualizar dependências
pip install --upgrade -r requirements.txt

# Reinstalar (limpar cache)
pip install -r requirements.txt --force-reinstall
```

### Não precisa mais de:
```powershell
# ❌ ANTES (não usar mais)
pip install -r requirements-dev.txt
```

## 📝 Arquivos Atualizados

Os seguintes arquivos foram atualizados para refletir a mudança:

1. ✅ `requirements.txt` - Consolidado com todas as dependências
2. ✅ `requirements-dev.txt` - **REMOVIDO**
3. ✅ `Dockerfile` - Removida referência a requirements-dev.txt
4. ✅ `docs/QUICKSTART.md` - Comandos atualizados
5. ✅ `docs/TESTING_GUIDE.md` - Comandos atualizados
6. ✅ `docs/IMPROVEMENTS_SUMMARY.md` - Documentação atualizada

## 🚀 Próximos Passos

Se você já tinha o ambiente configurado:

```powershell
# 1. Atualizar dependências
pip install -r requirements.txt --upgrade

# 2. Verificar instalação
pip list

# 3. Rodar testes para confirmar
pytest
```

## 💡 Vantagens

1. **Simplicidade:** Um único comando para instalar tudo
2. **Consistência:** Mesmo ambiente para todos os desenvolvedores
3. **Manutenção:** Atualizar um único arquivo
4. **Produção:** Pode usar o mesmo arquivo com `--no-dev` flags se necessário
5. **Docker:** Builds mais simples e diretos
6. **CI/CD:** Menos complexidade nos workflows

## 📖 Referências

- `requirements.txt` - Arquivo consolidado na raiz do projeto
- `docs/QUICKSTART.md` - Guia de instalação atualizado
- `docs/IMPROVEMENTS_SUMMARY.md` - Documentação completa das melhorias

---

**Nota:** Esta mudança **não afeta a funcionalidade** do projeto. É apenas uma reorganização para simplificar o gerenciamento de dependências.
