'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import {
  AnalyticsFailingRules,
  AnalyticsHeatmaps,
  AnalyticsOverview,
  AnalyticsRepeatOffenders,
  AnalyticsTrends,
} from '@/types';
import {
  BarChart3,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Users,
  MapPin,
  TrendingUp,
  Building2,
  Calendar,
  Layers,
  Lock,
  RefreshCw,
} from 'lucide-react';

export default function AnalyticsPage() {
  const { user, loading: authLoading, isSupervisor } = useAuth();
  const router = useRouter();

  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [trends, setTrends] = useState<AnalyticsTrends | null>(null);
  const [heatmaps, setHeatmaps] = useState<AnalyticsHeatmaps | null>(null);
  const [repeatOffenders, setRepeatOffenders] = useState<AnalyticsRepeatOffenders | null>(null);
  const [failingRules, setFailingRules] = useState<AnalyticsFailingRules | null>(null);

  const [trendPeriod, setTrendPeriod] = useState<'monthly' | 'weekly' | 'daily'>('monthly');
  const [stateFilter, setStateFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalyticsData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovData, trData, hmData, roData, frData] = await Promise.all([
        api.getAnalyticsOverview(),
        api.getAnalyticsTrends(trendPeriod),
        api.getAnalyticsHeatmaps(stateFilter || undefined),
        api.getAnalyticsRepeatOffenders(10),
        api.getAnalyticsFailingRules(20),
      ]);
      setOverview(ovData);
      setTrends(trData);
      setHeatmaps(hmData);
      setRepeatOffenders(roData);
      setFailingRules(frData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load supervisor analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push('/login');
      } else if (isSupervisor) {
        fetchAnalyticsData();
      }
    }
  }, [authLoading, user, isSupervisor, trendPeriod, stateFilter]);

  // RBAC Access Restriction View for Inspectors
  if (!authLoading && user && !isSupervisor) {
    return (
      <div className="max-w-lg mx-auto my-16 bg-white p-8 rounded-2xl shadow border border-slate-200 text-center space-y-4">
        <div className="p-3 bg-rose-50 text-rose-600 rounded-full w-fit mx-auto">
          <Lock className="h-8 w-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Access Restricted (403 Forbidden)</h2>
        <p className="text-xs text-slate-500">
          The macro-level analytics portal and enforcement heatmaps are restricted to <b>Supervisors</b> and <b>Administrators</b> only.
        </p>
        <a
          href="/inspections"
          className="inline-block bg-brand-900 text-white font-semibold text-xs px-5 py-2.5 rounded-xl shadow transition-colors"
        >
          Return to My Inspections
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-brand-900" />
            Supervisor Analytics & Violation Intelligence
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Aggregated statutory compliance metrics, regional risk heatmaps, and recurring non-compliance tracking across all field inspections.
          </p>
        </div>

        <button
          onClick={fetchAnalyticsData}
          className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors text-xs font-semibold flex items-center gap-1.5 w-fit"
          title="Refresh Analytics"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 1. High-Level KPI Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* Total Inspections */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Total Scans</div>
          <div className="text-2xl font-black text-slate-900 mt-1">
            {overview?.total_inspections ?? 0}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Packaged commodity sessions</div>
        </div>

        {/* Compliance Rate */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider flex items-center gap-1">
            <ShieldCheck className="h-3.5 w-3.5" /> Compliance Rate
          </div>
          <div className="text-2xl font-black text-emerald-600 mt-1">
            {overview?.compliance_rate_percent ?? 0}%
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">
            {overview?.compliant_inspections ?? 0} compliant scans
          </div>
        </div>

        {/* Total Violations */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div className="text-[11px] font-bold text-rose-700 uppercase tracking-wider flex items-center gap-1">
            <ShieldAlert className="h-3.5 w-3.5" /> Total Violations
          </div>
          <div className="text-2xl font-black text-rose-600 mt-1">
            {overview?.total_violations ?? 0}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">LMPC statutory infractions</div>
        </div>

        {/* High / Critical Severity */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div className="text-[11px] font-bold text-amber-700 uppercase tracking-wider flex items-center gap-1">
            <AlertTriangle className="h-3.5 w-3.5" /> High Severity
          </div>
          <div className="text-2xl font-black text-amber-600 mt-1">
            {overview?.high_or_critical_violations ?? 0}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Missing MRP / Net Quantity</div>
        </div>

        {/* Active Inspectors */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 col-span-2 md:col-span-1">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
            <Users className="h-3.5 w-3.5" /> Active Officers
          </div>
          <div className="text-2xl font-black text-slate-900 mt-1">
            {overview?.active_inspecting_officers ?? 0}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">In field operations</div>
        </div>
      </div>

      {/* 2. Temporal Compliance Trends */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-brand-900" />
            Inspection & Violation Trends Over Time
          </h2>

          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
            {(['monthly', 'weekly', 'daily'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setTrendPeriod(p)}
                className={`px-3 py-1 rounded-md text-xs font-semibold uppercase tracking-wider transition-all ${
                  trendPeriod === p
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Time-series Table / Representation */}
        {trends && trends.data_points.length > 0 ? (
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-4 py-3">Time Interval</th>
                  <th className="px-4 py-3">Total Scans</th>
                  <th className="px-4 py-3">Compliant</th>
                  <th className="px-4 py-3">Non-Compliant</th>
                  <th className="px-4 py-3">Needs Review</th>
                  <th className="px-4 py-3">Violations Logged</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {trends.data_points.map((pt, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-4 py-2.5 font-mono font-bold text-slate-800">{pt.period_start}</td>
                    <td className="px-4 py-2.5 font-bold">{pt.total_inspections}</td>
                    <td className="px-4 py-2.5 text-emerald-600 font-semibold">{pt.compliant_count}</td>
                    <td className="px-4 py-2.5 text-rose-600 font-semibold">{pt.non_compliant_count}</td>
                    <td className="px-4 py-2.5 text-amber-600 font-semibold">{pt.needs_review_count}</td>
                    <td className="px-4 py-2.5 text-slate-700 font-mono font-bold">{pt.violation_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-slate-400">No trend data available.</div>
        )}
      </div>

      {/* 3. Regional Violation Heatmaps & Failing Rules */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Heatmaps */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
          <div className="flex justify-between items-center pb-3 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <MapPin className="h-4 w-4 text-brand-900" />
              Regional Violation Density ({heatmaps?.total_regions ?? 0} Regions)
            </h2>

            <input
              type="text"
              placeholder="Filter state (e.g. DL, MH)"
              value={stateFilter}
              onChange={(e) => setStateFilter(e.target.value)}
              className="text-xs px-2.5 py-1 bg-slate-50 border border-slate-300 rounded-lg w-36 uppercase font-mono"
            />
          </div>

          <div className="border border-slate-200 rounded-xl overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-3.5 py-2.5">Region</th>
                  <th className="px-3.5 py-2.5">Scans</th>
                  <th className="px-3.5 py-2.5">Violations</th>
                  <th className="px-3.5 py-2.5">Non-Compliance %</th>
                  <th className="px-3.5 py-2.5">GPS Anchor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {heatmaps?.clusters.map((c, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-3.5 py-2.5 font-bold text-slate-800">
                      {c.district}, <span className="font-mono text-slate-500">{c.state}</span>
                    </td>
                    <td className="px-3.5 py-2.5">{c.inspection_count}</td>
                    <td className="px-3.5 py-2.5 font-mono text-rose-600 font-bold">{c.violation_count}</td>
                    <td className="px-3.5 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          c.non_compliance_rate_percent > 50
                            ? 'bg-rose-100 text-rose-800'
                            : c.non_compliance_rate_percent > 0
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {c.non_compliance_rate_percent}%
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-[11px] text-slate-400 font-mono">
                      {c.has_gps_coordinates && c.latitude && c.longitude
                        ? `${c.latitude.toFixed(2)}, ${c.longitude.toFixed(2)}`
                        : 'Location Unavailable'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Failing Statutory Rules */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 pb-3 border-b border-slate-100">
            <ShieldAlert className="h-4 w-4 text-rose-600" />
            Most Frequently Violated LMPC Rules
          </h2>

          <div className="space-y-2.5">
            {failingRules?.failing_rules.map((rule) => (
              <div
                key={rule.rule_code}
                className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-3"
              >
                <div>
                  <div className="font-mono font-bold text-slate-900 text-xs flex items-center gap-2">
                    {rule.rule_code}
                    <span className="text-[10px] font-normal text-slate-500 truncate max-w-[200px]">
                      {rule.statutory_reference}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5">{rule.title}</p>
                </div>

                <div className="text-right shrink-0">
                  <div className="text-sm font-black text-rose-600">{rule.failure_count} fails</div>
                  <div className="text-[10px] text-slate-400 font-bold">{rule.failure_percentage}% of fails</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 4. Recurring Non-Compliance Intelligence (Top Entities) */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 pb-3 border-b border-slate-100">
          <Building2 className="h-4 w-4 text-brand-900" />
          Recurring Non-Compliance Intelligence (Top Entities)
        </h2>

        <div className="border border-slate-200 rounded-xl overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
            <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-4 py-3">Manufacturer / Brand Entity</th>
                <th className="px-4 py-3">Scans Conducted</th>
                <th className="px-4 py-3">Non-Compliant Scans</th>
                <th className="px-4 py-3">Violations Logged</th>
                <th className="px-4 py-3">Recurrence Rate</th>
                <th className="px-4 py-3">Top Failing Rule Codes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {repeatOffenders?.entities.map((entity, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-bold text-slate-900">{entity.entity_name}</td>
                  <td className="px-4 py-3">{entity.inspection_count}</td>
                  <td className="px-4 py-3 text-rose-600 font-semibold">{entity.non_compliant_inspection_count}</td>
                  <td className="px-4 py-3 font-mono font-bold">{entity.violation_count}</td>
                  <td className="px-4 py-3">
                    <span className="bg-rose-50 text-rose-700 border border-rose-200 font-bold px-2 py-0.5 rounded text-[11px]">
                      {entity.recurrence_rate_percent}%
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {entity.common_failed_rule_codes.map((rc) => (
                        <span
                          key={rc}
                          className="bg-slate-100 text-slate-700 font-mono text-[10px] px-1.5 py-0.5 rounded border border-slate-200"
                        >
                          {rc}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

