import axios, { AxiosError } from 'axios';
import {
  AnalyticsFailingRules,
  AnalyticsHeatmaps,
  AnalyticsOverview,
  AnalyticsRepeatOffenders,
  AnalyticsTrends,
  AuditLog,
  Declaration,
  DemoSeedResponse,
  DigitalListingCrossCheckResponse,
  DigitalListingInput,
  Evidence,
  ImageQualityDiagnostics,
  Inspection,
  InspectionBatch,
  InspectionImage,
  MeasurementInput,
  MeasurementResponse,
  PipelineExecutionResult,
  Report,
  ReviewWorkspaceResponse,
  User,
  Violation,
  EnforcementNotice,
  CompoundingCalculationResponse,
  GravimetricTestCreate,
  GravimetricTestResponse,
  ExemptionEvaluationRequest,
  ExemptionEvaluationResponse,
  GeoValidationRequest,
  GeoValidationResponse,
  OfflineSyncBatchRequest,
  OfflineSyncBatchResponse,
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token from localStorage to every request
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 Unauthorized globally
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      if (!window.location.pathname.startsWith('/login')) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  // --- Auth ---
  login: async (email: string, password: string): Promise<{ access_token: string; token_type: string }> => {
    const res = await apiClient.post('/auth/login', { email, password });
    return res.data;
  },

  getMe: async (): Promise<User> => {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },

  // --- Inspections ---
  createInspection: async (data: {
    product_id?: string;
    batch_id?: string;
    store_name?: string;
    store_address?: string;
    district?: string;
    state?: string;
    gps_latitude?: number;
    gps_longitude?: number;
  }): Promise<Inspection> => {
    const res = await apiClient.post<Inspection>('/inspections/', data);
    return res.data;
  },

  listInspections: async (params?: {
    skip?: number;
    limit?: number;
    status_filter?: string;
    result_filter?: string;
    state_filter?: string;
    district_filter?: string;
    search?: string;
  }): Promise<Inspection[]> => {
    const res = await apiClient.get<Inspection[]>('/inspections/', { params });
    return res.data;
  },

  getInspection: async (id: string): Promise<Inspection> => {
    const res = await apiClient.get<Inspection>(`/inspections/${id}`);
    return res.data;
  },

  updateDeclaration: async (id: string, data: Partial<Declaration>): Promise<Declaration> => {
    const res = await apiClient.patch<Declaration>(`/inspections/${id}/declaration`, data);
    return res.data;
  },

  // --- Images & Diagnostics ---
  uploadImage: async (
    inspectionId: string,
    file: File,
    imageType: string = 'LABEL',
    sequenceNumber?: number
  ): Promise<InspectionImage> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('image_type', imageType);
    if (sequenceNumber !== undefined) {
      formData.append('sequence_number', sequenceNumber.toString());
    }

    const res = await apiClient.post<InspectionImage>(`/inspections/${inspectionId}/images`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  listImages: async (inspectionId: string): Promise<InspectionImage[]> => {
    const res = await apiClient.get<InspectionImage[]>(`/inspections/${inspectionId}/images`);
    return res.data;
  },

  getImageDiagnostics: async (inspectionId: string, imageId: string): Promise<ImageQualityDiagnostics> => {
    const res = await apiClient.post<ImageQualityDiagnostics>(`/inspections/${inspectionId}/images/${imageId}/diagnostics`);
    return res.data;
  },

  runQualityGate: async (inspectionId: string, imageId: string): Promise<ImageQualityDiagnostics> => {
    const res = await apiClient.post<ImageQualityDiagnostics>(`/inspections/${inspectionId}/images/${imageId}/quality-gate`);
    return res.data;
  },

  // --- Pipeline, Evaluation & Adjudication ---
  runPipeline: async (inspectionId: string): Promise<PipelineExecutionResult> => {
    const res = await apiClient.post<PipelineExecutionResult>(`/inspections/${inspectionId}/pipeline`);
    return res.data;
  },

  evaluateInspection: async (inspectionId: string) => {
    const res = await apiClient.post(`/inspections/${inspectionId}/evaluate`);
    return res.data;
  },

  getViolations: async (inspectionId: string): Promise<Violation[]> => {
    const res = await apiClient.get<Violation[]>(`/inspections/${inspectionId}/violations`);
    return res.data;
  },

  getEvidence: async (inspectionId: string): Promise<Evidence[]> => {
    const res = await apiClient.get<Evidence[]>(`/inspections/${inspectionId}/evidence`);
    return res.data;
  },

  // --- Review & Finalization Workspace ---
  getReviewWorkspace: async (inspectionId: string): Promise<ReviewWorkspaceResponse> => {
    const res = await apiClient.get<ReviewWorkspaceResponse>(`/inspections/${inspectionId}/review`);
    return res.data;
  },

  submitReview: async (
    inspectionId: string,
    data: {
      review_action: 'CONFIRM' | 'CORRECT' | 'REQUEST_RETAKE' | 'MARK_UNRESOLVED';
      review_notes?: string;
      declaration_overrides?: Record<string, any>;
    }
  ): Promise<ReviewWorkspaceResponse> => {
    const res = await apiClient.post<ReviewWorkspaceResponse>(`/inspections/${inspectionId}/review`, data);
    return res.data;
  },

  finalizeInspection: async (
    inspectionId: string,
    data: { finalization_notes?: string }
  ): Promise<Inspection> => {
    const res = await apiClient.post<Inspection>(`/inspections/${inspectionId}/finalize`, data);
    return res.data;
  },

  getAuditTrail: async (inspectionId: string): Promise<AuditLog[]> => {
    const res = await apiClient.get<AuditLog[]>(`/inspections/${inspectionId}/audit`);
    return res.data;
  },

  // --- Digital Listing & Physical Measurement Assistant ---
  submitDigitalListing: async (
    inspectionId: string,
    data: DigitalListingInput
  ): Promise<DigitalListingCrossCheckResponse> => {
    const res = await apiClient.post<DigitalListingCrossCheckResponse>(`/inspections/${inspectionId}/listing`, data);
    return res.data;
  },

  recordMeasurement: async (
    inspectionId: string,
    data: MeasurementInput
  ): Promise<MeasurementResponse> => {
    const res = await apiClient.post<MeasurementResponse>(`/inspections/${inspectionId}/measurement`, data);
    return res.data;
  },

  // --- Demo Presets ---
  seedDemoPresets: async (): Promise<DemoSeedResponse> => {
    const res = await apiClient.post<DemoSeedResponse>('/inspections/demo-seed');
    return res.data;
  },

  // --- Reports ---
  generateReport: async (inspectionId: string, reportType: 'PDF' | 'JSON' | 'NOTICE_SEC36'): Promise<Report> => {
    const res = await apiClient.post<Report>(`/inspections/${inspectionId}/reports`, { report_type: reportType });
    return res.data;
  },

  listReports: async (inspectionId: string): Promise<Report[]> => {
    const res = await apiClient.get<Report[]>(`/inspections/${inspectionId}/reports`);
    return res.data;
  },

  downloadReport: async (inspectionId: string, reportId: string, filename: string): Promise<void> => {
    const res = await apiClient.get(`/inspections/${inspectionId}/reports/${reportId}/download`, {
      responseType: 'blob',
    });

    const contentType = (res.headers['content-type'] as string) || (filename.endsWith('.json') ? 'application/json' : 'application/pdf');
    const blob = new Blob([res.data], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // --- Supervisor Analytics ---
  getAnalyticsOverview: async (): Promise<AnalyticsOverview> => {
    const res = await apiClient.get<AnalyticsOverview>('/analytics/overview');
    return res.data;
  },

  getAnalyticsTrends: async (period: 'monthly' | 'weekly' | 'daily' = 'monthly'): Promise<AnalyticsTrends> => {
    const res = await apiClient.get<AnalyticsTrends>('/analytics/trends', { params: { period } });
    return res.data;
  },

  getAnalyticsHeatmaps: async (state?: string): Promise<AnalyticsHeatmaps> => {
    const res = await apiClient.get<AnalyticsHeatmaps>('/analytics/heatmaps', { params: { state } });
    return res.data;
  },

  getAnalyticsRepeatOffenders: async (limit: number = 10): Promise<AnalyticsRepeatOffenders> => {
    const res = await apiClient.get<AnalyticsRepeatOffenders>('/analytics/repeat-offenders', { params: { limit } });
    return res.data;
  },

  getAnalyticsFailingRules: async (limit: number = 20): Promise<AnalyticsFailingRules> => {
    const res = await apiClient.get<AnalyticsFailingRules>('/analytics/failing-rules', { params: { limit } });
    return res.data;
  },

  // --- Phase 2.1: Batch / Lot Inspections & Bulk Evidence Export ---
  createBatch: async (data: {
    name: string;
    lot_size?: number;
    sample_size?: number;
    store_name?: string;
    store_address?: string;
    district?: string;
    state?: string;
  }): Promise<InspectionBatch> => {
    const res = await apiClient.post<InspectionBatch>('/batches/', data);
    return res.data;
  },

  listBatches: async (params?: { status?: string }): Promise<InspectionBatch[]> => {
    const res = await apiClient.get<InspectionBatch[]>('/batches/', { params });
    return res.data;
  },

  getBatchDetail: async (batchId: string): Promise<InspectionBatch> => {
    const res = await apiClient.get<InspectionBatch>(`/batches/${batchId}`);
    return res.data;
  },

  attachInspectionToBatch: async (batchId: string, inspectionId: string): Promise<InspectionBatch> => {
    const res = await apiClient.post<InspectionBatch>(`/batches/${batchId}/inspections/${inspectionId}`);
    return res.data;
  },

  downloadBatchExportBundle: async (batchId: string, filename: string): Promise<void> => {
    const res = await apiClient.get(`/batches/${batchId}/export-bundle`, {
      responseType: 'blob',
    });
    const blob = new Blob([res.data], { type: 'application/zip' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // --- Phase 2.2: Section 36 Notices & Compounding Calculator ---
  calculateCompounding: async (data: {
    offence_count: number;
    violation_rule_codes?: string[];
    is_repeat_within_three_years?: boolean;
  }): Promise<CompoundingCalculationResponse> => {
    const res = await apiClient.post<CompoundingCalculationResponse>('/enforcement/calculate-compounding', data);
    return res.data;
  },

  createEnforcementNotice: async (data: {
    inspection_id: string;
    notice_type?: string;
    offence_count?: number;
    officer_remarks?: string;
  }): Promise<EnforcementNotice> => {
    const res = await apiClient.post<EnforcementNotice>('/enforcement/notices', data);
    return res.data;
  },

  listEnforcementNotices: async (params?: { status?: string }): Promise<EnforcementNotice[]> => {
    const res = await apiClient.get<EnforcementNotice[]>('/enforcement/notices', { params });
    return res.data;
  },

  getEnforcementNotice: async (noticeId: string): Promise<EnforcementNotice> => {
    const res = await apiClient.get<EnforcementNotice>(`/enforcement/notices/${noticeId}`);
    return res.data;
  },

  updateEnforcementNotice: async (
    noticeId: string,
    data: {
      status?: string;
      compounding_amount?: number;
      challan_reference?: string;
      officer_remarks?: string;
    }
  ): Promise<EnforcementNotice> => {
    const res = await apiClient.patch<EnforcementNotice>(`/enforcement/notices/${noticeId}`, data);
    return res.data;
  },

  downloadChallanPdf: async (noticeId: string, filename: string): Promise<void> => {
    const res = await apiClient.get(`/enforcement/notices/${noticeId}/challan-pdf`, {
      responseType: 'blob',
    });
    const blob = new Blob([res.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // --- Phase 2.3: Gravimetric & MPE Verification ---
  createGravimetricTest: async (data: GravimetricTestCreate): Promise<GravimetricTestResponse> => {
    const res = await apiClient.post<GravimetricTestResponse>('/gravimetric/tests', data);
    return res.data;
  },

  getGravimetricTest: async (testId: string): Promise<GravimetricTestResponse> => {
    const res = await apiClient.get<GravimetricTestResponse>(`/gravimetric/tests/${testId}`);
    return res.data;
  },

  downloadGravimetricPdf: async (testId: string, filename: string): Promise<void> => {
    const res = await apiClient.get(`/gravimetric/tests/${testId}/pdf`, {
      responseType: 'blob',
    });
    const blob = new Blob([res.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // --- Phase 2.4: Statutory Exemptions & Special Packaging ---
  evaluateExemptionRules: async (data: ExemptionEvaluationRequest): Promise<ExemptionEvaluationResponse> => {
    const res = await apiClient.post<ExemptionEvaluationResponse>('/exemptions/evaluate', data);
    return res.data;
  },

  applyExemptionToInspection: async (inspectionId: string, data: ExemptionEvaluationRequest): Promise<ExemptionEvaluationResponse> => {
    const res = await apiClient.post<ExemptionEvaluationResponse>(`/exemptions/apply/${inspectionId}`, data);
    return res.data;
  },

  // --- Phase 2.5: Geofence Validation & Offline Sync ---
  validateGpsCoordinates: async (data: GeoValidationRequest): Promise<GeoValidationResponse> => {
    const res = await apiClient.post<GeoValidationResponse>('/provenance/geovalidate', data);
    return res.data;
  },

  syncOfflineInspections: async (data: OfflineSyncBatchRequest): Promise<OfflineSyncBatchResponse> => {
    const res = await apiClient.post<OfflineSyncBatchResponse>('/provenance/sync-offline', data);
    return res.data;
  },
};
