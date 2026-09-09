'use client';

import React from 'react';
import { AuditLog } from '@/types';

interface AuditTimelineProps {
  auditLogs: AuditLog[];
}

export const AuditTimeline: React.FC<AuditTimelineProps> = ({ auditLogs }) => {
  if (!auditLogs || auditLogs.length === 0) {
    return (
      <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-6 text-slate-900 shadow-sm">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-2">
          <svg className="w-5 h-5 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Chronological Audit Trail
        </h3>
        <p className="text-xs text-slate-500 italic">No audit log entries recorded yet.</p>
      </div>
    );
  }

  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case 'INSPECTION_CREATED':
      case 'DEMO_SEED_CREATED':
        return 'bg-blue-50 text-blue-800 border-blue-200';
      case 'IMAGE_UPLOADED':
      case 'OCR_PROCESSED':
      case 'PIPELINE_EXECUTED':
        return 'bg-purple-50 text-purple-800 border-purple-200';
      case 'DECLARATION_UPDATED':
      case 'MEASUREMENT_RECORDED':
      case 'DIGITAL_LISTING_CROSSCHECKED':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'INSPECTION_REVIEWED':
      case 'RULES_EVALUATED':
        return 'bg-cyan-50 text-cyan-800 border-cyan-200';
      case 'INSPECTION_FINALIZED':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'REPORT_GENERATED':
        return 'bg-indigo-50 text-indigo-800 border-indigo-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-6 text-slate-900 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <svg className="w-5 h-5 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Chronological Audit Trail &amp; Evidence Lineage
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Immutable log of all automated pipeline passes and officer adjudication decisions
          </p>
        </div>
        <span className="px-2.5 py-1 bg-slate-100 text-slate-600 text-[11px] font-mono font-semibold rounded-full">
          {auditLogs.length} Events Logged
        </span>
      </div>

      {/* Timeline List */}
      <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {auditLogs.map((entry, idx) => (
          <div key={entry.id || idx} className="relative group">
            {/* Timeline Dot */}
            <div className="absolute -left-6 top-1.5 w-4 h-4 rounded-full bg-white border-2 border-cyan-600 group-hover:scale-110 transition shrink-0 shadow-xs" />

            <div className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-3.5 hover:bg-white hover:border-slate-300 transition shadow-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 text-[10px] font-bold font-mono rounded-lg border ${getActionBadgeColor(entry.action)}`}>
                    {entry.action}
                  </span>
                  {entry.entity_type && (
                    <span className="text-xs text-slate-500 font-medium">
                      Target: {entry.entity_type}
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-slate-500 font-mono">
                  {new Date(entry.created_at).toLocaleString('en-IN', {
                    timeZone: 'Asia/Kolkata',
                    dateStyle: 'short',
                    timeStyle: 'medium',
                  })}
                </div>
              </div>

              {entry.metadata_json && Object.keys(entry.metadata_json).length > 0 && (
                <div className="bg-white rounded-xl p-2.5 text-[11px] font-mono text-slate-600 border border-slate-200 overflow-x-auto mt-2">
                  <pre className="whitespace-pre-wrap break-all text-[10px]">
                    {JSON.stringify(entry.metadata_json, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

