"""Add visitor_stats table

Revision ID: 002
Revises: 001
Create Date: 2025-10-19

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Criar tabela visitor_stats
    op.create_table(
        'visitor_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('total_visitors', sa.Integer(), server_default='0'),
        sa.Column('unique_visitors_today', sa.Integer(), server_default='0'),
        sa.Column('last_sync', sa.DateTime(), nullable=False),
        sa.Column('peak_hour', sa.String(5), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Criar índices
    op.create_index(op.f('ix_visitor_stats_id'), 'visitor_stats', ['id'], unique=False)
    op.create_index(op.f('ix_visitor_stats_last_sync'), 'visitor_stats', ['last_sync'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remover índices
    op.drop_index(op.f('ix_visitor_stats_last_sync'), table_name='visitor_stats')
    op.drop_index(op.f('ix_visitor_stats_id'), table_name='visitor_stats')
    
    # Remover tabela
    op.drop_table('visitor_stats')
