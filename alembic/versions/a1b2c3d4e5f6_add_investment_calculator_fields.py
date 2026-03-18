"""add investment calculator fields

Revision ID: a1b2c3d4e5f6
Revises: e4c487fc6ea2
Create Date: 2026-03-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e4c487fc6ea2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add investment calculator fields with server_default for existing rows
    op.add_column('properties', sa.Column('calc_rent_estimate', sa.Integer(), nullable=True))
    op.add_column('properties', sa.Column('calc_rehab_estimate', sa.Integer(), server_default='2000000', nullable=True))
    op.add_column('properties', sa.Column('calc_property_tax', sa.Integer(), server_default='350000', nullable=True))
    op.add_column('properties', sa.Column('calc_insurance', sa.Integer(), server_default='70000', nullable=True))
    op.add_column('properties', sa.Column('calc_maintenance', sa.Integer(), server_default='100000', nullable=True))
    op.add_column('properties', sa.Column('calc_target_yield', sa.Integer(), server_default='700', nullable=True))
    op.add_column('properties', sa.Column('calc_broker_fee', sa.Integer(), server_default='300', nullable=True))
    op.add_column('properties', sa.Column('calc_closing_fee', sa.Integer(), server_default='150', nullable=True))
    op.add_column('properties', sa.Column('calc_inspection', sa.Integer(), server_default='50000', nullable=True))


def downgrade() -> None:
    op.drop_column('properties', 'calc_inspection')
    op.drop_column('properties', 'calc_closing_fee')
    op.drop_column('properties', 'calc_broker_fee')
    op.drop_column('properties', 'calc_target_yield')
    op.drop_column('properties', 'calc_maintenance')
    op.drop_column('properties', 'calc_insurance')
    op.drop_column('properties', 'calc_property_tax')
    op.drop_column('properties', 'calc_rehab_estimate')
    op.drop_column('properties', 'calc_rent_estimate')
