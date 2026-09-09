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
  package_type?: string;
  exemption_applied?: string | null;
  exemption_rationale?: string | null;
  multi_piece_count?: number | null;
  combination_items?: Record<string, any>[] | null;
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
  geo_verified?: boolean;
  synced_at?: string | null;
  offline_client_id?: string | null;
  language_detected?: string | null;
  status: InspectionStatus;
  overall_result: ComplianceResult;
  statutory_verdict?: ComplianceResult | null;
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
  commodity_category?: string;
  is_agricultural_farm_produce?: boolean;
  is_institutional_consumer?: boolean;
  has_institutional_marking?: boolean;
  is_fast_food_takeout?: boolean;
  is_tobacco_product?: boolean;
  multi_piece_count?: number;
  combination_items?: Record<string, any>[];
}

export interface ExemptionEvaluationResponse {
  package_type: string;
  is_exempt: boolean;
  assessment_status: string;
  exemption_rule?: string | null;
  exempt_mandatory_declarations: string[];
  applicable_special_rules: string[];
  statutory_citations: string[];
  rationale: string;
  missing_statutory_facts?: string[];
  statutory_conditions?: string[];
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

// Phase 2.6: Rule 27 Pre-Packer Registry
export interface PackerRegistration {
  id: string;
  registration_number: string;
  entity_name: string;
  registered_address: string;
  jurisdiction_level: string;
  state: string;
  issuing_authority: string;
  registered_categories: string[];
  valid_from: string;
  valid_to?: string | null;
  is_active: boolean;
  certificate_sha256?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RegistrationVerifyRequest {
  registration_number?: string;
  entity_name?: string;
  state?: string;
  commodity_category?: string;
}

export interface RegistrationVerifyResponse {
  verification_status: string;
  registration_number?: string | null;
  matched_entity_name?: string | null;
  registered_address?: string | null;
  jurisdiction_level?: string | null;
  state?: string | null;
  is_active: boolean;
  valid_from?: string | null;
  valid_to?: string | null;
  is_compliant: boolean;
  statutory_citation: string;
  rationale: string;
  disclaimer: string;
}

// Phase 2.7: Section 15 Seizures & Panchnama
export interface SeizureItem {
  id: string;
  seizure_id: string;
  commodity_name: string;
  brand_name?: string | null;
  batch_lot_number?: string | null;
  declared_net_quantity?: string | null;
  total_packages_seized: number;
  sample_packages_taken: number;
  sample_seal_tag_number?: string | null;
  mrp?: string | null;
}

export interface SeizureRecordCreate {
  inspection_id?: string;
  batch_id?: string;
  premises_name: string;
  premises_address: string;
  seizure_date?: string;
  statutory_grounds?: string;
  witness_1: { name: string; address: string; phone?: string };
  witness_2: { name: string; address: string; phone?: string };
  custody_location?: string;
  items: Array<{
    commodity_name: string;
    brand_name?: string;
    batch_lot_number?: string;
    declared_net_quantity?: string;
    total_packages_seized: number;
    sample_packages_taken?: number;
    sample_seal_tag_number?: string;
    mrp?: string;
  }>;
  officer_remarks?: string;
}

export interface SeizureRecord {
  id: string;
  seizure_memo_number: string;
  inspection_id?: string | null;
  batch_id?: string | null;
  premises_name: string;
  premises_address: string;
  seizure_date: string;
  statutory_grounds: string;
  inspecting_officer_id: string;
  witness_1_name: string;
  witness_1_address: string;
  witness_1_phone?: string | null;
  witness_2_name: string;
  witness_2_address: string;
  witness_2_phone?: string | null;
  custody_location: string;
  status: string;
  sha256_seal_hash?: string | null;
  officer_remarks?: string | null;
  items: SeizureItem[];
  created_at: string;
  updated_at: string;
  disclaimer?: string;
}

// Phase 2.8: Section 49 Corporate Liability
export interface NominatedDirector {
  id: string;
  company_id: string;
  director_name: string;
  din: string;
  designation: string;
  form_i_notice_date: string;
  form_i_reference?: string | null;
  effective_from: string;
  effective_to?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Company {
  id: string;
  cin: string;
  company_name: string;
  registered_office: string;
  state: string;
  email?: string | null;
  phone?: string | null;
  is_active: boolean;
  nominated_directors: NominatedDirector[];
  created_at: string;
  updated_at: string;
}

export interface Section49LiabilityAssessment {
  company_id?: string | null;
  company_name: string;
  cin?: string | null;
  statutory_basis: string;
  has_nominated_director: boolean;
  nominated_director?: NominatedDirector | null;
  liability_determination: string;
  notice_recipient_name: string;
  notice_recipient_designation: string;
  rationale: string;
  disclaimer: string;
}

// Phase 2.9: Operational Case Intelligence, Evidence Completeness & Supervisor Triage
export type EvidenceFacetStatus = 'COMPLETE' | 'PARTIAL' | 'MISSING' | 'NOT_APPLICABLE';
export type PriorityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type ActionRecommendationCategory = 'EVIDENCE_COLLECTION' | 'VERIFICATION' | 'LEGAL_WORKFLOW' | 'SUPERVISORY_ACTION';

export interface EvidenceFacet {
  name: string;
  facet_code: string;
  status: EvidenceFacetStatus;
  score: number;
  weight: number;
  is_required: boolean;
  is_applicable: boolean;
  evidence_present: string[];
  evidence_missing: string[];
  actionable_gap?: string | null;
}

export interface EvidenceGap {
  code: string;
  title: string;
  description: string;
  severity: ViolationSeverity;
  action: string;
  facet_code: string;
  is_blocking: boolean;
}

export interface EvidenceCompleteness {
  score: number;
  status: string;
  facets: EvidenceFacet[];
  gaps: EvidenceGap[];
  disclaimer: string;
}

export interface PriorityFactor {
  code: string;
  description: string;
  points_contributed: number;
  severity: string;
}

export interface CasePriority {
  score: number;
  level: PriorityLevel;
  factors: PriorityFactor[];
  summary: string;
  disclaimer: string;
}

export interface ActionRecommendation {
  code: string;
  title: string;
  description: string;
  priority: PriorityLevel;
  category: ActionRecommendationCategory;
  is_advisory: boolean;
  related_rule?: string | null;
  action_label: string;
}

export interface CaseIntelligenceResponse {
  inspection_id: string;
  evidence_completeness: EvidenceCompleteness;
  case_priority: CasePriority;
  recommendations: ActionRecommendation[];
  legal_context: {
    overall_result: string;
    inspection_status: string;
    store_name?: string | null;
    district?: string | null;
    state?: string | null;
    is_finalized: boolean;
  };
  disclaimer: string;
}

export interface SupervisorTriageItem {
  inspection_id: string;
  created_at: string;
  store_name?: string | null;
  district?: string | null;
  state?: string | null;
  inspector_name?: string | null;
  inspector_id?: string | null;
  entity_name?: string | null;
  commodity_name?: string | null;
  overall_result: ComplianceResult;
  status: InspectionStatus;
  evidence_completeness_score: number;
  priority_score: number;
  priority_level: PriorityLevel;
  unresolved_review_count: number;
  violation_count: number;
  max_violation_severity?: string | null;
  primary_attention_reason: string;
  has_repeat_offence_history: boolean;
}

export interface SupervisorTriageResponse {
  total_items: number;
  items: SupervisorTriageItem[];
  priority_counts: Record<string, number>;
  disclaimer: string;
}

// --- Phase 3.0: Market Surveillance Investigation Dossiers ---
export type DossierStatus =
  | 'ACTIVE'
  | 'EVALUATION'
  | 'NOTICE_REVIEW'
  | 'COMPOUNDING_REVIEW'
  | 'CLOSED';

export type DossierPriority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';

export interface DossierInspection {
  id: string;
  dossier_id: string;
  inspection_id: string;
  added_by_id: string;
  relevance_notes?: string | null;
  added_at: string;
  inspection?: Inspection | null;
  added_by?: User | null;
}

export interface InvestigationDossier {
  id: string;
  dossier_number: string;
  title: string;
  description?: string | null;
  target_entity_name?: string | null;
  company_id?: string | null;
  status: DossierStatus;
  priority: DossierPriority;
  lead_supervisor_id: string;
  tags: string[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  closed_at?: string | null;
  lead_supervisor?: User | null;
  company?: Company | null;
  inspections: DossierInspection[];
}

export interface InvestigationDossierCreate {
  title: string;
  description?: string | null;
  target_entity_name?: string | null;
  company_id?: string | null;
  priority?: DossierPriority;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface InvestigationDossierUpdate {
  title?: string | null;
  description?: string | null;
  target_entity_name?: string | null;
  company_id?: string | null;
  status?: DossierStatus | null;
  priority?: DossierPriority | null;
  tags?: string[] | null;
  metadata?: Record<string, any> | null;
}

export interface DossierSummaryCounts {
  total_inspections: number;
  compliant_count: number;
  non_compliant_count: number;
  needs_review_count: number;
  pending_count: number;
  total_violations: number;
  critical_violations: number;
  high_violations: number;
  medium_violations: number;
  low_violations: number;
}

export interface ObservedFindingSummary {
  rule_code: string;
  rule_name: string;
  affected_inspection_count: number;
  severity_levels: string[];
  observation_label: string;
}

export interface RecordedSeizureSummary {
  total_seizure_records: number;
  total_seized_quantity: number;
  seizure_items_count: number;
  description: string;
}

export interface DossierNominatedDirectorReview {
  director_name: string;
  din: string;
  designation: string;
  form_i_notice_date?: string | null;
  form_i_reference?: string | null;
  effective_from: string;
  effective_to?: string | null;
  is_active: boolean;
  statutory_role_note: string;
}

export interface DossierTimelineEvent {
  timestamp: string;
  event_type: string;
  description: string;
  actor_id?: string | null;
  inspection_id?: string | null;
}

export interface DossierSynthesisResponse {
  dossier_id: string;
  dossier_number: string;
  title: string;
  target_entity_name?: string | null;
  company_id?: string | null;
  status: DossierStatus;
  priority: DossierPriority;
  summary_counts: DossierSummaryCounts;
  observed_findings: ObservedFindingSummary[];
  recorded_seizure_summary: RecordedSeizureSummary;
  districts_covered: string[];
  states_covered: string[];
  premises_count: number;
  batches_count: number;
  evidence_completeness_avg?: number | null;
  nominated_directors_review: DossierNominatedDirectorReview[];
  timeline_events: DossierTimelineEvent[];
  advisory_disclaimer: string;
}

