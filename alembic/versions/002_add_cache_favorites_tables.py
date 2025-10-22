"""Add cache and favorites tables.

Revision ID: 002_cache_favorites
Revises: 001_postgis
Create Date: 2025-10-22

Este script:
1. Cria tabela 'user_session_cache' para rastreamento de sessões
2. Cria tabela 'cache_metadata' para metadados de cache
3. Cria tabela 'user_favorites' para coleções de favoritos
4. Cria tabela 'favorite_location' para localizações favoritas
"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '002_cache_favorites'
down_revision = '001_postgis'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade: adiciona tabelas de cache e favoritos."""
    
    # 1. Criar tabela user_session_cache
    op.create_table(
        'user_session_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(50), nullable=False, unique=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('last_access', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('cache_size_mb', sa.Float(), nullable=False, server_default='0.0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_session_cache_session_id', 'user_session_cache', ['session_id'], unique=True)
    op.create_index('idx_user_session_cache_last_access', 'user_session_cache', ['last_access'])
    
    # 2. Criar tabela cache_metadata
    op.create_table(
        'cache_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(50), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('data_type', sa.String(50), nullable=False, server_default='climate'),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('ttl', sa.Integer(), nullable=False, server_default='3600'),
        sa.Column('data_source', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['user_session_cache.session_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_cache_metadata_session_location', 'cache_metadata', 
                   ['session_id', 'location_id'], unique=True)
    op.create_index('idx_cache_metadata_expires', 'cache_metadata', ['last_updated'])
    
    # 3. Criar tabela user_favorites
    op.create_table(
        'user_favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(50), nullable=True, unique=True),
        sa.Column('user_id', sa.Integer(), nullable=True, unique=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_favorites_session', 'user_favorites', ['session_id'])
    op.create_index('idx_user_favorites_user', 'user_favorites', ['user_id'])
    
    # 4. Criar tabela favorite_location
    op.create_table(
        'favorite_location',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_favorites_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_favorites_id'], ['user_favorites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_favorite_location_user_favorites', 'favorite_location', 
                   ['user_favorites_id', 'location_id'], unique=True)
    op.create_index('idx_favorite_location_popular', 'favorite_location', ['location_id'])
    
    print("✅ Tabelas de cache e favoritos criadas com sucesso")
    print("   - user_session_cache (rastreamento de sessões)")
    print("   - cache_metadata (metadados de cache)")
    print("   - user_favorites (coleções de favoritos)")
    print("   - favorite_location (localizações favoritas)")


def downgrade() -> None:
    """Downgrade: remove tabelas de cache e favoritos."""
    # Remover em ordem reversa (respeitando foreign keys)
    op.drop_table('favorite_location')
    op.drop_table('user_favorites')
    op.drop_table('cache_metadata')
    op.drop_table('user_session_cache')
    
    print("⚠️  Tabelas de cache e favoritos removidas")
