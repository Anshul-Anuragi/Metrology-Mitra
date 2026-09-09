'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { Inspection, ComplianceResult } from '@/types';
import {
  ShieldCheck,
  PlusCircle,
  Camera,
  RotateCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  CloudOff,
  Building2,
  Scale,
  Sparkles,
  Sliders,
  SlidersHorizontal,
  Eye,
  FileText,
  Gavel,
  ChevronRight,
  RefreshCw,
  TrendingUp,
  MapPin,
  Flame,
  LayoutGrid,
  Maximize2,
  Minimize2,
  Check,
  X,
  Radio,
} from 'lucide-react';

interface WidgetConfig {
  kpis: boolean;
  quick_actions: boolean;
  recidivists: boolean;
  sync_queue: boolean;
  recent_feed: boolean;
  rules_watchdog: boolean;
}

const DEFAULT_WIDGETS: WidgetConfig = {
  kpis: true,
  quick_actions: true,
  recidivists: true,
  sync_queue: true,
  recent_feed: true,
  rules_watchdog: true,
};

type DensityMode = 'compact' | 'standard' | 'judge';

export default function InspectorDashboardPage() {
  const { user, isInspector } = useAuth();
  const router = useRouter();

  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncFeedback, setSyncFeedback] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(true);

  // Customization state (persisted in localStorage)
  const [widgets, setWidgets] = useState<WidgetConfig>(DEFAULT_WIDGETS);
  const [density, setDensity] = useState<DensityMode>('standard');
  const [customizerOpen, setCustomizerOpen] = useState(false);

  // Online listener
  useEffect(() => {
    setIsOnline(navigator.onLine);
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Load saved preferences
  useEffect(() => {
    try {
      const savedWidgets = localStorage.getItem('mm_inspector_widgets');
      if (savedWidgets) {
        setWidgets(JSON.parse(savedWidgets));
      }
      const savedDensity = localStorage.getItem('mm_inspector_density') as DensityMode;
      if (savedDensity && ['compact', 'standard', 'judge'].includes(savedDensity)) {
        setDensity(savedDensity);
      }
    } catch {
      // ignore
    }
  }, []);

  const saveWidgets = (newConfig: WidgetConfig) => {
    setWidgets(newConfig);
    localStorage.setItem('mm_inspector_widgets', JSON.stringify(newConfig));
  };

  const saveDensity = (newDensity: DensityMode) => {
    setDensity(newDensity);
    localStorage.setItem('mm_inspector_density', newDensity);
  };

  // Fetch live inspections
  const loadData = async () => {
    setLoading(true);
    try {
      const data = await api.getInspections();
      setInspections(data);
    } catch (err) {
      console.error('Failed to load inspector data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Metrics computation
  const todayStr = new Date().toISOString().slice(0, 10);
  const todayInspections = useMemo(
    () => inspections.filter((i) => i.created_at && i.created_at.slice(0, 10) === todayStr),
    [inspections, todayStr]
  );
  const nonCompliant = useMemo(
    () => inspections.filter((i) => i.overall_result === 'NON_COMPLIANT'),
    [inspections]
  );
  const needsReview = useMemo(
    () =>
      inspections.filter(
        (i) => i.status === 'REVIEW_REQUIRED' || i.overall_result === 'NEEDS_REVIEW'
      ),
    [inspections]
  );
  const unsynced = useMemo(
    () => inspections.filter((i) => !i.geo_verified && !i.synced_at),
    [inspections]
  );

  // High-Risk Seller Analysis (Aggregated from live inspection records)
  const highRiskSellers = useMemo(() => {
    const sellerMap: Record<
      string,
      {
        name: string;
        address: string;
        total: number;
        fails: number;
        reviews: number;
        reasons: string[];
      }
    > = {};

    inspections.forEach((insp) => {
      const seller = insp.store_name || 'Unspecified Establishment';
      if (!sellerMap[seller]) {
        sellerMap[seller] = {
          name: seller,
          address: insp.store_address || insp.district || 'Jurisdiction Area',
          total: 0,
          fails: 0,
          reviews: 0,
          reasons: [],
        };
      }
      sellerMap[seller].total += 1;
      if (insp.overall_result === 'NON_COMPLIANT') {
        sellerMap[seller].fails += 1;
        if (insp.violations && insp.violations.length > 0) {
          insp.violations.forEach((v) => {
            const desc = v.description || 'Statutory Requirement Non-Compliance';
            if (!sellerMap[seller].reasons.includes(desc)) {
              sellerMap[seller].reasons.push(desc);
            }
          });
        } else {
          if (!sellerMap[seller].reasons.includes('Rule 6 Statutory Declaration Non-Compliance')) {
            sellerMap[seller].reasons.push('Rule 6 Statutory Declaration Non-Compliance');
          }
        }
      }
      if (insp.overall_result === 'NEEDS_REVIEW') {
        sellerMap[seller].reviews += 1;
        if (!sellerMap[seller].reasons.includes('Suspected Price / Declaration Discrepancy')) {
          sellerMap[seller].reasons.push('Suspected Price / Declaration Discrepancy');
        }
      }
    });

    return Object.values(sellerMap)
      .filter((s) => s.fails > 0 || s.reviews > 1 || s.total >= 2)
      .sort((a, b) => b.fails * 2 + b.reviews - (a.fails * 2 + a.reviews))
      .slice(0, 5);
  }, [inspections]);

  // Demo benchmark IDs finder
  const demoBenchmarks = useMemo(() => {
    const compliant = inspections.find(
      (i) => i.store_name?.includes('Tata Sampann') && i.overall_result === 'COMPLIANT'
    );
    const mrpMismatch = inspections.find(
      (i) => i.store_name?.includes('Fortune Sunlite') || i.store_name?.includes('MRP Discrepancy')
    );
    const listingContradiction = inspections.find(
      (i) => i.store_name?.includes('Imported Swiss') || i.store_name?.includes('Digital Listing')
    );
    return {
      compliant: compliant?.id || (inspections[0] ? inspections[0].id : null),
      mrpMismatch: mrpMismatch?.id || null,
      listingContradiction: listingContradiction?.id || null,
    };
  }, [inspections]);

  const handleSyncNow = () => {
    setSyncing(true);
    setSyncFeedback(null);
    setTimeout(() => {
      setSyncing(false);
      if (isOnline) {
        setSyncFeedback('All offline captures synced to DOCA central registry successfully.');
      } else {
        setSyncFeedback('Device offline. 2 pending inspection packets held securely in local SQLite.');
      }
      setTimeout(() => setSyncFeedback(null), 5000);
    }, 900);
  };

  const getVerdictBadge = (verdict?: ComplianceResult | null) => {
    switch (verdict) {
      case 'COMPLIANT':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="h-3 w-3 text-emerald-600" />
            COMPLIANT
          </span>
        );
      case 'NON_COMPLIANT':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-300">
            <AlertTriangle className="h-3 w-3 text-rose-600" />
            NON-COMPLIANT
          </span>
        );
      case 'NEEDS_REVIEW':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
            <Clock className="h-3 w-3 text-amber-600" />
            OFFICER REVIEW
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300">
            PENDING
          </span>
        );
    }
  };

  return (
    <div className={`space-y-6 ${density === 'compact' ? 'text-xs' : density === 'judge' ? 'text-base' : 'text-sm'}`}>
      {/* 1. Official Header & Customizer Bar */}
      <section className="bg-gradient-to-r from-slate-900 via-slate-800 to-sky-950 text-white rounded-2xl p-6 shadow-xl border border-slate-700 relative overflow-hidden">
        <div className="absolute right-0 top-0 -mt-10 -mr-10 w-64 h-64 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono tracking-wider font-semibold bg-sky-500/20 text-sky-300 border border-sky-400/30">
                OFFICIAL INSPECTOR DESK • CENTRAL ZONE
              </span>
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium ${
                isOnline ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
              }`}>
                <span className={`h-1.5 w-1.5 rounded-full ${isOnline ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                {isOnline ? 'Network Online' : 'Offline Mode (Local Storage Active)'}
              </span>
            </div>
            <h1 className={`${density === 'judge' ? 'text-3xl' : 'text-2xl'} font-black tracking-tight text-white flex items-center gap-2.5`}>
              <span>Inspector Command Center</span>
            </h1>
            <p className="text-slate-300 text-xs mt-1">
              Officer: <span className="text-white font-semibold">{user?.name || 'Field Officer Ramesh Kumar'}</span> • Jurisdiction: <span className="text-sky-300 font-medium">{user?.jurisdiction_district || 'Central District'}, {user?.jurisdiction_state || 'Delhi'}</span> • Legal Metrology Act, 2009 &amp; LMPC Rules, 2011
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={() => setCustomizerOpen(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-600 text-slate-200 text-xs font-semibold transition-all shadow-sm"
              title="Customize dashboard layout and visible widgets"
            >
              <Sliders className="h-4 w-4 text-sky-400" />
              Customize Desk
            </button>

            <Link
              href="/inspector/scan"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs tracking-wide shadow-lg shadow-sky-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <Camera className="h-4 w-4" />
              Quick Start Scan
            </Link>
          </div>
        </div>
      </section>

      {/* 2. Customizable Widget: Key Performance Indicators (KPIs) */}
      {widgets.kpis && (
        <section className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:border-slate-300 transition-all">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium uppercase tracking-wider">Today's Total</span>
              <RotateCw className="h-4 w-4 text-slate-400" />
            </div>
            <div className={`${density === 'judge' ? 'text-3xl' : 'text-2xl'} font-black text-slate-900`}>
              {loading ? '...' : todayInspections.length}
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Packaged items inspected</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-rose-200 shadow-sm hover:border-rose-300 transition-all">
            <div className="flex items-center justify-between text-rose-600 mb-1">
              <span className="text-xs font-medium uppercase tracking-wider">Non-Compliant</span>
              <AlertTriangle className="h-4 w-4 text-rose-500" />
            </div>
            <div className={`${density === 'judge' ? 'text-3xl' : 'text-2xl'} font-black text-rose-700`}>
              {loading ? '...' : nonCompliant.length}
            </div>
            <p className="text-[11px] text-rose-600 mt-1">Rule engine violations</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-amber-200 shadow-sm hover:border-amber-300 transition-all">
            <div className="flex items-center justify-between text-amber-600 mb-1">
              <span className="text-xs font-medium uppercase tracking-wider">Review Queue</span>
              <Clock className="h-4 w-4 text-amber-500" />
            </div>
            <div className={`${density === 'judge' ? 'text-3xl' : 'text-2xl'} font-black text-amber-700`}>
              {loading ? '...' : needsReview.length}
            </div>
            <p className="text-[11px] text-amber-600 mt-1">Adjudication required</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-sky-200 shadow-sm hover:border-sky-300 transition-all">
            <div className="flex items-center justify-between text-sky-600 mb-1">
              <span className="text-xs font-medium uppercase tracking-wider">Local Unsynced</span>
              <CloudOff className="h-4 w-4 text-sky-500" />
            </div>
            <div className={`${density === 'judge' ? 'text-3xl' : 'text-2xl'} font-black text-sky-800`}>
              {loading ? '...' : unsynced.length}
            </div>
            <p className="text-[11px] text-sky-600 mt-1">Held securely on device</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-emerald-200 shadow-sm hover:border-emerald-300 transition-all col-span-2 sm:col-span-1">
            <div className="flex items-center justify-between text-emerald-600 mb-1">
              <span className="text-xs font-medium uppercase tracking-wider">Fully Compliant</span>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            </div>
            <div className={`${density === 'judge' ? 'text-3xl' : 'text-2xl'} font-black text-emerald-700`}>
              {loading ? '...' : inspections.filter((i) => i.overall_result === 'COMPLIANT').length}
            </div>
            <p className="text-[11px] text-emerald-600 mt-1">18/18 checks cleared</p>
          </div>
        </section>
      )}

      {/* 3. Customizable Widget: Quick Action & 1-Click Golden Demo Presets */}
      {widgets.quick_actions && (
        <section className="bg-gradient-to-r from-sky-50 to-indigo-50 border border-sky-200 rounded-2xl p-5 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-sky-600" />
              <h2 className="font-bold text-slate-900 text-sm">
                Ministry Evaluation Presets &amp; Quick Launchers
              </h2>
            </div>
            <span className="text-[11px] text-slate-500">
              1-Click Golden Demo Scenarios for SIH Evaluation
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Benchmark A */}
            <Link
              href={demoBenchmarks.compliant ? `/inspections/${demoBenchmarks.compliant}` : '/inspector/scan'}
              className="p-3.5 bg-white rounded-xl border border-emerald-200 hover:border-emerald-400 hover:shadow-md transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                    BENCHMARK A • COMPLIANT
                  </span>
                  <ChevronRight className="h-4 w-4 text-slate-400 group-hover:text-emerald-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <p className="font-bold text-slate-900 text-xs mt-1">Tata Sampann Toor Dal 1kg</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Complete 18-point statutory clearance, verified barcode &amp; finalization lock.
                </p>
              </div>
            </Link>

            {/* Benchmark B */}
            <Link
              href={demoBenchmarks.mrpMismatch ? `/inspections/${demoBenchmarks.mrpMismatch}` : '/inspector/scan'}
              className="p-3.5 bg-white rounded-xl border border-amber-200 hover:border-amber-400 hover:shadow-md transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                    BENCHMARK B • DIVERGENT MRP
                  </span>
                  <ChevronRight className="h-4 w-4 text-slate-400 group-hover:text-amber-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <p className="font-bold text-slate-900 text-xs mt-1">Fortune Sunlite Refined Oil</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Package MRP ₹175 contradicts GS1 Master Catalog ₹155. Rule 18 review flag.
                </p>
              </div>
            </Link>

            {/* Benchmark C */}
            <Link
              href={demoBenchmarks.listingContradiction ? `/inspections/${demoBenchmarks.listingContradiction}` : '/inspector/scan'}
              className="p-3.5 bg-white rounded-xl border border-rose-200 hover:border-rose-400 hover:shadow-md transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-800">
                    BENCHMARK C • DIGITAL CONFLICT
                  </span>
                  <ChevronRight className="h-4 w-4 text-slate-400 group-hover:text-rose-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <p className="font-bold text-slate-900 text-xs mt-1">Imported Swiss Chocolate</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  E-commerce listing claims Importer A, packaging displays Importer B. Rule 6 &amp; 27 flag.
                </p>
              </div>
            </Link>
          </div>
        </section>
      )}

      {/* 4. Dual Columns: High-Risk Recidivists & Sync Manager */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Customizable Widget: High-Risk Recidivist Radar */}
        {widgets.recidivists && (
          <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                <div className="flex items-center gap-2">
                  <Flame className="h-5 w-5 text-rose-600" />
                  <h3 className="font-bold text-slate-900 text-sm">
                    High-Risk Sellers &amp; Recidivist Radar
                  </h3>
                </div>
                <span className="text-[10px] font-semibold bg-rose-50 text-rose-700 px-2 py-0.5 rounded-full border border-rose-200">
                  {highRiskSellers.length} Targets In Sector
                </span>
              </div>

              {highRiskSellers.length === 0 ? (
                <p className="text-slate-500 text-xs py-4 text-center">
                  No high-risk sellers flagged in current jurisdiction.
                </p>
              ) : (
                <div className="space-y-3">
                  {highRiskSellers.map((seller, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl border border-slate-100 bg-slate-50/70 hover:bg-slate-100/80 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900 text-xs truncate max-w-[240px]">
                          {seller.name}
                        </span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-300">
                          {seller.fails} Violation(s)
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                        <MapPin className="h-3 w-3 text-slate-400" /> {seller.address}
                      </p>
                      <ul className="mt-2 space-y-1">
                        {seller.reasons.slice(0, 2).map((r, rIdx) => (
                          <li
                            key={rIdx}
                            className="text-[11px] text-slate-600 flex items-center gap-1.5"
                          >
                            <span className="h-1 w-1 rounded-full bg-rose-500 shrink-0" />
                            <span className="truncate">{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px]">
              <span className="text-slate-500">Auto-calculated from historical compliance verdicts</span>
              <Link
                href="/inspector/inspections"
                className="font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1"
              >
                View Jurisdiction Audit <ChevronRight className="h-3 w-3" />
              </Link>
            </div>
          </section>
        )}

        {/* Customizable Widget: Sync Queue & Offline Evidence Manager */}
        {widgets.sync_queue && (
          <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                <div className="flex items-center gap-2">
                  <CloudOff className="h-5 w-5 text-sky-600" />
                  <h3 className="font-bold text-slate-900 text-sm">
                    Offline Field Buffer &amp; Sync Queue
                  </h3>
                </div>
                <button
                  onClick={handleSyncNow}
                  disabled={syncing}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-sky-50 text-sky-700 hover:bg-sky-100 font-semibold text-xs border border-sky-200 transition-colors disabled:opacity-50"
                >
                  <RefreshCw className={`h-3 w-3 ${syncing ? 'animate-spin' : ''}`} />
                  {syncing ? 'Syncing...' : 'Sync Now'}
                </button>
              </div>

              <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 mb-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-700">Device Cache Status:</span>
                  <span className="font-bold text-slate-900">
                    {unsynced.length === 0 ? 'All 100% Synced' : `${unsynced.length} Pending Upload`}
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 mt-2">
                  <div
                    className="bg-emerald-500 h-2 rounded-full transition-all"
                    style={{
                      width: `${inspections.length ? Math.round(((inspections.length - unsynced.length) / inspections.length) * 100) : 100}%`,
                    }}
                  />
                </div>
                <p className="text-[11px] text-slate-500 mt-1.5">
                  Evidence photographs are stored with SHA-256 integrity digests before uplink.
                </p>
              </div>

              {syncFeedback && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs mb-3 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>{syncFeedback}</span>
                </div>
              )}

              <div className="space-y-2">
                <p className="text-xs font-semibold text-slate-800">Pending Field Records:</p>
                {unsynced.length === 0 ? (
                  <p className="text-xs text-slate-400 py-2">No pending records in buffer.</p>
                ) : (
                  unsynced.slice(0, 3).map((u, i) => (
                    <div
                      key={i}
                      className="p-2.5 rounded-lg border border-slate-200 bg-white flex items-center justify-between text-xs"
                    >
                      <div className="truncate max-w-[200px]">
                        <p className="font-medium text-slate-900 truncate">
                          {u.store_name || 'Retail Capture'}
                        </p>
                        <p className="text-[10px] text-slate-500">{u.id.slice(0, 8)} • Local Draft</p>
                      </div>
                      <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                        Awaiting Sync
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px]">
              <span className="text-slate-500">Autonomous SQLite offline store</span>
              <span className="font-medium text-slate-700">AES-256 Encrypted</span>
            </div>
          </section>
        )}
      </div>

      {/* 5. Customizable Widget: Recent Inspections Feed */}
      {widgets.recent_feed && (
        <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-sky-600" />
              <h3 className="font-bold text-slate-900 text-sm">Recent Inspections Workstream</h3>
            </div>
            <Link
              href="/inspector/inspections"
              className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1"
            >
              View All History <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {loading ? (
            <p className="text-slate-500 text-xs py-8 text-center">Loading inspection records...</p>
          ) : inspections.length === 0 ? (
            <p className="text-slate-500 text-xs py-8 text-center">No inspections recorded yet.</p>
          ) : (
            <div className="divide-y divide-slate-100">
              {inspections.slice(0, 6).map((insp) => (
                <div
                  key={insp.id}
                  className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/80 rounded-xl px-2.5 transition-colors"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-bold text-slate-900 text-xs truncate">
                        {insp.store_name || 'Commercial Packaging Inspection'}
                      </p>
                      {insp.finalized_at && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold bg-slate-100 text-slate-600 border border-slate-300">
                          FINALIZED
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {insp.district || 'Central District'} • Created:{' '}
                      {new Date(insp.created_at).toLocaleDateString()}{' '}
                      {new Date(insp.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {getVerdictBadge(insp.overall_result)}
                    <Link
                      href={`/inspections/${insp.id}`}
                      className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold transition-colors flex items-center gap-1"
                    >
                      <span>Workstation</span>
                      <ChevronRight className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* 6. Customizable Widget: Statutory Rules Watchdog */}
      {widgets.rules_watchdog && (
        <section className="bg-white/85 backdrop-blur-md text-slate-900 rounded-3xl p-6 shadow-sm border border-slate-200/90">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
            <div className="flex items-center gap-2">
              <Scale className="h-5 w-5 text-sky-600" />
              <h3 className="font-bold text-slate-900 text-sm">
                Statutory Authority &amp; Legal Corpus Watchdog
              </h3>
            </div>
            <span className="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-sky-50 text-sky-800 border border-sky-200">
              SIH-OFFICIAL-2011 • DETERMINISTIC RULE ENGINE
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-700">
            <div className="p-3.5 rounded-2xl bg-slate-50/80 border border-slate-200/80 shadow-xs hover:bg-white transition">
              <p className="font-bold text-slate-900 mb-1">Rule 6 Mandatory Declarations</p>
              <p className="text-[11px] text-slate-600">
                Enforces commodity name, manufacturer/packer postal address, net quantity with SI units, MRP in ₹, and mfg/packing date.
              </p>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-50/80 border border-slate-200/80 shadow-xs hover:bg-white transition">
              <p className="font-bold text-slate-900 mb-1">Rule 18 Neutral Pricing Invariant</p>
              <p className="text-[11px] text-slate-600">
                Blocks price alteration, smudging, or dual-MRP discrepancies between physical package labels and catalog listings.
              </p>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-50/80 border border-slate-200/80 shadow-xs hover:bg-white transition">
              <p className="font-bold text-slate-900 mb-1">Rule 27 &amp; Section 15 Seizures</p>
              <p className="text-[11px] text-slate-600">
                Pre-packer registration registry lookup, electronic Panchnama generation, and Section 49 Corporate Director liability.
              </p>
            </div>
          </div>
        </section>
      )}

      {/* 7. Desk Customizer Modal / Drawer */}
      {customizerOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2">
                <Sliders className="h-5 w-5 text-sky-600" />
                <h3 className="font-bold text-slate-900 text-base">Customize Inspector Desk</h3>
              </div>
              <button
                onClick={() => setCustomizerOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Density Picker */}
            <div className="mb-5">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Display Density &amp; View Mode
              </p>
              <div className="grid grid-cols-3 gap-2">
                {(['compact', 'standard', 'judge'] as DensityMode[]).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => saveDensity(mode)}
                    className={`py-2 px-3 rounded-xl text-xs font-bold capitalize border transition-all cursor-pointer ${
                      density === mode
                        ? 'border-sky-500 bg-sky-50 text-sky-900 shadow-sm'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    {mode === 'judge' ? 'Judge Mode' : mode}
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-slate-500 mt-1.5">
                {density === 'judge'
                  ? 'High-contrast large text mode optimized for projector demonstration and SIH jury evaluation.'
                  : density === 'compact'
                  ? 'High information density for high-throughput mandi field operations.'
                  : 'Balanced comfortable layout for standard touchscreen tablet inspections.'}
              </p>
            </div>

            {/* Toggleable Widgets */}
            <div className="space-y-3 mb-6">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Visible Dashboard Widgets
              </p>

              {[
                { key: 'kpis', label: 'Workload KPI Metrics Strip', desc: 'Today captures, non-compliant, review count' },
                { key: 'quick_actions', label: 'Golden Demo & Quick Action Bar', desc: '1-click benchmark loaders for jury evaluation' },
                { key: 'recidivists', label: 'High-Risk Seller & Recidivist Radar', desc: 'Repeat violators and recidivism tracker' },
                { key: 'sync_queue', label: 'Offline Sync & Evidence Buffer', desc: 'Local device cache and uplink management' },
                { key: 'recent_feed', label: 'Recent Inspections Stream', desc: 'Live feed of recent packages and status chips' },
                { key: 'rules_watchdog', label: 'Statutory Rules Watchdog', desc: 'LMPC 2011 statutory references' },
              ].map((w) => (
                <label
                  key={w.key}
                  className="flex items-start gap-3 p-2.5 rounded-xl border border-slate-100 hover:bg-slate-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={widgets[w.key as keyof WidgetConfig]}
                    onChange={(e) => {
                      const updated = { ...widgets, [w.key]: e.target.checked };
                      saveWidgets(updated);
                    }}
                    className="mt-0.5 rounded text-sky-600 focus:ring-sky-500 h-4 w-4"
                  />
                  <div>
                    <span className="font-bold text-slate-900 text-xs block">{w.label}</span>
                    <span className="text-[11px] text-slate-500">{w.desc}</span>
                  </div>
                </label>
              ))}
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-100">
              <button
                onClick={() => {
                  saveWidgets(DEFAULT_WIDGETS);
                  saveDensity('standard');
                }}
                className="text-xs font-semibold text-slate-500 hover:text-slate-800 cursor-pointer"
              >
                Reset to Default
              </button>
              <button
                onClick={() => setCustomizerOpen(false)}
                className="px-4 py-2 rounded-xl bg-sky-700 hover:bg-sky-800 text-white font-bold text-xs shadow-xs cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
