"""audit_logs_and_review_workflow

Revision ID: 0002_audit_logs
Revises: 0001_initial_schema
Create Date: 2026-09-02 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0002_audit_logs'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add review & finalization tracking columns to inspections table
    op.add_column('inspections', sa.Column('review_notes', sa.Text(), nullable=True))
    op.add_column('inspections', sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('inspections', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('inspections', sa.Column('finalized_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('inspections', sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True))

    op.create_foreign_key(
        'fk_inspections_reviewed_by', 'inspections', 'users', ['reviewed_by_id'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_inspections_finalized_by', 'inspections', 'users', ['finalized_by_id'], ['id'], ondelete='SET NULL'
    )

    # 2. Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], name='fk_audit_logs_inspection_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name='fk_audit_logs_actor_user_id', ondelete='SET NULL'),
    )
    op.create_index('idx_audit_logs_inspection_id', 'audit_logs', ['inspection_id'])
    op.create_index('idx_audit_logs_actor_user_id', 'audit_logs', ['actor_user_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_inspection_created', 'audit_logs', ['inspection_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_audit_logs_inspection_created', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_actor_user_id', table_name='audit_logs')
    op.drop_index('idx_audit_logs_inspection_id', table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_constraint('fk_inspections_finalized_by', 'inspections', type_='foreignkey')
    op.drop_constraint('fk_inspections_reviewed_by', 'inspections', type_='foreignkey')
    op.drop_column('inspections', 'finalized_at')
    op.drop_column('inspections', 'finalized_by_id')
    op.drop_column('inspections', 'reviewed_at')
    op.drop_column('inspections', 'reviewed_by_id')
    op.drop_column('inspections', 'review_notes')

