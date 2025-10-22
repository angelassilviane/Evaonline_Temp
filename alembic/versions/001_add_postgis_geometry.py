"""Add PostGIS geometry column to world_locations.

Revision ID: 001_postgis
Revises: 
Create Date: 2025-10-22

Este script:
1. Ativa extensão PostGIS no PostgreSQL
2. Adiciona coluna 'geometry' com tipo Point para lat/lon
3. Cria índice GIST para queries de proximidade rápidas
4. Permite usar ST_Distance para buscar locações próximas
"""
import sqlalchemy as sa
from geoalchemy2 import Geometry

from alembic import op

# revision identifiers, used by Alembic.
revision = '001_postgis'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade: adiciona geometria PostGIS."""
    # 1. Ativar extensão PostGIS
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # 2. Adicionar coluna geometry Point(lat, lon)
    # SRID 4326 = WGS84 (latitude/longitude coordenadas do GPS)
    op.add_column(
        'world_locations',
        sa.Column(
            'geometry',
            Geometry('POINT', srid=4326),
            nullable=True,
            comment='PostGIS point geometry (lat, lon) para queries de proximidade'
        )
    )
    
    # 3. Fazer update de todos os registros existentes
    # ST_Point(lon, lat) - IMPORTANTE: ordem é LON, LAT (não LAT, LON)
    op.execute(
        """
        UPDATE world_locations
        SET geometry = ST_SetSRID(ST_Point(lon, lat), 4326)
        WHERE geometry IS NULL
        """
    )
    
    # 4. Tornar coluna geometry NOT NULL após popular
    op.alter_column(
        'world_locations',
        'geometry',
        existing_type=Geometry('POINT', srid=4326),
        nullable=False
    )
    
    # 5. Criar índice GIST para performance de queries espaciais
    # GIST = Generalized Search Tree (ideal para geometrias)
    op.create_index(
        'idx_world_locations_geometry',
        'world_locations',
        ['geometry'],
        postgresql_using='gist',
        postgresql_ops={'geometry': 'gist_geometry_ops'}
    )
    
    print("✅ PostGIS geometry adicionado com sucesso")
    print("   - Extensão PostGIS ativada")
    print("   - Coluna 'geometry' criada (POINT, SRID 4326)")
    print("   - Índice GIST criado para performance")


def downgrade() -> None:
    """Downgrade: remove geometria PostGIS."""
    # 1. Remover índice
    op.drop_index('idx_world_locations_geometry', table_name='world_locations')
    
    # 2. Remover coluna
    op.drop_column('world_locations', 'geometry')
    
    # 3. Remover extensão PostGIS
    op.execute('DROP EXTENSION IF NOT EXISTS postgis')
    
    print("⚠️  PostGIS geometry removido")
