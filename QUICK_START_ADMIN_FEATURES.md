# 🎯 GUIA RÁPIDO: Implementação Step-by-Step

## ⚡ COMEÇAR HOJE - 2 Horas

### Fase 1: Setup PostgreSQL (30 min)

#### Passo 1.1: Remover PostGIS
```bash
# docker-compose.yml
# ANTES:
# postgres:
#   image: postgis/postgis:15-3.4-alpine

# DEPOIS:
# postgres:
#   image: postgres:15-alpine

# Depois: docker-compose restart postgres
```

#### Passo 1.2: Criar Alembic Migration
```bash
cd backend
alembic revision --autogenerate -m "Add admin features"
```

#### Passo 1.3: Editar Migration (copiar de DATABASE_MIGRATIONS.md)
```bash
# Abrir alembic/versions/002_add_admin_features.py
# Copiar conteúdo de DATABASE_MIGRATIONS.md e colar
```

#### Passo 1.4: Executar Migration
```bash
alembic upgrade head

# Verificar
alembic current
```

---

### Fase 2: Contador Visitantes (45 min)

#### Passo 2.1: Criar VisitorTracker
Arquivo: `backend/infrastructure/visitor_tracking.py`

```python
import redis
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.models import VisitorStats

class VisitorTracker:
    """Rastreia visitantes com persistência"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.redis_key = "visitors:total"
    
    async def increment_visitor(self) -> int:
        """Incrementa e retorna contagem"""
        return self.redis.incr(self.redis_key)
    
    async def get_total(self) -> int:
        """Retorna total"""
        return int(self.redis.get(self.redis_key) or 0)
```

#### Passo 2.2: Criar Endpoint
Arquivo: `backend/api/routes/stats.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import VisitorStats
import redis

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])
redis_client = redis.from_url("redis://redis:6379")

@router.get("/visitors")
async def get_visitors(db: Session = Depends(get_db)):
    """Retorna contagem de visitantes"""
    total = int(redis_client.get("visitors:total") or 0)
    return {"total_visitors": total}

@router.post("/visit")
async def record_visit(db: Session = Depends(get_db)):
    """Registra uma visita"""
    total = redis_client.incr("visitors:total")
    return {"total_visitors": total}
```

#### Passo 2.3: Adicionar ao Backend Main
Arquivo: `backend/main.py`

```python
# Adicionar import
from backend.api.routes import stats

# Adicionar rota
app.include_router(stats.router)
```

#### Passo 2.4: Criar Footer Component
Arquivo: `frontend/components/footer.py`

```python
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
import requests

def create_footer(lang: str = "pt") -> dbc.Container:
    return dbc.Container([
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-users me-2"),
                    html.Span("Visitantes: "),
                    html.Strong(id="visitor-counter", children="0")
                ], style={"fontSize": "14px"})
            ], width=3),
            dbc.Col([
                html.Small("© 2025 EVAonline", style={"color": "#666"})
            ], width=9, className="text-end")
        ], className="mt-3 mb-3")
    ], fluid=True)

@callback(
    Output("visitor-counter", "children"),
    Input("interval-update-visitors", "n_intervals")
)
def update_counter(n):
    try:
        r = requests.get("http://localhost:8000/api/v1/stats/visitors")
        return f"{r.json()['total_visitors']:,}"
    except:
        return "N/A"
```

#### Passo 2.5: Adicionar Footer ao Layout
Arquivo: `frontend/app.py`

```python
# Adicionar import
from frontend.components.footer import create_footer

# No layout da app:
app.layout = dbc.Container([
    # ... seu conteúdo ...
    create_footer(),
    
    # Adicionar intervalo para updates
    dcc.Interval(id="interval-update-visitors", interval=10000)  # 10s
], fluid=True)
```

#### Passo 2.6: Testar
```bash
# Terminal 1: Backend
docker-compose exec api python -m uvicorn backend.main:app --reload

# Terminal 2: Frontend
docker-compose exec api python frontend/app.py

# Browser: http://localhost:8050
# Deve ver contador no footer, incrementando
```

---

### Fase 3: Admin Dashboard (45 min)

#### Passo 3.1: Criar Autenticação
Arquivo: `backend/api/security/auth.py`

```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import jwt
from datetime import datetime, timedelta
from backend.database.models import AdminUser
import redis

security = HTTPBearer()
redis_client = redis.from_url("redis://redis:6379")

class AdminAuthManager:
    SECRET_KEY = "sua-chave-super-secreta"  # Use env vars!
    
    @classmethod
    def create_token(cls, user_id: int, role: str) -> str:
        payload = {
            "sub": str(user_id),
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm="HS256")
    
    @classmethod
    async def verify_token(cls, token: str) -> dict:
        try:
            return jwt.decode(token, cls.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except:
            raise HTTPException(status_code=401, detail="Token inválido")
```

#### Passo 3.2: Criar Endpoint Login
Arquivo: `backend/api/routes/admin.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import AdminUser
from backend.api.security.auth import AdminAuthManager
import bcrypt

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.post("/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter_by(username=username).first()
    
    if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuário inativo")
    
    token = AdminAuthManager.create_token(user.id, user.role)
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "dashboards": {
            "grafana": "http://localhost:3000",
            "prometheus": "http://localhost:9090"
        }
    }
```

#### Passo 3.3: Criar Admin Page
Arquivo: `frontend/pages/admin_page.py`

