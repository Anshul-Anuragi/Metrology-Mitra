"""gravimetric_tests_and_exemptions

Revision ID: 0005_gravimetric_and_exemptions
Revises: 0004_batch_and_enforcement
Create Date: 2026-09-03 17:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0005_gravimetric_and_exemptions'
down_revision: Union[str, None] = '0004_batch_and_enforcement'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create gravimetric_tests table
    op.create_table(
        'gravimetric_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inspections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inspection_batches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('nominal_quantity_value', sa.Float(), nullable=False),
        sa.Column('nominal_quantity_unit', sa.String(20), nullable=False, server_default='g'),
        sa.Column('declared_tare_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('mpe_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('sample_units_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sample_mean_net_quantity', sa.Float(), nullable=True),
        sa.Column('sample_std_dev', sa.Float(), nullable=True),
        sa.Column('defective_units_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lot_decision', sa.String(50), nullable=False, server_default='INCOMPLETE'),
        sa.Column('statutory_standard', sa.String(255), nullable=False, server_default='LMPC Rules, 2011 — Schedule IV & Rule 24'),
        sa.Column('disclaimer', sa.Text(), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_gravimetric_tests_inspection_id', 'gravimetric_tests', ['inspection_id'])
    op.create_index('ix_gravimetric_tests_batch_id', 'gravimetric_tests', ['batch_id'])

    # 2. Alter declarations table to add package type and exemption fields
    op.add_column('declarations', sa.Column('package_type', sa.String(50), nullable=False, server_default='STANDARD'))
    op.add_column('declarations', sa.Column('exemption_applied', sa.String(100), nullable=True))
    op.add_column('declarations', sa.Column('exemption_rationale', sa.Text(), nullable=True))
    op.add_column('declarations', sa.Column('multi_piece_count', sa.Integer(), nullable=True))
    op.add_column('declarations', sa.Column('combination_items', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # 3. Alter inspections table to add offline and provenance fields
    op.add_column('inspections', sa.Column('offline_client_id', sa.String(100), nullable=True))
    op.add_column('inspections', sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('inspections', sa.Column('geo_verified', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('inspections', 'geo_verified')
    op.drop_column('inspections', 'synced_at')
    op.drop_column('inspections', 'offline_client_id')
    op.drop_column('declarations', 'combination_items')
    op.drop_column('declarations', 'multi_piece_count')
    op.drop_column('declarations', 'exemption_rationale')
    op.drop_column('declarations', 'exemption_applied')
    op.drop_column('declarations', 'package_type')
    op.drop_index('ix_gravimetric_tests_batch_id', table_name='gravimetric_tests')
    op.drop_index('ix_gravimetric_tests_inspection_id', table_name='gravimetric_tests')
    op.drop_table('gravimetric_tests')

