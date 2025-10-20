# 📦 Migrações SQL: PostgreSQL Setup

## 🔄 Alembic Migration Files

### Criar nova migração

```bash
cd backend
alembic revision --autogenerate -m "Add visitor stats, admin users, and elevation cache"
```

---

## 📝 Migration Content (Auto-generated)

Salvar em: `alembic/versions/002_add_admin_features.py`

```python
"""Add visitor stats, admin users, and elevation cache

Revision ID: 002_add_admin_features
Revises: 001_create_initial_tables
Create Date: 2025-10-18 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


revision = '002_add_admin_features'
down_revision = '001_create_initial_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Adiciona novas tabelas para features administrativas"""
    
    # ====================================================
    # 1. Tabela: visitor_stats
    # ====================================================
    op.create_table(
        'visitor_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('total_visitors', sa.Integer(), server_default='0', nullable=False),
        sa.Column('unique_visitors_today', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_sync', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('peak_hour', sa.String(5), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ====================================================
    # 2. Tabela: admin_users (com índices)
    # ====================================================
    op.create_table(
        'admin_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), server_default='DEVELOPER', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('api_token', sa.String(255), nullable=False, unique=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username', name='uq_admin_users_username'),
        sa.UniqueConstraint('email', name='uq_admin_users_email'),
        sa.UniqueConstraint('api_token', name='uq_admin_users_api_token')
    )
    
    # Índices para busca rápida
    op.create_index('idx_admin_users_username', 'admin_users', ['username'])
    op.create_index('idx_admin_users_email', 'admin_users', ['email'])
    op.create_index('idx_admin_users_role', 'admin_users', ['role'])
    op.create_index('idx_admin_users_is_active', 'admin_users', ['is_active'])
    
    # ====================================================
    # 3. Tabela: city_elevations (com índices geoespaciais)
    # ====================================================
    op.create_table(
        'city_elevations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('city_name', sa.String(255), nullable=False),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('elevation_m', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Índices compostos para busca por proximidade
    op.create_index('idx_city_elevations_lat_lon', 'city_elevations', ['latitude', 'longitude'])
    op.create_index('idx_city_elevations_city_name', 'city_elevations', ['city_name'])
    op.create_index('idx_city_elevations_country', 'city_elevations', ['country'])
    
    # ====================================================
    # 4. Tabela: admin_audit_logs
    # ====================================================
    op.create_table(
        'admin_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('resource', sa.String(255), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['admin_user_id'], ['admin_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Índices para queries de auditoria
    op.create_index('idx_audit_logs_admin_user_id', 'admin_audit_logs', ['admin_user_id'])
    op.create_index('idx_audit_logs_action', 'admin_audit_logs', ['action'])
    op.create_index('idx_audit_logs_created_at', 'admin_audit_logs', ['created_at'])
    
    # ====================================================
    # 5. Tabela: visitor_backups (histórico)
    # ====================================================
    op.create_table(
        'visitor_backups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('visitors_count', sa.Integer(), nullable=False),
        sa.Column('backup_date', sa.Date(), nullable=False),
        sa.Column('backup_hour', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Índice para queries por data
    op.create_index('idx_visitor_backups_date', 'visitor_backups', ['backup_date'])


def downgrade():
    """Remove tabelas e índices"""
    
    # Remove em ordem reversa (por causa das foreign keys)
    op.drop_table('visitor_backups')
    op.drop_table('admin_audit_logs')
    op.drop_table('city_elevations')
    op.drop_table('admin_users')
    op.drop_table('visitor_stats')
```

---

## 🚀 Executar Migrações

```bash
# Aplicar migrações
cd backend
alembic upgrade head

# Verificar status
alembic current

# Reverter última (se necessário)
alembic downgrade -1
```

---

## 📊 SQL Direto (se preferir)

Se quiser criar as tabelas manualmente:

