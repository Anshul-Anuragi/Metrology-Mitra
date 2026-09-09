'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Inspection, ComplianceResult } from '@/types';
import {
  FileText,
  Download,
  Printer,
  Search,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Briefcase,
  Gavel,
  Lock,
  ChevronRight,
  RotateCcw,
} from 'lucide-react';

export default function InspectorReportsPage() {
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterVerdict, setFilterVerdict] = useState<string>('ALL');

  useEffect(() => {
    async function loadInspections() {
      setLoading(true);
      try {
        const data = await api.getInspections();
        setInspections(data);
      } catch (err) {
        console.error('Failed to load reports:', err);
      } finally {
        setLoading(false);
      }
    }
    loadInspections();
  }, []);

  const eligibleInspections = useMemo(() => {
    return inspections.filter((i) => {
      // Verdict filter
      if (filterVerdict !== 'ALL' && i.overall_result !== filterVerdict) return false;

      // Text search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const store = (i.store_name || '').toLowerCase();
        const prod = (i.declaration?.commodity_name || '').toLowerCase();
        const id = i.id.toLowerCase();
        return store.includes(q) || prod.includes(q) || id.includes(q);
      }
      return true;
    });
  }, [inspections, filterVerdict, searchQuery]);

  const handleDownloadPDF = (id: string, store: string) => {
    // In production, trigger PDF generation endpoint
    const url = `/api/v1/inspections/${id}/report`;
    window.open(url, '_blank');
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">
              Statutory Reports &amp; Enforcement Hub
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-sky-100 text-sky-800 border border-sky-300">
              LEGAL CERTIFICATES
            </span>
          </div>
          <p className="text-slate-500 text-xs mt-1">
            Export legally admissible inspection certificates, Section 15 seizure panchnamas, and investigation dossiers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/dossiers"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold transition-colors"
          >
            <Briefcase className="h-4 w-4 text-slate-600" />
            Investigation Dossiers
          </Link>
          <Link
            href="/seizures"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold transition-colors"
          >
            <Gavel className="h-4 w-4 text-slate-600" />
            Panchnama Records
          </Link>
        </div>
      </div>

      {/* Search & Filter Ribbon */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search report by premises, product, or docket reference..."
            className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-semibold text-slate-500">Filter:</span>
          <select
            value={filterVerdict}
            onChange={(e) => setFilterVerdict(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="ALL">All Outcomes</option>
            <option value="COMPLIANT">Compliant Certificates</option>
            <option value="NON_COMPLIANT">Violation Records</option>
            <option value="NEEDS_REVIEW">Review Records</option>
          </select>
        </div>
      </div>

      {/* Reports Grid */}
      {loading ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200 text-slate-500 text-xs">
          Loading report inventory...
        </div>
      ) : eligibleInspections.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
          <p className="text-sm font-semibold text-slate-800">No reports found</p>
          <p className="text-xs text-slate-500 mt-1">
            Complete and finalize inspections to produce exportable statutory certificates.
          </p>
          <button
            onClick={() => {
              setFilterVerdict('ALL');
              setSearchQuery('');
            }}
            className="mt-4 inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700"
          >
            <RotateCcw className="h-3.5 w-3.5" /> Reset Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {eligibleInspections.map((insp) => (
            <div
              key={insp.id}
              className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:border-slate-300 hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm truncate max-w-[260px]">
                      {insp.store_name || 'Commercial Inspection Docket'}
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {insp.declaration?.commodity_name ? `Product: ${insp.declaration.commodity_name}` : insp.district || 'Central District'}
                    </p>
                  </div>
                  {getVerdictBadge(insp.overall_result)}
                </div>

                <div className="bg-slate-50 rounded-xl p-3 border border-slate-100 my-3 text-xs space-y-1">
                  <div className="flex justify-between text-slate-600">
                    <span>Docket Reference:</span>
                    <span className="font-mono font-semibold text-slate-900">{insp.id.slice(0, 13)}...</span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Inspection Date:</span>
                    <span className="font-medium text-slate-900">
                      {new Date(insp.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Finalization Status:</span>
                    <span className="font-semibold text-slate-900 flex items-center gap-1">
                      {insp.finalized_at ? (
                        <>
                          <Lock className="h-3 w-3 text-slate-600" /> Sealed
                        </>
                      ) : (
                        'Draft / Unsealed'
                      )}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                <Link
                  href={`/inspections/${insp.id}`}
                  className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1"
                >
                  View Workstation <ChevronRight className="h-3.5 w-3.5" />
                </Link>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => window.print()}
                    className="p-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
                    title="Print report summary"
                  >
                    <Printer className="h-4 w-4" />
                  </button>

                  <Link
                    href={`/inspections/${insp.id}`}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-sky-700 hover:bg-sky-800 text-white text-xs font-bold transition-all shadow-xs"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>Report Memo</span>
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

