'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { ComplianceResult, Inspection } from '@/types';
import {
  ClipboardList,
  PlusCircle,
  Search,
  Filter,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  Clock,
  AlertTriangle,
  RefreshCw,
  Building2,
  MapPin,
  Sparkles,
  CheckCircle2,
  X,
  FileCheck,
  SlidersHorizontal,
  Camera,
  Layers,
  Scale,
  FileText,
  Shield,
  Activity,
  AlertOctagon,
  Eye,
} from 'lucide-react';

export default function InspectionsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [allInspections, setAllInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [seedingDemo, setSeedingDemo] = useState(false);
  const [demoFeedback, setDemoFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [resultFilter, setResultFilter] = useState<string>('');

  // Dual-dimension portfolio summary metrics
  const [summaryStats, setSummaryStats] = useState({
    total: 0,
    completed: 0,
    inProgress: 0,
    completedCompliant: 0,
    compliant: 0,
    nonCompliant: 0,
    needsReview: 0,
  });

  const fetchSummaryCounts = async () => {
    try {
      const allData = await api.listInspections({ limit: 250 });
      setAllInspections(allData);
      setSummaryStats({
        total: allData.length,
        completed: allData.filter((i) => i.status === 'COMPLETED').length,
        inProgress: allData.filter((i) => i.status !== 'COMPLETED').length,
        completedCompliant: allData.filter(
          (i) => i.status === 'COMPLETED' && (i.statutory_verdict || i.overall_result) === 'COMPLIANT'
        ).length,
        compliant: allData.filter((i) => (i.statutory_verdict || i.overall_result) === 'COMPLIANT').length,
        nonCompliant: allData.filter((i) => (i.statutory_verdict || i.overall_result) === 'NON_COMPLIANT').length,
        needsReview: allData.filter((i) => (i.statutory_verdict || i.overall_result) === 'NEEDS_REVIEW').length,
      });
    } catch {
      // Non-blocking
    }
  };

  const fetchInspections = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listInspections({
        status_filter: statusFilter || undefined,
        result_filter: resultFilter || undefined,
      });
      setInspections(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load inspection history.');
    } finally {
      setLoading(false);
    }
  };

  const handleSeedDemoPresets = async () => {
    setSeedingDemo(true);
    setDemoFeedback(null);
    try {
      const res = await api.seedDemoPresets();
      setDemoFeedback(res.message);
      await Promise.all([fetchInspections(), fetchSummaryCounts()]);
      setTimeout(() => setDemoFeedback(null), 6000);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to seed controlled demo presets.');
    } finally {
      setSeedingDemo(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push('/login');
      } else {
        fetchInspections();
        fetchSummaryCounts();
      }
    }
  }, [authLoading, user, statusFilter, resultFilter]);

  const clearFilters = () => {
    setStatusFilter('');
    setResultFilter('');
    setSearchTerm('');
  };

  const filteredInspections = useMemo(() => {
    return inspections.filter((insp) => {
      const store = (insp.store_name || '').toLowerCase();
      const district = (insp.district || '').toLowerCase();
      const state = (insp.state || '').toLowerCase();
      const commodity = (insp.declaration?.commodity_name || '').toLowerCase();
      const id = insp.id.toLowerCase();
      const q = searchTerm.toLowerCase();
      return (
        store.includes(q) ||
        district.includes(q) ||
        state.includes(q) ||
        commodity.includes(q) ||
        id.includes(q)
      );
    });
  }, [inspections, searchTerm]);

  // Operational Evidence Readiness Metrics (Real Data Calculation)
  const readinessMetrics = useMemo(() => {
    const dataset = allInspections.length > 0 ? allInspections : inspections;
    if (dataset.length === 0) {
      return {
        evidenceCoverage: 0,
        declarationCoverage: 0,
        physicalVerification: 0,
        qualityHealth: 100,
        retakeCount: 0,
      };
    }

    const total = dataset.length;

    // 1. Evidence Coverage: has at least 1 image
    const withImages = dataset.filter((i) => i.images && i.images.length > 0).length;
    const evidenceCoverage = Math.round((withImages / total) * 100);

    // 2. Declaration Coverage: has extracted commodity / MRP / net quantity
    const withDeclarations = dataset.filter(
      (i) =>
        i.declaration &&
        (i.declaration.commodity_name ||
          i.declaration.mrp ||
          i.declaration.net_quantity ||
          i.declaration.manufacturer_name)
    ).length;
    const declarationCoverage = Math.round((withDeclarations / total) * 100);

    // 3. Physical Verification: net quantity / area / gravimetric verified
    const withPhysical = dataset.filter(
      (i) =>
        i.declaration &&
        (i.declaration.measurement_data ||
          i.declaration.pdp_area_sq_cm ||
          i.declaration.is_human_verified)
    ).length;
    const physicalVerification = Math.round((withPhysical / total) * 100);

    // 4. Optical Quality Health
    let totalImages = 0;
    let cleanImages = 0;
    let retakeNeeded = 0;

    dataset.forEach((i) => {
      if (i.images && i.images.length > 0) {
        totalImages += i.images.length;
        i.images.forEach((img) => {
          const qg = img.quality_gate_result;
          if (qg && (qg.blur_detected || qg.glare_detected || qg.decision === 'RETAKE_RECOMMENDED')) {
            retakeNeeded += 1;
          } else {
            cleanImages += 1;
          }
        });
      }
    });

    const qualityHealth = totalImages > 0 ? Math.round((cleanImages / totalImages) * 100) : 100;

    return {
      evidenceCoverage,
      declarationCoverage,
      physicalVerification,
      qualityHealth,
      retakeCount: retakeNeeded,
    };
  }, [allInspections, inspections]);

  const getResultBadge = (result: ComplianceResult | undefined | null) => {
    switch (result) {
      case 'COMPLIANT':
        return (
          <span className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-300 font-bold px-2.5 py-1 rounded-full text-[11px] tracking-wide">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" /> COMPLIANT
          </span>
        );
      case 'NON_COMPLIANT':
        return (
          <span className="inline-flex items-center gap-1.5 bg-rose-50 text-rose-700 border border-rose-300 font-bold px-2.5 py-1 rounded-full text-[11px] tracking-wide">
            <ShieldAlert className="h-3.5 w-3.5 text-rose-600" /> NON-COMPLIANT
          </span>
        );
      case 'NEEDS_REVIEW':
        return (
          <span className="inline-flex items-center gap-1.5 bg-amber-50 text-amber-700 border border-amber-300 font-bold px-2.5 py-1 rounded-full text-[11px] tracking-wide">
            <Clock className="h-3.5 w-3.5 text-amber-600" /> NEEDS REVIEW
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 bg-slate-100 text-slate-700 border border-slate-300 font-bold px-2.5 py-1 rounded-full text-[11px] tracking-wide">
            PENDING
          </span>
        );
    }
  };

  // Canonical Controlled Demo IDs
  const CANONICAL_DEMO_A = '73a3b89a-0042-495c-adb0-c30cd0f37a8d';
  const CANONICAL_DEMO_B = '292e1441-a1c8-452f-9df9-4da7725ad62d';
  const CANONICAL_DEMO_C = 'e867bb21-2702-4704-a38a-0076b746b46d';

  const demoA = (allInspections.length > 0 ? allInspections : inspections).find(
    (i) => i.id === CANONICAL_DEMO_A || (i.store_name || '').includes('Tata Sampann')
  );
  const demoB = (allInspections.length > 0 ? allInspections : inspections).find(
    (i) => i.id === CANONICAL_DEMO_B || (i.store_name || '').includes('Dry Fruits')
  );
  const demoC = (allInspections.length > 0 ? allInspections : inspections).find(
    (i) => i.id === CANONICAL_DEMO_C || (i.store_name || '').includes('Heritage Spices')
  );

  const isCompletedCompliantActive = statusFilter === 'COMPLETED' && resultFilter === 'COMPLIANT';

  return (
    <div className="space-y-6">
      {/* Hero Workspace Header */}
      <div className="bg-white p-6 rounded-2xl shadow-xs border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700 border border-slate-200">
              Station ID: {user?.jurisdiction_district || 'CENTRAL'}-{user?.jurisdiction_state || 'DELHI'}
            </span>
            <span className="text-slate-300">•</span>
            <span className="text-[11px] font-medium text-slate-500">
              {new Date().toLocaleDateString('en-IN', {
                weekday: 'short',
                year: 'numeric',
                month: 'short',
                day: 'numeric',
              })}
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <ClipboardList className="h-6 w-6 text-brand-900" />
            Inspection Command Center
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Monitor evidence sufficiency, compliance outcomes, and cases requiring officer adjudication under Legal Metrology (Packaged Commodities) Rules, 2011.
          </p>
        </div>

        {/* Global Toolbar Actions */}
        <div className="flex flex-wrap items-center gap-2">
          {user && user.role !== 'INSPECTOR' && (
            <a
              href="/inspections/triage"
              className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl transition shadow-xs flex items-center gap-1.5"
              title="Open Operational Supervisor Triage Queue"
            >
              <ClipboardList className="h-3.5 w-3.5" />
              Supervisor Triage
            </a>
          )}

          <button
            onClick={handleSeedDemoPresets}
            disabled={seedingDemo}
            className="px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-bold rounded-xl transition flex items-center gap-1.5 disabled:opacity-50"
            title="Seed 7 Controlled Demo Case Presets"
          >
            <Sparkles className={`h-3.5 w-3.5 ${seedingDemo ? 'animate-spin' : 'text-indigo-600'}`} />
            {seedingDemo ? 'Seeding Presets...' : 'Load 7 Demo Presets'}
          </button>

          <button
            onClick={() => {
              fetchInspections();
              fetchSummaryCounts();
            }}
            className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition text-xs font-semibold flex items-center gap-1.5"
            title="Refresh Inspection Stream"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <a
            href="/inspections/new"
            className="bg-brand-900 hover:bg-brand-800 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-xs transition flex items-center gap-1.5"
          >
            <PlusCircle className="h-4 w-4" />
            New Inspection
          </a>
        </div>
      </div>

      {/* Demo Feedback Banner */}
      {demoFeedback && (
        <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-xl text-xs text-indigo-800 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-indigo-600 shrink-0" />
          <span><strong>Demo Fixtures:</strong> {demoFeedback}</span>
        </div>
      )}

      {/* Curated SIH26034 Benchmark Suite Showcase */}
      <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-6 shadow-sm text-slate-900 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-sky-50 text-sky-800 border border-sky-200 flex items-center gap-1.5">
                <Sparkles className="h-3 w-3 text-sky-600" />
                CURATED SIH26034 BENCHMARK SUITE
              </span>
              <span className="text-slate-300 hidden sm:inline">•</span>
              <span className="text-[11px] font-semibold text-slate-500">
                Deterministic Legal Verification
              </span>
            </div>
            <h2 className="text-base sm:text-lg font-black tracking-tight text-slate-900 flex items-center gap-2">
              <Scale className="h-5 w-5 text-sky-600" />
              Pre-Calibrated Golden Benchmark Evaluations
            </h2>
            <p className="text-xs text-slate-500 mt-0.5 max-w-2xl">
              Instant 1-click access to verified inspection cases testing full statutory compliance, optical anomaly detection, and mandatory declaration omissions under PCR 2011.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              type="button"
              onClick={handleSeedDemoPresets}
              disabled={seedingDemo}
              className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-bold rounded-xl transition flex items-center gap-1.5 disabled:opacity-50 cursor-pointer shadow-xs"
              title="Ensure all 7 demo presets are seeded in database"
            >
              <RefreshCw className={`h-3.5 w-3.5 text-sky-600 ${seedingDemo ? 'animate-spin' : ''}`} />
              {seedingDemo ? 'Refreshing Presets...' : 'Sync Presets'}
            </button>
          </div>
        </div>

        {/* 3 Interactive Benchmark Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Benchmark A */}
          <div className="bg-emerald-50/40 hover:bg-emerald-50/70 border border-emerald-200 rounded-2xl p-5 transition-all flex flex-col justify-between space-y-3 shadow-xs">
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full border border-emerald-200">
                  Benchmark A • Full Compliance
                </span>
                <span className="inline-flex items-center gap-1 bg-emerald-100 text-emerald-800 border border-emerald-200 font-bold px-2.5 py-0.5 rounded-full text-[10px]">
                  <CheckCircle2 className="h-3 w-3 text-emerald-600" /> COMPLETED
                </span>
              </div>

              <div>
                <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                  Tata Sampann Toor Dal 1kg
                </h3>
                <div className="text-[11px] font-mono font-bold text-emerald-700 mt-0.5">
                  Verdict: COMPLIANT (18/18 Checks PASS)
                </div>
              </div>

              <p className="text-[11px] text-slate-600 leading-relaxed">
                Golden compliant package with 100% statutory coverage across MRP, Net Quantity, Packer Address, and Customer Care. Finalized &amp; locked against mutation.
              </p>
            </div>

            <div className="pt-2.5 border-t border-emerald-200/80 flex items-center justify-between">
              <span className="text-[10px] text-slate-500 font-mono">0 Violations • Locked</span>
              <a
                href={`/inspections/${demoA ? demoA.id : CANONICAL_DEMO_A}`}
                className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 hover:text-emerald-800 transition"
              >
                <span>Open Case A</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>

          {/* Benchmark B */}
          <div className="bg-rose-50/40 hover:bg-rose-50/70 border border-rose-200 rounded-2xl p-5 transition-all flex flex-col justify-between space-y-3 shadow-xs">
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-rose-800 bg-rose-100 px-2.5 py-0.5 rounded-full border border-rose-200">
                  Benchmark B • Optical Anomaly
                </span>
                <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-800 border border-amber-200 font-bold px-2.5 py-0.5 rounded-full text-[10px]">
                  <Clock className="h-3 w-3 text-amber-600" /> REVIEW REQUIRED
                </span>
              </div>

              <div>
                <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                  Premium Dry Fruits (Almonds)
                </h3>
                <div className="text-[11px] font-mono font-bold text-rose-700 mt-0.5">
                  Verdict: NON-COMPLIANT (Statutory Defect)
                </div>
              </div>

              <p className="text-[11px] text-slate-600 leading-relaxed">
                Pre-flight quality gate flagged specular glare on plastic pouch. Rule engine evaluation verified statutory declaration defects requiring officer review.
              </p>
            </div>

            <div className="pt-2.5 border-t border-rose-200/80 flex items-center justify-between">
              <span className="text-[10px] text-slate-500 font-mono">Retake Advised</span>
              <a
                href={`/inspections/${demoB ? demoB.id : CANONICAL_DEMO_B}`}
                className="inline-flex items-center gap-1 text-xs font-bold text-rose-700 hover:text-rose-800 transition"
              >
                <span>Open Case B</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>

          {/* Benchmark C */}
          <div className="bg-amber-50/40 hover:bg-amber-50/70 border border-amber-200 rounded-2xl p-5 transition-all flex flex-col justify-between space-y-3 shadow-xs">
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-amber-800 bg-amber-100 px-2.5 py-0.5 rounded-full border border-amber-200">
                  Benchmark C • Mandatory Omission
                </span>
                <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-800 border border-amber-200 font-bold px-2.5 py-0.5 rounded-full text-[10px]">
                  <Clock className="h-3 w-3 text-amber-600" /> REVIEW REQUIRED
                </span>
              </div>

              <div>
                <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                  Heritage Spices Garam Masala
                </h3>
                <div className="text-[11px] font-mono font-bold text-amber-800 mt-0.5">
                  Verdict: NEEDS REVIEW (Missing MRP)
                </div>
              </div>

              <p className="text-[11px] text-slate-600 leading-relaxed">
                Missing mandatory retail price declaration under Rule 6(1)(e). Zero false certainty safety invariant engaged: routed to officer adjudication queue.
              </p>
            </div>

            <div className="pt-2.5 border-t border-amber-200/80 flex items-center justify-between">
              <span className="text-[10px] text-slate-500 font-mono">Zero False Certainty</span>
              <a
                href={`/inspections/${demoC ? demoC.id : CANONICAL_DEMO_C}`}
                className="inline-flex items-center gap-1 text-xs font-bold text-amber-700 hover:text-amber-800 transition"
              >
                <span>Open Case C</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Dual-Dimension Portfolio KPI Metric Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* All Records */}
        <button
          type="button"
          onClick={clearFilters}
          className={`p-4 rounded-xl border text-left transition-all ${
            statusFilter === '' && resultFilter === ''
              ? 'bg-sky-800 text-white border-sky-800 shadow-sm ring-2 ring-sky-500/20'
              : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="text-[10px] font-bold uppercase tracking-wider opacity-75">All Records</div>
          <div className="text-2xl font-black mt-1">{summaryStats.total}</div>
          <div className="text-[10px] opacity-70 mt-0.5">Total registered cases</div>
        </button>

        {/* Completed & Compliant (Key Statutory Anchor) */}
        <button
          type="button"
          onClick={() => {
            setStatusFilter('COMPLETED');
            setResultFilter('COMPLIANT');
          }}
          className={`p-4 rounded-xl border text-left transition-all ${
            isCompletedCompliantActive
              ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs ring-2 ring-emerald-400/30'
              : 'bg-emerald-50/60 text-emerald-950 border-emerald-200 hover:border-emerald-300 hover:bg-emerald-50'
          }`}
        >
          <div className="text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
            <FileCheck className="h-3.5 w-3.5 text-emerald-700" /> Completed &amp; Compliant
          </div>
          <div className="text-2xl font-black mt-1">{summaryStats.completedCompliant}</div>
          <div className="text-[10px] opacity-80 mt-0.5 font-medium">Finalized compliant cases</div>
        </button>

        {/* All Completed (Lifecycle) */}
        <button
          type="button"
          onClick={() => {
            setStatusFilter('COMPLETED');
            setResultFilter('');
          }}
          className={`p-4 rounded-xl border text-left transition-all ${
            statusFilter === 'COMPLETED' && resultFilter === ''
              ? 'bg-sky-800 text-white border-sky-800 shadow-xs'
              : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="text-[10px] font-bold uppercase tracking-wider opacity-75 flex items-center gap-1">
            <CheckCircle2 className="h-3.5 w-3.5" /> All Completed
          </div>
          <div className="text-2xl font-black mt-1">{summaryStats.completed}</div>
          <div className="text-[10px] opacity-70 mt-0.5">Finalized lifecycle</div>
        </button>

        {/* Action Required (Lifecycle) */}
        <button
          type="button"
          onClick={() => {
            setStatusFilter('REVIEW_REQUIRED');
            setResultFilter('');
          }}
          className={`p-4 rounded-xl border text-left transition-all ${
            statusFilter === 'REVIEW_REQUIRED' && resultFilter === ''
              ? 'bg-amber-600 text-white border-amber-600 shadow-xs'
              : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="text-[10px] font-bold uppercase tracking-wider opacity-75 flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" /> Action Required
          </div>
          <div className="text-2xl font-black mt-1">{summaryStats.inProgress}</div>
          <div className="text-[10px] opacity-70 mt-0.5">Active inspection stream</div>
        </button>

        {/* Statutory: Non-Compliant */}
        <button
          type="button"
          onClick={() => {
            setStatusFilter('');
            setResultFilter('NON_COMPLIANT');
          }}
          className={`p-4 rounded-xl border text-left transition-all ${
            statusFilter === '' && resultFilter === 'NON_COMPLIANT'
              ? 'bg-rose-600 text-white border-rose-600 shadow-xs'
              : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="text-[10px] font-bold uppercase tracking-wider opacity-75 flex items-center gap-1">
            <ShieldAlert className="h-3.5 w-3.5" /> Non-Compliant
          </div>
          <div className="text-2xl font-black mt-1">{summaryStats.nonCompliant}</div>
          <div className="text-[10px] opacity-70 mt-0.5">Statutory violations</div>
        </button>

        {/* Statutory: Needs Review */}
        <button
          type="button"
          onClick={() => {
            setStatusFilter('');
            setResultFilter('NEEDS_REVIEW');
          }}
          className={`p-4 rounded-xl border text-left transition-all ${
            statusFilter === '' && resultFilter === 'NEEDS_REVIEW'
              ? 'bg-amber-500 text-white border-amber-500 shadow-xs'
              : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="text-[10px] font-bold uppercase tracking-wider opacity-75 flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" /> Needs Review
          </div>
          <div className="text-2xl font-black mt-1">{summaryStats.needsReview}</div>
          <div className="text-[10px] opacity-70 mt-0.5">Low confidence / blur</div>
        </button>
      </div>

      {/* Middle Grid: Operational Inspection Readiness & Priority Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Inspection Readiness Panel (7 cols) */}
        <div className="lg:col-span-7 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-sky-600" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                Operational Evidence Readiness Health
              </h2>
            </div>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Real-time Portfolio Health
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Meter 1: Evidence Coverage */}
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="font-bold text-slate-700 flex items-center gap-1.5">
                  <Camera className="h-3.5 w-3.5 text-sky-600" /> Evidence Coverage
                </span>
                <span className="font-mono font-bold text-slate-900">
                  {readinessMetrics.evidenceCoverage}%
                </span>
              </div>
              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-sky-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${readinessMetrics.evidenceCoverage}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 mt-1.5">
                Cases with attached package photographs
              </div>
            </div>

            {/* Meter 2: Declaration Extraction */}
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="font-bold text-slate-700 flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5 text-indigo-600" /> Declaration Coverage
                </span>
                <span className="font-mono font-bold text-slate-900">
                  {readinessMetrics.declarationCoverage}%
                </span>
              </div>
              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${readinessMetrics.declarationCoverage}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 mt-1.5">
                Extracted mandatory statutory declarations
              </div>
            </div>

            {/* Meter 3: Physical Verification */}
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="font-bold text-slate-700 flex items-center gap-1.5">
                  <Scale className="h-3.5 w-3.5 text-emerald-600" /> Physical Verification
                </span>
                <span className="font-mono font-bold text-slate-900">
                  {readinessMetrics.physicalVerification}%
                </span>
              </div>
              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${readinessMetrics.physicalVerification}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 mt-1.5">
                Net weight, PDP area, or officer verification
              </div>
            </div>

            {/* Meter 4: Image Quality Health */}
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="font-bold text-slate-700 flex items-center gap-1.5">
                  <Eye className="h-3.5 w-3.5 text-teal-600" /> Optical Quality Health
                </span>
                <span className="font-mono font-bold text-slate-900">
                  {readinessMetrics.qualityHealth}%
                </span>
              </div>
              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-teal-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${readinessMetrics.qualityHealth}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 mt-1.5">
                Photographs passing blur &amp; glare diagnostics
              </div>
            </div>
          </div>

          <p className="text-[10px] text-slate-400 italic">
            * Operational evidence indicators — not statutory verdicts. Reflects perceptual completeness and optical quality across current inspection records.
          </p>
        </div>

        {/* Priority Actions Panel (5 cols) */}
        <div className="lg:col-span-5 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3.5">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <AlertOctagon className="h-4 w-4 text-amber-600" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                Action Items Requiring Officer Focus
              </h2>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            {/* Priority Item 1: Needs Review Cases */}
            {summaryStats.needsReview > 0 ? (
              <button
                type="button"
                onClick={() => {
                  setStatusFilter('');
                  setResultFilter('NEEDS_REVIEW');
                }}
                className="w-full p-2.5 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-200 text-left transition flex items-center justify-between group"
              >
                <div className="flex items-center gap-2 text-amber-900">
                  <Clock className="h-4 w-4 text-amber-600 shrink-0" />
                  <span className="font-semibold">
                    {summaryStats.needsReview} case(s) require officer adjudication
                  </span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-amber-600 group-hover:translate-x-0.5 transition-transform" />
              </button>
            ) : null}

            {/* Priority Item 2: Optical Retakes */}
            {readinessMetrics.retakeCount > 0 ? (
              <button
                type="button"
                onClick={() => {
                  setStatusFilter('REVIEW_REQUIRED');
                  setResultFilter('');
                }}
                className="w-full p-2.5 rounded-xl bg-orange-50 hover:bg-orange-100 border border-orange-200 text-left transition flex items-center justify-between group"
              >
                <div className="flex items-center gap-2 text-orange-900">
                  <Camera className="h-4 w-4 text-orange-600 shrink-0" />
                  <span className="font-semibold">
                    {readinessMetrics.retakeCount} image(s) flagged for optical retake
                  </span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-orange-600 group-hover:translate-x-0.5 transition-transform" />
              </button>
            ) : null}

            {/* Priority Item 3: Active Non-Compliant Violations */}
            {summaryStats.nonCompliant > 0 ? (
              <button
                type="button"
                onClick={() => {
                  setStatusFilter('');
                  setResultFilter('NON_COMPLIANT');
                }}
                className="w-full p-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 border border-rose-200 text-left transition flex items-center justify-between group"
              >
                <div className="flex items-center gap-2 text-rose-900">
                  <ShieldAlert className="h-4 w-4 text-rose-600 shrink-0" />
                  <span className="font-semibold">
                    {summaryStats.nonCompliant} inspection(s) with statutory violations
                  </span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-rose-600 group-hover:translate-x-0.5 transition-transform" />
              </button>
            ) : null}

            {/* Priority Item 4: Completed & Compliant Ready */}
            {summaryStats.completedCompliant > 0 ? (
              <button
                type="button"
                onClick={() => {
                  setStatusFilter('COMPLETED');
                  setResultFilter('COMPLIANT');
                }}
                className="w-full p-2.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-left transition flex items-center justify-between group"
              >
                <div className="flex items-center gap-2 text-emerald-900">
                  <FileCheck className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span className="font-semibold">
                    {summaryStats.completedCompliant} finalized compliant case(s) ready for report export
                  </span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-emerald-600 group-hover:translate-x-0.5 transition-transform" />
              </button>
            ) : null}

            {/* Fallback if everything is clear */}
            {summaryStats.needsReview === 0 &&
              summaryStats.nonCompliant === 0 &&
              summaryStats.completedCompliant === 0 && (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-center text-slate-500 text-xs">
                  All active inspection queues verified. No pending urgent officer actions.
                </div>
              )}
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white p-4 rounded-xl shadow-xs border border-slate-200 space-y-3">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="h-4 w-4 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              placeholder="Search by store name, commodity, district, state, or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none transition"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-slate-400 hidden sm:block" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none font-medium"
            >
              <option value="">Lifecycle: All Statuses</option>
              <option value="CREATED">CREATED</option>
              <option value="PROCESSING">PROCESSING</option>
              <option value="REVIEW_REQUIRED">REVIEW REQUIRED</option>
              <option value="COMPLETED">COMPLETED</option>
            </select>

            {/* Result Filter */}
            <select
              value={resultFilter}
              onChange={(e) => setResultFilter(e.target.value)}
              className="text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none font-medium"
            >
              <option value="">Verdict: All Verdicts</option>
              <option value="COMPLIANT">COMPLIANT</option>
              <option value="NON_COMPLIANT">NON-COMPLIANT</option>
              <option value="NEEDS_REVIEW">NEEDS REVIEW</option>
              <option value="PENDING">PENDING</option>
            </select>
          </div>
        </div>

        {/* Quick Filter Pills & Active Filter Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 text-xs">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-slate-400 text-[11px] font-medium mr-1 flex items-center gap-1">
              <Filter className="h-3 w-3" /> Presets:
            </span>
            <button
              type="button"
              onClick={clearFilters}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition ${
                statusFilter === '' && resultFilter === ''
                  ? 'bg-slate-800 text-white border-slate-800'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
              }`}
            >
              All
            </button>
            <button
              type="button"
              onClick={() => {
                setStatusFilter('COMPLETED');
                setResultFilter('COMPLIANT');
              }}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition flex items-center gap-1 ${
                isCompletedCompliantActive
                  ? 'bg-emerald-700 text-white border-emerald-700'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
              }`}
            >
              <ShieldCheck className="h-3 w-3" /> Completed &amp; Compliant
            </button>
            <button
              type="button"
              onClick={() => {
                setStatusFilter('COMPLETED');
                setResultFilter('');
              }}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition ${
                statusFilter === 'COMPLETED' && resultFilter === ''
                  ? 'bg-sky-700 text-white border-sky-700'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
              }`}
            >
              Completed Only
            </button>
            <button
              type="button"
              onClick={() => {
                setStatusFilter('REVIEW_REQUIRED');
                setResultFilter('');
              }}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition ${
                statusFilter === 'REVIEW_REQUIRED' && resultFilter === ''
                  ? 'bg-amber-600 text-white border-amber-600'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
              }`}
            >
              Review Required
            </button>
            <button
              type="button"
              onClick={() => {
                setStatusFilter('');
                setResultFilter('NON_COMPLIANT');
              }}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition ${
                statusFilter === '' && resultFilter === 'NON_COMPLIANT'
                  ? 'bg-rose-700 text-white border-rose-700'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
              }`}
            >
              Non-Compliant
            </button>
            <button
              type="button"
              onClick={() => {
                setStatusFilter('');
                setResultFilter('NEEDS_REVIEW');
              }}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition ${
                statusFilter === '' && resultFilter === 'NEEDS_REVIEW'
                  ? 'bg-amber-600 text-white border-amber-600'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
              }`}
            >
              Needs Review
            </button>
          </div>

          {(statusFilter || resultFilter || searchTerm) && (
            <button
              onClick={clearFilters}
              className="text-[11px] text-slate-500 hover:text-rose-600 flex items-center gap-1 font-medium transition"
            >
              <X className="h-3.5 w-3.5" /> Clear active filters
            </button>
          )}
        </div>
      </div>

      {/* Error Alert with Retry */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => fetchInspections()}
            className="px-3 py-1 bg-rose-100 hover:bg-rose-200 text-rose-800 rounded font-semibold text-[11px] transition"
          >
            Retry
          </button>
        </div>
      )}

      {/* Inspections Master Table & Data Stream */}
      <div className="bg-white rounded-2xl shadow-xs border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="p-8 space-y-4">
            <div className="flex items-center justify-center py-12 text-xs text-slate-500 flex-col gap-3">
              <RefreshCw className="h-8 w-8 text-sky-600 animate-spin" />
              <span className="font-semibold text-slate-700">Loading inspection repository...</span>
            </div>
          </div>
        ) : filteredInspections.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-500 flex flex-col items-center justify-center p-6">
            <ClipboardList className="h-10 w-10 text-slate-300 mb-3" />
            <p className="font-bold text-slate-800 text-sm">No inspection records found</p>
            {isCompletedCompliantActive ? (
              <p className="text-slate-500 mt-1 max-w-md">
                No inspection records currently have both <span className="font-semibold text-emerald-700">Status = COMPLETED</span> and <span className="font-semibold text-emerald-700">Verdict = COMPLIANT</span> under your jurisdiction. Click &quot;Load 7 Demo Presets&quot; above to seed a pre-finalized compliant benchmark case.
              </p>
            ) : statusFilter || resultFilter || searchTerm ? (
              <div className="mt-1">
                <p className="text-slate-400 max-w-sm">
                  No inspections match your active filter criteria.
                </p>
                <button
                  onClick={clearFilters}
                  className="mt-3 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg text-xs transition"
                >
                  Clear all filters
                </button>
              </div>
            ) : (
              <p className="text-slate-400 mt-1 max-w-sm">
                You currently have no inspections recorded. Click &quot;Load 7 Demo Presets&quot; or &quot;New Inspection&quot; to begin.
              </p>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-4 py-3.5">Store &amp; Commodity</th>
                  <th className="px-4 py-3.5">Location</th>
                  <th className="px-4 py-3.5">Lifecycle Status</th>
                  <th className="px-4 py-3.5">Statutory Verdict</th>
                  <th className="px-4 py-3.5">Evidence Health</th>
                  <th className="px-4 py-3.5">Date / Time</th>
                  <th className="px-4 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {filteredInspections.map((insp) => {
                  const verdict = insp.statutory_verdict || insp.overall_result;
                  const isCompletedCompliant = insp.status === 'COMPLETED' && verdict === 'COMPLIANT';
                  const imageCount = insp.images ? insp.images.length : 0;
                  const commodity = insp.declaration?.commodity_name || 'Standard Commodity';

                  return (
                    <tr
                      key={insp.id}
                      className={`hover:bg-slate-50/80 transition-colors ${
                        isCompletedCompliant ? 'bg-emerald-50/20' : ''
                      }`}
                    >
                      {/* Store & Commodity */}
                      <td className="px-4 py-3.5">
                        <div className="font-bold text-slate-900 flex items-center gap-1.5">
                          <Building2 className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                          <span className="truncate max-w-[220px]">{insp.store_name || 'Retail Establishment'}</span>
                        </div>
                        <div className="text-[11px] text-slate-600 font-medium mt-0.5 truncate max-w-[240px]">
                          {commodity}
                        </div>
                        <div className="text-[9px] text-slate-400 font-mono mt-0.5">
                          ID: {insp.id.slice(0, 16)}...
                        </div>
                      </td>

                      {/* Location */}
                      <td className="px-4 py-3.5 text-slate-600">
                        <div className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                          <span>
                            {insp.district || 'N/A'}, {insp.state || 'N/A'}
                          </span>
                        </div>
                      </td>

                      {/* Lifecycle Status */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        {insp.status === 'COMPLETED' ? (
                          <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 border border-emerald-300 font-bold px-2 py-0.5 rounded text-[10px]">
                            <CheckCircle2 className="h-3 w-3 text-emerald-600" /> COMPLETED
                          </span>
                        ) : insp.status === 'REVIEW_REQUIRED' ? (
                          <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 border border-amber-300 font-bold px-2 py-0.5 rounded text-[10px]">
                            <Clock className="h-3 w-3 text-amber-600" /> REVIEW REQUIRED
                          </span>
                        ) : insp.status === 'PROCESSING' ? (
                          <span className="inline-flex items-center gap-1 bg-sky-50 text-sky-700 border border-sky-300 font-bold px-2 py-0.5 rounded text-[10px]">
                            <RefreshCw className="h-3 w-3 text-sky-600 animate-spin" /> PROCESSING
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 bg-slate-100 text-slate-700 border border-slate-300 font-semibold px-2 py-0.5 rounded text-[10px]">
                            {insp.status}
                          </span>
                        )}
                      </td>

                      {/* Statutory Verdict */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        {getResultBadge(verdict)}
                      </td>

                      {/* Evidence Health Column */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <div className="flex items-center gap-1.5 text-slate-600 text-[11px]">
                          <Camera className="h-3.5 w-3.5 text-slate-400" />
                          <span>{imageCount} photo{imageCount === 1 ? '' : 's'}</span>
                          {insp.declaration?.is_human_verified && (
                            <span className="text-[9px] bg-sky-100 text-sky-800 font-bold px-1.5 py-0.2 rounded">
                              Verified
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Timestamp */}
                      <td className="px-4 py-3.5 text-slate-500 whitespace-nowrap">
                        <div>
                          {new Date(insp.created_at).toLocaleDateString()}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {new Date(insp.created_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3.5 text-right whitespace-nowrap">
                        <a
                          href={`/inspections/${insp.id}`}
                          className="inline-flex items-center gap-1 bg-brand-50 hover:bg-brand-100 text-brand-900 font-bold px-3 py-1.5 rounded-lg border border-brand-200 transition-colors"
                        >
                          {insp.status === 'COMPLETED' ? 'View Record' : 'Open Workspace'}
                          <ArrowRight className="h-3.5 w-3.5" />
                        </a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Global Legal Safety Microcopy Card */}
      <div className="bg-slate-50/90 text-slate-700 p-4.5 rounded-2xl border border-slate-200 shadow-xs flex items-start gap-3">
        <Shield className="h-5 w-5 text-sky-600 shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <div className="font-bold text-slate-900 flex items-center gap-2">
            Statutory Compliance Governance &amp; Decision Support Notice
          </div>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            MetrologyMitra operates strictly as an evidence-backed decision-support system for authorized Legal Metrology officers. Computer vision and optical character recognition supply evidence items and confidence signals only. All statutory verdicts (<span className="text-emerald-700 font-semibold">COMPLIANT</span>, <span className="text-rose-700 font-semibold">NON_COMPLIANT</span>, <span className="text-amber-700 font-semibold">NEEDS_REVIEW</span>) are determined exclusively by the deterministic Legal Metrology (Packaged Commodities) Rules, 2011 engine under human supervision.
          </p>
        </div>
      </div>
    </div>
  );
}
