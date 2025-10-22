# 🌙 PLANO EXECUÇÃO CAMINHO C - TRABALHO NOTURNO

**Objetivo**: FASE 0.2 + FASE 1.0 (Cache + Favoritos) COMPLETOS EM UMA NOITE

**Timeline Total**: 6h30min  
**Horário**: 🌙 Noite (flexible)  
**Status**: PRONTO PARA INICIAR

---

## 📊 BREAKDOWN POR FASE

### ⏱️ BLOCO 1: PASSO 7-9 (1h)
**Objetivo**: Fechar FASE 0.2  
**Saídas**: 1 Alembic migration + 28 endpoints testados + 1 git commit

#### PASSO 7: PostGIS Optimization (30 min)
```
Checklist:
├─ [ ] Criar alembic/versions/xxx_add_postgis_geometry.py
├─ [ ] Adicionar geometry column em world_locations
├─ [ ] Criar índice GIST para performance
├─ [ ] Testar ST_Distance query
└─ [ ] Validar sem errors
```

**Arquivos a criar/modificar:**
- `alembic/versions/xxx_add_postgis_geometry.py` (NEW - 50L)
- `backend/database/models/world_locations.py` (MODIFY - add geometry col)

---

#### PASSO 8: Testes E2E (30 min)
```
Checklist:
├─ [ ] pytest tests/ -v (rodar todos testes)
├─ [ ] Testar 5 endpoints críticos:
│   ├─ GET /api/locations/ (list)
│   ├─ GET /api/locations/1 (detail)
│   ├─ GET /api/locations/nearest (PostGIS)
│   ├─ GET /api/climate/sources (climate)
│   └─ GET /api/health (health)
├─ [ ] Validar sem errors
└─ [ ] Conferir 28 endpoints registered
```

**Comandos:**
```bash
cd backend
python -m pytest tests/ -v --tb=short
python -c "from backend.api.routes import api_router; print(f'✅ {len(api_router.routes)} endpoints')"
```

---

#### PASSO 9: Git Commit Final FASE 0.2 (10 min)
```bash
git add -A
git commit -m "FASE 0.2 COMPLETO: PostGIS otimizado, todos endpoints testados"
git log --oneline -3
```

---

### ⏱️ BLOCO 2: CACHE SYSTEM (3h)
**Objetivo**: Sistema completo de cache Redis + PostgreSQL + Frontend  
**Saídas**: 2 service files + 2 model files + 1 route file + Dash integration

#### PASSO 1: Service Layer (1h)
**Arquivo**: `backend/api/services/cache_manager.py` (NEW - 200L)

```python
# Estrutura:
class SessionCache:
    def __init__(self, redis_pool)
    def get_or_fetch_climate(self, location_id, session_id)
    def cache_climate_data(self, location_id, data, ttl=3600)
    
class ClimateCache:
    def __init__(self, redis_pool, db_session)
    def aggregate_hourly_data(self, location_id)
    def get_cached_aggregate(self, location_id)

# Métodos principais:
- generate_session_id()
- cache_hit_ratio()
```

**Checklist:**
- [ ] Criar service com SessionCache class
- [ ] Implementar get_or_fetch_climate() com fallback
- [ ] Implementar cache_climate_data()
- [ ] Testar imports (sem errors)

---

#### PASSO 2: PostgreSQL Models (30 min)
**Arquivo**: `backend/database/models/user_cache.py` (NEW - 80L)

```python
# Models:
class UserSessionCache:
    id: Integer (PK)
    session_id: String (unique)
    user_agent: String
    created_at: DateTime
    last_access: DateTime
    cache_size_mb: Float

class CacheMetadata:
    id: Integer (PK)
    session_id: FK(UserSessionCache)
    location_id: FK(WorldLocations)
    data_type: String (climate/elevation/etc)
    last_updated: DateTime
    ttl: Integer (seconds)
```

**Checklist:**
- [ ] Criar models/user_cache.py
- [ ] Adicionar __init__.py exports
- [ ] Criar alembic migration para tabelas
- [ ] Testar imports

---

#### PASSO 3: FastAPI Endpoints (45 min)
**Arquivo**: `backend/api/routes/cache_routes.py` (NEW - 120L)

```python
@router.get("/cache/climate/{location_id}")
async def get_cached_climate(location_id: int, session_id: str = Header(None))

@router.post("/cache/prefetch")
async def prefetch_climate_data(location_ids: List[int], session_id: str)

@router.get("/cache/stats")
async def get_cache_stats(session_id: str)

@router.delete("/cache/clear")
async def clear_cache(session_id: str)
```

