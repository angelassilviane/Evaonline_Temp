# 🔍 Revisão de Configurações - EVAonline

**Data:** 2025-10-14  
**Objetivo:** Identificar e corrigir problemas de configuração relacionados ao PostgreSQL e UTF-8

---

## 📋 Problemas Identificados

### 🔴 **PROBLEMA 1: Inconsistência de Credenciais PostgreSQL**

#### **Localização:**
- `config/settings/app_settings.py` - Credenciais padrão
- `docker-compose.yml` - Credenciais para containers
- `tests/integration/test_docker_services.py` - Credenciais para testes

#### **Inconsistências Encontradas:**

| Arquivo | User | Password | Database |
|---------|------|----------|----------|
| `app_settings.py` (linha 38-40) | `postgres` | `postgres` | `evaonline` |
| `docker-compose.yml` (linha 37-39) | `evaonline` | `evaonline` | `evaonline` |
| `test_docker_services.py` (linha 27-29) | `evaonline` | `` (vazio) | `evaonline` |

#### **Impacto:**
- ❌ Testes falham com erro de autenticação
- ❌ Aplicação não consegue conectar ao banco em produção
- ❌ Configurações conflitantes entre ambientes

---

### 🔴 **PROBLEMA 2: Erro UTF-8 no Windows com psycopg2**

#### **Causa Raiz:**
O caminho do projeto contém caractere especial: `C:\Users\User\OneDrive\Documentos` (ç em "Documentos")

- Byte problemático: `0xe7` (ç em encoding não-UTF-8)
- Driver psycopg2 tenta decodificar como UTF-8 → **UnicodeDecodeError**

#### **Erro:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe7 in position 78: invalid continuation byte
```

#### **Tentativas Anteriores (FALHARAM):**
1. ✗ Usar psycopg3 (postgresql+psycopg://) - Falha de autenticação
2. ✗ Adicionar `client_encoding=utf8` em connect_args - Erro persiste
3. ✗ Configurar pg_hba.conf para trust - Erro persiste

---

### 🟡 **PROBLEMA 3: Configuração pg_hba.conf Complexa**

#### **Situação Atual:**
- Script `init-db/99-configure-pg-hba.sh` remove linha `scram-sha-256`
- Adiciona regra `trust` para `0.0.0.0/0` (todo mundo sem senha!)
- Mas testes ainda falham com erro de autenticação

#### **Problemas de Segurança:**
- 🔓 **INSEGURO:** `host all all 0.0.0.0/0 trust` permite acesso sem senha de qualquer IP!
- Adequado apenas para **desenvolvimento local**, não produção

---

### 🟡 **PROBLEMA 4: Dockerfile Multi-Stage com Stage Desnecessário**

#### **Issue:**
- Stage 3 (development) reinstala ferramentas de build sem necessidade
- `requirements.txt` já contém todas as dependências

#### **Otimização Possível:**
- Remover instalação duplicada de dependências
- Consolidar desenvolvimento e runtime

---

### 🟡 **PROBLEMA 5: Entrypoint.sh com Lógica Complexa**

#### **Issues:**
- Comando `nc -z` para verificar portas (netcat-traditional instalado)
- Aguarda 30 tentativas (60 segundos) que pode ser muito tempo
- Erro de importação em verificação do banco: `from database.connection import get_db`

---

## ✅ Soluções Propostas

### **SOLUÇÃO 1: Padronizar Credenciais**

**Opção A - Usar `evaonline/evaonline` (Recomendado):**
```python
# config/settings/app_settings.py
POSTGRES_USER: str = os.getenv("POSTGRES_USER", "evaonline")  # ← MUDAR
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "evaonline")  # ← MUDAR
```

**Vantagens:**
- ✅ Consistente com docker-compose.yml
- ✅ Menos confusão (user ≠ postgres)
- ✅ Melhor para produção (não usa user padrão)

**Opção B - Criar arquivo `.env` na raiz:**
```bash
# .env
POSTGRES_USER=evaonline
POSTGRES_PASSWORD=evaonline
POSTGRES_DB=evaonline
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

---

### **SOLUÇÃO 2: Resolver Erro UTF-8 no Windows**

**Opção A - Definir PYTHONUTF8=1 (Mais Simples):**
```powershell
# No PowerShell ou adicionar ao .env
$env:PYTHONUTF8=1
```

**Opção B - Usar pytest.ini para definir variável:**
```ini
# pytest.ini
[pytest]
env = 
    PYTHONUTF8=1
```

