'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { ComplianceResult, InspectionBatch } from '@/types';
import {
  Boxes,
  ArrowLeft,
  Download,
  PlusCircle,
  Building2,
  MapPin,
  ShieldCheck,
  ShieldAlert,
  Clock,
  RefreshCw,
  AlertTriangle,
  ArrowRight,
  PieChart,
  CheckCircle2,
} from 'lucide-react';

export default function BatchDetailPage() {
  const params = useParams();
  const batchId = params.id as string;
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [batch, setBatch] = useState<InspectionBatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBatch = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getBatchDetail(batchId);
      setBatch(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load batch inspection details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push('/login');
      } else {
        fetchBatch();
      }
    }
  }, [authLoading, user, batchId]);

  const handleExportZip = async () => {
    if (!batch) return;
    setExporting(true);
    try {
      const filename = `Batch_${batch.name.replace(/\s+/g, '_')}_EvidenceBundle.zip`;
      await api.downloadBatchExportBundle(batchId, filename);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to download batch evidence bundle.');
    } finally {
      setExporting(false);
    }
  };

  const handleAddSample = async () => {
    if (!batch) return;
    try {
      const newInsp = await api.createInspection({
        store_name: batch.store_name || undefined,
        store_address: batch.store_address || undefined,
        district: batch.district || undefined,
        state: batch.state || undefined,
        batch_id: batch.id,
      });
      router.push(`/inspections/${newInsp.id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to create sample inspection.');
    }
  };

  const getResultBadge = (result?: ComplianceResult | null) => {
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

  if (loading) {
    return (
      <div className="py-24 text-center text-xs text-slate-500 flex flex-col items-center justify-center">
        <RefreshCw className="h-8 w-8 text-sky-600 animate-spin mb-3" />
        <span>Loading batch lot inspection...</span>
      </div>
    );
  }

  if (!batch) {
    return (
      <div className="p-6 bg-white rounded-2xl border border-slate-200 text-center">
        <p className="text-sm font-bold text-slate-700">Batch Not Found</p>
        <a href="/batches" className="mt-3 inline-block text-xs font-bold text-sky-600 hover:underline">
          &larr; Back to Batches
        </a>
      </div>
    );
  }

  const schedStats = batch.schedule_iv_compliance || batch.summary_stats;

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div>
          <a
            href="/batches"
            className="inline-flex items-center gap-1 text-xs font-bold text-slate-500 hover:text-slate-800 transition mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Batch Lots
          </a>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <Boxes className="h-6 w-6 text-brand-900" />
            {batch.name}
          </h1>
          <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
            <span className="flex items-center gap-1 font-medium">
              <Building2 className="h-3.5 w-3.5 text-slate-400" /> {batch.store_name || 'Unspecified'}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5 text-slate-400" /> {batch.district || 'N/A'}, {batch.state || 'N/A'}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleExportZip}
            disabled={exporting}
            className="px-3.5 py-2.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-800 border border-indigo-200 font-bold text-xs rounded-xl shadow-sm transition flex items-center gap-1.5 disabled:opacity-50"
            title="Download Offline Legal Filing Bundle with SHA-256 Manifest"
          >
            <Download className={`h-4 w-4 ${exporting ? 'animate-bounce' : 'text-indigo-600'}`} />
            {exporting ? 'Exporting ZIP...' : 'Download Evidence ZIP Bundle'}
          </button>

          <button
            onClick={handleAddSample}
            className="px-4 py-2.5 bg-brand-900 hover:bg-brand-800 text-white font-bold text-xs rounded-xl shadow transition flex items-center gap-1.5"
          >
            <PlusCircle className="h-4 w-4" />
            Add Sample Package
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Schedule IV Statistical Sampling Card */}
      {schedStats && (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-black text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <PieChart className="h-4 w-4 text-brand-900" />
                Schedule IV Statistical Sampling Assessment (Declarations)
              </h2>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Evaluates label declaration compliance across sample packages under LMPC Rules, 2011 Schedule IV protocol.
              </p>
            </div>
            <span className="text-[11px] font-bold px-3 py-1 rounded-full bg-slate-100 text-slate-800 border border-slate-300 self-start sm:self-auto">
              Reference Status: <strong>{schedStats.lot_acceptance_verdict || 'IN_PROGRESS'}</strong>
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-center">
              <span className="text-[10px] text-slate-500 font-bold uppercase">Total Lot Size</span>
              <div className="text-xl font-black text-slate-900 mt-0.5">{schedStats.lot_size} units</div>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-center">
              <span className="text-[10px] text-slate-500 font-bold uppercase">Target Samples</span>
              <div className="text-xl font-black text-indigo-700 mt-0.5">{schedStats.sample_size_target}</div>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-center">
              <span className="text-[10px] text-slate-500 font-bold uppercase">Samples Inspected</span>
              <div className="text-xl font-black text-slate-900 mt-0.5">{schedStats.samples_inspected}</div>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-center">
              <span className="text-[10px] text-slate-500 font-bold uppercase">Compliance Rate</span>
              <div className={`text-xl font-black mt-0.5 ${
                (schedStats.compliance_rate_percent || 0) >= 90 ? 'text-emerald-700' : 'text-amber-700'
              }`}>
                {schedStats.compliance_rate_percent}%
              </div>
            </div>
          </div>

          {/* Metrology Disclaimer Notice */}
          <div className="p-3 bg-amber-50/80 border border-amber-200 rounded-xl text-[11px] text-amber-900 flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Physical Metrology Notice:</span>{' '}
              Statistical sampling assessment reflects label declaration compliance of inspected units. It does NOT constitute certified gravimetric or volumetric net-quantity testing under Rule 24. Physical net-content disputes require verified metrological weighing equipment.
            </div>
          </div>
        </div>
      )}

      {/* Child Sample Inspections Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Sample Package Records ({batch.inspections?.length || 0})
          </h3>
        </div>

        {!batch.inspections || batch.inspections.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-500">
            <p className="font-semibold text-slate-700">No samples attached yet</p>
            <p className="text-slate-400 mt-1">Click &quot;Add Sample Package&quot; to inspect the first commodity unit.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-4 py-3.5">Sample ID</th>
                  <th className="px-4 py-3.5">Script / Language</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Statutory Verdict</th>
                  <th className="px-4 py-3.5">Date Added</th>
                  <th className="px-4 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {batch.inspections.map((insp, idx) => (
                  <tr key={insp.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-3.5 font-bold text-slate-900">
                      Sample #{idx + 1}
                      <span className="block font-mono text-[10px] text-slate-400 font-normal">
                        {insp.id.slice(0, 16)}...
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                        insp.language_detected === 'HIN' || insp.language_detected === 'MIXED'
                          ? 'bg-amber-50 text-amber-800 border-amber-200'
                          : 'bg-slate-50 text-slate-700 border-slate-200'
                      }`}>
                        {insp.language_detected || 'ENG'}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="text-[10px] font-semibold bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200">
                        {insp.status}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">{getResultBadge(insp.overall_result)}</td>
                    <td className="px-4 py-3.5 text-slate-500 whitespace-nowrap">
                      {new Date(insp.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3.5 text-right whitespace-nowrap">
                      <a
                        href={`/inspections/${insp.id}`}
                        className="inline-flex items-center gap-1 bg-brand-50 hover:bg-brand-100 text-brand-900 font-bold px-3 py-1.5 rounded-lg border border-brand-200 transition"
                      >
                        Inspect <ArrowRight className="h-3.5 w-3.5" />
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