**Checklist:**
- [ ] Criar routes/cache_routes.py
- [ ] Integrar SessionCache service
- [ ] Adicionar a __init__.py api_router
- [ ] Testar endpoints (curl)

---

#### PASSO 4: Dash Frontend Integration (45 min)
**Arquivo**: `frontend/app.py` (MODIFY + NEW)

**Mudanças:**
```python
# Em app.py:
app.layout = html.Div([
    dcc.Store(id='session-id-store', data=generate_session_id()),
    dcc.Store(id='cache-store', data={}),
    # ... resto do layout
    callbacks=[
        # Cache sync callbacks
    ]
])

# Callbacks novos:
@app.callback(
    Output('cache-store', 'data'),
    Input('location-selector', 'value'),
    State('session-id-store', 'data')
)
def sync_cache(location_id, session_id):
    # Buscar do cache backend antes de fazer request
    return fetch_from_cache(location_id, session_id)
```

**Checklist:**
- [ ] Adicionar dcc.Store para session ID
- [ ] Criar callback de sync cache
- [ ] Testar comunicação frontend-backend
- [ ] Verificar localStorage persistence

---

### ⏱️ BLOCO 3: FAVORITES SYSTEM (2h30min)
**Objetivo**: Sistema completo de favoritos com sincronização localStorage + Backend  
**Saídas**: 2 model files + 1 route file + Dash integration

#### PASSO 5: Backend Models (30 min)
**Arquivo**: `backend/database/models/user_favorites.py` (NEW - 100L)

```python
class UserFavorites:
    id: Integer (PK)
    session_id: String (unique, anon support)
    user_id: Integer (nullable, para login futuro)
    created_at: DateTime
    updated_at: DateTime

class FavoriteLocation:
    id: Integer (PK)
    user_favorites_id: FK(UserFavorites)
    location_id: FK(WorldLocations)
    added_at: DateTime
    notes: String (opcional)
    
    # Limite máximo 20
    # Índice em (session_id, location_id) para unique constraint
```

**Checklist:**
- [ ] Criar models/user_favorites.py
- [ ] Adicionar constraints (max 20 favoritos)
- [ ] Criar alembic migration
- [ ] Testar imports

---

#### PASSO 6: Routes + CRUD Endpoints (45 min)
**Arquivo**: `backend/api/routes/favorites_routes.py` (NEW - 150L)

```python
@router.get("/favorites")
async def list_favorites(session_id: str = Header(...))
# Retorna: [{ id, location_id, name, lat, lon, added_at }]

@router.post("/favorites")
async def add_favorite(location_id: int, session_id: str = Header(...))
# Valida limite 20, retorna updated list

@router.delete("/favorites/{location_id}")
async def remove_favorite(location_id: int, session_id: str = Header(...))
# Retorna updated list

@router.get("/favorites/{location_id}/exists")
async def check_favorite_exists(location_id: int, session_id: str = Header(...))
# Retorna: { exists: bool }
```

**Checklist:**
- [ ] Criar routes/favorites_routes.py
- [ ] Implementar todas 4 endpoints
- [ ] Adicionar validação (limit 20)
- [ ] Integrar com cache
- [ ] Testar endpoints

---

#### PASSO 7: Dash Frontend Integration (45 min)
**Arquivo**: `frontend/components/favorites.py` (NEW - 80L) + `frontend/app.py` (MODIFY)

**Nova Componente:**
```python
# components/favorites.py
def create_favorites_button(location_id):
    return dcc.Button(
        id={'type': 'favorite-btn', 'index': location_id},
        children='⭐ Favorite',
        n_clicks=0
    )

@app.callback(
    [Output('favorites-store', 'data'),
     Output({'type': 'favorite-btn', 'index': ALL}, 'children')],
    Input({'type': 'favorite-btn', 'index': ALL}, 'n_clicks'),
    State('favorites-store', 'data'),
    State('session-id-store', 'data'),
    prevent_initial_call=True
)
def toggle_favorite(n_clicks, favorites, session_id):
    # Sync com backend + localStorage
```

**Checklist:**
- [ ] Criar components/favorites.py
- [ ] Adicionar dcc.Store para favorites
- [ ] Criar callbacks de toggle
- [ ] Testar localStorage persistence
- [ ] Validar UI updates

---

### ⏱️ BLOCO 4: TESTES + DOCUMENTAÇÃO (1h)
**Objetivo**: Validar tudo + documentar resultados

