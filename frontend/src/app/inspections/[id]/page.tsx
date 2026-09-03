'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import {
  AuditLog,
  ComplianceCheck,
  Declaration,
  Evidence,
  Inspection,
  ReviewWorkspaceResponse,
  Violation,
} from '@/types';
import ImageBBoxViewer from '@/components/ImageBBoxViewer';
import DeclarationForm from '@/components/DeclarationForm';
import ComplianceVerdictCard from '@/components/ComplianceVerdictCard';
import MasterCatalogComparisonCard from '@/components/MasterCatalogComparisonCard';
import { PreFlightDiagnostics } from '@/components/PreFlightDiagnostics';
import { MeasurementAssistant } from '@/components/MeasurementAssistant';
import { DigitalListingCrossCheck } from '@/components/DigitalListingCrossCheck';
import { ReviewWorkspace } from '@/components/ReviewWorkspace';
import { AuditTimeline } from '@/components/AuditTimeline';
import {
  ArrowLeft,
  Building2,
  MapPin,
  Calendar,
  Layers,
  Sparkles,
  RefreshCw,
  AlertCircle,
  FileCheck2,
  CheckCircle2,
  ShieldCheck,
  Sliders,
  Scale,
} from 'lucide-react';

export default function InspectionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [workspaceData, setWorkspaceData] = useState<ReviewWorkspaceResponse | null>(null);
  const [evidenceItems, setEvidenceItems] = useState<Evidence[]>([]);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active view states
  const [selectedImageIndex, setSelectedImageIndex] = useState<number>(0);
  const [activeFieldName, setActiveFieldName] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'declarations' | 'compliance' | 'review' | 'tools'>('declarations');

  const loadInspectionData = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [inspData, wsData, evData, violData, auditData] = await Promise.all([
        api.getInspection(id),
        api.getReviewWorkspace(id).catch(() => null),
        api.getEvidence(id).catch(() => []),
        api.getViolations(id).catch(() => []),
        api.getAuditTrail(id).catch(() => []),
      ]);
      setInspection(inspData);
      setWorkspaceData(wsData);
      setEvidenceItems(evData);
      setViolations(violData);
      setAuditLogs(auditData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load inspection workspace.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push('/login');
      } else {
        loadInspectionData();
      }
    }
  }, [authLoading, user, loadInspectionData, router]);

  const handleSaveDeclaration = async (updatedData: Partial<Declaration>) => {
    if (!id) return;
    try {
      const res = await api.updateDeclaration(id, updatedData);
      setInspection((prev) => (prev ? { ...prev, declaration: res } : null));
      await api.evaluateInspection(id);
      await loadInspectionData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to update declaration.');
    }
  };

  if (loading && !inspection) {
    return (
      <div className="py-24 text-center text-xs text-slate-500 flex flex-col items-center justify-center">
        <RefreshCw className="h-8 w-8 text-sky-600 animate-spin mb-3" />
        <span className="font-semibold text-slate-700">Loading MetrologyMitra workspace...</span>
      </div>
    );
  }

  if (error || !inspection) {
    return (
      <div className="max-w-xl mx-auto p-6 bg-white rounded-2xl shadow border border-slate-200 text-center space-y-4">
        <AlertCircle className="h-10 w-10 text-rose-600 mx-auto" />
        <h2 className="text-lg font-bold text-slate-900">Unable to load inspection</h2>
        <p className="text-xs text-slate-500">{error || 'Inspection record not found.'}</p>
        <a
          href="/inspections"
          className="inline-flex items-center gap-1.5 bg-slate-900 text-white text-xs font-bold px-4 py-2 rounded-lg"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Inspections
        </a>
      </div>
    );
  }

  const images = inspection.images || [];
  const currentImage = images[selectedImageIndex] || null;

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Case Status Bar */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4 text-white">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <a
              href="/inspections"
              className="text-xs font-semibold text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Inspections
            </a>
            <span className="text-slate-600">•</span>
            <span className="text-xs font-mono font-bold text-cyan-400">ID: {inspection.id.slice(0, 18)}...</span>
            <span className="text-slate-600">•</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
              inspection.status === 'COMPLETED'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
            }`}>
              {inspection.status}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 pt-1">
            <div className="text-base font-bold text-white flex items-center gap-1.5">
              <Building2 className="h-4 w-4 text-cyan-400" />
              {inspection.store_name || 'Retail Establishment'}
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5 text-slate-500" />
              {inspection.district || 'District N/A'}, {inspection.state || 'DL'}
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5 text-slate-500" />
              {new Date(inspection.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
            </div>
          </div>
        </div>

        {/* Action / Refresh */}
        <div className="flex items-center gap-2">
          <button
            onClick={loadInspectionData}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Main 2-Column Split Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT PANE: Package Image & Pre-Flight Quality Gate (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {currentImage ? (
            <div className="space-y-4">
              {/* Image & Bounding Box Visualizer */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
                <ImageBBoxViewer
                  imageUrl={currentImage.image_url}
                  evidenceItems={evidenceItems.filter((e) => !e.image_id || e.image_id === currentImage.id)}
                  selectedFieldName={activeFieldName}
                  onSelectEvidence={(ev) => {
                    if (ev.description) {
                      setActiveFieldName(ev.description);
                    }
                  }}
                />

                {/* Multi-angle Thumbnails */}
                {images.length > 1 && (
                  <div className="flex gap-2 overflow-x-auto pt-3 mt-3 border-t border-slate-800">
                    {images.map((img, idx) => (
                      <button
                        key={img.id}
                        onClick={() => setSelectedImageIndex(idx)}
                        className={`relative rounded-lg overflow-hidden border-2 transition-all p-0.5 ${
                          selectedImageIndex === idx ? 'border-cyan-500 shadow' : 'border-transparent opacity-60 hover:opacity-100'
                        }`}
                      >
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={img.image_url.startsWith('http') ? img.image_url : `http://localhost:8000${img.image_url}`}
                          alt={`Angle ${idx + 1}`}
                          className="h-12 w-12 object-cover rounded"
                        />
                        <span className="absolute bottom-0 inset-x-0 bg-slate-950/80 text-[8px] text-white font-mono text-center truncate">
                          {img.image_type}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Pre-Flight Quality Gate & SHA-256 Fingerprint */}
              <PreFlightDiagnostics
                inspectionId={inspection.id}
                imageId={currentImage.id}
                initialDiagnostics={currentImage.quality_gate_result as any}
                sha256Hash={currentImage.sha256_hash}
                onRetakeRequested={() => setActiveTab('review')}
              />
            </div>
          ) : (
            <div className="p-12 bg-slate-900 rounded-2xl border border-dashed border-slate-800 text-center text-xs text-slate-500 shadow-xl">
              No package photograph attached to this inspection session.
            </div>
          )}
        </div>

        {/* RIGHT PANE: Workspace Tabs (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Tab Navigation */}
          <div className="flex border border-slate-800 bg-slate-900 rounded-xl p-1 shadow-xl">
            <button
              onClick={() => setActiveTab('declarations')}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
                activeTab === 'declarations'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <FileCheck2 className="h-3.5 w-3.5" />
              Declarations
            </button>

            <button
              onClick={() => setActiveTab('compliance')}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
                activeTab === 'compliance'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Sparkles className="h-3.5 w-3.5" />
              Rule Matrix
            </button>

            <button
              onClick={() => setActiveTab('review')}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
                activeTab === 'review'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              Adjudication
            </button>

            <button
              onClick={() => setActiveTab('tools')}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
                activeTab === 'tools'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Sliders className="h-3.5 w-3.5" />
              Field Tools
            </button>
          </div>

          {/* Active Tab Content */}
          {activeTab === 'declarations' && (
            <div className="space-y-4">
              <MasterCatalogComparisonCard
                barcodeData={inspection.declaration?.raw_extractions?.barcode_data}
              />
              <DeclarationForm
                declaration={inspection.declaration}
                onSave={handleSaveDeclaration}
                onSelectField={(fieldName) => setActiveFieldName(fieldName)}
                activeFieldName={activeFieldName}
              />
            </div>
          )}

          {activeTab === 'compliance' && (
            <div className="space-y-4">
              <MasterCatalogComparisonCard
                barcodeData={inspection.declaration?.raw_extractions?.barcode_data}
              />
              <ComplianceVerdictCard
                inspectionId={inspection.id}
                overallResult={inspection.overall_result}
                checks={inspection.compliance_checks || []}
                violations={violations}
                evidenceItems={evidenceItems}
                reports={inspection.reports || []}
                onRefresh={loadInspectionData}
              />
            </div>
          )}

          {activeTab === 'review' && workspaceData && (
            <ReviewWorkspace
              inspectionId={inspection.id}
              workspaceData={workspaceData}
              onReviewSubmitted={() => loadInspectionData()}
              onFinalized={() => loadInspectionData()}
            />
          )}

          {activeTab === 'tools' && (
            <div className="space-y-4">
              <MeasurementAssistant
                inspectionId={inspection.id}
                initialPdpArea={inspection.declaration?.pdp_area_sq_cm}
                onMeasurementSaved={() => loadInspectionData()}
              />
              <DigitalListingCrossCheck
                inspectionId={inspection.id}
                physicalDeclaration={inspection.declaration}
                onCrossCheckCompleted={() => loadInspectionData()}
              />
            </div>
          )}
        </div>
      </div>

      {/* Bottom Full-Width Section: Chronological Audit Trail */}
      <div className="mt-8">
        <AuditTimeline auditLogs={auditLogs} />
      </div>
    </div>
  );
}
