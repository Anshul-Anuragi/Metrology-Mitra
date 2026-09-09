"""investigation_dossiers

Revision ID: 0007_investigation_dossiers
Revises: 0006_registry_seizures_corporate
Create Date: 2026-09-04 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0007_investigation_dossiers'
down_revision: Union[str, None] = '0006_registry_seizures_corporate'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums with IF NOT EXISTS via raw SQL
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE dossier_status AS ENUM (
                'ACTIVE', 'EVALUATION', 'NOTICE_REVIEW', 'COMPOUNDING_REVIEW', 'CLOSED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE dossier_priority AS ENUM (
                'LOW', 'NORMAL', 'HIGH', 'CRITICAL'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    dossier_status = postgresql.ENUM(
        'ACTIVE', 'EVALUATION', 'NOTICE_REVIEW', 'COMPOUNDING_REVIEW', 'CLOSED',
        name='dossier_status',
        create_type=False,
    )

    dossier_priority = postgresql.ENUM(
        'LOW', 'NORMAL', 'HIGH', 'CRITICAL',
        name='dossier_priority',
        create_type=False,
    )

    # 2. Create investigation_dossiers table
    op.create_table(
        'investigation_dossiers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dossier_number', sa.String(64), unique=True, nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_entity_name', sa.String(255), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', dossier_status, nullable=False, server_default='ACTIVE'),
        sa.Column('priority', dossier_priority, nullable=False, server_default='NORMAL'),
        sa.Column('lead_supervisor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name='fk_dossiers_company_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lead_supervisor_id'], ['users.id'], name='fk_dossiers_lead_supervisor', ondelete='RESTRICT'),
    )
    op.create_index('ix_investigation_dossiers_dossier_number', 'investigation_dossiers', ['dossier_number'])
    op.create_index('ix_investigation_dossiers_status', 'investigation_dossiers', ['status'])
    op.create_index('ix_investigation_dossiers_lead_supervisor_id', 'investigation_dossiers', ['lead_supervisor_id'])
    op.create_index('ix_investigation_dossiers_company_id', 'investigation_dossiers', ['company_id'])

    # 3. Create dossier_inspections table
    op.create_table(
        'dossier_inspections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dossier_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('added_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('relevance_notes', sa.Text(), nullable=True),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['dossier_id'], ['investigation_dossiers.id'], name='fk_dossier_inspections_dossier', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], name='fk_dossier_inspections_inspection', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['added_by_id'], ['users.id'], name='fk_dossier_inspections_added_by', ondelete='SET NULL'),
        sa.UniqueConstraint('dossier_id', 'inspection_id', name='uq_dossier_inspection'),
    )
    op.create_index('ix_dossier_inspections_dossier_id', 'dossier_inspections', ['dossier_id'])
    op.create_index('ix_dossier_inspections_inspection_id', 'dossier_inspections', ['inspection_id'])


def downgrade() -> None:
    op.drop_table('dossier_inspections')
    op.drop_table('investigation_dossiers')
    op.execute("DROP TYPE IF EXISTS dossier_priority CASCADE")
    op.execute("DROP TYPE IF EXISTS dossier_status CASCADE")

