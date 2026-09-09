'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import {
  DossierPriority,
  DossierStatus,
  DossierSynthesisResponse,
  Inspection,
  InvestigationDossier,
  ObservedFindingSummary,
} from '@/types';
import {
  Briefcase,
  ArrowLeft,
  Shield,
  ShieldAlert,
  Building2,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  AlertOctagon,
  Scale,
  Users,
  PlusCircle,
  Trash2,
  ExternalLink,
  RefreshCw,
  Info,
  MapPin,
  Calendar,
  Layers,
  ChevronRight,
  Filter,
  Download,
} from 'lucide-react';

type ActiveTab = 'overview' | 'inspections' | 'findings' | 'seizures' | 'corporate' | 'timeline';

export default function DossierWorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { user, isSupervisor, isAdmin } = useAuth();

  const [dossier, setDossier] = useState<InvestigationDossier | null>(null);
  const [synthesis, setSynthesis] = useState<DossierSynthesisResponse | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');
  const [loading, setLoading] = useState<boolean>(true);
  const [updatingStatus, setUpdatingStatus] = useState<boolean>(false);
  const [downloadingPdf, setDownloadingPdf] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Link Inspection Modal state
  const [showLinkModal, setShowLinkModal] = useState<boolean>(false);
  const [availableInspections, setAvailableInspections] = useState<Inspection[]>([]);
  const [loadingInspections, setLoadingInspections] = useState<boolean>(false);
  const [selectedInspectionId, setSelectedInspectionId] = useState<string>('');
  const [relevanceNotes, setRelevanceNotes] = useState<string>('');
  const [inspectionSearch, setInspectionSearch] = useState<string>('');
  const [linking, setLinking] = useState<boolean>(false);

  // Unlink state
  const [unlinkingId, setUnlinkingId] = useState<string | null>(null);

  const fetchDossierData = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const [dossierData, synthData] = await Promise.all([
        api.getDossier(id),
        api.getDossierSynthesis(id),
      ]);
      setDossier(dossierData);
      setSynthesis(synthData);
    } catch (err: any) {
      console.error('Failed to load dossier data', err);
      setError(err?.response?.data?.detail || 'Failed to load investigation dossier.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDossierData();
  }, [id]);

  const handleStatusChange = async (newStatus: DossierStatus) => {
    if (!dossier || dossier.status === newStatus) return;
    try {
      setUpdatingStatus(true);
      const updated = await api.updateDossier(dossier.id, { status: newStatus });
      setDossier(updated);
      const synthData = await api.getDossierSynthesis(dossier.id);
      setSynthesis(synthData);
    } catch (err: any) {
      console.error('Failed to update status', err);
      alert(err?.response?.data?.detail || 'Failed to update dossier status.');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!dossier) return;
    try {
      setDownloadingPdf(true);
      await api.downloadDossierPdf(dossier.id, `Dossier_${dossier.dossier_number}_Report.pdf`);
    } catch (err: any) {
      console.error('Failed to download PDF report', err);
      alert(err?.response?.data?.detail || 'Failed to download dossier PDF report.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleOpenLinkModal = async () => {
    setShowLinkModal(true);
    setLoadingInspections(true);
    try {
      const allInspections = await api.listInspections({ limit: 50 });
      // Exclude already linked inspections
      const linkedIds = new Set(dossier?.inspections?.map((di) => di.inspection_id) || []);
      const unlinked = allInspections.filter((insp) => !linkedIds.has(insp.id));
      setAvailableInspections(unlinked);
      if (unlinked.length > 0) {
        setSelectedInspectionId(unlinked[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch unlinked inspections', err);
    } finally {
      setLoadingInspections(false);
    }
  };

  const handleLinkInspection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dossier || !selectedInspectionId) return;
    try {
      setLinking(true);
      await api.linkDossierInspection(dossier.id, {
        inspection_id: selectedInspectionId,
        relevance_notes: relevanceNotes.trim() || undefined,
      });
      setShowLinkModal(false);
      setSelectedInspectionId('');
      setRelevanceNotes('');
      await fetchDossierData();
    } catch (err: any) {
      console.error('Failed to link inspection', err);
      alert(err?.response?.data?.detail || 'Failed to link inspection to dossier.');
    } finally {
      setLinking(false);
    }
  };

  const handleUnlinkInspection = async (inspectionId: string) => {
    if (!dossier) return;
    if (
      !confirm(
        'Are you sure you want to unlink this inspection from the dossier? The underlying inspection, its evidence, and statutory legal verdict will remain completely intact.'
      )
    ) {
      return;
    }

    try {
      setUnlinkingId(inspectionId);
      await api.unlinkDossierInspection(dossier.id, inspectionId);
      await fetchDossierData();
    } catch (err: any) {
      console.error('Failed to unlink inspection', err);
      alert(err?.response?.data?.detail || 'Failed to unlink inspection.');
    } finally {
      setUnlinkingId(null);
    }
  };

  // Status badge styling helper
  const getStatusBadge = (status: DossierStatus) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-sky-100 text-sky-800 border-sky-300';
      case 'EVALUATION':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'NOTICE_REVIEW':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'COMPOUNDING_REVIEW':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'CLOSED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  // Legal Result badge styling helper
  const getResultBadge = (result?: string) => {
    switch (result) {
      case 'COMPLIANT':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'NON_COMPLIANT':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'NEEDS_REVIEW':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-300';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 text-brand-700 animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-600">Loading investigation workspace...</p>
        </div>
      </div>
    );
  }

  if (error || !dossier) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-xl border border-red-200 max-w-md w-full text-center shadow-xs">
          <AlertTriangle className="h-10 w-10 text-red-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-900">Unable to Load Dossier</h2>
          <p className="text-sm text-slate-600 mt-2">{error || 'Dossier not found.'}</p>
          <Link
            href="/dossiers"
            className="mt-5 inline-flex items-center gap-1.5 px-4 py-2 bg-brand-800 hover:bg-brand-900 text-white text-xs font-semibold rounded-lg"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Dossiers
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 pb-16">
      {/* Top Navigation Bar */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-3">
            <Link href="/dossiers" className="hover:text-brand-800 flex items-center gap-1">
              <ArrowLeft className="h-3.5 w-3.5" />
              Investigation Dossiers
            </Link>
            <ChevronRight className="h-3 w-3 text-slate-400" />
            <span className="font-mono font-semibold text-slate-700">{dossier.dossier_number}</span>
          </div>

          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <span className="font-mono text-sm font-bold px-2.5 py-1 rounded bg-slate-100 text-slate-800 border border-slate-300">
                  {dossier.dossier_number}
                </span>

                <h1 className="text-2xl font-bold text-slate-900">{dossier.title}</h1>

                <span
                  className={`text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded ${
                    dossier.priority === 'URGENT'
                      ? 'bg-red-600 text-white'
                      : dossier.priority === 'HIGH'
                      ? 'bg-orange-500 text-white'
                      : 'bg-blue-600 text-white'
                  }`}
                >
                  {dossier.priority}
                </span>
              </div>

              {/* Target Entity & Metadata */}
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 mt-2">
                <div className="flex items-center gap-1.5">
                  <Building2 className="h-3.5 w-3.5 text-slate-400" />
                  <span className="font-semibold text-slate-800">
                    {dossier.target_entity_name || 'No designated corporate entity'}
                  </span>
                </div>

                <div className="flex items-center gap-1.5">
                  <Users className="h-3.5 w-3.5 text-slate-400" />
                  <span>Lead Supervisor: {dossier.lead_supervisor?.name || 'Assigned Supervisor'}</span>
                </div>

                <div className="flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5 text-slate-400" />
                  <span>Created: {new Date(dossier.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>

            {/* Status Selector for Supervisors */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-600">Workflow Status:</span>
                {isSupervisor || isAdmin ? (
                  <select
                    value={dossier.status}
                    disabled={updatingStatus}
                    onChange={(e) => handleStatusChange(e.target.value as DossierStatus)}
                    className={`text-xs font-bold py-1.5 px-3 rounded-md border focus:ring-2 focus:ring-brand-500 ${getStatusBadge(
                      dossier.status
                    )} cursor-pointer`}
                  >
                    <option value="ACTIVE">ACTIVE</option>
                    <option value="EVALUATION">EVALUATION</option>
                    <option value="NOTICE_REVIEW">NOTICE_REVIEW</option>
                    <option value="COMPOUNDING_REVIEW">COMPOUNDING_REVIEW</option>
                    <option value="CLOSED">CLOSED</option>
                  </select>
                ) : (
                  <span
                    className={`text-xs font-bold py-1.5 px-3 rounded-md border ${getStatusBadge(
                      dossier.status
                    )}`}
                  >
                    {dossier.status.replace('_', ' ')}
                  </span>
                )}
              </div>

                <button
                  onClick={handleDownloadPdf}
                  disabled={downloadingPdf}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-lg shadow-xs cursor-pointer disabled:opacity-50 transition-colors"
                  title="Download Consolidated Inspection & Evidence Report PDF"
                >
                  <Download className={`h-3.5 w-3.5 ${downloadingPdf ? 'animate-bounce' : ''}`} />
                  {downloadingPdf ? 'Generating PDF...' : 'Download Report (PDF)'}
                </button>

              {(isSupervisor || isAdmin) && (
                <button
                  onClick={handleOpenLinkModal}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold rounded-lg shadow-xs cursor-pointer"
                >
                  <PlusCircle className="h-3.5 w-3.5" />
                  Link Inspection
                </button>
              )}
            </div>
          </div>

          {/* Legal Boundary Advisory Banner */}
          <div className="mt-4 p-3 rounded-lg bg-amber-50 border border-amber-200 flex items-start gap-2.5">
            <ShieldAlert className="h-4 w-4 text-amber-700 flex-shrink-0 mt-0.5" />
            <div className="text-[11px] text-amber-900 leading-relaxed">
              <strong className="font-semibold">OPERATIONAL SYNTHESIS DISCLAIMER: </strong>
              {synthesis?.advisory_disclaimer ||
                'This dossier is an operational supervisory case-management view aggregating factual findings from multiple inspections. The individual legal results (COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW) of linked inspections remain authoritative and are not altered by inclusion in this dossier.'}
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b border-slate-200 mt-6 gap-2 overflow-x-auto">
            <button
              onClick={() => setActiveTab('overview')}
              className={`pb-3 px-3 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === 'overview'
                  ? 'border-brand-800 text-brand-800'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
              Overview & Synthesis
            </button>

            <button
              onClick={() => setActiveTab('inspections')}
              className={`pb-3 px-3 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === 'inspections'
                  ? 'border-brand-800 text-brand-800'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              Linked Inspections ({dossier.inspections?.length || 0})
            </button>

            <button
              onClick={() => setActiveTab('findings')}
              className={`pb-3 px-3 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === 'findings'
                  ? 'border-brand-800 text-brand-800'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Scale className="h-3.5 w-3.5" />
              Observed Finding Patterns ({synthesis?.observed_findings?.length || 0})
            </button>

            <button
              onClick={() => setActiveTab('seizures')}
              className={`pb-3 px-3 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === 'seizures'
                  ? 'border-brand-800 text-brand-800'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <AlertOctagon className="h-3.5 w-3.5" />
              Recorded Seizures ({synthesis?.recorded_seizure_summary?.total_seizure_records || 0})
            </button>

            <button
              onClick={() => setActiveTab('corporate')}
              className={`pb-3 px-3 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === 'corporate'
                  ? 'border-brand-800 text-brand-800'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Building2 className="h-3.5 w-3.5" />
              Corporate Governance (Sec 49)
            </button>

            <button
              onClick={() => setActiveTab('timeline')}
              className={`pb-3 px-3 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === 'timeline'
                  ? 'border-brand-800 text-brand-800'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Clock className="h-3.5 w-3.5" />
              Timeline & Audit Log
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        {/* TAB 1: OVERVIEW & SYNTHESIS */}
        {activeTab === 'overview' && synthesis && (
          <div className="space-y-6">
            {/* Factual Aggregate Cards */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Factual Inspection Verdict Breakdown
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
                  <div className="text-xs text-slate-500 font-medium">Total Linked</div>
                  <div className="text-2xl font-bold text-slate-900 mt-1">
                    {synthesis.summary_counts.total_inspections}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">Inspection records</div>
                </div>

                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 shadow-xs">
                  <div className="text-xs text-emerald-800 font-medium flex items-center gap-1">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                    Compliant
                  </div>
                  <div className="text-2xl font-bold text-emerald-900 mt-1">
                    {synthesis.summary_counts.compliant_count}
                  </div>
                  <div className="text-[10px] text-emerald-700 mt-1">Statutory pass</div>
                </div>

                <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 shadow-xs">
                  <div className="text-xs text-rose-800 font-medium flex items-center gap-1">
                    <XCircle className="h-3.5 w-3.5 text-rose-600" />
                    Non-Compliant
                  </div>
                  <div className="text-2xl font-bold text-rose-900 mt-1">
                    {synthesis.summary_counts.non_compliant_count}
                  </div>
                  <div className="text-[10px] text-rose-700 mt-1">Statutory infractions</div>
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 shadow-xs">
                  <div className="text-xs text-amber-800 font-medium flex items-center gap-1">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
                    Needs Review
                  </div>
                  <div className="text-2xl font-bold text-amber-900 mt-1">
                    {synthesis.summary_counts.needs_review_count}
                  </div>
                  <div className="text-[10px] text-amber-700 mt-1">Awaiting review</div>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 shadow-xs">
                  <div className="text-xs text-slate-600 font-medium">Pending</div>
                  <div className="text-2xl font-bold text-slate-800 mt-1">
                    {synthesis.summary_counts.pending_count}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">In progress</div>
                </div>

                <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
                  <div className="text-xs text-slate-600 font-medium">Total Violations</div>
                  <div className="text-2xl font-bold text-slate-900 mt-1">
                    {synthesis.summary_counts.total_violations}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">
                    {synthesis.summary_counts.critical_violations} Crit • {synthesis.summary_counts.high_violations} High
                  </div>
                </div>
              </div>
            </div>

            {/* Territorial & Scope Footprint */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
                <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-brand-700" />
                  Territorial Scope
                </h3>
                <div className="space-y-3">
                  <div>
                    <div className="text-xs font-semibold text-slate-600 mb-1.5">Districts Covered:</div>
                    <div className="flex flex-wrap gap-1.5">
                      {synthesis.districts_covered.length > 0 ? (
                        synthesis.districts_covered.map((district, idx) => (
                          <span
                            key={idx}
                            className="text-xs bg-slate-100 text-slate-800 px-2.5 py-1 rounded-md border border-slate-200"
                          >
                            {district}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-400">No districts recorded</span>
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="text-xs font-semibold text-slate-600 mb-1.5">States Covered:</div>
                    <div className="flex flex-wrap gap-1.5">
                      {synthesis.states_covered.length > 0 ? (
                        synthesis.states_covered.map((state, idx) => (
                          <span
                            key={idx}
                            className="text-xs bg-brand-50 text-brand-900 px-2.5 py-1 rounded-md border border-brand-200 font-medium"
                          >
                            {state}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-400">No states recorded</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
                <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                  <Layers className="h-4 w-4 text-brand-700" />
                  Operational Footprint
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="text-xs text-slate-500 font-medium">Premises Inspected</div>
                    <div className="text-xl font-bold text-slate-900 mt-1">
                      {synthesis.premises_count}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">Distinct physical stores</div>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="text-xs text-slate-500 font-medium">Batches Sampled</div>
                    <div className="text-xl font-bold text-slate-900 mt-1">
                      {synthesis.batches_count}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">Commodity lots</div>
                  </div>

                  <div className="col-span-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-slate-600 font-medium">
                        Evidence Completeness Index (Avg)
                      </div>
                      <div className="text-sm font-bold text-brand-800">
                        {synthesis.evidence_completeness_avg !== null
                          ? `${Math.round((synthesis.evidence_completeness_avg || 0) * 100)}%`
                          : 'N/A'}
                      </div>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-1">
                      Decision-support index across linked inspection records. Does not alter statutory verdicts.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: LINKED INSPECTIONS */}
        {activeTab === 'inspections' && (
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
            <div className="p-4 bg-slate-50/70 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Linked Inspection Records</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Inspections linked to this surveillance dossier. Unlinking removes grouping only without altering the inspection.
                </p>
              </div>

              {(isSupervisor || isAdmin) && (
                <button
                  onClick={handleOpenLinkModal}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-800 hover:bg-brand-900 text-white text-xs font-semibold rounded-lg shadow-xs cursor-pointer"
                >
                  <PlusCircle className="h-3.5 w-3.5" />
                  Add Inspection
                </button>
              )}
            </div>

            {dossier.inspections?.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="h-10 w-10 text-slate-300 mx-auto mb-2" />
                <h4 className="text-sm font-semibold text-slate-700">No inspections linked yet</h4>
                <p className="text-xs text-slate-500 mt-1">
                  Click &apos;Add Inspection&apos; to link individual market inspections to this dossier.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                  <thead className="bg-slate-50 font-semibold text-slate-700 uppercase tracking-wider">
                    <tr>
                      <th className="px-4 py-3">Store / Premises</th>
                      <th className="px-4 py-3">District & State</th>
                      <th className="px-4 py-3">Inspector</th>
                      <th className="px-4 py-3">Legal Result</th>
                      <th className="px-4 py-3">Relevance Notes</th>
                      <th className="px-4 py-3">Linked Date</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-600">
                    {dossier.inspections.map((di) => {
                      const insp = di.inspection;
                      return (
                        <tr key={di.id} className="hover:bg-slate-50/80">
                          <td className="px-4 py-3">
                            <div className="font-semibold text-slate-900">
                              {insp?.store_name || 'Premises / Store'}
                            </div>
                            <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                              {di.inspection_id.slice(0, 8)}...
                            </div>
                          </td>

                          <td className="px-4 py-3">
                            <div>{insp?.district || '—'}</div>
                            <div className="text-[11px] text-slate-400">{insp?.state || '—'}</div>
                          </td>

                          <td className="px-4 py-3">
                            <div>{insp?.inspector?.name || di.added_by?.name || 'Officer'}</div>
                          </td>

                          <td className="px-4 py-3">
                            <span
                              className={`text-[11px] font-bold px-2 py-0.5 rounded border ${getResultBadge(
                                insp?.overall_result
                              )}`}
                            >
                              {insp?.overall_result || 'PENDING'}
                            </span>
                          </td>

                          <td className="px-4 py-3 max-w-xs">
                            <span className="text-slate-600 line-clamp-2">
                              {di.relevance_notes || '—'}
                            </span>
                          </td>

                          <td className="px-4 py-3 text-slate-500">
                            {new Date(di.added_at).toLocaleDateString()}
                          </td>

                          <td className="px-4 py-3 text-right whitespace-nowrap">
                            <div className="inline-flex items-center gap-2">
                              <Link
                                href={`/inspections/${di.inspection_id}`}
                                className="inline-flex items-center gap-1 text-xs font-semibold text-brand-700 hover:text-brand-900"
                                title="View Inspection Record"
                              >
                                View
                                <ExternalLink className="h-3 w-3" />
                              </Link>

                              {(isSupervisor || isAdmin) && (
                                <button
                                  onClick={() => handleUnlinkInspection(di.inspection_id)}
                                  disabled={unlinkingId === di.inspection_id}
                                  className="text-xs font-semibold text-red-600 hover:text-red-800 disabled:opacity-50 cursor-pointer"
                                  title="Unlink from Dossier (keeps inspection intact)"
                                >
                                  {unlinkingId === di.inspection_id ? 'Unlinking...' : 'Unlink'}
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: OBSERVED FINDING PATTERNS */}
        {activeTab === 'findings' && synthesis && (
          <div className="space-y-4">
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3">
              <Info className="h-5 w-5 text-amber-700 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-amber-900 leading-relaxed">
                <strong className="font-semibold">STATUTORY OBSERVATION NOTICE: </strong>
                Observed finding patterns group existing inspection findings across the linked inspection records for supervisory review and market surveillance coordination. They <strong>do not constitute</strong> new statutory offences or collective guilt. Each finding originates from an individual statutory inspection.
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
              <div className="p-4 bg-slate-50/70 border-b border-slate-200">
                <h3 className="text-sm font-bold text-slate-900">Observed Finding Frequency Across Linked Cases</h3>
              </div>

              {synthesis.observed_findings.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle2 className="h-10 w-10 text-emerald-400 mx-auto mb-2" />
                  <h4 className="text-sm font-semibold text-slate-700">No observed finding patterns</h4>
                  <p className="text-xs text-slate-500 mt-1">
                    No violations or irregularities have been recorded across the linked inspection records.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {synthesis.observed_findings.map((finding, idx) => (
                    <div key={idx} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/50">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-brand-50 text-brand-800 border border-brand-200">
                            {finding.rule_code}
                          </span>
                          <h4 className="text-sm font-bold text-slate-900">{finding.rule_name}</h4>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">
                          Observation label: <span className="font-medium text-slate-700">{finding.observation_label}</span>
                        </p>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div className="text-xs font-bold text-slate-800">
                            {finding.affected_inspection_count} inspection{finding.affected_inspection_count > 1 ? 's' : ''} affected
                          </div>
                          <div className="flex items-center gap-1 mt-1 justify-end">
                            {finding.severity_levels.map((sev, sIdx) => (
                              <span
                                key={sIdx}
                                className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                                  sev === 'CRITICAL'
                                    ? 'bg-red-100 text-red-800'
                                    : sev === 'HIGH'
                                    ? 'bg-orange-100 text-orange-800'
                                    : 'bg-amber-100 text-amber-800'
                                }`}
                              >
                                {sev}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: RECORDED SEIZURES */}
        {activeTab === 'seizures' && synthesis && (
          <div className="space-y-5">
            <div className="p-4 bg-sky-50 border border-sky-200 rounded-xl flex items-start gap-3">
              <Shield className="h-5 w-5 text-sky-700 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-sky-900 leading-relaxed">
                <strong className="font-semibold">SECTION 15 SEIZURE SUMMARY: </strong>
                The metrics below aggregate strictly from statutory Panchnama search and seizure records lawfully executed under Section 15 of the Legal Metrology Act, 2009 during the linked inspections.
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
                <div className="text-xs text-slate-500 font-medium">Total Seizure Records</div>
                <div className="text-2xl font-bold text-slate-900 mt-1">
                  {synthesis.recorded_seizure_summary.total_seizure_records}
                </div>
                <div className="text-[10px] text-slate-400 mt-1">Lawfully executed Panchnamas</div>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
                <div className="text-xs text-slate-500 font-medium">Total Seized Quantity</div>
                <div className="text-2xl font-bold text-slate-900 mt-1">
                  {synthesis.recorded_seizure_summary.total_seized_quantity.toLocaleString()} units
                </div>
                <div className="text-[10px] text-slate-400 mt-1">Packages held in safe custody</div>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
                <div className="text-xs text-slate-500 font-medium">Itemized Inventory Rows</div>
                <div className="text-2xl font-bold text-slate-900 mt-1">
                  {synthesis.recorded_seizure_summary.seizure_items_count}
                </div>
                <div className="text-[10px] text-slate-400 mt-1">Distinct product lots seized</div>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex items-center justify-between">
              <div>
                <h4 className="text-sm font-bold text-slate-900">Dedicated Seizures Registry</h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  View the full Section 15 Panchnama forms, witness records, and formal custody chains.
                </p>
              </div>
              <Link
                href="/seizures"
                className="px-4 py-2 bg-brand-800 hover:bg-brand-900 text-white text-xs font-semibold rounded-lg inline-flex items-center gap-1.5"
              >
                Open Seizures Workspace
                <ExternalLink className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        )}

        {/* TAB 5: CORPORATE GOVERNANCE & DIRECTORS (SEC 49) */}
        {activeTab === 'corporate' && synthesis && (
          <div className="space-y-6">
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3">
              <ShieldAlert className="h-5 w-5 text-amber-700 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-amber-900 leading-relaxed">
                <strong className="font-semibold">SECTION 49 STATUTORY NOTICE: </strong>
                Nominated director information is presented for factual reference under Section 49(2) of the Legal Metrology Act, 2009. A Form I nomination designates operational responsibility for packaged commodities. <strong>It does NOT establish automatic personal criminal liability</strong>; prosecutorial sanction requires independent statutory determination by the competent authority.
              </div>
            </div>

            {dossier.company ? (
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
                <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-brand-700" />
                  Registered Corporate Entity
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                  <div>
                    <span className="text-slate-400">Company Name:</span>
                    <div className="font-bold text-slate-900 mt-0.5">{dossier.company.company_name}</div>
                  </div>
                  <div>
                    <span className="text-slate-400">CIN:</span>
                    <div className="font-mono font-bold text-slate-800 mt-0.5">{dossier.company.cin}</div>
                  </div>
                  <div>
                    <span className="text-slate-400">Registered State:</span>
                    <div className="font-medium text-slate-800 mt-0.5">{dossier.company.state}</div>
                  </div>
                  <div>
                    <span className="text-slate-400">Registered Office:</span>
                    <div className="text-slate-600 mt-0.5 line-clamp-2">{dossier.company.registered_office}</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white border border-slate-200 rounded-xl p-6 text-center shadow-xs">
                <Building2 className="h-10 w-10 text-slate-300 mx-auto mb-2" />
                <h4 className="text-sm font-semibold text-slate-700">No Corporate Entity Linked</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                  {dossier.target_entity_name
                    ? `Entity name descriptor is '${dossier.target_entity_name}'. To associate statutory Form I records, link a registered company.`
                    : 'No target entity designated for this dossier.'}
                </p>
              </div>
            )}

            {/* Nominated Directors Review */}
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
              <div className="p-4 bg-slate-50/70 border-b border-slate-200">
                <h3 className="text-sm font-bold text-slate-900">
                  Nominated Directors under Section 49(2)
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Directors nominated via Form I resolution to the Controller of Legal Metrology.
                </p>
              </div>

              {synthesis.nominated_directors_review.length === 0 ? (
                <div className="text-center py-10">
                  <Users className="h-8 w-8 text-slate-300 mx-auto mb-2" />
                  <h4 className="text-xs font-semibold text-slate-700">No Nominated Directors Recorded</h4>
                  <p className="text-[11px] text-slate-500 mt-1">
                    No Form I director nominations have been recorded for the associated corporate entity.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                    <thead className="bg-slate-50 font-semibold text-slate-700 uppercase tracking-wider">
                      <tr>
                        <th className="px-4 py-3">Director Name</th>
                        <th className="px-4 py-3">DIN</th>
                        <th className="px-4 py-3">Designation</th>
                        <th className="px-4 py-3">Effective Date</th>
                        <th className="px-4 py-3">Notice Date</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3">Statutory Note</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-600">
                      {synthesis.nominated_directors_review.map((dir, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/80">
                          <td className="px-4 py-3 font-semibold text-slate-900">
                            {dir.director_name}
                          </td>
                          <td className="px-4 py-3 font-mono font-medium text-slate-800">
                            {dir.din}
                          </td>
                          <td className="px-4 py-3">{dir.designation}</td>
                          <td className="px-4 py-3 text-slate-500">
                            {dir.effective_from ? new Date(dir.effective_from).toLocaleDateString() : '—'}
                          </td>
                          <td className="px-4 py-3 text-slate-500">
                            {dir.form_i_notice_date ? new Date(dir.form_i_notice_date).toLocaleDateString() : '—'}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                dir.is_active
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {dir.is_active ? 'ACTIVE' : 'INACTIVE'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-[11px] text-slate-500 max-w-xs">
                            {dir.statutory_role_note}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 6: TIMELINE & AUDIT LOG */}
        {activeTab === 'timeline' && synthesis && (
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Clock className="h-4 w-4 text-brand-700" />
              Operational Dossier Audit Trail
            </h3>

            {synthesis.timeline_events.length === 0 ? (
              <div className="text-center py-10 text-xs text-slate-500">
                No timeline events recorded.
              </div>
            ) : (
              <div className="relative pl-6 border-l-2 border-slate-200 space-y-6">
                {synthesis.timeline_events.map((evt, idx) => (
                  <div key={idx} className="relative">
                    <div className="absolute -left-[31px] top-0.5 h-3.5 w-3.5 rounded-full bg-brand-700 border-2 border-white shadow-xs" />
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-brand-800">
                        {evt.event_type}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {new Date(evt.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 mt-1">{evt.description}</p>
                    {evt.actor_id && (
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        Actor: {evt.actor_id}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Link Inspection Modal */}
      {showLinkModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 border border-slate-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <PlusCircle className="h-5 w-5 text-brand-800" />
                <h3 className="text-base font-bold text-slate-900">Link Inspection to Dossier</h3>
              </div>
              <button
                onClick={() => setShowLinkModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-semibold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleLinkInspection} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Select Inspection Record <span className="text-red-500">*</span>
                </label>
                {loadingInspections ? (
                  <div className="py-6 text-center text-xs text-slate-500">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-1 text-brand-700" />
                    Loading available inspections...
                  </div>
                ) : availableInspections.length === 0 ? (
                  <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-500 text-center">
                    No unlinked inspections available. All current inspections are already linked.
                  </div>
                ) : (
                  <select
                    required
                    value={selectedInspectionId}
                    onChange={(e) => setSelectedInspectionId(e.target.value)}
                    className="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-white focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  >
                    {availableInspections.map((insp) => (
                      <option key={insp.id} value={insp.id}>
                        {insp.store_name || 'Premises'} ({insp.district || 'District'}, {insp.state || 'State'}) — [{insp.overall_result || 'PENDING'}] — ID: {insp.id.slice(0, 8)}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Relevance Notes (Operational Context)
                </label>
                <textarea
                  rows={3}
                  value={relevanceNotes}
                  onChange={(e) => setRelevanceNotes(e.target.value)}
                  placeholder="e.g. Same brand / distributor verified across regional retail points..."
                  className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-brand-500 focus:outline-none"
                />
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-[11px] text-slate-500 leading-relaxed">
                <strong>Legal Rule:</strong> Linking an inspection groups it under this supervisory dossier for coordination. It does not alter the inspection&apos;s legal verdict.
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowLinkModal(false)}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-lg font-medium cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={linking || !selectedInspectionId}
                  className="px-5 py-2 text-xs bg-brand-800 hover:bg-brand-900 text-white font-semibold rounded-lg shadow-xs disabled:opacity-50 cursor-pointer"
                >
                  {linking ? 'Linking...' : 'Link Inspection'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

