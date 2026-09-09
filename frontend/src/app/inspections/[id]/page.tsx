'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import {
  AuditLog,
  CaseIntelligenceResponse,
  ComplianceCheck,
  Declaration,
  Evidence,
  Inspection,
  ReviewWorkspaceResponse,
  Violation,
} from '@/types';

// Workstation Components
import DecisionSummaryBar from '@/components/DecisionSummaryBar';
import DecisionPipelineVisualizer from '@/components/DecisionPipelineVisualizer';
import EvidenceCoveragePanel from '@/components/EvidenceCoveragePanel';
import NextBestActionPanel from '@/components/NextBestActionPanel';
import PackageEvidenceWorkspace from '@/components/PackageEvidenceWorkspace';
import DeclarationReviewTable from '@/components/DeclarationReviewTable';
import WhyThisResultRuleTrace from '@/components/WhyThisResultRuleTrace';
import PhysicalVerificationSection from '@/components/PhysicalVerificationSection';
import InspectionReplayTimeline from '@/components/InspectionReplayTimeline';
import ReportExportSection from '@/components/ReportExportSection';
import EvidenceFusionCard from '@/components/EvidenceFusionCard';
import MasterCatalogComparisonCard from '@/components/MasterCatalogComparisonCard';
import { ReviewWorkspace } from '@/components/ReviewWorkspace';
import ExemptionPanel from '@/components/ExemptionPanel';
import CompanyLiabilityCard from '@/components/CompanyLiabilityCard';
import { MeasurementAssistant } from '@/components/MeasurementAssistant';
import { DigitalListingCrossCheck } from '@/components/DigitalListingCrossCheck';

