'use client';

import React from 'react';
import { AuditLog } from '@/types';
import {
  History,
  Shield,
  Lock,
  User,
  Cpu,
  Camera,
  Clock,
} from 'lucide-react';

interface InspectionReplayTimelineProps {
  auditLogs: AuditLog[];
}

export default function InspectionReplayTimeline({
  auditLogs = [],
}: InspectionReplayTimelineProps) {
  if (!auditLogs || auditLogs.length === 0) {
    return (
      <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-8 text-center shadow-sm space-y-2">
        <History className="h-8 w-8 text-slate-400 mx-auto" />
        <h3 className="text-sm font-bold text-slate-800">No Chronological Events Recorded</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          Audit events are recorded when images are uploaded, OCR pipeline runs, declarations are reviewed, or the inspection is finalized.
        </p>
      </div>
    );
  }

  const getEventCategory = (action: string) => {
    switch (action) {
      case 'INSPECTION_FINALIZED':
        return { label: 'Finalization', color: 'bg-emerald-50 text-emerald-800 border-emerald-200', icon: Lock };
      case 'INSPECTION_REVIEWED':
      case 'DECLARATION_UPDATED':
        return { label: 'Officer Action', color: 'bg-amber-50 text-amber-800 border-amber-200', icon: User };
      case 'RULES_EVALUATED':
      case 'PIPELINE_EXECUTED':
        return { label: 'Deterministic Engine', color: 'bg-sky-50 text-sky-800 border-sky-200', icon: Cpu };
      case 'IMAGE_UPLOADED':
      case 'QUALITY_GATE_EVALUATED':
        return { label: 'Evidence Ingestion', color: 'bg-indigo-50 text-indigo-800 border-indigo-200', icon: Camera };
      default:
        return { label: 'System Event', color: 'bg-slate-100 text-slate-700 border-slate-200', icon: Clock };
    }
  };

  return (
    <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-6 text-slate-900 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <History className="h-4 w-4 text-sky-600" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
            Inspection Replay &amp; Chronological Audit Trail
          </h3>
        </div>
        <span className="text-[10px] font-mono font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
          {auditLogs.length} Total Lifecycle Events
        </span>
      </div>

      {/* Timeline Stream */}
      <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {auditLogs.map((log, idx) => {
          const cat = getEventCategory(log.action);
          const date = new Date(log.created_at);

          return (
            <div key={log.id || idx} className="relative group">
              {/* Timeline Dot */}
              <div className="absolute -left-6 top-1 h-4 w-4 rounded-full bg-white border-2 border-sky-600 flex items-center justify-center shadow-xs">
                <span className="h-1 w-1 rounded-full bg-sky-600" />
              </div>

              <div className="p-3.5 bg-slate-50/80 rounded-2xl border border-slate-200/80 space-y-2 text-xs hover:bg-white hover:border-slate-300 transition shadow-xs">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold border ${cat.color}`}>
                      {cat.label}
                    </span>
                    <span className="font-bold text-slate-900 font-mono">
                      {log.action}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono font-medium">
                    {date.toLocaleDateString('en-IN')}{' '}
                    {date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </div>
                </div>

                {/* Actor & Entity Info */}
                <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-600">
                  {log.actor_user_id && (
                    <div className="flex items-center gap-1 font-mono">
                      <User className="h-3 w-3 text-slate-400" />
                      <span>Actor: {log.actor_user_id.slice(0, 8)}...</span>
                    </div>
                  )}
                  {log.entity_type && (
                    <div className="text-slate-500 font-mono text-[10px]">
                      Target: {log.entity_type} {log.entity_id ? `(${log.entity_id.slice(0, 8)}...)` : ''}
                    </div>
                  )}
                </div>

                {/* Metadata JSON details if present */}
                {log.metadata_json && Object.keys(log.metadata_json).length > 0 && (
                  <div className="mt-1 p-2 rounded-xl bg-white border border-slate-200 font-mono text-[10px] text-slate-600 overflow-x-auto">
                    {JSON.stringify(log.metadata_json)}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="text-[10px] text-slate-500 pt-2 border-t border-slate-100 italic">
        * Immutable chronological audit records are preserved in compliance with government legal metrology chain-of-custody standards.
      </div>
    </div>
  );
}
