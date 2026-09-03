'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { ComplianceResult, Inspection, InspectionStatus } from '@/types';
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
} from 'lucide-react';

export default function InspectionsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [seedingDemo, setSeedingDemo] = useState(false);
  const [demoFeedback, setDemoFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [resultFilter, setResultFilter] = useState<string>('');

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
      await fetchInspections();
      setTimeout(() => setDemoFeedback(null), 5000);
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
      }
    }
  }, [authLoading, user, statusFilter, resultFilter]);

  const filteredInspections = inspections.filter((insp) => {
    const store = (insp.store_name || '').toLowerCase();
    const district = (insp.district || '').toLowerCase();
    const state = (insp.state || '').toLowerCase();
    const q = searchTerm.toLowerCase();
    return store.includes(q) || district.includes(q) || state.includes(q) || insp.id.includes(q);
  });

  const getResultBadge = (result: ComplianceResult) => {
    switch (result) {
      case 'COMPLIANT':
        return (
          <span className="bg-emerald-50 text-emerald-700 border border-emerald-300 font-bold px-2.5 py-1 rounded-full text-[11px] flex items-center gap-1">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" /> COMPLIANT
          </span>
        );
      case 'NON_COMPLIANT':
        return (
          <span className="bg-rose-50 text-rose-700 border border-rose-300 font-bold px-2.5 py-1 rounded-full text-[11px] flex items-center gap-1">
            <ShieldAlert className="h-3.5 w-3.5 text-rose-600" /> NON-COMPLIANT
          </span>
        );
      case 'NEEDS_REVIEW':
        return (
          <span className="bg-amber-50 text-amber-700 border border-amber-300 font-bold px-2.5 py-1 rounded-full text-[11px] flex items-center gap-1">
            <Clock className="h-3.5 w-3.5 text-amber-600" /> NEEDS REVIEW
          </span>
        );
      default:
        return (
          <span className="bg-slate-100 text-slate-700 border border-slate-300 font-bold px-2.5 py-1 rounded-full text-[11px] flex items-center gap-1">
            PENDING
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <ClipboardList className="h-6 w-6 text-brand-900" />
            Field Inspections Repository
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            MetrologyMitra — Compliance verification cases under Legal Metrology (Packaged Commodities) Rules, 2011.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleSeedDemoPresets}
            disabled={seedingDemo}
            className="px-3 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-bold rounded-xl transition flex items-center gap-1.5 disabled:opacity-50"
            title="Seed 7 Controlled Demo Case Presets"
          >
            <Sparkles className={`h-3.5 w-3.5 ${seedingDemo ? 'animate-spin' : 'text-indigo-600'}`} />
            {seedingDemo ? 'Seeding Presets...' : 'Load 7 Demo Presets'}
          </button>

          <button
            onClick={fetchInspections}
            className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors text-xs font-semibold flex items-center gap-1.5"
            title="Refresh List"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <a
            href="/inspections/new"
            className="bg-brand-900 hover:bg-brand-800 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow transition-colors flex items-center gap-1.5"
          >
            <PlusCircle className="h-4 w-4" />
            New Inspection
          </a>
        </div>
      </div>

      {demoFeedback && (
        <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-xl text-xs text-indigo-800 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-indigo-600 shrink-0" />
          <span><strong>Demo Fixtures:</strong> {demoFeedback}</span>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex flex-col md:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="h-4 w-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by store name, district, state, or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400 hidden sm:block" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none font-medium"
          >
            <option value="">All Statuses</option>
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
            <option value="">All Verdicts</option>
            <option value="COMPLIANT">COMPLIANT</option>
            <option value="NON_COMPLIANT">NON-COMPLIANT</option>
            <option value="NEEDS_REVIEW">NEEDS REVIEW</option>
            <option value="PENDING">PENDING</option>
          </select>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Table / List */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-xs text-slate-500 flex flex-col items-center justify-center">
            <RefreshCw className="h-8 w-8 text-sky-600 animate-spin mb-3" />
            <span>Loading inspection records...</span>
          </div>
        ) : filteredInspections.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-500 flex flex-col items-center justify-center">
            <ClipboardList className="h-10 w-10 text-slate-300 mb-3" />
            <p className="font-semibold text-slate-700 text-sm">No inspection records found</p>
            <p className="text-slate-400 mt-1 max-w-sm">
              No inspections match your search filters. Click &quot;Load 7 Demo Presets&quot; or &quot;New Inspection&quot; to begin.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-4 py-3.5">Store / Establishment</th>
                  <th className="px-4 py-3.5">Location</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Statutory Verdict</th>
                  <th className="px-4 py-3.5">Date Created</th>
                  <th className="px-4 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {filteredInspections.map((insp) => (
                  <tr key={insp.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-3.5">
                      <div className="font-bold text-slate-900 flex items-center gap-1.5">
                        <Building2 className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        <span>{insp.store_name || 'Unspecified Store'}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        ID: {insp.id.slice(0, 16)}...
                      </div>
                    </td>

                    <td className="px-4 py-3.5 text-slate-600">
                      <div className="flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        <span>
                          {insp.district || 'N/A'}, {insp.state || 'N/A'}
                        </span>
                      </div>
                    </td>

                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                        insp.status === 'COMPLETED'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}>
                        {insp.status}
                      </span>
                    </td>

                    <td className="px-4 py-3.5 whitespace-nowrap">
                      {getResultBadge(insp.overall_result)}
                    </td>

                    <td className="px-4 py-3.5 text-slate-500 whitespace-nowrap">
                      {new Date(insp.created_at).toLocaleDateString()} {new Date(insp.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>

                    <td className="px-4 py-3.5 text-right whitespace-nowrap">
                      <a
                        href={`/inspections/${insp.id}`}
                        className="inline-flex items-center gap-1 bg-brand-50 hover:bg-brand-100 text-brand-900 font-bold px-3 py-1.5 rounded-lg border border-brand-200 transition-colors"
                      >
                        Open Workspace <ArrowRight className="h-3.5 w-3.5" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
