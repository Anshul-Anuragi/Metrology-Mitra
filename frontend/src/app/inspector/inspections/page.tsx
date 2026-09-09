'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Inspection, ComplianceResult } from '@/types';
import {
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ChevronRight,
  FileText,
  Lock,
  RotateCcw,
  PlusCircle,
  MapPin,
  Sparkles,
  Download,
} from 'lucide-react';

type FilterTab = 'ALL' | 'COMPLIANT' | 'NON_COMPLIANT' | 'NEEDS_REVIEW' | 'FINALIZED' | 'UNSYNCED';

export default function InspectorInspectionsListPage() {
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<FilterTab>('ALL');

  useEffect(() => {
    async function fetchInspections() {
      setLoading(true);
      try {
        const data = await api.getInspections();
        setInspections(data);
      } catch (err) {
        console.error('Failed to fetch inspections:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchInspections();
  }, []);

  const filteredInspections = useMemo(() => {
    return inspections.filter((insp) => {
      // Tab filter
      if (activeTab === 'COMPLIANT' && insp.overall_result !== 'COMPLIANT') return false;
      if (activeTab === 'NON_COMPLIANT' && insp.overall_result !== 'NON_COMPLIANT') return false;
      if (activeTab === 'NEEDS_REVIEW' && insp.overall_result !== 'NEEDS_REVIEW') return false;
      if (activeTab === 'FINALIZED' && !insp.finalized_at) return false;
      if (activeTab === 'UNSYNCED' && (insp.geo_verified || insp.synced_at)) return false;

      // Text search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const store = (insp.store_name || '').toLowerCase();
        const address = (insp.store_address || '').toLowerCase();
        const district = (insp.district || '').toLowerCase();
        const id = insp.id.toLowerCase();
        const commodity = (insp.declaration?.commodity_name || '').toLowerCase();
        return store.includes(q) || address.includes(q) || district.includes(q) || id.includes(q) || commodity.includes(q);
      }

      return true;
    });
  }, [inspections, activeTab, searchQuery]);

  const stats = useMemo(() => {
    const total = inspections.length;
    const compliant = inspections.filter((i) => i.overall_result === 'COMPLIANT').length;
    const nonCompliant = inspections.filter((i) => i.overall_result === 'NON_COMPLIANT').length;
    const review = inspections.filter((i) => i.overall_result === 'NEEDS_REVIEW').length;
    const finalized = inspections.filter((i) => !!i.finalized_at).length;
    const rate = total > 0 ? Math.round((compliant / total) * 100) : 0;
    return { total, compliant, nonCompliant, review, finalized, rate };
  }, [inspections]);

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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Inspection History</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-slate-100 text-slate-700 border border-slate-300">
              {inspections.length} Total Records
            </span>
          </div>
          <p className="text-slate-500 text-xs mt-1">
            Searchable log of pre-packaged commodity evaluations with statutory rule traceability.
          </p>
        </div>

        <Link
          href="/inspector/scan"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold shadow-md transition-all self-start sm:self-auto"
        >
          <PlusCircle className="h-4 w-4" />
          New Field Scan
        </Link>
      </div>

      {/* KPI Stats Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Compliance Rate</span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">{stats.rate}%</span>
          <span className="text-[11px] text-emerald-600 font-medium">{stats.compliant} verified compliant</span>
        </div>
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Violations Flagged</span>
          <span className="text-2xl font-black text-rose-700 mt-1 block">{stats.nonCompliant}</span>
          <span className="text-[11px] text-rose-600 font-medium">Statutory infractions</span>
        </div>
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Awaiting Adjudication</span>
          <span className="text-2xl font-black text-amber-700 mt-1 block">{stats.review}</span>
          <span className="text-[11px] text-amber-600 font-medium">Requires officer decision</span>
        </div>
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Finalized &amp; Sealed</span>
          <span className="text-2xl font-black text-slate-800 mt-1 block">{stats.finalized}</span>
          <span className="text-[11px] text-slate-500 font-medium">Cryptographic lock active</span>
        </div>
      </div>

      {/* Search & Filter Tabs */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by store name, address, commodity, or inspection ID..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          {(
            [
              { id: 'ALL', label: 'All Records', count: inspections.length },
              { id: 'COMPLIANT', label: 'Compliant', count: stats.compliant },
              { id: 'NON_COMPLIANT', label: 'Non-Compliant', count: stats.nonCompliant },
              { id: 'NEEDS_REVIEW', label: 'Officer Review', count: stats.review },
              { id: 'FINALIZED', label: 'Finalized', count: stats.finalized },
            ] as { id: FilterTab; label: string; count: number }[]
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all flex items-center gap-1.5 ${
                activeTab === tab.id
                  ? 'bg-sky-700 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <span>{tab.label}</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === tab.id ? 'bg-sky-800 text-sky-100' : 'bg-slate-200 text-slate-600'
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Inspections List */}
      <div className="space-y-3">
        {loading ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-slate-200 text-slate-500 text-xs">
            Loading inspection records...
          </div>
        ) : filteredInspections.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
            <p className="text-sm font-semibold text-slate-800">No inspections found</p>
            <p className="text-xs text-slate-500 mt-1">
              No inspection records match your current filter or search criteria.
            </p>
            <button
              onClick={() => {
                setActiveTab('ALL');
                setSearchQuery('');
              }}
              className="mt-4 inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700"
            >
              <RotateCcw className="h-3.5 w-3.5" /> Reset Filters
            </button>
          </div>
        ) : (
          filteredInspections.map((insp) => (
            <div
              key={insp.id}
              className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm hover:border-slate-300 hover:shadow-md transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="min-w-0 space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-bold text-slate-900 text-sm truncate">
                    {insp.store_name || 'Retail Premises'}
                  </h3>
                  {getVerdictBadge(insp.overall_result)}
                  {insp.finalized_at && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-slate-100 text-slate-700 border border-slate-300">
                      <Lock className="h-2.5 w-2.5" /> SEALED
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                  {insp.declaration?.commodity_name && (
                    <span className="font-medium text-slate-700">
                      Product: {insp.declaration.commodity_name}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3 w-3 text-slate-400" />
                    {insp.store_address || insp.district || 'Jurisdiction Area'}
                  </span>
                  <span>
                    Created: {new Date(insp.created_at).toLocaleDateString()} at{' '}
                    {new Date(insp.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                  <span className="font-mono text-[10px] text-slate-400">ID: {insp.id.slice(0, 8)}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                <Link
                  href={`/inspections/${insp.id}`}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-sky-700 hover:bg-sky-800 text-white text-xs font-bold transition-colors shadow-sm"
                >
                  <span>Workstation</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

