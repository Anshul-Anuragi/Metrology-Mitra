export type UserRole = 'INSPECTOR' | 'SUPERVISOR' | 'ADMIN';

export type InspectionStatus = 'CREATED' | 'PROCESSING' | 'REVIEW_REQUIRED' | 'COMPLETED';

export type ComplianceResult = 'COMPLIANT' | 'NON_COMPLIANT' | 'NEEDS_REVIEW' | 'PENDING';

export type CheckResult = 'PASS' | 'FAIL' | 'REVIEW';

export type ImageType = 'FRONT' | 'BACK' | 'SIDE' | 'TOP' | 'BOTTOM' | 'LABEL' | 'MRP_PANEL' | 'OTHER';

export type ViolationSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type ViolationStatus = 'OPEN' | 'REVIEWED' | 'RESOLVED';

export type EvidenceType = 'BOUNDING_BOX' | 'CROPPED_IMAGE' | 'OCR_SNIPPET' | 'MANUAL_ANNOTATION';

export type ReportType = 'PDF' | 'JSON' | 'INSPECTION_MEMO' | 'NOTICE_SEC36';

export type QualityGateDecision = 'READY_FOR_ANALYSIS' | 'RETAKE_RECOMMENDED' | 'MANUAL_REVIEW';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  phone_number?: string | null;
  designation?: string | null;
  jurisdiction_state?: string | null;
  jurisdiction_district?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InspectionImage {
  id: string;
  inspection_id: string;
  image_url: string;
  image_type: ImageType;
  sequence_number?: number | null;
  resolution_width?: number | null;
  resolution_height?: number | null;
  sha256_hash?: string | null;
  quality_gate_result?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface Declaration {
  id: string;
  inspection_id: string;
  commodity_name?: string | null;
  manufacturer_name?: string | null;
  packer_name?: string | null;
  importer_name?: string | null;
  address?: string | null;
  country_of_origin?: string | null;
  is_imported: boolean;
  net_quantity?: string | null;
  mrp?: string | null;
  unit_sale_price?: string | null;
  manufacturing_date?: string | null;
  packing_date?: string | null;
  import_date?: string | null;
  expiry_date?: string | null;
  best_before?: string | null;
  consumer_care?: string | null;
  consumer_care_email?: string | null;
  consumer_care_phone?: string | null;
  pdp_area_sq_cm?: number | null;
  field_confidences?: Record<string, number> | null;
  raw_extractions?: Record<string, any> | null;
  digital_listing_data?: Record<string, any> | null;
  measurement_data?: Record<string, any> | null;
  is_human_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface LegalRule {
  id: string;
  rule_code: string;
  title: string;
  description?: string | null;
  source_reference?: string | null;
  rule_type: string;
  version?: string | null;
  penalty_clause?: string | null;
  effective_from?: string | null;
  effective_to?: string | null;
  channel?: string | null;
  source_version?: string | null;
  is_active: boolean;
}

export interface ComplianceCheck {
  id: string;
  inspection_id: string;
  legal_rule_id: string;
  field_name?: string | null;
  observed_value?: string | null;
  result: CheckResult;
  confidence?: number | null;
  reason?: string | null;
  checked_at: string;
  legal_rule?: LegalRule | null;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Violation {
  id: string;
  inspection_id: string;
  compliance_check_id: string;
  severity: ViolationSeverity;
  title: string;
  description?: string | null;
  rule_citation?: string | null;
  status: ViolationStatus;
  created_at: string;
}

export interface Evidence {
  id: string;
  inspection_id: string;
  compliance_check_id?: string | null;
  violation_id?: string | null;
  image_id?: string | null;
  evidence_type: EvidenceType;
  description?: string | null;
  bounding_box?: BoundingBox | null;
  created_at: string;
}

export interface Report {
  id: string;
  inspection_id: string;
  report_number: string;
  report_type: ReportType;
  file_url: string;
  generated_by: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  inspection_id: string;
  actor_user_id?: string | null;
  action: string;
  entity_type?: string | null;
  entity_id?: string | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
}

export interface Inspection {
  id: string;
  inspector_id: string;
  product_id?: string | null;
  batch_id?: string | null;
  store_name?: string | null;
  store_address?: string | null;
  district?: string | null;
  state?: string | null;
  gps_latitude?: number | null;
  gps_longitude?: number | null;
  language_detected?: string | null;
  status: InspectionStatus;
  overall_result: ComplianceResult;
  started_at?: string | null;
  completed_at?: string | null;
  reviewed_by_id?: string | null;
  reviewed_at?: string | null;
  finalized_by_id?: string | null;
  finalized_at?: string | null;
  review_notes?: string | null;
  created_at: string;
  updated_at: string;
  images?: InspectionImage[];
  declaration?: Declaration | null;
  compliance_checks?: ComplianceCheck[];
  violations?: Violation[];
  evidence_items?: Evidence[];
  reports?: Report[];
  audit_logs?: AuditLog[];
  inspector?: User | null;
}

export interface ScheduleIVCompliance {
  lot_size: number;
  sample_size_target: number;
  samples_inspected: number;
  compliant_count: number;
  non_compliant_count: number;
  review_count: number;
  pending_count: number;
  compliance_rate_percent: number;
  lot_acceptance_verdict: string;
  assessment_type?: string;
  physical_gravimetric_verified?: boolean;
  evaluation_standard: string;
  source_version?: string;
  effective_from?: string;
  disclaimer?: string;
}

export interface InspectionBatch {
  id: string;
  name: string;
  lot_size: number;
  sample_size: number;
  store_name?: string | null;
  store_address?: string | null;
  district?: string | null;
  state?: string | null;
  created_by_id: string;
  status: string;
  summary_stats?: Record<string, any> | null;
  schedule_iv_compliance?: ScheduleIVCompliance | null;
  inspections?: Inspection[];
  created_at: string;
  updated_at: string;
}

export interface EnforcementNotice {
  id: string;
  inspection_id: string;
  notice_number: string;
  notice_type: string;
  status: string;
  offence_count: number;
  statutory_sections?: string[] | null;
  compounding_amount?: number | null;
  challan_reference?: string | null;
  officer_remarks?: string | null;
  issued_at?: string | null;
  compounded_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompoundingCalculationResponse {
  offence_count: number;
  assessment_status: string;
  statutory_section: string;
  compounding_amount_reference?: number | null;
  base_compounding_fee?: number | null;
  max_statutory_penalty?: number | null;
  is_compoundable?: boolean | null;
  amount_determinable: boolean;
  statutory_citations: string[];
  source_legislation?: string;
  source_version?: string;
  effective_from?: string;
  effective_to?: string | null;
  legal_rationale: string;
  disclaimer?: string;
}

export interface PipelineExecutionResult {
  inspection_id: string;
  status: InspectionStatus;
  overall_result: ComplianceResult;
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  review_checks: number;
  total_violations: number;
  total_evidence_items: number;
  declaration?: Declaration | null;
  checks: ComplianceCheck[];
  violations: Violation[];
  evidence_items: Evidence[];
}

export interface AnalyticsOverview {
  total_inspections: number;
  compliant_inspections: number;
  non_compliant_inspections: number;
  needs_review_inspections: number;
  pending_inspections: number;
  compliance_rate_percent: number;
  total_violations: number;
  high_or_critical_violations: number;
  active_inspecting_officers: number;
}

export interface TrendDataPoint {
  period_start: string;
  total_inspections: number;
  compliant_count: number;
  non_compliant_count: number;
  needs_review_count: number;
  violation_count: number;
}

export interface AnalyticsTrends {
  period: string;
  data_points: TrendDataPoint[];
}

export interface HeatmapClusterPoint {
  state: string;
  district: string;
  inspection_count: number;
  violation_count: number;
  non_compliant_count: number;
  non_compliance_rate_percent: number;
  latitude?: number | null;
  longitude?: number | null;
  has_gps_coordinates: boolean;
}

export interface AnalyticsHeatmaps {
  total_regions: number;
  clusters: HeatmapClusterPoint[];
}

export interface RecurringNonComplianceEntity {
  entity_name: string;
  entity_type: string;
  inspection_count: number;
  violation_count: number;
  non_compliant_inspection_count: number;
  recurrence_rate_percent: number;
  common_failed_rule_codes: string[];
}

export interface AnalyticsRepeatOffenders {
  total_entities_tracked: number;
  entities: RecurringNonComplianceEntity[];
}

export interface FailingRuleMetric {
  rule_code: string;
  title: string;
  statutory_reference?: string | null;
  rule_type?: string | null;
  failure_count: number;
  failure_percentage: number;
}

export interface AnalyticsFailingRules {
  total_failed_checks: number;
  failing_rules: FailingRuleMetric[];
}

export interface ImageQualityDiagnostics {
  image_id: string;
  width: number;
  height: number;
  blur_score: number;
  blur_status: 'PASS' | 'WARNING' | 'FAIL';
  glare_ratio: number;
  glare_status: 'PASS' | 'WARNING' | 'FAIL';
  glare_detected: boolean;
  exposure_mean?: number;
  exposure_status?: 'PASS' | 'WARNING' | 'FAIL';
  gate_decision: QualityGateDecision;
  resolution_status: 'PASS' | 'WARNING' | 'FAIL';
  overall_status: 'PASS' | 'WARNING' | 'FAIL';
  is_acceptable: boolean;
  guidance_message: string;
  actionable_reasons?: string[];
  sha256_hash?: string | null;
}

export interface CatalogMatchInfo {
  matched: boolean;
  product_name?: string | null;
  brand_name?: string | null;
  catalog_mrp?: number | null;
  observed_mrp?: number | null;
  discrepancy: 'MATCH' | 'MISMATCH' | 'NO_OBSERVED_MRP' | 'NO_CATALOG_MATCH';
  reason: string;
}

export interface BarcodeDataInfo {
  value: string;
  format: string;
  bounding_box?: BoundingBox | null;
  source_image_id?: string | null;
  catalog_match?: CatalogMatchInfo | null;
}

export interface DigitalListingInput {
  title?: string;
  description?: string;
  price?: number;
  country_of_origin?: string;
  net_quantity?: string;
  manufacturer_name?: string;
  listing_url?: string;
}

export interface ListingDiscrepancyItem {
  field_name: string;
  physical_value: string;
  listing_value: string;
  is_contradiction: boolean;
  finding: string;
}

export interface DigitalListingCrossCheckResponse {
  has_contradictions: boolean;
  summary_verdict: CheckResult;
  items: ListingDiscrepancyItem[];
}

export interface MeasurementInput {
  pdp_area_cm2: number;
  pixel_height: number;
  pixel_scale_mm_per_px?: number;
  scale_source?: string;
  scale_confidence?: number;
  is_blown_or_moulded?: boolean;
}

export interface MeasurementResponse {
  inspection_id: string;
  pixel_height: number;
  physical_height_mm?: number | null;
  scale_source: string;
  scale_confidence: number;
  measurement_confidence: number;
  threshold_mm: number;
  pdp_area_cm2: number;
  result: CheckResult;
  reason: string;
  is_prototype: boolean;
}

export interface ReviewWorkspaceResponse {
  inspection_id: string;
  status: InspectionStatus;
  overall_result?: ComplianceResult | null;
  can_finalize: boolean;
  blocking_reasons: string[];
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  review_checks: number;
  declaration?: Declaration | null;
  checks: ComplianceCheck[];
  violations: Violation[];
  evidence_items: Evidence[];
  audit_logs: AuditLog[];
}

export interface DemoSeedResponse {
  status: string;
  message: string;
  total_presets: number;
  disclaimer: string;
}

// Phase 2.3: Gravimetric & MPE Types
export interface SampleUnitWeightInput {
  unit_number: number;
  gross_weight: number;
  tare_weight?: number;
}

export interface SampleUnitWeightResult {
  unit_number: number;
  gross_weight: number;
  tare_weight: number;
  net_weight: number;
  error_value: number;
  error_percent: number;
  is_negative_error: boolean;
  exceeds_mpe: boolean;
  exceeds_double_mpe: boolean;
}

export interface GravimetricTestCreate {
  inspection_id?: string;
  batch_id?: string;
  nominal_quantity_value: number;
  nominal_quantity_unit: string;
  declared_tare_weight: number;
  samples: SampleUnitWeightInput[];
  lot_size?: number;
}

export interface GravimetricTestResponse {
  id: string;
  inspection_id?: string | null;
  batch_id?: string | null;
  nominal_quantity_value: number;
  nominal_quantity_unit: string;
  declared_tare_weight: number;
  mpe_value: number;
  mpe_description: string;
  sample_units_data?: SampleUnitWeightResult[];
  sample_mean_net_quantity?: number | null;
  sample_std_dev?: number | null;
  defective_units_count: number;
  double_mpe_defective_count: number;
  lot_decision: string;
  statutory_standard: string;
  disclaimer?: string | null;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

// Phase 2.4: Statutory Exemptions & Special Packaging
export interface ExemptionEvaluationRequest {
  package_type: string;
  declared_net_quantity_value?: number;
  declared_net_quantity_unit?: string;
  is_institutional_consumer?: boolean;
  multi_piece_count?: number;
  combination_items?: Record<string, any>[];
}

export interface ExemptionEvaluationResponse {
  package_type: string;
  is_exempt: boolean;
  exemption_rule?: string | null;
  exempt_mandatory_declarations: string[];
  applicable_special_rules: string[];
  statutory_citations: string[];
  rationale: string;
  source_legislation: string;
  source_version: string;
  effective_from: string;
  effective_to?: string | null;
  disclaimer: string;
}

// Phase 2.5: Geofence Validation & Offline Synchronization
export interface GeoValidationRequest {
  latitude: number;
  longitude: number;
  expected_state?: string;
  expected_district?: string;
}

export interface GeoValidationResponse {
  is_valid_coordinate: boolean;
  in_bounds: boolean;
  matched_region: string;
  confidence: number;
  geofence_status: string;
  disclaimer: string;
}

export interface OfflineInspectionItem {
  client_temp_id: string;
  store_name?: string;
  store_address?: string;
  district?: string;
  state?: string;
  gps_latitude?: number;
  gps_longitude?: number;
  created_at_local?: string;
  commodity_name?: string;
  manufacturer_name?: string;
  net_quantity?: string;
  mrp?: string;
  package_type?: string;
  review_notes?: string;
}

export interface OfflineSyncBatchRequest {
  device_id?: string;
  offline_inspections: OfflineInspectionItem[];
}

export interface OfflineSyncBatchResponse {
  synced_count: number;
  failed_count: number;
  synced_records: Record<string, any>[];
  synced_at: string;
}
