'use client';

import React, { useState } from 'react';
import { ComplianceCheck, ComplianceResult, Evidence, Report, Violation } from '@/types';
import { api } from '@/lib/api';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  FileText,
  Download,
  CheckCircle,
  XCircle,
  Clock,
  RotateCw,
  FileSpreadsheet,
} from 'lucide-react';

interface ComplianceVerdictCardProps {
  inspectionId: string;
  overallResult: ComplianceResult;
  checks?: ComplianceCheck[];
  violations?: Violation[];
  evidenceItems?: Evidence[];
  reports?: Report[];
  onRefresh?: () => Promise<void>;
}

export default function ComplianceVerdictCard({
  inspectionId,
  overallResult,
  checks = [],
  violations = [],
  evidenceItems = [],
  reports = [],
  onRefresh,
}: ComplianceVerdictCardProps) {
  const [downloadingType, setDownloadingType] = useState<string | null>(null);
  const [isReevaluating, setIsReevaluating] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleDownload = async (reportType: 'PDF' | 'JSON' | 'NOTICE_SEC36') => {
    setDownloadingType(reportType);
    setErrorMessage(null);
    try {
      // 1. Generate or fetch report
      const rep = await api.generateReport(inspectionId, reportType);
      const ext = reportType === 'JSON' ? 'json' : 'pdf';
      const filename = `${rep.report_number.replace(/\//g, '_')}.${ext}`;
      // 2. Download binary blob
      await api.downloadReport(inspectionId, rep.id, filename);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Failed to generate report document.';
      setErrorMessage(detail);
    } finally {
      setDownloadingType(null);
    }
  };

  const handleReevaluate = async () => {
    setIsReevaluating(true);
    setErrorMessage(null);
    try {
      await api.evaluateInspection(inspectionId);
      if (onRefresh) await onRefresh();
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.detail || 'Failed to re-evaluate compliance rules.');
    } finally {
      setIsReevaluating(false);
    }
  };

  const isCompliant = overallResult === 'COMPLIANT';
  const isNonCompliant = overallResult === 'NON_COMPLIANT';
  const isNeedsReview = overallResult === 'NEEDS_REVIEW';

  const bannerColor = isCompliant
    ? 'bg-emerald-600 text-white'
    : isNonCompliant
    ? 'bg-rose-600 text-white'
    : isNeedsReview
    ? 'bg-amber-600 text-white'
    : 'bg-slate-700 text-white';

  const verdictIcon = isCompliant ? (
    <ShieldCheck className="h-8 w-8 text-emerald-200" />
  ) : isNonCompliant ? (
    <ShieldAlert className="h-8 w-8 text-rose-200" />
  ) : (
    <AlertTriangle className="h-8 w-8 text-amber-200" />
  );

  return (
    <div className="bg-white rounded-xl shadow border border-slate-200 overflow-hidden flex flex-col space-y-6 p-6">
      {/* 1. Overall Compliance Banner */}
      <div className={`rounded-xl p-5 shadow-sm flex items-center justify-between ${bannerColor}`}>
        <div className="flex items-center gap-4">
          {verdictIcon}
          <div>
            <div className="text-[11px] uppercase tracking-wider font-semibold opacity-90">
              Statutory Compliance Verdict (LMPC Rules, 2011)
            </div>
            <div className="text-2xl font-black tracking-tight">{overallResult}</div>
            <p className="text-xs opacity-80 mt-0.5">
              {isCompliant
                ? 'Package satisfies all mandatory Legal Metrology declaration provisions.'
                : isNonCompliant
                ? `${violations.length} statutory violations detected under LMPC Rules, 2011.`
                : 'Further human inspection is required for principal display panel or optical contrast.'}
            </p>
          </div>
        </div>

        <button
          onClick={handleReevaluate}
          disabled={isReevaluating}
          className="bg-white/15 hover:bg-white/25 text-white text-xs font-semibold px-4 py-2 rounded-lg border border-white/20 flex items-center gap-1.5 transition-colors disabled:opacity-50"
        >
          <RotateCw className={`h-4 w-4 ${isReevaluating ? 'animate-spin' : ''}`} />
          {isReevaluating ? 'Evaluating...' : 'Re-Evaluate Rules'}
        </button>
      </div>

      {errorMessage && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* 2. Detected Violations Panel (if non-compliant) */}
      {violations.length > 0 && (
        <div className="border border-rose-200 bg-rose-50/40 rounded-xl p-4">
          <h4 className="text-sm font-bold text-rose-900 flex items-center gap-2 mb-3">
            <ShieldAlert className="h-4 w-4 text-rose-600" />
            Detected Statutory Violations ({violations.length})
          </h4>

          <div className="space-y-2.5">
            {violations.map((v) => (
              <div
                key={v.id}
                className="bg-white p-3.5 rounded-lg border border-rose-100 shadow-sm flex items-start justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                        v.severity === 'HIGH' || v.severity === 'CRITICAL'
                          ? 'bg-rose-100 text-rose-800 border border-rose-200'
                          : 'bg-amber-100 text-amber-800 border border-amber-200'
                      }`}
                    >
                      {v.severity}
                    </span>
                    <span className="text-xs font-bold text-slate-900">{v.title}</span>
                  </div>
                  <p className="text-xs text-slate-600">{v.description}</p>
                  <p className="text-[11px] font-mono text-slate-400 mt-1">
                    Citation: {v.rule_citation || 'LMPC Rules, 2011'}
                  </p>
                </div>

                <div className="shrink-0 text-right">
                  <span className="text-[10px] font-semibold bg-slate-100 text-slate-700 px-2 py-1 rounded">
                    Status: {v.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Statutory Compliance Checks Table */}
      <div>
        <h4 className="text-sm font-bold text-slate-900 mb-3 flex items-center justify-between">
          <span>Statutory Compliance Matrix ({checks.length} Rules Evaluated)</span>
          <span className="text-xs font-normal text-slate-500">Legal Metrology Act, 2009 Grounding</span>
        </h4>

        <div className="border border-slate-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
            <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-3.5 py-2.5">Rule Code</th>
                <th className="px-3.5 py-2.5">Statutory Reference</th>
                <th className="px-3.5 py-2.5">Observed Value</th>
                <th className="px-3.5 py-2.5">Result</th>
                <th className="px-3.5 py-2.5">Findings</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {checks.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-3.5 py-2.5 font-mono font-semibold text-slate-900">
                    {c.legal_rule?.rule_code || 'LMPC-RULE'}
                  </td>
                  <td className="px-3.5 py-2.5 text-slate-600">
                    {c.legal_rule?.source_reference || 'LMPC Rules, 2011'}
                  </td>
                  <td className="px-3.5 py-2.5 text-slate-800 font-medium max-w-[160px] truncate">
                    {c.observed_value || <span className="text-slate-400 italic">NOT DECLARED</span>}
                  </td>
                  <td className="px-3.5 py-2.5 whitespace-nowrap">
                    {c.result === 'PASS' ? (
                      <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 border border-emerald-200 font-semibold px-2 py-0.5 rounded text-[11px]">
                        <CheckCircle className="h-3.5 w-3.5" /> PASS
                      </span>
                    ) : c.result === 'FAIL' ? (
                      <span className="inline-flex items-center gap-1 text-rose-700 bg-rose-50 border border-rose-200 font-semibold px-2 py-0.5 rounded text-[11px]">
                        <XCircle className="h-3.5 w-3.5" /> FAIL
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-amber-700 bg-amber-50 border border-amber-200 font-semibold px-2 py-0.5 rounded text-[11px]">
                        <Clock className="h-3.5 w-3.5" /> REVIEW
                      </span>
                    )}
                  </td>
                  <td className="px-3.5 py-2.5 text-slate-500 max-w-[220px] truncate" title={c.reason || ''}>
                    {c.reason || 'Verified'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Document Generation & Export Actions */}
      <div className="pt-4 border-t border-slate-200">
        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
          Download & Export Official Inspection Records
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Draft PDF Memo */}
          <button
            onClick={() => handleDownload('PDF')}
            disabled={downloadingType !== null}
            className="p-3 bg-brand-50 hover:bg-brand-100 border border-brand-200 rounded-lg text-left flex items-center justify-between transition-colors text-brand-900 group"
          >
            <div>
              <div className="text-xs font-bold flex items-center gap-1.5">
                <FileText className="h-4 w-4 text-brand-600" />
                Draft Inspection Memo
              </div>
              <div className="text-[10px] text-slate-500">Official PDF Record</div>
            </div>
            <Download className="h-4 w-4 text-brand-600 group-hover:translate-y-0.5 transition-transform" />
          </button>

          {/* Section 36 Draft Notice */}
          <button
            onClick={() => handleDownload('NOTICE_SEC36')}
            disabled={downloadingType !== null || isCompliant}
            className={`p-3 border rounded-lg text-left flex items-center justify-between transition-colors ${
              isCompliant
                ? 'bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed opacity-60'
                : 'bg-rose-50 hover:bg-rose-100 border-rose-200 text-rose-900 group'
            }`}
            title={isCompliant ? 'Section 36 notice is only available for non-compliant inspections' : 'Download Draft Section 36 Notice'}
          >
            <div>
              <div className="text-xs font-bold flex items-center gap-1.5">
                <ShieldAlert className="h-4 w-4 text-rose-600" />
                Section 36 Draft Notice
              </div>
              <div className="text-[10px] text-slate-500">
                {isCompliant ? 'N/A (Fully Compliant)' : 'Non-Compliance PDF'}
              </div>
            </div>
            <Download className="h-4 w-4 text-rose-600 group-hover:translate-y-0.5 transition-transform" />
          </button>

          {/* JSON Export */}
          <button
            onClick={() => handleDownload('JSON')}
            disabled={downloadingType !== null}
            className="p-3 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-left flex items-center justify-between transition-colors text-slate-800 group"
          >
            <div>
              <div className="text-xs font-bold flex items-center gap-1.5">
                <FileSpreadsheet className="h-4 w-4 text-slate-600" />
                Machine-Readable JSON
              </div>
              <div className="text-[10px] text-slate-500">Standard Export Bundle</div>
            </div>
            <Download className="h-4 w-4 text-slate-600 group-hover:translate-y-0.5 transition-transform" />
          </button>
        </div>
      </div>
    </div>
  );
}

