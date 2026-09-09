'use client';

import React, { useState } from 'react';
import { Report, ComplianceResult } from '@/types';
import { api } from '@/lib/api';
import {
  FileText,
  Download,
  ShieldAlert,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Clock,
  Printer,
} from 'lucide-react';
import InspectorDecisionSection from '@/components/InspectorDecisionSection';

interface ReportExportSectionProps {
  inspectionId: string;
  verdict: ComplianceResult | string;
  status?: string;
  reviewedBy?: string | null;
  reviewedAt?: string | null;
  reviewNotes?: string | null;
  reports?: Report[];
  onReportGenerated?: () => void;
  onDecisionSubmitted?: () => void;
}

export default function ReportExportSection({
  inspectionId,
  verdict,
  status,
  reviewedBy,
  reviewedAt,
  reviewNotes,
  reports = [],
  onReportGenerated,
  onDecisionSubmitted,
}: ReportExportSectionProps) {
  const [downloadingType, setDownloadingType] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const isCompliant = verdict === 'COMPLIANT';

  const handleDownload = async (reportType: 'PDF' | 'JSON' | 'NOTICE_SEC36') => {
    setDownloadingType(reportType);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const rep = await api.generateReport(inspectionId, reportType);
      const ext = reportType === 'JSON' ? 'json' : 'pdf';
      const filename = `${rep.report_number.replace(/\//g, '_')}.${ext}`;
      await api.downloadReport(inspectionId, rep.id, filename);
      setSuccessMessage(`Generated ${rep.report_number} successfully!`);
      if (onReportGenerated) onReportGenerated();
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Failed to generate official report document.';
      setErrorMessage(detail);
    } finally {
      setDownloadingType(null);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <FileText className="h-4 w-4 text-brand-900" />
            <span>Official Inspection Reports &amp; Export Center</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Generate and export statutory inspection memos, non-compliance notices, and evidentiary audit bundles
          </p>
        </div>
        <span className="text-[10px] font-mono font-bold bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded border border-slate-200">
          REPORTLAB PDF ENGINE
        </span>
      </div>

      {/* Messages */}
      {errorMessage && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* 3 Report Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Draft Inspection Memo */}
        <button
          type="button"
          onClick={() => handleDownload('PDF')}
          disabled={downloadingType !== null}
          className="p-3.5 bg-brand-50 hover:bg-brand-100/80 border border-brand-200 rounded-xl text-left flex items-start justify-between transition group disabled:opacity-50"
        >
          <div className="space-y-1">
            <div className="text-xs font-bold text-brand-900 flex items-center gap-1.5">
              <FileText className="h-4 w-4 text-brand-700" />
              <span>Inspection Memo (PDF)</span>
            </div>
            <p className="text-[11px] text-slate-600">
              Official 14-section compliance report with image thumbnails &amp; rule matrix
            </p>
          </div>
          <Download className={`h-4 w-4 text-brand-700 group-hover:translate-y-0.5 transition-transform shrink-0 ${downloadingType === 'PDF' ? 'animate-bounce' : ''}`} />
        </button>

        {/* Section 36 Draft Notice */}
        <button
          type="button"
          onClick={() => handleDownload('NOTICE_SEC36')}
          disabled={downloadingType !== null || isCompliant}
          className={`p-3.5 border rounded-xl text-left flex items-start justify-between transition ${
            isCompliant
              ? 'bg-slate-50 border-slate-200 opacity-60 cursor-not-allowed text-slate-400'
              : 'bg-rose-50 hover:bg-rose-100/80 border-rose-200 text-rose-900 group'
          }`}
          title={isCompliant ? 'Section 36 notice is only applicable when violations are detected' : 'Download Draft Section 36 Notice'}
        >
          <div className="space-y-1">
            <div className="text-xs font-bold flex items-center gap-1.5">
              <ShieldAlert className="h-4 w-4 text-rose-600" />
              <span>Section 36 Notice (PDF)</span>
            </div>
            <p className="text-[11px] text-slate-600">
              {isCompliant ? 'Exempt: Package is fully compliant' : 'Statutory show-cause memo under Legal Metrology Act, 2009'}
            </p>
          </div>
          <Download className="h-4 w-4 text-rose-600 shrink-0" />
        </button>

        {/* Machine-Readable JSON */}
        <button
          type="button"
          onClick={() => handleDownload('JSON')}
          disabled={downloadingType !== null}
          className="p-3.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl text-left flex items-start justify-between transition group disabled:opacity-50"
        >
          <div className="space-y-1">
            <div className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
              <FileSpreadsheet className="h-4 w-4 text-slate-600" />
              <span>Evidence Bundle (JSON)</span>
            </div>
            <p className="text-[11px] text-slate-600">
              Machine-readable audit package with SHA-256 hashes &amp; rule results
            </p>
          </div>
          <Download className="h-4 w-4 text-slate-600 group-hover:translate-y-0.5 transition-transform shrink-0" />
        </button>
      </div>

      {/* Previously Generated Reports History */}
      {reports && reports.length > 0 && (
        <div className="pt-2 border-t border-slate-100 space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Previously Generated Documents ({reports.length})
          </div>
          <div className="space-y-1.5">
            {reports.map((rep) => (
              <div
                key={rep.id}
                className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2">
                  <FileText className="h-3.5 w-3.5 text-slate-500" />
                  <span className="font-mono font-bold text-slate-800">{rep.report_number}</span>
                  <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.2 rounded font-semibold">
                    {rep.report_type}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] text-slate-400 font-mono">
                    {new Date(rep.created_at).toLocaleDateString()}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      const ext = rep.report_type === 'JSON' ? 'json' : 'pdf';
                      api.downloadReport(inspectionId, rep.id, `${rep.report_number.replace(/\//g, '_')}.${ext}`);
                    }}
                    className="text-brand-900 hover:text-brand-700 font-bold flex items-center gap-1"
                  >
                    <Download className="h-3 w-3" /> Download
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Inspector Decision & Statutory Adjudication (Immediately following report generation) */}
      <div className="pt-2">
        <InspectorDecisionSection
          inspectionId={inspectionId}
          status={status}
          overallResult={typeof verdict === 'string' ? verdict : undefined}
          reviewedBy={reviewedBy}
          reviewedAt={reviewedAt}
          reviewNotes={reviewNotes}
          onDecisionSubmitted={onDecisionSubmitted}
          onOpenReport={() => handleDownload('PDF')}
        />
      </div>
    </div>
  );
}

