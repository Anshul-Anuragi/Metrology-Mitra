'use client';

import React, { useState } from 'react';
import { EvidenceCompleteness, EvidenceFacet, EvidenceGap } from '@/types';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Layers,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  Info,
  Sparkles,
} from 'lucide-react';

interface EvidenceCompletenessCardProps {
  completeness: EvidenceCompleteness;
  onRefresh?: () => void;
}

export function EvidenceCompletenessCard({ completeness, onRefresh }: EvidenceCompletenessCardProps) {
  const [expandedFacet, setExpandedFacet] = useState<string | null>(null);

  const getScoreColor = (score: number) => {
    if (score >= 85) return { text: 'text-emerald-700', bg: 'bg-emerald-600', ring: 'border-emerald-200' };
    if (score >= 65) return { text: 'text-sky-700', bg: 'bg-sky-600', ring: 'border-sky-200' };
    if (score >= 40) return { text: 'text-amber-700', bg: 'bg-amber-600', ring: 'border-amber-200' };
    return { text: 'text-rose-700', bg: 'bg-rose-600', ring: 'border-rose-200' };
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETE':
        return (
          <span className="px-2 py-0.5 rounded-lg text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3 text-emerald-600" /> COMPLETE
          </span>
        );
      case 'PARTIAL':
        return (
          <span className="px-2 py-0.5 rounded-lg text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1">
            <AlertTriangle className="h-3 w-3 text-amber-600" /> PARTIAL
          </span>
        );
      case 'MISSING':
        return (
          <span className="px-2 py-0.5 rounded-lg text-[10px] font-bold bg-rose-50 text-rose-800 border border-rose-200 flex items-center gap-1">
            <XCircle className="h-3 w-3 text-rose-600" /> MISSING
          </span>
        );
      case 'NOT_APPLICABLE':
      default:
        return (
          <span className="px-2 py-0.5 rounded-lg text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200">
            N/A
          </span>
        );
    }
  };

  const colors = getScoreColor(completeness.score);

  return (
    <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-6 shadow-sm space-y-5 text-slate-900">
      {/* Header & Gauge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-cyan-600" />
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Evidence Completeness Index
            </h3>
            <span className="text-[10px] bg-cyan-50 text-cyan-800 font-mono font-bold px-2 py-0.5 rounded-full border border-cyan-200">
              6 Facets
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Measures data sufficiency for inspection adjudication. (Not a legal compliance score).
          </p>
        </div>

        {/* Circular / Pill Score Display */}
        <div className="flex items-center gap-3 bg-slate-50/80 px-4 py-2 rounded-2xl border border-slate-200/80 self-start sm:self-auto shadow-xs">
          <div className="text-right">
            <div className={`text-xl font-mono font-bold ${colors.text}`}>
              {completeness.score.toFixed(0)}%
            </div>
            <div className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">
              {completeness.status}
            </div>
          </div>
          <div className="w-12 h-2 bg-slate-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${colors.bg} transition-all duration-500`}
              style={{ width: `${completeness.score}%` }}
            />
          </div>
        </div>
      </div>

      {/* Six Evidentiary Facets Grid */}
      <div className="space-y-2">
        <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
          Evidentiary Facets Breakdown
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
          {completeness.facets.map((facet) => {
            const isExpanded = expandedFacet === facet.facet_code;
            return (
              <div
                key={facet.facet_code}
                className={`p-3.5 rounded-2xl border transition-all ${
                  isExpanded ? 'bg-slate-50 border-slate-300 shadow-xs' : 'bg-white/80 border-slate-200/80 hover:bg-slate-50/60 hover:border-slate-300 shadow-xs'
                }`}
              >
                <div
                  className="flex items-center justify-between cursor-pointer select-none"
                  onClick={() => setExpandedFacet(isExpanded ? null : facet.facet_code)}
                >
                  <div className="space-y-0.5">
                    <div className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                      {facet.name}
                      <span className="text-[9px] text-slate-500 font-mono font-normal">(w:{facet.weight}%)</span>
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">
                      Score: {facet.score.toFixed(0)}%
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(facet.status)}
                    {isExpanded ? (
                      <ChevronUp className="h-3.5 w-3.5 text-slate-500" />
                    ) : (
                      <ChevronDown className="h-3.5 w-3.5 text-slate-500" />
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="mt-3 pt-2.5 border-t border-slate-200 space-y-2 text-[11px]">
                    {facet.evidence_present.length > 0 && (
                      <div>
                        <div className="font-bold text-emerald-700 text-[10px] mb-1">Observed Evidence:</div>
                        <ul className="list-disc list-inside space-y-0.5 text-slate-700">
                          {facet.evidence_present.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {facet.evidence_missing.length > 0 && (
                      <div>
                        <div className="font-bold text-rose-700 text-[10px] mb-1">Missing Evidence:</div>
                        <ul className="list-disc list-inside space-y-0.5 text-slate-600">
                          {facet.evidence_missing.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {facet.actionable_gap && (
                      <div className="p-2.5 bg-amber-50/90 rounded-xl border border-amber-200 text-amber-900 text-xs">
                        <span className="font-bold">Directive:</span> {facet.actionable_gap}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Actionable Evidence Gaps List */}
      {completeness.gaps.length > 0 && (
        <div className="space-y-2 pt-3 border-t border-slate-100">
          <div className="flex items-center gap-1.5 text-[11px] font-bold text-amber-700 uppercase tracking-wider">
            <AlertTriangle className="h-3.5 w-3.5" />
            Detected Evidence Gaps ({completeness.gaps.length})
          </div>
          <div className="space-y-2">
            {completeness.gaps.map((gap) => (
              <div
                key={gap.code}
                className="p-3.5 bg-amber-50/70 border border-amber-200/80 rounded-2xl space-y-1 text-xs shadow-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-amber-950">{gap.title}</span>
                  <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold ${
                    gap.is_blocking ? 'bg-rose-100 text-rose-800 border border-rose-200' : 'bg-slate-100 text-slate-700 border border-slate-200'
                  }`}>
                    {gap.is_blocking ? 'BLOCKING FINALIZATION' : 'ADVISORY GAP'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-700">{gap.description}</p>
                <div className="text-[11px] font-bold text-amber-900 pt-1">
                  Required Action: {gap.action}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statutory Disclaimer */}
      <div className="pt-2 border-t border-slate-100 text-[10px] text-slate-500 italic flex items-center gap-1.5">
        <Info className="h-3 w-3 text-slate-400 shrink-0" />
        {completeness.disclaimer}
      </div>
    </div>
  );
}

export default EvidenceCompletenessCard;

