'use client';

import React from 'react';
import { AuditLog } from '@/types';

interface AuditTimelineProps {
  auditLogs: AuditLog[];
}

export const AuditTimeline: React.FC<AuditTimelineProps> = ({ auditLogs }) => {
  if (!auditLogs || auditLogs.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-white shadow-xl">
        <h3 className="text-base font-semibold text-white flex items-center gap-2 mb-2">
          <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'IMAGE_UPLOADED':
      case 'OCR_PROCESSED':
      case 'PIPELINE_EXECUTED':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'DECLARATION_UPDATED':
      case 'MEASUREMENT_RECORDED':
      case 'DIGITAL_LISTING_CROSSCHECKED':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'INSPECTION_REVIEWED':
      case 'RULES_EVALUATED':
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
      case 'INSPECTION_FINALIZED':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'REPORT_GENERATED':
        return 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30';
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-white shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Chronological Audit Trail & Evidence Lineage
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Immutable log of all automated pipeline passes and officer adjudication decisions
          </p>
        </div>
        <span className="px-2.5 py-1 bg-slate-800 text-slate-300 text-[11px] font-mono rounded">
          {auditLogs.length} Events Logged
        </span>
      </div>

      {/* Timeline List */}
      <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {auditLogs.map((entry, idx) => (
          <div key={entry.id || idx} className="relative group">
            {/* Timeline Dot */}
            <div className="absolute -left-6 top-1.5 w-4 h-4 rounded-full bg-slate-900 border-2 border-cyan-500 group-hover:scale-110 transition shrink-0" />

            <div className="bg-slate-950 border border-slate-800/80 rounded-lg p-3 hover:border-slate-700 transition">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 text-[10px] font-semibold font-mono rounded border ${getActionBadgeColor(entry.action)}`}>
                    {entry.action}
                  </span>
                  {entry.entity_type && (
                    <span className="text-xs text-slate-400 font-medium">
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
                <div className="bg-slate-900/80 rounded p-2 text-[11px] font-mono text-slate-300 overflow-x-auto">
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