#### PASSO 8: E2E Testing (30 min)
```bash
# Testes:
pytest tests/ -v

# Validações manuais:
curl http://localhost:8000/api/cache/climate/1 -H "Session-ID: test123"
curl -X POST http://localhost:8000/api/favorites -H "Session-ID: test123" -d '{"location_id": 1}'
curl http://localhost:8000/api/favorites -H "Session-ID: test123"

# Verificar:
- [ ] Todos pytest passando
- [ ] Cache endpoints respondendo
- [ ] Favorites endpoints respondendo
- [ ] localStorage sincronizando
- [ ] Performance melhorada (< 50ms para cached requests)
```

**Checklist:**
- [ ] Rodar pytest completo
- [ ] 5 curl tests de cache
- [ ] 5 curl tests de favorites
- [ ] Validar localStorage no browser
- [ ] Conferir performance com chrome devtools

---

#### PASSO 9: Final Documentation (30 min)
**Arquivo**: `RESULTADO_FINAL_CAMINHO_C.md` (NEW)

Conteúdo:
- ✅ FASE 0.2 status (PostGIS + Testes + Commit)
- ✅ FASE 1.0 MVP status (Cache + Favorites)
- 📊 Performance metrics (antes vs depois)
- 📋 Files criados/modificados (lista)
- 🔄 Git commits (3 no total)
- 📝 Next steps (FASE 2.0, Kalman Ensemble)

**Checklist:**
- [ ] Criar documento final
- [ ] Git commit: "CAMINHO C COMPLETO: FASE 0.2 + FASE 1.0 MVP"
- [ ] Git log para visualizar histórico
- [ ] Validar docker-compose startup

---

## 🎯 TIMELINE VISUAL

```
Horário    Bloco              Tempo    Status
──────────────────────────────────────────────
20:00      PASSO 7            30 min   ⏳ Próximo
20:30      PASSO 8-9          40 min   ⏳ Depois
21:10      Cache Service      1h       ⏳ Depois
22:10      Favorites Models   30 min   ⏳ Depois
22:40      Cache Routes       45 min   ⏳ Depois
23:25      Favorites Routes   45 min   ⏳ Depois
00:10      Frontend Cache     45 min   ⏳ Depois
00:55      Frontend Favorites 45 min   ⏳ Depois
01:40      E2E Testing        30 min   ⏳ Depois
02:10      Documentation      30 min   ⏳ Depois
02:40      ✅ PRONTO!
```

**Total**: 6h40min

---

## 📁 ARQUIVOS NOVOS (RESUMO)

```
backend/
├── api/
│   ├── routes/
│   │   ├── cache_routes.py (NEW - 120L)
│   │   └── favorites_routes.py (NEW - 150L)
│   └── services/
│       └── cache_manager.py (NEW - 200L)
├── database/
│   ├── models/
│   │   ├── user_cache.py (NEW - 80L)
│   │   └── user_favorites.py (NEW - 100L)
│   └── migrations/
│       ├── xxx_add_postgis_geometry.py (NEW)
│       └── yyy_add_cache_favorites_tables.py (NEW)
frontend/
├── components/
│   └── favorites.py (NEW - 80L)
└── app.py (MODIFY - add cache + favorites callbacks)
```

**Total Novo**: ~1,000L de código

---

## ⚡ COMO COMEÇAR

### 1️⃣ Confirme que está pronto:
```bash
cd backend
python -m pytest tests/ -q  # Verificar estado atual
```

### 2️⃣ Comece PASSO 7 (PostGIS):
```bash
python -m alembic revision --autogenerate -m "add_postgis_geometry"
```

### 3️⃣ Enquanto eu crio os arquivos:

**Eu vou:**
- [ ] Criar cache_manager.py com SessionCache
- [ ] Criar user_cache.py models
- [ ] Criar cache_routes.py endpoints
- [ ] Criar user_favorites.py models
- [ ] Criar favorites_routes.py endpoints
- [ ] Criar favorites.py component

**Você vai:**
- [ ] Executar os migrations
- [ ] Testar os endpoints
- [ ] Revisar o código
- [ ] Sugerir mudanças

---

## 📝 REGRAS PARA NOITE

✅ **FAZER:**
- Pausar entre blocos (5-10 min)
- Testar cada componente antes do próximo
- Commit após cada passo (git history limpo)
- Verificar imports (evitar erros surpresa)

❌ **EVITAR:**
- Pular testes (vai dar problema)
- Deixar migration pendente (database inconsistente)
- Fazer tudo de uma vez sem validar
- Cometer sem testar

---

## 🚀 COMEÇAMOS?

**Próxima ação:**
1. Você confirma "pronto para PASSO 7"
2. Eu começo a criar os arquivos
3. Você executa os migrations + testes

Quer começar agora? 🌙✨
