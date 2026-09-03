"""regulatory_intelligence_and_versioning

Revision ID: 0003_regulatory_intelligence
Revises: 0002_audit_logs
Create Date: 2026-09-03 06:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0003_regulatory_intelligence'
down_revision: Union[str, None] = '0002_audit_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add versioning and channel columns to legal_rules table
    op.add_column('legal_rules', sa.Column('effective_from', sa.Date(), nullable=True))
    op.add_column('legal_rules', sa.Column('effective_to', sa.Date(), nullable=True))
    op.add_column('legal_rules', sa.Column('channel', sa.String(50), nullable=False, server_default='BOTH'))
    op.add_column('legal_rules', sa.Column('source_version', sa.String(50), nullable=True))

    # 2. Add SHA-256 evidence integrity hash and quality gate result to inspection_images
    op.add_column('inspection_images', sa.Column('sha256_hash', sa.String(64), nullable=True))
    op.add_column('inspection_images', sa.Column('quality_gate_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # 3. Add digital listing data and measurement data to declarations
    op.add_column('declarations', sa.Column('digital_listing_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('declarations', sa.Column('measurement_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('declarations', 'measurement_data')
    op.drop_column('declarations', 'digital_listing_data')
    op.drop_column('inspection_images', 'quality_gate_result')
    op.drop_column('inspection_images', 'sha256_hash')
    op.drop_column('legal_rules', 'source_version')
    op.drop_column('legal_rules', 'channel')
    op.drop_column('legal_rules', 'effective_to')
    op.drop_column('legal_rules', 'effective_from')

