"""registry_seizures_and_corporate_liability

Revision ID: 0006_registry_seizures_corporate
Revises: 0005_gravimetric_and_exemptions
Create Date: 2026-09-03 22:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0006_registry_seizures_corporate'
down_revision: Union[str, None] = '0005_gravimetric_and_exemptions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create packer_registrations table (Phase 2.6: Rule 27)
    op.create_table(
        'packer_registrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('registration_number', sa.String(100), unique=True, nullable=False),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('registered_address', sa.Text(), nullable=False),
        sa.Column('jurisdiction_level', sa.String(50), nullable=False, server_default='CENTRAL_DIRECTOR'),
        sa.Column('state', sa.String(100), nullable=False),
        sa.Column('issuing_authority', sa.String(255), nullable=False, server_default='Director of Legal Metrology, GoI'),
        sa.Column('registered_categories', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('certificate_sha256', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_packer_registrations_reg_num', 'packer_registrations', ['registration_number'])
    op.create_index('ix_packer_registrations_entity_name', 'packer_registrations', ['entity_name'])

    # 2. Create companies table (Phase 2.8: Section 49)
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cin', sa.String(50), unique=True, nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('registered_office', sa.Text(), nullable=False),
        sa.Column('state', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_companies_cin', 'companies', ['cin'])
    op.create_index('ix_companies_company_name', 'companies', ['company_name'])

    # 3. Create nominated_directors table (Phase 2.8: Section 49(2))
    op.create_table(
        'nominated_directors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('director_name', sa.String(255), nullable=False),
        sa.Column('din', sa.String(50), nullable=False),
        sa.Column('designation', sa.String(100), nullable=False, server_default='Whole-time Director'),
        sa.Column('form_i_notice_date', sa.Date(), nullable=False),
        sa.Column('form_i_reference', sa.String(100), nullable=True),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_nominated_directors_company_id', 'nominated_directors', ['company_id'])
    op.create_index('ix_nominated_directors_din', 'nominated_directors', ['din'])

    # 4. Create seizure_records table (Phase 2.7: Section 15 & Rule 29)
    op.create_table(
        'seizure_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('seizure_memo_number', sa.String(100), unique=True, nullable=False),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inspections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inspection_batches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('premises_name', sa.String(255), nullable=False),
        sa.Column('premises_address', sa.Text(), nullable=False),
        sa.Column('seizure_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('statutory_grounds', sa.Text(), nullable=False),
        sa.Column('inspecting_officer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('witness_1_name', sa.String(255), nullable=False),
        sa.Column('witness_1_address', sa.Text(), nullable=False),
        sa.Column('witness_1_phone', sa.String(50), nullable=True),
        sa.Column('witness_2_name', sa.String(255), nullable=False),
        sa.Column('witness_2_address', sa.Text(), nullable=False),
        sa.Column('witness_2_phone', sa.String(50), nullable=True),
        sa.Column('custody_location', sa.String(255), nullable=False, server_default='Department of Legal Metrology Safe Custody Room'),
        sa.Column('status', sa.String(50), nullable=False, server_default='SEIZED_IN_CUSTODY'),
        sa.Column('sha256_seal_hash', sa.String(64), nullable=True),
        sa.Column('officer_remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_seizure_records_memo_num', 'seizure_records', ['seizure_memo_number'])
    op.create_index('ix_seizure_records_inspection_id', 'seizure_records', ['inspection_id'])

    # 5. Create seizure_items table
    op.create_table(
        'seizure_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('seizure_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('seizure_records.id', ondelete='CASCADE'), nullable=False),
        sa.Column('commodity_name', sa.String(255), nullable=False),
        sa.Column('brand_name', sa.String(255), nullable=True),
        sa.Column('batch_lot_number', sa.String(100), nullable=True),
        sa.Column('declared_net_quantity', sa.String(50), nullable=True),
        sa.Column('total_packages_seized', sa.Integer(), nullable=False),
        sa.Column('sample_packages_taken', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sample_seal_tag_number', sa.String(100), nullable=True),
        sa.Column('mrp', sa.String(100), nullable=True),
    )
    op.create_index('ix_seizure_items_seizure_id', 'seizure_items', ['seizure_id'])

    # 6. Alter inspections table to add company_id
    op.add_column('inspections', sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='SET NULL'), nullable=True))
    op.create_index('ix_inspections_company_id', 'inspections', ['company_id'])


def downgrade() -> None:
    op.drop_index('ix_inspections_company_id', table_name='inspections')
    op.drop_column('inspections', 'company_id')
    op.drop_table('seizure_items')
    op.drop_table('seizure_records')
    op.drop_table('nominated_directors')
    op.drop_table('companies')
    op.drop_table('packer_registrations')

