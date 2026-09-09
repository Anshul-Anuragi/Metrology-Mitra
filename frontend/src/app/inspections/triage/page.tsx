'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { PriorityLevel, SupervisorTriageItem, SupervisorTriageResponse } from '@/types';
import {
  ShieldAlert,
  AlertCircle,
  CheckCircle2,
  Clock,
  Search,
  Filter,
  ArrowRight,
  RefreshCw,
  Building2,
  MapPin,
  Sparkles,
  Layers,
  ArrowLeft,
  Info,
  SlidersHorizontal,
} from 'lucide-react';

export default function SupervisorTriagePage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [triageData, setTriageData] = useState<SupervisorTriageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [resultFilter, setResultFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const fetchTriage = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSupervisorTriage({
        priority_level: priorityFilter || undefined,
        status_filter: statusFilter || undefined,
        result_filter: resultFilter || undefined,
        search: searchTerm || undefined,
      });
      setTriageData(data);
    } catch (err: any) {
      if (err?.response?.status === 403) {
        setError('Access restricted: Supervisor or Administrator role required for operational triage.');
      } else {
        setError(err?.response?.data?.detail || 'Failed to load supervisor triage queue.');
      }
    } finally {
      setLoading(false);
    }
  }, [priorityFilter, statusFilter, resultFilter, searchTerm]);

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push('/login');
      } else if (user.role === 'INSPECTOR') {
        setError('Access restricted: Field Inspectors do not have supervisory triage permissions.');
        setLoading(false);
      } else {
        fetchTriage();
      }
    }
  }, [authLoading, user, router, fetchTriage]);

  const getPriorityBadge = (level: PriorityLevel, score: number) => {
    switch (level) {
      case 'CRITICAL':
        return (
          <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1.5 animate-pulse">
            <ShieldAlert className="h-3 w-3 text-rose-400" /> CRITICAL ({score.toFixed(0)})
          </span>
        );
      case 'HIGH':
        return (
          <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1.5">
            <AlertCircle className="h-3 w-3 text-amber-400" /> HIGH ({score.toFixed(0)})
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40 flex items-center gap-1.5">
            <Info className="h-3 w-3 text-sky-400" /> MEDIUM ({score.toFixed(0)})
          </span>
        );
      case 'LOW':
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5">
            <CheckCircle2 className="h-3 w-3 text-emerald-400" /> LOW ({score.toFixed(0)})
          </span>
        );
    }
  };

  const getResultBadge = (result: string) => {
    switch (result) {
      case 'COMPLIANT':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            COMPLIANT
          </span>
        );
      case 'NON_COMPLIANT':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
            NON-COMPLIANT
          </span>
        );
      case 'NEEDS_REVIEW':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
            NEEDS REVIEW
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-700 text-slate-300">
            PENDING
          </span>
        );
    }
  };

  if (error) {
    return (
      <div className="max-w-xl mx-auto p-8 bg-white border border-slate-200 rounded-3xl text-center space-y-4 text-slate-900 shadow-sm">
        <ShieldAlert className="h-10 w-10 text-rose-600 mx-auto" />
        <h2 className="text-lg font-bold">Supervisory Access Restricted</h2>
        <p className="text-xs text-slate-500">{error}</p>
        <a
          href="/inspections"
          className="inline-flex items-center gap-1.5 bg-sky-700 hover:bg-sky-800 text-white text-xs font-bold px-4 py-2 rounded-xl transition shadow-xs"
        >
          <ArrowLeft className="h-4 w-4" /> Return to Inspections
        </a>
      </div>
    );
  }

  const items = triageData?.items || [];
  const counts = triageData?.priority_counts || {};

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-slate-900">Supervisor Operational Triage</h1>
            <span className="text-xs bg-indigo-50 text-indigo-700 font-bold px-2.5 py-0.5 rounded-full border border-indigo-200">
              Phase 2.9 Intelligence
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Prioritized case management queue ranked by statutory severity, repeat risk, and evidentiary completeness.
          </p>
        </div>

        <button
          onClick={fetchTriage}
          className="inline-flex items-center gap-2 px-4 py-2 bg-sky-700 hover:bg-sky-800 text-white font-bold text-xs rounded-xl transition shadow-xs self-start sm:self-auto cursor-pointer"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Triage
        </button>
      </div>

      {/* Priority Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div
          onClick={() => setPriorityFilter(priorityFilter === 'CRITICAL' ? '' : 'CRITICAL')}
          className={`p-4 rounded-2xl border cursor-pointer transition ${
            priorityFilter === 'CRITICAL'
              ? 'bg-rose-950 border-rose-500 shadow-md text-white'
              : 'bg-white border-slate-200 hover:border-rose-300 text-slate-900'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-rose-600">Critical Priority</span>
            <ShieldAlert className="h-4 w-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold mt-2 font-mono">{counts['CRITICAL'] || 0}</div>
          <div className="text-[10px] text-slate-500 mt-1">Severe statutory violations</div>
        </div>

        <div
          onClick={() => setPriorityFilter(priorityFilter === 'HIGH' ? '' : 'HIGH')}
          className={`p-4 rounded-2xl border cursor-pointer transition ${
            priorityFilter === 'HIGH'
              ? 'bg-amber-950 border-amber-500 shadow-md text-white'
              : 'bg-white border-slate-200 hover:border-amber-300 text-slate-900'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-600">High Priority</span>
            <AlertCircle className="h-4 w-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold mt-2 font-mono">{counts['HIGH'] || 0}</div>
          <div className="text-[10px] text-slate-500 mt-1">Unresolved reviews / non-compliance</div>
        </div>

        <div
          onClick={() => setPriorityFilter(priorityFilter === 'MEDIUM' ? '' : 'MEDIUM')}
          className={`p-4 rounded-2xl border cursor-pointer transition ${
            priorityFilter === 'MEDIUM'
              ? 'bg-sky-950 border-sky-500 shadow-md text-white'
              : 'bg-white border-slate-200 hover:border-sky-300 text-slate-900'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-sky-600">Medium Priority</span>
            <Info className="h-4 w-4 text-sky-600" />
          </div>
          <div className="text-2xl font-bold mt-2 font-mono">{counts['MEDIUM'] || 0}</div>
          <div className="text-[10px] text-slate-500 mt-1">Standard review queue</div>
        </div>

        <div
          onClick={() => setPriorityFilter(priorityFilter === 'LOW' ? '' : 'LOW')}
          className={`p-4 rounded-2xl border cursor-pointer transition ${
            priorityFilter === 'LOW'
              ? 'bg-emerald-950 border-emerald-500 shadow-md text-white'
              : 'bg-white border-slate-200 hover:border-emerald-300 text-slate-900'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-600">Low Priority</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold mt-2 font-mono">{counts['LOW'] || 0}</div>
          <div className="text-[10px] text-slate-500 mt-1">Compliant & verified</div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-1 max-w-md">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search store, district, state, or manufacturer..."
            className="w-full bg-transparent text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs font-medium text-slate-700"
          >
            <option value="">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs font-medium text-slate-700"
          >
            <option value="">All Statuses</option>
            <option value="CREATED">Created</option>
            <option value="REVIEW_REQUIRED">Review Required</option>
            <option value="COMPLETED">Completed</option>
          </select>

          <select
            value={resultFilter}
            onChange={(e) => setResultFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs font-medium text-slate-700"
          >
            <option value="">All Legal Results</option>
            <option value="COMPLIANT">Compliant</option>
            <option value="NON_COMPLIANT">Non-Compliant</option>
            <option value="NEEDS_REVIEW">Needs Review</option>
            <option value="PENDING">Pending</option>
          </select>
        </div>
      </div>

      {/* Triage Queue Table */}
      <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl shadow-sm overflow-hidden text-slate-900">
        <div className="p-4 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-sky-600" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Triage Queue ({items.length} items)
            </h3>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Sorted by Priority Score &amp; Urgency</span>
        </div>

        {loading ? (
          <div className="py-16 text-center text-xs text-slate-500 flex flex-col items-center justify-center">
            <RefreshCw className="h-6 w-6 text-sky-600 animate-spin mb-2" />
            <span>Calculating dynamic case intelligence...</span>
          </div>
        ) : items.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-500">
            No inspection cases match the selected triage filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-[10px] text-slate-600 font-bold uppercase tracking-wider">
                  <th className="py-3.5 px-4">Priority &amp; Score</th>
                  <th className="py-3.5 px-4">Establishment / Commodity</th>
                  <th className="py-3.5 px-4">Legal Result</th>
                  <th className="py-3.5 px-4">Completeness</th>
                  <th className="py-3.5 px-4">Primary Attention Reason</th>
                  <th className="py-3.5 px-4">Inspector</th>
                  <th className="py-3.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((row) => (
                  <tr key={row.inspection_id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-4 whitespace-nowrap">
                      {getPriorityBadge(row.priority_level, row.priority_score)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">
                        {row.store_name || 'Retail Establishment'}
                      </div>
                      <div className="text-[10px] text-slate-500">
                        {row.commodity_name || row.entity_name || 'Commodity Unspecified'} • {row.district || 'District N/A'}, {row.state || 'DL'}
                      </div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {getResultBadge(row.overall_result)}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] font-bold text-slate-700">
                          {row.evidence_completeness_score.toFixed(0)}%
                        </span>
                        <div className="w-12 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              row.evidence_completeness_score >= 80
                                ? 'bg-emerald-600'
                                : row.evidence_completeness_score >= 50
                                ? 'bg-amber-500'
                                : 'bg-rose-500'
                            }`}
                            style={{ width: `${row.evidence_completeness_score}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-[11px] text-amber-800 font-bold">
                        {row.primary_attention_reason}
                      </span>
                      {row.violation_count > 0 && (
                        <div className="text-[10px] text-rose-700 font-semibold">
                          {row.violation_count} statutory violation(s)
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4 text-[11px] text-slate-600 whitespace-nowrap">
                      {row.inspector_name || 'Field Officer'}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <a
                        href={`/inspections/${row.inspection_id}`}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-sky-700 hover:bg-sky-800 text-white rounded-xl text-[11px] font-bold transition shadow-xs cursor-pointer"
                      >
                        Review Case <ArrowRight className="h-3 w-3" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="p-3.5 border-t border-slate-100 bg-slate-50/80 text-[10px] text-slate-500 italic flex items-center gap-1.5">
          <Info className="h-3 w-3 text-slate-400 shrink-0" />
          {triageData?.disclaimer || 'Operational supervisor triage queue. Does not alter underlying statutory inspection determinations.'}
        </div>
      </div>
    </div>
  );
}

