# 🧹 PLANO DE LIMPEZA - EVAonline

**Data:** 14 de Janeiro de 2025  
**Objetivo:** Remover arquivos obsoletos e limpar cache do Docker

---

## 📋 ANÁLISE DE ARQUIVOS OBSOLETOS

### 🗑️ Arquivos para DELETAR da pasta `docs/`

#### Documentos de Auditoria/Status Antigos (já integrados em IMPROVEMENTS_SUMMARY.md)
- ❌ `PROJECT_STATUS.md` - Status de 09/out/2025, obsoleto
- ❌ `API_LIMITATIONS_CORRECTED.md` - Auditoria antiga
- ❌ `CLIMATE_API_AUDIT.md` - Auditoria antiga
- ❌ `CLIMATE_API_VALIDATION.md` - Validação antiga
- ❌ `CSS_AUDIT_REPORT.md` - Auditoria CSS antiga
- ❌ `CACHE_AND_CLIENTS_SUMMARY.md` - Resumo antigo

#### Documentos de Planejamento Obsoletos
- ❌ `CELERY_REDIS_NEXT_STEPS.md` - Já implementado
- ❌ `CLIMATE_API_ACTION_PLAN.md` - Plano antigo
- ❌ `DATA_PIPELINE_REFACTORING_PLAN.md` - Refatoração antiga
- ❌ `ADDITIONAL_CLIMATE_SOURCES_RESEARCH.md` - Pesquisa antiga

#### Documentos Substituídos
- ❌ `VISUAL_TEST_CHECKLIST.md` - Substituído por TESTING_GUIDE.md
- ❌ `PROJECT_ORGANIZATION.md` - Substituído por PROJECT_STRUCTURE.md

### ✅ Arquivos para MANTER

#### Essenciais (criados recentemente)
- ✅ `IMPROVEMENTS_SUMMARY.md` - Resumo de todas melhorias (NOVO)
- ✅ `QUICKSTART.md` - Guia de início rápido (NOVO)
- ✅ `TESTING_GUIDE.md` - Guia completo de testes (NOVO)

#### Importantes
- ✅ `PROJECT_STRUCTURE.md` - Estrutura do projeto
- ✅ `REQUIREMENTS.md` - Requisitos
- ✅ `ROADMAP.md` - Roadmap futuro
- ✅ `DATABASE_README.md` - Documentação do banco
- ✅ `DOCKER_PROFILES.md` - Profiles do Docker
- ✅ `MONITORING.md` - Arquitetura de monitoramento
- ✅ `MONITORING_QUICKSTART.md` - Guia rápido de monitoramento
- ✅ `MONITORING_ARCHITECTURE.md` - Arquitetura de monitoramento

#### Específicos Técnicos (manter por referência)
- ✅ `MUNDIAL_MAP_SOURCE_SELECTION.md` - Seleção de fontes (importante)
- ✅ `CLIMATE_SOURCES_ARCHITECTURE.md` - Arquitetura de fontes
- ✅ `CORRECT_APIs_HISTORICAL_VS_FORECAST.md` - Diferenças APIs
- ✅ `ENSEMBLE_KALMAN_FUSION.md` - Fusão de dados
- ✅ `CSS_DESIGN_SYSTEM.md` - Sistema de design
- ✅ `architecture.mmd` - Diagrama de arquitetura

### 📁 Subpastas

#### `docs/guides/` - Revisar
- ❌ `DOCKER_TEST_PLAN.md` - Substituído por TESTING_GUIDE.md
- ✅ `DOCKER_TESTING_GUIDE.md` - Manter (específico)
- ✅ `GRAFANA_README.md` - Manter
- ❌ `LOCAL_TESTING_RESULTS.md` - Resultados antigos, deletar
- ✅ `README.md` - Índice, manter
- ✅ `REDIS_MANUAL_SETUP.md` - Manter
- ✅ `REDIS_VSCODE_GUIDE.md` - Manter

#### `docs/setup/` - Revisar
- ❌ `CLEANUP_STATUS.md` - Status antigo, deletar
- ✅ `CELERY_REDIS_SETUP.md` - Manter (referência)

#### `docs/maintenance/` - Manter
- ✅ `CLEANUP_PLAN.md` - Manter
- ✅ `README.md` - Manter

#### `docs/api/` - Manter tudo
- ✅ Toda documentação de API

#### `docs/archive/` - Manter
- ✅ Arquivos históricos/MATOPIBA

---

## 🐳 LIMPEZA DO DOCKER

### Comandos a Executar

```powershell
# 1. Parar todos os containers
docker-compose down

# 2. Remover containers órfãos
docker container prune -f

# 3. Remover imagens não utilizadas
docker image prune -a -f

# 4. Remover volumes não utilizados
docker volume prune -f

# 5. Remover networks não utilizadas
docker network prune -f

# 6. Remover build cache (MUITO ESPAÇO LIBERADO!)
docker builder prune -a -f

# 7. Ver espaço total recuperado
docker system df
```

### Estimativa de Espaço Liberado
- Build cache: ~2-5 GB
- Images antigas: ~1-3 GB
- Containers parados: ~100-500 MB
- Volumes órfãos: ~500 MB - 2 GB
- **Total estimado: 4-10 GB** 🚀

---

## 📊 RESUMO DE AÇÕES

### Arquivos a Deletar (14 arquivos)
```
docs/PROJECT_STATUS.md
docs/API_LIMITATIONS_CORRECTED.md
docs/CLIMATE_API_AUDIT.md
docs/CLIMATE_API_VALIDATION.md
docs/CSS_AUDIT_REPORT.md
docs/CACHE_AND_CLIENTS_SUMMARY.md
docs/CELERY_REDIS_NEXT_STEPS.md
docs/CLIMATE_API_ACTION_PLAN.md
docs/DATA_PIPELINE_REFACTORING_PLAN.md
docs/ADDITIONAL_CLIMATE_SOURCES_RESEARCH.md
docs/VISUAL_TEST_CHECKLIST.md
docs/PROJECT_ORGANIZATION.md
docs/guides/DOCKER_TEST_PLAN.md
docs/guides/LOCAL_TESTING_RESULTS.md
docs/setup/CLEANUP_STATUS.md
```

### Espaço Estimado Liberado
- Documentos obsoletos: ~500 KB
- Docker cache: ~4-10 GB
- **Total: ~4-10 GB** 🎉

---

## ✅ CHECKLIST DE EXECUÇÃO

- [ ] Backup da pasta docs (opcional)
- [ ] Deletar arquivos obsoletos da docs/
- [ ] Parar containers Docker
- [ ] Limpar cache do Docker
- [ ] Verificar espaço liberado
- [ ] Rebuild apenas o necessário
- [ ] Testar aplicação

---

## 🚀 PRÓXIMOS PASSOS APÓS LIMPEZA

1. Rebuild Docker com cache limpo
2. Rodar testes de integração
3. Verificar se tudo funciona
4. Commit das mudanças
5. Implementar funcionalidades do mapa mundial