```sql
-- 1. Visitor Stats
CREATE TABLE IF NOT EXISTS visitor_stats (
    id SERIAL PRIMARY KEY,
    total_visitors INTEGER DEFAULT 0 NOT NULL,
    unique_visitors_today INTEGER DEFAULT 0 NOT NULL,
    last_sync TIMESTAMP DEFAULT NOW() NOT NULL,
    peak_hour VARCHAR(5),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- 2. Admin Users
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'DEVELOPER' NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    api_token VARCHAR(255) UNIQUE NOT NULL
);

-- Índices para admin_users
CREATE INDEX idx_admin_users_username ON admin_users(username);
CREATE INDEX idx_admin_users_email ON admin_users(email);
CREATE INDEX idx_admin_users_role ON admin_users(role);
CREATE INDEX idx_admin_users_is_active ON admin_users(is_active);

-- 3. City Elevations
CREATE TABLE IF NOT EXISTS city_elevations (
    id SERIAL PRIMARY KEY,
    city_name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    elevation_m FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Índices para busca por proximidade
CREATE INDEX idx_city_elevations_lat_lon ON city_elevations(latitude, longitude);
CREATE INDEX idx_city_elevations_city_name ON city_elevations(city_name);
CREATE INDEX idx_city_elevations_country ON city_elevations(country);

-- 4. Admin Audit Logs
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
    action VARCHAR(255) NOT NULL,
    resource VARCHAR(255) NOT NULL,
    details TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Índices para auditoria
CREATE INDEX idx_audit_logs_admin_user_id ON admin_audit_logs(admin_user_id);
CREATE INDEX idx_audit_logs_action ON admin_audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON admin_audit_logs(created_at);

-- 5. Visitor Backups
CREATE TABLE IF NOT EXISTS visitor_backups (
    id SERIAL PRIMARY KEY,
    visitors_count INTEGER NOT NULL,
    backup_date DATE NOT NULL,
    backup_hour INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Índice para queries por data
CREATE INDEX idx_visitor_backups_date ON visitor_backups(backup_date);
```

---

## 👤 Inserir Admin Inicial

```sql
-- Gerar senha (usar bcrypt):
-- python -c "import bcrypt; print(bcrypt.hashpw(b'sua-senha', bcrypt.gensalt()).decode())"

-- Insertar super admin
INSERT INTO admin_users (username, email, password_hash, role, api_token)
VALUES (
    'admin',
    'admin@evaonline.local',
    '$2b$12$SEU_HASH_BCRYPT_AQUI',  -- Substituir com hash real!
    'SUPER_ADMIN',
    'sk_live_' || md5(random()::text)
);

-- Verificar
SELECT id, username, role, is_active FROM admin_users;
```

---

## 🌍 Bulk Load Cidades

### Via Python

```python
import pandas as pd
from sqlalchemy.orm import Session
from backend.database.models import CityElevation
from backend.database.connection import engine

# Ler CSV
df = pd.read_csv('data/csv/worldcities.csv')

# Preparar dados
records = []
for _, row in df.iterrows():
    records.append({
        'city_name': row['city'],
        'country': row['country'],
        'latitude': float(row['lat']),
        'longitude': float(row['lng']),
        'elevation_m': float(row.get('elevation', 0))
    })

# Bulk insert
with Session(engine) as session:
    session.bulk_insert_mappings(CityElevation, records)
    session.commit()
    print(f"✅ {len(records)} cidades carregadas")
```

### Via SQL COPY (mais rápido)

```sql
-- Formato CSV esperado:
-- city_name,country,latitude,longitude,elevation_m

COPY city_elevations(city_name, country, latitude, longitude, elevation_m)
FROM '/data/csv/worldcities.csv'
WITH (FORMAT csv, HEADER true, DELIMITER ',');

-- Verificar
SELECT COUNT(*) FROM city_elevations;
-- Esperado: ~48,060 cidades
```

---

## ✅ Validar Setup

```sql
-- 1. Verificar tabelas criadas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'visitor_stats',
    'admin_users',
    'city_elevations',
    'admin_audit_logs',
    'visitor_backups'
);

-- 2. Verificar índices
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'city_elevations';

-- 3. Contar cidades
SELECT COUNT(*) as total_cities FROM city_elevations;

-- 4. Verificar admin user
SELECT username, role, is_active FROM admin_users;

-- 5. Verificar espaço em disco
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🔧 Troubleshooting

### Erro: "relation does not exist"

```bash
# Verificar se migrations rodaram
alembic current

# Se não, executar:
alembic upgrade head

# Ver histórico
alembic history
```

### Erro: "Duplicate key value"

```sql
-- Resetar sequence (se necessário)
SELECT setval('admin_users_id_seq', (SELECT MAX(id) FROM admin_users)+1);
SELECT setval('city_elevations_id_seq', (SELECT MAX(id) FROM city_elevations)+1);
```

### Erro: "Foreign key constraint failed"

```sql
-- Desabilitar temporariamente (cuidado!)
ALTER TABLE admin_audit_logs
DISABLE TRIGGER ALL;

-- Fazer operação...

-- Reabilitar
ALTER TABLE admin_audit_logs
ENABLE TRIGGER ALL;
```