import {
  Camera,
  FileCheck2,
  Scale,
  Layers,
  ShieldCheck,
  History,
  FileText,
  Sliders,
  ExternalLink,
  Boxes,
  Building2,
  AlertOctagon,
  Gavel,
  Briefcase,
  RefreshCw,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Shield,
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
  const [intelligence, setIntelligence] = useState<CaseIntelligenceResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isReevaluating, setIsReevaluating] = useState(false);

  // Active view states
  const [activeTab, setActiveTab] = useState<
    | 'evidence'
    | 'declarations'
    | 'rules'
    | 'fusion'
    | 'physical'
    | 'adjudication'
    | 'replay'
    | 'reports'
    | 'tools'
  >('rules');

  const [activeFieldName, setActiveFieldName] = useState<string | null>(null);

  const loadInspectionData = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [inspData, wsData, evData, violData, auditData, intelData] = await Promise.all([
        api.getInspection(id),
        api.getReviewWorkspace(id).catch(() => null),
        api.getEvidence(id).catch(() => []),
        api.getViolations(id).catch(() => []),
        api.getAuditTrail(id).catch(() => []),
        api.getCaseIntelligence(id).catch(() => null),
      ]);
      setInspection(inspData);
      setWorkspaceData(wsData);
      setEvidenceItems(evData);
      setViolations(violData);
      setAuditLogs(auditData);
      setIntelligence(intelData);
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

  const handleReevaluate = async () => {
    if (!id) return;
    setIsReevaluating(true);
    try {
      await api.evaluateInspection(id);
      await loadInspectionData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to re-evaluate legal rules.');
    } finally {
      setIsReevaluating(false);
    }
  };

  const checks = inspection?.compliance_checks || [];
  const passedChecksCount = checks.filter((c) => c.result === 'PASS').length;
  const failedChecksCount = checks.filter((c) => c.result === 'FAIL').length;
  const images = inspection?.images || [];
  const verdict = (inspection as any)?.statutory_verdict || inspection?.overall_result || 'PENDING';
  const hasBarcode = Boolean(inspection?.declaration?.raw_extractions?.barcode_data);
  const hasPhysical = Boolean(inspection?.declaration?.measurement_data);

  if (loading && !inspection) {
    return (
      <div className="py-24 text-center text-xs text-slate-500 flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="h-8 w-8 text-sky-600 animate-spin" />
        <span className="font-semibold text-slate-700">Loading Inspection Workstation...</span>
        <span className="text-[11px] text-slate-400">Assembling multi-modal evidentiary records</span>
      </div>
    );
  }

  if (error || !inspection) {
    return (
      <div className="max-w-xl mx-auto p-6 bg-white rounded-2xl shadow border border-slate-200 text-center space-y-4 my-12">
        <AlertCircle className="h-10 w-10 text-rose-600 mx-auto" />
        <h2 className="text-lg font-bold text-slate-900">Unable to load inspection</h2>
        <p className="text-xs text-slate-500">{error || 'Inspection record not found.'}</p>
        <a
          href="/inspections"
          className="inline-flex items-center gap-1.5 bg-sky-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition hover:bg-sky-800 shadow-xs"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Inspections
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Decision Summary Bar & Top Identity Header */}
      <DecisionSummaryBar
        inspection={inspection}
        checks={checks}
        violations={violations}
        onReevaluate={handleReevaluate}
        isReevaluating={isReevaluating}
        onJumpToSection={(sectionId) => {
          if (sectionId === 'reports') setActiveTab('reports');
          else if (sectionId === 'replay') setActiveTab('replay');
        }}
      />

      {/* 2. Visual Pipeline Flow Bar (Package → Evidence → Fusion → Rules → Decision) */}
      <DecisionPipelineVisualizer
        imagesCount={images.length}
        checksCount={checks.length}
        passedChecksCount={passedChecksCount}
        verdict={verdict}
        hasBarcode={hasBarcode}
        hasGravimetric={hasPhysical}
      />

      {/* 3. Dual Operational Panels: Evidence Coverage & Next Best Action */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Evidence Coverage Panel (7 cols) */}
        <div className="lg:col-span-7">
          <EvidenceCoveragePanel
            declaration={inspection.declaration}
            completeness={intelligence?.evidence_completeness}
            hasImages={images.length > 0}
            hasBarcode={hasBarcode}
            hasPhysicalVerification={hasPhysical}
          />
        </div>

        {/* Next Best Action Panel (5 cols) */}
        <div className="lg:col-span-5">
          <NextBestActionPanel
            recommendations={intelligence?.recommendations}
            images={images}
            declaration={inspection.declaration}
            onActionClick={(target) => {
              if (target === 'evidence') setActiveTab('evidence');
              else if (target === 'declarations') setActiveTab('declarations');
              else if (target === 'rules') setActiveTab('rules');
            }}
          />
        </div>
      </div>

      {/* 4. Sticky Workstation Sub-Navigation Bar (Translucent Light Styling) */}
      <div className="sticky top-16 z-20 bg-white/90 backdrop-blur-md border border-slate-200/90 rounded-2xl p-1.5 shadow-sm">
        <div className="flex items-center gap-1 overflow-x-auto text-xs font-semibold scrollbar-none">
          <button
            type="button"
            onClick={() => setActiveTab('rules')}
            className={`px-3 py-2 rounded-xl transition flex items-center gap-1.5 shrink-0 cursor-pointer ${
              activeTab === 'rules'
                ? 'bg-sky-50 text-sky-800 border border-sky-200/90 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
          >
            <Scale className="h-3.5 w-3.5" />
            <span>Why This Result?</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
              activeTab === 'rules' ? 'bg-sky-200/60 text-sky-900 font-bold' : 'bg-slate-100 text-slate-600 border border-slate-200'
            }`}>
              {passedChecksCount}/{checks.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('evidence')}
            className={`px-3 py-2 rounded-xl transition flex items-center gap-1.5 shrink-0 cursor-pointer ${
              activeTab === 'evidence'
                ? 'bg-sky-50 text-sky-800 border border-sky-200/90 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
          >
            <Camera className="h-3.5 w-3.5" />
            <span>Package Evidence</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
              activeTab === 'evidence' ? 'bg-sky-200/60 text-sky-900 font-bold' : 'bg-slate-100 text-slate-600 border border-slate-200'
            }`}>
              {images.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('declarations')}
            className={`px-3 py-2 rounded-xl transition flex items-center gap-1.5 shrink-0 cursor-pointer ${
              activeTab === 'declarations'
                ? 'bg-sky-50 text-sky-800 border border-sky-200/90 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
          >
            <FileCheck2 className="h-3.5 w-3.5" />
            <span>Declarations Review</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('fusion')}
            className={`px-3 py-2 rounded-xl transition flex items-center gap-1.5 shrink-0 cursor-pointer ${
              activeTab === 'fusion'
                ? 'bg-sky-50 text-sky-800 border border-sky-200/90 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>Evidence Fusion</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('physical')}
            className={`px-3 py-2 rounded-xl transition flex items-center gap-1.5 shrink-0 cursor-pointer ${
              activeTab === 'physical'
                ? 'bg-sky-50 text-sky-800 border border-sky-200/90 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
          >
            <Scale className="h-3.5 w-3.5" />
            <span>Physical Verification</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('adjudication')}
            className={`px-3 py-2 rounded-xl transition flex items-center gap-1.5 shrink-0 cursor-pointer ${
              activeTab === 'adjudication'
                ? 'bg-sky-50 text-sky-800 border border-sky-200/90 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Officer Adjudication</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('replay')}
            className={`px-3 py-2 rounded-xl transition flex items-center gap-1.5 shrink-0 cursor-pointer ${
              activeTab === 'replay'
                ? 'bg-sky-50 text-sky-800 border border-sky-200/90 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
          >
            <History className="h-3.5 w-3.5" />
            <span>Audit Replay</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
              activeTab === 'replay' ? 'bg-sky-200/60 text-sky-900 font-bold' : 'bg-slate-100 text-slate-600 border border-slate-200'
            }`}>
              {auditLogs.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('reports')}
            className={`px-3 py-2 rounded-xl transition flex items-center gap-1.5 shrink-0 cursor-pointer ${
              activeTab === 'reports'
                ? 'bg-sky-50 text-sky-800 border border-sky-200/90 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Reports &amp; Documents</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('tools')}
            className={`px-3 py-2 rounded-xl transition flex items-center gap-1.5 shrink-0 cursor-pointer ${
              activeTab === 'tools'
                ? 'bg-sky-50 text-sky-800 border border-sky-200/90 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
          >
            <Sliders className="h-3.5 w-3.5" />
            <span>Field Tools</span>
          </button>
        </div>
      </div>

      {/* 5. Main Active Workstation View */}
      <div className="space-y-6">
        {/* Tab 1: WHY THIS RESULT? (Rule Trace Matrix Centerpiece) */}
        {activeTab === 'rules' && (
          <div className="space-y-6">
            <WhyThisResultRuleTrace
              checks={checks}
              violations={violations}
              images={images}
              declaration={inspection.declaration}
              inspectionId={inspection.id}
              inspectionStatus={inspection.status}
              reviewedBy={inspection.inspector?.name}
              reviewedAt={inspection.reviewed_at}
              reviewNotes={inspection.review_notes}
              onDecisionSubmitted={() => loadInspectionData()}
              onOpenReport={() => setActiveTab('reports')}
            />
            <MasterCatalogComparisonCard
              barcodeData={inspection.declaration?.raw_extractions?.barcode_data}
            />
          </div>
        )}

        {/* Tab 2: Package Evidence Workspace */}
        {activeTab === 'evidence' && (
          <PackageEvidenceWorkspace
            images={images}
            evidenceItems={evidenceItems}
            activeFieldName={activeFieldName}
            onSelectEvidence={(ev) => {
              if (ev.description) setActiveFieldName(ev.description);
            }}
          />
        )}

        {/* Tab 3: Declarations Review Table */}
        {activeTab === 'declarations' && (
          <DeclarationReviewTable
            declaration={inspection.declaration}
            activeFieldName={activeFieldName}
            onSelectField={(f) => {
              setActiveFieldName(f);
              setActiveTab('evidence');
            }}
          />
        )}

        {/* Tab 4: Evidence Fusion */}
        {activeTab === 'fusion' && (
          <div className="space-y-6">
            <EvidenceFusionCard
              fusedEvidence={inspection.declaration?.raw_extractions?.fused_evidence}
            />
            <MasterCatalogComparisonCard
              barcodeData={inspection.declaration?.raw_extractions?.barcode_data}
            />
          </div>
        )}

        {/* Tab 5: Physical Verification */}
        {activeTab === 'physical' && (
          <PhysicalVerificationSection declaration={inspection.declaration} />
        )}

        {/* Tab 6: Officer Adjudication Workspace */}
        {activeTab === 'adjudication' && workspaceData && (
          <ReviewWorkspace
            inspectionId={inspection.id}
            workspaceData={workspaceData}
            onReviewSubmitted={() => loadInspectionData()}
            onFinalized={() => loadInspectionData()}
          />
        )}

        {/* Tab 7: Inspection Replay & Chronological Audit Timeline */}
        {activeTab === 'replay' && (
          <InspectionReplayTimeline auditLogs={auditLogs} />
        )}

        {/* Tab 8: Official Reports & Documents */}
        {activeTab === 'reports' && (
          <ReportExportSection
            inspectionId={inspection.id}
            verdict={verdict}
            status={inspection.status}
            reviewedBy={inspection.inspector?.name}
            reviewedAt={inspection.reviewed_at}
            reviewNotes={inspection.review_notes}
            reports={inspection.reports || []}
            onReportGenerated={() => loadInspectionData()}
            onDecisionSubmitted={() => loadInspectionData()}
          />
        )}

        {/* Tab 9: Field Tools (Exemptions, Measurements, Liability) */}
        {activeTab === 'tools' && (
          <div className="space-y-6">
            <ExemptionPanel
              inspectionId={inspection.id}
              initialPackageType={inspection.declaration?.package_type || 'STANDARD'}
              onExemptionApplied={() => loadInspectionData()}
            />
            <CompanyLiabilityCard
              initialCompanyName={inspection.declaration?.manufacturer_name || undefined}
            />
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

      {/* 6. Contextual Navigation to Statutory Modules */}
      <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-6 text-slate-900 shadow-sm space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
          <div className="flex items-center gap-2">
            <ExternalLink className="h-4 w-4 text-sky-600" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Related Statutory Workflow Modules (LMPC 2011)
            </h4>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">Cross-Module Integration</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5 text-xs">
          <a
            href="/gravimetric"
            className="p-3 rounded-2xl bg-slate-50/80 border border-slate-200/80 hover:border-sky-500/50 hover:bg-sky-50/50 transition flex flex-col items-center text-center gap-1.5 group shadow-2xs"
          >
            <Scale className="h-4 w-4 text-sky-600 group-hover:scale-110 transition-transform" />
            <span className="font-bold text-slate-800 group-hover:text-sky-900">Gravimetric MPE</span>
            <span className="text-[9px] text-slate-400">Sixth Sched</span>
          </a>

          <a
            href="/batches"
            className="p-3 rounded-2xl bg-slate-50/80 border border-slate-200/80 hover:border-indigo-500/50 hover:bg-indigo-50/50 transition flex flex-col items-center text-center gap-1.5 group shadow-2xs"
          >
            <Boxes className="h-4 w-4 text-indigo-600 group-hover:scale-110 transition-transform" />
            <span className="font-bold text-slate-800 group-hover:text-indigo-900">Batch Sampling</span>
            <span className="text-[9px] text-slate-400">Rule 19</span>
          </a>

          <a
            href={`/registrations${inspection.declaration?.manufacturer_name ? `?q=${encodeURIComponent(inspection.declaration.manufacturer_name)}` : ''}`}
            className="p-3 rounded-2xl bg-slate-50/80 border border-slate-200/80 hover:border-teal-500/50 hover:bg-teal-50/50 transition flex flex-col items-center text-center gap-1.5 group shadow-2xs"
          >
            <Building2 className="h-4 w-4 text-teal-600 group-hover:scale-110 transition-transform" />
            <span className="font-bold text-slate-800 group-hover:text-teal-900">Rule 27 Registry</span>
            <span className="text-[9px] text-slate-400">Packer Directory</span>
          </a>

          <a
            href="/seizures"
            className="p-3 rounded-2xl bg-slate-50/80 border border-slate-200/80 hover:border-amber-500/50 hover:bg-amber-50/50 transition flex flex-col items-center text-center gap-1.5 group shadow-2xs"
          >
            <AlertOctagon className="h-4 w-4 text-amber-600 group-hover:scale-110 transition-transform" />
            <span className="font-bold text-slate-800 group-hover:text-amber-900">Sec 15 Seizures</span>
            <span className="text-[9px] text-slate-400">Panchnama</span>
          </a>

          <a
            href="/enforcement"
            className="p-3 rounded-2xl bg-slate-50/80 border border-slate-200/80 hover:border-rose-500/50 hover:bg-rose-50/50 transition flex flex-col items-center text-center gap-1.5 group shadow-2xs"
          >
            <Gavel className="h-4 w-4 text-rose-600 group-hover:scale-110 transition-transform" />
            <span className="font-bold text-slate-800 group-hover:text-rose-900">Sec 48 Penalty</span>
            <span className="text-[9px] text-slate-400">Compounding</span>
          </a>

          <a
            href="/dossiers"
            className="p-3 rounded-2xl bg-slate-50/80 border border-slate-200/80 hover:border-purple-500/50 hover:bg-purple-50/50 transition flex flex-col items-center text-center gap-1.5 group shadow-2xs"
          >
            <Briefcase className="h-4 w-4 text-purple-600 group-hover:scale-110 transition-transform" />
            <span className="font-bold text-slate-800 group-hover:text-purple-900">Case Dossier</span>
            <span className="text-[9px] text-slate-400">Act 2009</span>
          </a>
        </div>
      </div>

      {/* 7. Persistent Legal Safety Microcopy */}
      <div className="bg-slate-50/90 text-slate-600 p-4 rounded-2xl border border-slate-200/90 text-xs flex items-start gap-3 shadow-2xs">
        <Shield className="h-5 w-5 text-sky-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-slate-800">
            Official Statutory Governance Notice
          </div>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            AI-assisted perception produces evidence and confidence signals only. Statutory classification is produced exclusively by the configured deterministic Legal Metrology (Packaged Commodities) Rules, 2011 engine. Authorized officer review remains an essential part of the inspection workflow. Finalized records are permanently locked against mutation under government audit trail integrity standards.
          </p>
        </div>
      </div>
    </div>
  );
}

