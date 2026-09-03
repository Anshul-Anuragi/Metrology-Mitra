'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { CompoundingCalculationResponse, EnforcementNotice } from '@/types';
import {
  Gavel,
  Calculator,
  FileText,
  Download,
  Search,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Building2,
  Scale,
} from 'lucide-react';

export default function EnforcementPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [notices, setNotices] = useState<EnforcementNotice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Compounding Calculator State
  const [calcOffenceCount, setCalcOffenceCount] = useState(1);
  const [calcRepeat3Years, setCalcRepeat3Years] = useState(false);
  const [calcRules, setCalcRules] = useState('LMPC-R6-MRP, LMPC-R6-DATE');
  const [calcResult, setCalcResult] = useState<CompoundingCalculationResponse | null>(null);
  const [calculating, setCalculating] = useState(false);

  const fetchNotices = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listEnforcementNotices();
      setNotices(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load enforcement notices.');
    } finally {
      setLoading(false);
    }
  };

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCalculating(true);
    try {
      const ruleList = calcRules.split(',').map((r) => r.trim()).filter(Boolean);
      const res = await api.calculateCompounding({
        offence_count: calcOffenceCount,
        is_repeat_within_three_years: calcRepeat3Years,
        violation_rule_codes: ruleList,
      });
      setCalcResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to calculate compounding fee.');
    } finally {
      setCalculating(false);
    }
  };

  const handleDownloadChallan = async (notice: EnforcementNotice) => {
    try {
      const filename = `Challan_${notice.notice_number.replace(/\//g, '_')}.pdf`;
      await api.downloadChallanPdf(notice.id, filename);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to download compounding challan PDF.');
    }
  };

  const handleUpdateStatus = async (noticeId: string, nextStatus: string) => {
    try {
      await api.updateEnforcementNotice(noticeId, { status: nextStatus });
      await fetchNotices();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update notice status.');
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push('/login');
      } else {
        fetchNotices();
      }
    }
  }, [authLoading, user]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <Gavel className="h-6 w-6 text-brand-900" />
            Statutory Enforcement & Compounding (Section 48)
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Section 36 notices, statutory compounding calculators, and compounding challan memorandums under Legal Metrology Act, 2009.
          </p>
        </div>

        <button
          onClick={fetchNotices}
          className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors text-xs font-semibold flex items-center gap-1.5 self-start sm:self-auto"
          title="Refresh Notices"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Grid: Compounding Calculator + Notices Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Section 48 Compounding Calculator Tool */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
          <div className="flex items-center gap-2">
            <Calculator className="h-5 w-5 text-indigo-700" />
            <h2 className="text-sm font-black text-slate-900 uppercase tracking-wider">
              Section 48 Compounding Calculator
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Computes statutory compounding fee limits under Section 48 for Section 36(1) violations.
          </p>

          <form onSubmit={handleCalculate} className="space-y-3 text-xs">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Offence Occurrence *</label>
              <select
                value={calcOffenceCount}
                onChange={(e) => setCalcOffenceCount(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none font-medium"
              >
                <option value={1}>First Offence (Up to ₹25,000)</option>
                <option value={2}>Second Offence (Up to ₹50,000)</option>
                <option value={3}>Subsequent (Court Prosecution / Penal)</option>
              </select>
            </div>

            {calcOffenceCount >= 2 && (
              <div className="flex items-center gap-2 p-2 bg-amber-50 border border-amber-200 rounded-lg">
                <input
                  type="checkbox"
                  id="repeat3years"
                  checked={calcRepeat3Years}
                  onChange={(e) => setCalcRepeat3Years(e.target.checked)}
                  className="rounded text-amber-600 focus:ring-amber-500"
                />
                <label htmlFor="repeat3years" className="text-[11px] font-bold text-amber-900">
                  Repeat within 3 years of earlier compounding? (Sec 48(2))
                </label>
              </div>
            )}

            <div>
              <label className="block font-bold text-slate-700 mb-1">Violated Rule Codes (comma-separated)</label>
              <input
                type="text"
                value={calcRules}
                onChange={(e) => setCalcRules(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={calculating}
              className="w-full py-2 bg-indigo-700 hover:bg-indigo-800 text-white font-bold rounded-xl shadow transition flex items-center justify-center gap-1.5"
            >
              <Scale className="h-4 w-4" />
              {calculating ? 'Calculating...' : 'Compute Fee Limits'}
            </button>
          </form>

            {/* Result Card */}
          {calcResult && (
            <div className={`p-4 rounded-xl border text-xs space-y-2 mt-4 ${
              calcResult.assessment_status === 'COMPOUNDABLE'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
                : calcResult.assessment_status === 'NON_COMPOUNDABLE'
                ? 'bg-rose-50 border-rose-200 text-rose-950'
                : 'bg-amber-50 border-amber-200 text-amber-950'
            }`}>
              <div className="flex items-center justify-between">
                <span className="font-bold uppercase text-[10px]">Assessment Status</span>
                <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                  calcResult.assessment_status === 'COMPOUNDABLE'
                    ? 'bg-emerald-200 text-emerald-800'
                    : calcResult.assessment_status === 'NON_COMPOUNDABLE'
                    ? 'bg-rose-200 text-rose-800'
                    : 'bg-amber-200 text-amber-800'
                }`}>
                  {calcResult.assessment_status}
                </span>
              </div>

              <div>
                <span className="text-slate-500 block text-[10px]">Statutory Ceiling Reference (Sec 36(1)):</span>
                <span className="text-lg font-black text-slate-900">
                  {calcResult.compounding_amount_reference
                    ? `₹ ${calcResult.compounding_amount_reference.toLocaleString('en-IN')}`
                    : 'Discretionary / Not Determinable'}
                </span>
              </div>

              <p className="text-[11px] text-slate-600 leading-relaxed">
                {calcResult.legal_rationale}
              </p>

              <p className="text-[10px] text-amber-800 font-semibold border-t border-amber-200/60 pt-1.5">
                {calcResult.disclaimer}
              </p>
            </div>
          )}
        </div>

        {/* Right: Enforcement Notices List */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Draft Enforcement & Compounding Notices ({notices.length})
            </h2>
          </div>

          {loading ? (
            <div className="py-16 text-center text-xs text-slate-500 flex flex-col items-center justify-center">
              <RefreshCw className="h-8 w-8 text-sky-600 animate-spin mb-3" />
              <span>Loading enforcement notices...</span>
            </div>
          ) : notices.length === 0 ? (
            <div className="py-16 text-center text-xs text-slate-500">
              <FileText className="h-10 w-10 text-slate-300 mx-auto mb-2" />
              <p className="font-semibold text-slate-700">No draft enforcement notices generated</p>
              <p className="text-slate-400 mt-1">
                Draft notices can be prepared from finalized non-compliant inspection sessions.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-4 py-3.5">Draft Notice ID</th>
                    <th className="px-4 py-3.5">Notice Type</th>
                    <th className="px-4 py-3.5">Statutory Reference Ceiling</th>
                    <th className="px-4 py-3.5">Status</th>
                    <th className="px-4 py-3.5">Challan Ref</th>
                    <th className="px-4 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white">
                  {notices.map((n) => (
                    <tr key={n.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-4 py-3.5">
                        <div className="font-bold text-slate-900">{n.notice_number}</div>
                        <div className="text-[10px] text-slate-400 font-mono">Offence #{n.offence_count}</div>
                      </td>
                      <td className="px-4 py-3.5 font-medium text-slate-700">{n.notice_type}</td>
                      <td className="px-4 py-3.5 font-bold text-rose-700">
                        {n.compounding_amount ? `₹ ${n.compounding_amount.toLocaleString('en-IN')}` : 'Discretionary'}
                      </td>
                      <td className="px-4 py-3.5">
                        <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                          n.status === 'COMPOUNDED'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : n.status === 'ISSUED'
                            ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                            : 'bg-slate-100 text-slate-700 border-slate-200'
                        }`}>
                          {n.status}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 text-slate-500 font-mono text-[11px]">
                        {n.challan_reference || 'Pending Determination'}
                      </td>
                      <td className="px-4 py-3.5 text-right whitespace-nowrap">
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            onClick={() => handleDownloadChallan(n)}
                            className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition"
                            title="Download Draft Compounding Memo PDF"
                          >
                            <Download className="h-3.5 w-3.5 text-slate-600" />
                          </button>

                          {n.status === 'DRAFTED' && (
                            <button
                              onClick={() => handleUpdateStatus(n.id, 'ISSUED')}
                              className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-lg font-bold text-[10px]"
                            >
                              Approve Draft
                            </button>
                          )}

                          {n.status === 'ISSUED' && (
                            <button
                              onClick={() => handleUpdateStatus(n.id, 'COMPOUNDED')}
                              className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-lg font-bold text-[10px]"
                            >
                              Record Compounding
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

