'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { Section49LiabilityAssessment } from '@/types';
import { AlertCircle, Building2, CheckCircle2, Search, ShieldCheck, UserCheck } from 'lucide-react';

interface CompanyLiabilityCardProps {
  initialCompanyName?: string;
}

export default function CompanyLiabilityCard({ initialCompanyName }: CompanyLiabilityCardProps) {
  const [query, setQuery] = useState<string>(initialCompanyName || '');
  const [assessment, setAssessment] = useState<Section49LiabilityAssessment | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.lookupCorporateLiability(query.trim());
      setAssessment(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to lookup corporate liability.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4 text-xs">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] flex items-center gap-2">
          <Building2 className="h-4 w-4 text-indigo-700" />
          Section 49 Corporate Entity & Nominated Director Liability
        </h3>
        {assessment && (
          <span
            className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] border ${
              assessment.has_nominated_director
                ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                : 'bg-amber-50 text-amber-700 border-amber-300'
            }`}
          >
            {assessment.liability_determination}
          </span>
        )}
      </div>

      <p className="text-slate-600 text-[11px]">
        Evaluates offences by companies under Section 49. Determines whether notice lies against a Form I Nominated Director (Section 49(2)) or default persons in charge (Section 49(1)).
      </p>

      <form onSubmit={handleLookup} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter Company Name or CIN (e.g. L15400MH2000PLC123456)..."
          className="flex-1 px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl focus:bg-white focus:outline-none text-slate-800"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl transition flex items-center gap-1.5 shadow-sm"
        >
          <Search className="h-3.5 w-3.5" />
          {loading ? 'Evaluating...' : 'Assess Section 49'}
        </button>
      </form>

      {error && <p className="text-rose-600 text-[11px]">{error}</p>}

      {assessment && (
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3 text-slate-700 text-[11px]">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <span className="text-[10px] text-slate-400 font-semibold block">CORPORATE ENTITY:</span>
              <span className="font-bold text-slate-900">{assessment.company_name}</span>
              {assessment.cin && <span className="font-mono text-[10px] text-slate-500 block">CIN: {assessment.cin}</span>}
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-semibold block">STATUTORY NOTICE RECIPIENT:</span>
              <span className="font-bold text-indigo-900">{assessment.notice_recipient_name}</span>
              <span className="text-[10px] text-slate-500 block">{assessment.notice_recipient_designation}</span>
            </div>
          </div>

          {assessment.nominated_director && (
            <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-900 text-[10px] space-y-1">
              <div className="flex items-center gap-1.5 font-bold">
                <UserCheck className="h-3.5 w-3.5 text-emerald-700" />
                Form I Nominated Director on Record:
              </div>
              <p>
                <b>Director:</b> {assessment.nominated_director.director_name} (DIN: {assessment.nominated_director.din})
                <br />
                <b>Notice Date:</b> {assessment.nominated_director.form_i_notice_date} | <b>Designation:</b> {assessment.nominated_director.designation}
              </p>
            </div>
          )}

          <p className="text-slate-700 leading-relaxed">{assessment.rationale}</p>
          <p className="text-[10px] text-slate-400 pt-2 border-t border-slate-200">{assessment.disclaimer}</p>
        </div>
      )}
    </div>
  );
}

