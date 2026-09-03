"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-02 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums
    user_role = postgresql.ENUM('INSPECTOR', 'SUPERVISOR', 'ADMIN', name='user_role', create_type=False)
    user_role.create(op.get_bind(), checkfirst=True)

    product_category = postgresql.ENUM(
        'FOOD_BEVERAGE', 'COSMETIC_PERSONAL_CARE', 'ELECTRONICS', 'HOUSEHOLD', 'GENERAL',
        name='product_category', create_type=False
    )
    product_category.create(op.get_bind(), checkfirst=True)

    inspection_status = postgresql.ENUM(
        'CREATED', 'PROCESSING', 'REVIEW_REQUIRED', 'COMPLETED',
        name='inspection_status', create_type=False
    )
    inspection_status.create(op.get_bind(), checkfirst=True)

    compliance_result = postgresql.ENUM(
        'COMPLIANT', 'NON_COMPLIANT', 'NEEDS_REVIEW', 'PENDING',
        name='compliance_result', create_type=False
    )
    compliance_result.create(op.get_bind(), checkfirst=True)

    check_result = postgresql.ENUM('PASS', 'FAIL', 'REVIEW', name='check_result', create_type=False)
    check_result.create(op.get_bind(), checkfirst=True)

    image_type = postgresql.ENUM(
        'FRONT', 'BACK', 'SIDE', 'TOP', 'BOTTOM', 'LABEL', 'OTHER',
        name='image_type', create_type=False
    )
    image_type.create(op.get_bind(), checkfirst=True)

    violation_severity = postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='violation_severity', create_type=False)
    violation_severity.create(op.get_bind(), checkfirst=True)

    violation_status = postgresql.ENUM('OPEN', 'REVIEWED', 'RESOLVED', name='violation_status', create_type=False)
    violation_status.create(op.get_bind(), checkfirst=True)

    evidence_type = postgresql.ENUM(
        'BOUNDING_BOX', 'CROPPED_IMAGE', 'OCR_SNIPPET', 'MANUAL_ANNOTATION',
        name='evidence_type', create_type=False
    )
    evidence_type.create(op.get_bind(), checkfirst=True)

    report_type = postgresql.ENUM('PDF', 'JSON', 'INSPECTION_MEMO', 'NOTICE_SEC36', name='report_type', create_type=False)
    report_type.create(op.get_bind(), checkfirst=True)

    rule_type = postgresql.ENUM(
        'REQUIRED_FIELD', 'FORMAT_CHECK', 'NUMERAL_HEIGHT', 'UNIT_CHECK', 'EXPIRY_DATE_CHECK', 'CUSTOM_LOGIC',
        name='rule_type', create_type=False
    )
    rule_type.create(op.get_bind(), checkfirst=True)

    # 2. Table: users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('role', user_role, nullable=False, server_default='INSPECTOR'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 3. Table: products
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('commodity_name', sa.String(length=255), nullable=True),
        sa.Column('brand_name', sa.String(length=255), nullable=True),
        sa.Column('manufacturer_name', sa.String(length=255), nullable=True),
        sa.Column('category', product_category, nullable=False, server_default='GENERAL'),
        sa.Column('barcode', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_products_brand_name', 'products', ['brand_name'])
    op.create_index('ix_products_manufacturer_name', 'products', ['manufacturer_name'])
    op.create_index('ix_products_barcode', 'products', ['barcode'])

    # 4. Table: inspections
    op.create_table(
        'inspections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inspector_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('store_name', sa.String(length=255), nullable=True),
        sa.Column('store_address', sa.String(length=500), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('gps_latitude', sa.Float(), nullable=True),
        sa.Column('gps_longitude', sa.Float(), nullable=True),
        sa.Column('status', inspection_status, nullable=False, server_default='CREATED'),
        sa.Column('overall_result', compliance_result, nullable=True, server_default='PENDING'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['inspector_id'], ['users.id'], name='fk_inspection_inspector', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_inspection_product', ondelete='SET NULL'),
    )
    op.create_index('ix_inspections_inspector_id', 'inspections', ['inspector_id'])
    op.create_index('ix_inspections_product_id', 'inspections', ['product_id'])
    op.create_index('ix_inspections_status', 'inspections', ['status'])
    op.create_index('ix_inspections_district', 'inspections', ['district'])
    op.create_index('ix_inspections_state', 'inspections', ['state'])
    op.create_index('idx_inspections_created_at', 'inspections', ['created_at'])

    # 5. Table: inspection_images
    op.create_table(
        'inspection_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('image_url', sa.String(length=1000), nullable=False),
        sa.Column('image_type', image_type, nullable=False, server_default='OTHER'),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('resolution_width', sa.Integer(), nullable=True),
        sa.Column('resolution_height', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], name='fk_image_inspection', ondelete='CASCADE'),
        sa.UniqueConstraint('inspection_id', 'sequence_number', name='unique_inspection_sequence'),
    )
    op.create_index('ix_inspection_images_inspection_id', 'inspection_images', ['inspection_id'])

    # 6. Table: ocr_results
    op.create_table(
        'ocr_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('image_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('engine', sa.String(length=100), nullable=True),
        sa.Column('tokens_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['image_id'], ['inspection_images.id'], name='fk_ocr_image', ondelete='CASCADE'),
        sa.CheckConstraint('confidence IS NULL OR (confidence >= 0 AND confidence <= 1)', name='check_ocr_confidence_range'),
    )
    op.create_index('ix_ocr_results_image_id', 'ocr_results', ['image_id'], unique=True)

    # 7. Table: declarations
    op.create_table(
        'declarations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('commodity_name', sa.Text(), nullable=True),
        sa.Column('manufacturer_name', sa.Text(), nullable=True),
        sa.Column('packer_name', sa.Text(), nullable=True),
        sa.Column('importer_name', sa.Text(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('country_of_origin', sa.Text(), nullable=True),
        sa.Column('is_imported', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('net_quantity', sa.Text(), nullable=True),
        sa.Column('mrp', sa.Text(), nullable=True),
        sa.Column('unit_sale_price', sa.Text(), nullable=True),
        sa.Column('manufacturing_date', sa.Text(), nullable=True),
        sa.Column('packing_date', sa.Text(), nullable=True),
        sa.Column('import_date', sa.Text(), nullable=True),
        sa.Column('expiry_date', sa.Text(), nullable=True),
        sa.Column('best_before', sa.Text(), nullable=True),
        sa.Column('consumer_care', sa.Text(), nullable=True),
        sa.Column('consumer_care_email', sa.Text(), nullable=True),
        sa.Column('consumer_care_phone', sa.Text(), nullable=True),
        sa.Column('pdp_area_sq_cm', sa.Float(), nullable=True),
        sa.Column('field_confidences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('raw_extractions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_human_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], name='fk_declaration_inspection', ondelete='CASCADE'),
    )
    op.create_index('ix_declarations_inspection_id', 'declarations', ['inspection_id'], unique=True)

    # 8. Table: legal_rules
    op.create_table(
        'legal_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('rule_code', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=True),
        sa.Column('rule_type', rule_type, nullable=False, server_default='REQUIRED_FIELD'),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('version', sa.String(length=50), nullable=False, server_default='2011.1'),
        sa.Column('source_reference', sa.Text(), nullable=False),
        sa.Column('penalty_clause', sa.Text(), nullable=True),
        sa.Column('category_applicability', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('rule_code', 'version', name='unique_rule_version'),
    )
    op.create_index('ix_legal_rules_rule_code', 'legal_rules', ['rule_code'])
    op.create_index('ix_legal_rules_is_active', 'legal_rules', ['is_active'])

    # 9. Table: compliance_checks
    op.create_table(
        'compliance_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('legal_rule_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=True),
        sa.Column('observed_value', sa.Text(), nullable=True),
        sa.Column('result', check_result, nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], name='fk_check_inspection', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['legal_rule_id'], ['legal_rules.id'], name='fk_check_rule', ondelete='RESTRICT'),
        sa.CheckConstraint('confidence IS NULL OR (confidence >= 0 AND confidence <= 1)', name='check_compliance_confidence_range'),
    )
    op.create_index('ix_compliance_checks_inspection_id', 'compliance_checks', ['inspection_id'])
    op.create_index('ix_compliance_checks_legal_rule_id', 'compliance_checks', ['legal_rule_id'])

    # 10. Table: violations
    op.create_table(
        'violations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('compliance_check_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('severity', violation_severity, nullable=False, server_default='MEDIUM'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('rule_citation', sa.String(length=255), nullable=True),
        sa.Column('status', violation_status, nullable=False, server_default='OPEN'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], name='fk_violation_inspection', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['compliance_check_id'], ['compliance_checks.id'], name='fk_violation_check', ondelete='CASCADE'),
    )
    op.create_index('ix_violations_inspection_id', 'violations', ['inspection_id'])
    op.create_index('ix_violations_compliance_check_id', 'violations', ['compliance_check_id'])

    # 11. Table: evidence
    op.create_table(
        'evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('compliance_check_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('violation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('image_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('evidence_type', evidence_type, nullable=False, server_default='BOUNDING_BOX'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('bounding_box', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], name='fk_evidence_inspection', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['compliance_check_id'], ['compliance_checks.id'], name='fk_evidence_check', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['violation_id'], ['violations.id'], name='fk_evidence_violation', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['image_id'], ['inspection_images.id'], name='fk_evidence_image', ondelete='SET NULL'),
    )
    op.create_index('ix_evidence_inspection_id', 'evidence', ['inspection_id'])
    op.create_index('ix_evidence_compliance_check_id', 'evidence', ['compliance_check_id'])
    op.create_index('ix_evidence_violation_id', 'evidence', ['violation_id'])
    op.create_index('ix_evidence_image_id', 'evidence', ['image_id'])

    # 12. Table: reports
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_number', sa.String(length=100), nullable=False),
        sa.Column('report_type', report_type, nullable=False, server_default='PDF'),
        sa.Column('file_url', sa.Text(), nullable=False),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], name='fk_report_inspection', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['generated_by'], ['users.id'], name='fk_report_user', ondelete='RESTRICT'),
    )
    op.create_index('ix_reports_report_number', 'reports', ['report_number'], unique=True)
    op.create_index('ix_reports_inspection_id', 'reports', ['inspection_id'])


def downgrade() -> None:
    op.drop_table('reports')
    op.drop_table('evidence')
    op.drop_table('violations')
    op.drop_table('compliance_checks')
    op.drop_table('legal_rules')
    op.drop_table('declarations')
    op.drop_table('ocr_results')
    op.drop_table('inspection_images')
    op.drop_table('inspections')
    op.drop_table('products')
    op.drop_table('users')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS rule_type')
    op.execute('DROP TYPE IF EXISTS report_type')
    op.execute('DROP TYPE IF EXISTS evidence_type')
    op.execute('DROP TYPE IF EXISTS violation_status')
    op.execute('DROP TYPE IF EXISTS violation_severity')
    op.execute('DROP TYPE IF EXISTS image_type')
    op.execute('DROP TYPE IF EXISTS check_result')
    op.execute('DROP TYPE IF EXISTS compliance_result')
    op.execute('DROP TYPE IF EXISTS inspection_status')
    op.execute('DROP TYPE IF EXISTS product_category')
    op.execute('DROP TYPE IF EXISTS user_role')

