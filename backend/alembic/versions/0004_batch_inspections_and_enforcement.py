"""batch_inspections_and_enforcement

Revision ID: 0004_batch_and_enforcement
Revises: 0003_regulatory_intelligence
Create Date: 2026-09-03 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0004_batch_and_enforcement'
down_revision: Union[str, None] = '0003_regulatory_intelligence'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create inspection_batches table
    op.create_table(
        'inspection_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('lot_size', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sample_size', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('store_name', sa.String(255), nullable=True),
        sa.Column('store_address', sa.String(500), nullable=True),
        sa.Column('district', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='IN_PROGRESS'),
        sa.Column('summary_stats', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name='fk_batches_created_by', ondelete='RESTRICT'),
    )
    op.create_index('idx_batches_created_by', 'inspection_batches', ['created_by_id'])
    op.create_index('idx_batches_status', 'inspection_batches', ['status'])

    # 2. Add batch_id and language_detected to inspections table
    op.add_column('inspections', sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('inspections', sa.Column('language_detected', sa.String(50), nullable=True))
    op.create_foreign_key(
        'fk_inspections_batch_id', 'inspections', 'inspection_batches', ['batch_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index('idx_inspections_batch_id', 'inspections', ['batch_id'])

    # 3. Create enforcement_notices table
    op.create_table(
        'enforcement_notices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notice_number', sa.String(100), unique=True, nullable=False),
        sa.Column('notice_type', sa.String(50), nullable=False, server_default='SHOW_CAUSE_NOTICE'),
        sa.Column('status', sa.String(50), nullable=False, server_default='DRAFTED'),
        sa.Column('offence_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('statutory_sections', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('compounding_amount', sa.Float(), nullable=True),
        sa.Column('challan_reference', sa.String(100), nullable=True),
        sa.Column('officer_remarks', sa.Text(), nullable=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('compounded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], name='fk_notices_inspection_id', ondelete='CASCADE'),
    )
    op.create_index('idx_notices_inspection_id', 'enforcement_notices', ['inspection_id'])
    op.create_index('idx_notices_status', 'enforcement_notices', ['status'])
    op.create_index('idx_notices_notice_number', 'enforcement_notices', ['notice_number'])


def downgrade() -> None:
    op.drop_index('idx_notices_notice_number', table_name='enforcement_notices')
    op.drop_index('idx_notices_status', table_name='enforcement_notices')
    op.drop_index('idx_notices_inspection_id', table_name='enforcement_notices')
    op.drop_table('enforcement_notices')

    op.drop_constraint('fk_inspections_batch_id', 'inspections', type_='foreignkey')
    op.drop_index('idx_inspections_batch_id', table_name='inspections')
    op.drop_column('inspections', 'language_detected')
    op.drop_column('inspections', 'batch_id')

    op.drop_index('idx_batches_status', table_name='inspection_batches')
    op.drop_index('idx_batches_created_by', table_name='inspection_batches')
    op.drop_table('inspection_batches')