**Opção C - Conectar via IP ao invés de localhost:**
```python
# tests/integration/test_docker_services.py
host = os.getenv("POSTGRES_HOST", "127.0.0.1")  # ← IP direto
```

**Opção D - Mover projeto para pasta sem acentos:**
```
C:\Users\User\OneDrive\Documents\GitHub\...  # ← Sem acento
```

---

### **SOLUÇÃO 3: Simplificar pg_hba.conf**

**Para desenvolvimento local:**
```conf
# database/config/pg_hba_extra.conf
# IPv4/IPv6 localhost - sem senha (desenvolvimento)
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust

# Conexões externas - COM senha (produção)
host    all             all             0.0.0.0/0               scram-sha-256
```

**Modificar script:**
```bash
# init-db/99-configure-pg-hba.sh
#!/bin/bash
echo "Configurando pg_hba.conf para desenvolvimento..."

# Remove regra genérica insegura
sed -i '/^host all all all scram-sha-256/d' "$PGDATA/pg_hba.conf"

# Adiciona regras específicas
cat /tmp/pg_hba_extra.conf >> "$PGDATA/pg_hba.conf"

# Recarrega configuração
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_reload_conf();" || true
```

---

### **SOLUÇÃO 4: Otimizar Dockerfile**

```dockerfile
# Stage 3: Development - SIMPLIFICADO
FROM runtime as development

LABEL stage="development"

# Manter user evaonline
USER evaonline

# Ativar reload automático em dev (já tem dependências instaladas)
ENV FASTAPI_RELOAD=true \
    DASH_DEBUG=true \
    PYTHONPATH=/app
```

---

### **SOLUÇÃO 5: Simplificar Entrypoint**

```bash
# Remover verificação de importação que pode falhar
# echo "Verificando migrações do banco de dados..."
# python -c "from database.connection import get_db; ..." || echo "..."

# Substituir por:
echo "Aguardando PostgreSQL estar pronto..."
# Continua com wait_for_service que já funciona
```

---

## 🎯 Plano de Ação Recomendado

### **Prioridade 1 - CRÍTICO (Resolver Agora):**
1. ✅ Padronizar credenciais para `evaonline/evaonline` em todos os arquivos
2. ✅ Definir `PYTHONUTF8=1` no ambiente de testes
3. ✅ Ajustar `test_docker_services.py` para conectar com credenciais corretas

### **Prioridade 2 - IMPORTANTE (Próxima Sessão):**
4. ⚠️ Criar arquivo `.env` na raiz com todas as variáveis
5. ⚠️ Simplificar pg_hba.conf (trust localhost, senha externa)
6. ⚠️ Atualizar documentação com configurações corretas

### **Prioridade 3 - MELHORIAS (Futuro):**
7. 💡 Otimizar Dockerfile removendo stages desnecessários
8. 💡 Simplificar entrypoint.sh removendo verificações que falham
9. 💡 Adicionar validação de configuração na inicialização

---

## 📝 Checklist de Arquivos a Modificar

- [ ] `config/settings/app_settings.py` - Mudar credenciais padrão
- [ ] `tests/integration/test_docker_services.py` - Corrigir credenciais e conexão
- [ ] `.env` (criar) - Centralizar variáveis de ambiente
- [ ] `pytest.ini` - Adicionar PYTHONUTF8=1
- [ ] `database/config/pg_hba_extra.conf` - Ajustar regras de segurança
- [ ] `init-db/99-configure-pg-hba.sh` - Simplificar script
- [ ] `Dockerfile` - Remover duplicações
- [ ] `entrypoint.sh` - Remover verificações problemáticas
- [ ] `docs/QUICKSTART.md` - Atualizar com configurações corretas

---

## 🚀 Próximos Passos

**AGORA:**
1. Executar SOLUÇÃO 1 (padronizar credenciais)
2. Executar SOLUÇÃO 2-A (definir PYTHONUTF8=1)
3. Rodar testes novamente

**Se ainda falhar:**
- Analisar logs detalhados com `-vv`
- Verificar se PostgreSQL está realmente aceitando conexões
- Testar conexão direta com `psql` de fora do container

**Após testes passarem:**
- Criar arquivo .env
- Atualizar documentação
- Fazer commit das mudanças

---

## ⚡ Quick Fix - Comando Único

```powershell
# Definir UTF-8 e rodar testes
$env:PYTHONUTF8=1; $env:POSTGRES_USER="evaonline"; $env:POSTGRES_PASSWORD="evaonline"; C:/Users/User/OneDrive/Documentos/GitHub/Evaonline_Temp/.venv/Scripts/python.exe -m pytest tests/integration/test_docker_services.py -v
```
