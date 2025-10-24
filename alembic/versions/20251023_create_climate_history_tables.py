"""Create climate history tables for Kalman Ensemble

Revision ID: 20251023_001
Revises: 
Create Date: 2025-10-23 05:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geography


# revision identifiers, used by Alembic.
revision = '20251023_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar schema se não existir
    op.execute('CREATE SCHEMA IF NOT EXISTS climate_history')
    
    # Tabela de cidades com dados históricos
    op.create_table(
        'studied_cities',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('city_name', sa.String(150), nullable=False, unique=True),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('state_province', sa.String(100), nullable=True),
        sa.Column('latitude', sa.Float, nullable=False),
        sa.Column('longitude', sa.Float, nullable=False),
        sa.Column('elevation_m', sa.Float, nullable=True),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('data_sources', postgresql.JSONB, nullable=True, comment='Array de fontes de dados'),
        sa.Column('reference_periods', postgresql.JSONB, nullable=False, comment='Períodos de referência disponíveis'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        schema='climate_history'
    )
    
    # Índices para studied_cities
    op.create_index('idx_studied_cities_location', 'studied_cities', ['location'], 
                    postgresql_using='gist', schema='climate_history')
    op.create_index('idx_studied_cities_city_country', 'studied_cities', 
                    ['city_name', 'country'], schema='climate_history')
    
    # Tabela de normais mensais por cidade
    op.create_table(
        'monthly_climate_normals',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('city_id', sa.Integer, sa.ForeignKey('climate_history.studied_cities.id'), nullable=False),
        sa.Column('period_key', sa.String(20), nullable=False, comment='Ex: 1991-2020'),
        sa.Column('month', sa.Integer, nullable=False, comment='1-12'),
        sa.Column('eto_normal', sa.Float, nullable=True, comment='ETo normal em mm/dia'),
        sa.Column('eto_daily_mean', sa.Float, nullable=True),
        sa.Column('eto_daily_median', sa.Float, nullable=True),
        sa.Column('eto_daily_std', sa.Float, nullable=True),
        sa.Column('eto_p01', sa.Float, nullable=True),
        sa.Column('eto_p05', sa.Float, nullable=True),
        sa.Column('eto_p10', sa.Float, nullable=True),
        sa.Column('eto_p25', sa.Float, nullable=True),
        sa.Column('eto_p75', sa.Float, nullable=True),
        sa.Column('eto_p90', sa.Float, nullable=True),
        sa.Column('eto_p95', sa.Float, nullable=True),
        sa.Column('eto_p99', sa.Float, nullable=True),
        sa.Column('eto_abs_min', sa.Float, nullable=True),
        sa.Column('eto_abs_max', sa.Float, nullable=True),
        sa.Column('precip_normal', sa.Float, nullable=True, comment='Precipitação em mm'),
        sa.Column('precip_daily_mean', sa.Float, nullable=True),
        sa.Column('precip_daily_median', sa.Float, nullable=True),
        sa.Column('precip_daily_std', sa.Float, nullable=True),
        sa.Column('precip_p95', sa.Float, nullable=True),
        sa.Column('precip_p99', sa.Float, nullable=True),
        sa.Column('precip_max', sa.Float, nullable=True),
        sa.Column('rain_days', sa.Integer, nullable=True),
        sa.Column('dry_days', sa.Integer, nullable=True),
        sa.Column('rain_probability', sa.Float, nullable=True, comment='0-1'),
        sa.Column('precip_intensity', sa.Float, nullable=True),
        sa.Column('n_days', sa.Integer, nullable=True, comment='Dias de dados usados'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        schema='climate_history',
        sa.UniqueConstraint('city_id', 'period_key', 'month', name='uq_monthly_normals')
    )
    
    # Índices para monthly_climate_normals
    op.create_index('idx_monthly_normals_city_month', 'monthly_climate_normals', 
                    ['city_id', 'month'], schema='climate_history')
    op.create_index('idx_monthly_normals_city_period', 'monthly_climate_normals', 
                    ['city_id', 'period_key'], schema='climate_history')
    
    # Tabela de estações de dados próximas
    op.create_table(
        'weather_stations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('station_code', sa.String(50), nullable=False, unique=True),
        sa.Column('station_name', sa.String(150), nullable=False),
        sa.Column('latitude', sa.Float, nullable=False),
        sa.Column('longitude', sa.Float, nullable=False),
        sa.Column('elevation_m', sa.Float, nullable=True),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('data_source', sa.String(50), nullable=False, comment='nasa_power, cerra, etc'),
        sa.Column('data_available_from', sa.Date, nullable=True),
        sa.Column('data_available_to', sa.Date, nullable=True),
        sa.Column('variables_available', postgresql.JSONB, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        schema='climate_history'
    )
    
    # Índices para weather_stations
    op.create_index('idx_weather_stations_location', 'weather_stations', ['location'], 
                    postgresql_using='gist', schema='climate_history')
    op.create_index('idx_weather_stations_data_source', 'weather_stations', 
                    ['data_source'], schema='climate_history')
    
    # Tabela de relação entre cidades e estações próximas
    op.create_table(
        'city_nearby_stations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('city_id', sa.Integer, sa.ForeignKey('climate_history.studied_cities.id'), nullable=False),
        sa.Column('station_id', sa.Integer, sa.ForeignKey('climate_history.weather_stations.id'), nullable=False),
        sa.Column('distance_km', sa.Float, nullable=False),
        sa.Column('proximity_weight', sa.Float, nullable=True, comment='Peso = 1/distance'),
        sa.Column('confidence_score', sa.Float, nullable=True, comment='0-1, baseado em overlap de dados'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        schema='climate_history',
        sa.UniqueConstraint('city_id', 'station_id', name='uq_city_station')
    )
    
    # Índices para city_nearby_stations
    op.create_index('idx_city_nearby_stations_city', 'city_nearby_stations', 
                    ['city_id'], schema='climate_history')
    op.create_index('idx_city_nearby_stations_distance', 'city_nearby_stations', 
                    ['city_id', 'distance_km'], schema='climate_history')


def downgrade() -> None:
    op.drop_table('city_nearby_stations', schema='climate_history')
    op.drop_table('weather_stations', schema='climate_history')
    op.drop_table('monthly_climate_normals', schema='climate_history')
    op.drop_table('studied_cities', schema='climate_history')
    op.execute('DROP SCHEMA IF EXISTS climate_history')