```python
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, State
import requests

def create_admin_login():
    return dbc.Container([
        dbc.Row([dbc.Col([html.H2("🔐 Admin Login", className="mt-5")])]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Input(id="admin-username", placeholder="Usuário", className="mb-3"),
                        dbc.Input(id="admin-password", type="password", placeholder="Senha", className="mb-3"),
                        dbc.Button("Login", id="admin-login-btn", color="primary", className="w-100"),
                        html.Div(id="admin-login-msg", className="mt-3")
                    ])
                ], style={"maxWidth": "400px"})
            ], width=12, className="text-center")
        ], justify="center", className="mt-5")
    ])

@callback(
    Output("admin-login-msg", "children"),
    Output("admin-login-msg", "className"),
    Input("admin-login-btn", "n_clicks"),
    State("admin-username", "value"),
    State("admin-password", "value"),
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    if not username or not password:
        return "Preencha os campos", "alert alert-warning"
    
    try:
        r = requests.post(
            "http://localhost:8000/api/v1/admin/login",
            params={"username": username, "password": password}
        )
        if r.status_code == 200:
            return f"✅ Login bem-sucedido! Token: {r.json()['access_token'][:20]}...", "alert alert-success"
        else:
            return f"❌ {r.json()['detail']}", "alert alert-danger"
    except Exception as e:
        return f"❌ Erro: {str(e)}", "alert alert-danger"
```

#### Passo 3.4: Adicionar ao Frontend
Arquivo: `frontend/app.py`

```python
from frontend.pages.admin_page import create_admin_login

# No layout, adicionar página admin:
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/admin":
        return create_admin_login()
    # ... outras rotas ...
```

---

### Fase 4: Cache Elevação (30 min)

#### Passo 4.1: Criar Modelo CityElevation (já em DATABASE_MIGRATIONS.md)

#### Passo 4.2: Criar Service
Arquivo: `backend/api/services/elevation_cache_service.py`

```python
import redis
import json
from sqlalchemy.orm import Session
from backend.database.models import CityElevation

class ElevationCacheService:
    def __init__(self, redis_client: redis.Redis, db: Session):
        self.redis = redis_client
        self.db = db
    
    async def get_nearest_city(self, lat: float, lon: float) -> dict:
        # Cache key
        cache_key = f"elevation:{lat:.4f}:{lon:.4f}"
        
        # Check Redis
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Query PostgreSQL
        cities = self.db.query(CityElevation).filter(
            CityElevation.latitude.between(lat-0.1, lat+0.1),
            CityElevation.longitude.between(lon-0.1, lon+0.1)
        ).all()
        
        if cities:
            nearest = min(cities, key=lambda c: c.distance_to(lat, lon))
            result = {
                "city": nearest.city_name,
                "elevation": nearest.elevation_m,
                "source": "database"
            }
            self.redis.setex(cache_key, 86400*7, json.dumps(result))
            return result
        
        return {"source": "error", "message": "No cities found"}
```

#### Passo 4.3: Criar Endpoint
Arquivo: `backend/api/routes/elevation.py`

```python
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.api.services.elevation_cache_service import ElevationCacheService
import redis

router = APIRouter(prefix="/api/v1/elevation", tags=["elevation"])

@router.get("/nearest")
async def get_nearest(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    db: Session = Depends(get_db)
):
    redis_client = redis.from_url("redis://redis:6379")
    service = ElevationCacheService(redis_client, db)
    return await service.get_nearest_city(lat, lon)
```

---

## 🚀 TESTAR TUDO

```bash
# 1. Reiniciar Docker
docker-compose down
docker-compose up -d

# 2. Aplicar migrations
docker-compose exec api alembic upgrade head

# 3. Testar contador
curl http://localhost:8000/api/v1/stats/visitors
# Resposta: {"total_visitors": 0}

# 4. Testar admin login
curl -X POST "http://localhost:8000/api/v1/admin/login?username=admin&password=sua-senha"

# 5. Testar cache elevação
curl "http://localhost:8000/api/v1/elevation/nearest?lat=-15.7801&lon=-47.9292"

# 6. Browser
# http://localhost:8050 → Ver contador no footer
# http://localhost:8050/admin → Login admin
```

---

## 📊 MONITORAR NO GRAFANA

```
http://localhost:3000
Username: admin
Password: admin

Dashboards:
- EVAonline Main (deve estar em docker/monitoring/grafana/dashboards/)
```

---

## ✅ CHECKLIST FINAL

- [ ] PostGIS removido de docker-compose.yml
- [ ] Migration 002 criada e executada
- [ ] VisitorTracker implementado
- [ ] Footer com contador funcionando
- [ ] Admin autenticação trabalhando
- [ ] Cache elevação operacional
- [ ] Tudo testado localmente
- [ ] Pronto para Railway deployment!

---

## 🎉 PRÓXIMO PASSO

Depois de testar tudo localmente:
1. Commit das mudanças: `git add . && git commit -m "Add admin features and visitor tracking"`
2. Push para GitHub: `git push origin main`
3. Deploy Railway (veja DEPLOYMENT_ANALYSIS.md)

Dúvidas? Consulte:
- `REDIS_POSTGRESQL_INTEGRATION.md` - Conceitos detalhados
- `DATABASE_MIGRATIONS.md` - Schema SQL
- `HOSTING_PRICE_COMPARISON.md` - Roadmap

