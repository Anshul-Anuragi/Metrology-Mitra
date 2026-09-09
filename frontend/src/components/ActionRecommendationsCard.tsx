'use client';

import React from 'react';
import { ActionRecommendation, CasePriority, PriorityLevel } from '@/types';
import {
  Sparkles,
  ShieldAlert,
  AlertCircle,
  FileCheck,
  Scale,
  Building2,
  ArrowRight,
  Info,
  CheckCircle,
} from 'lucide-react';

interface ActionRecommendationsCardProps {
  priority: CasePriority;
  recommendations: ActionRecommendation[];
  onActionClick?: (rec: ActionRecommendation) => void;
}

export function ActionRecommendationsCard({
  priority,
  recommendations,
  onActionClick,
}: ActionRecommendationsCardProps) {
  const getPriorityBadge = (level: PriorityLevel) => {
    switch (level) {
      case 'CRITICAL':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-800 border border-rose-200 flex items-center gap-1.5 animate-pulse">
            <ShieldAlert className="h-3.5 w-3.5 text-rose-600" /> CRITICAL PRIORITY
          </span>
        );
      case 'HIGH':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1.5">
            <AlertCircle className="h-3.5 w-3.5 text-amber-600" /> HIGH PRIORITY
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-sky-50 text-sky-800 border border-sky-200 flex items-center gap-1.5">
            <Info className="h-3.5 w-3.5 text-sky-600" /> MEDIUM PRIORITY
          </span>
        );
      case 'LOW':
      default:
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1.5">
            <CheckCircle className="h-3.5 w-3.5 text-emerald-600" /> LOW PRIORITY
          </span>
        );
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'EVIDENCE_COLLECTION':
        return <FileCheck className="h-4 w-4 text-cyan-600" />;
      case 'VERIFICATION':
        return <Sparkles className="h-4 w-4 text-amber-600" />;
      case 'LEGAL_WORKFLOW':
        return <Scale className="h-4 w-4 text-rose-600" />;
      case 'SUPERVISORY_ACTION':
        return <Building2 className="h-4 w-4 text-emerald-600" />;
      default:
        return <Info className="h-4 w-4 text-slate-500" />;
    }
  };

  return (
    <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-6 shadow-sm space-y-5 text-slate-900">
      {/* Priority Banner Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-amber-600" />
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Case Priority &amp; Action Guidance
            </h3>
            <span className="text-[10px] bg-amber-50 text-amber-800 font-bold px-2 py-0.5 rounded-full border border-amber-200">
              ADVISORY
            </span>
          </div>
          <p className="text-xs text-slate-500">{priority.summary}</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs font-mono font-bold text-slate-600">
              Score: <span className="text-slate-900 text-sm font-bold">{priority.score.toFixed(0)}</span>/100
            </div>
          </div>
          {getPriorityBadge(priority.level)}
        </div>
      </div>

      {/* Priority Contributing Factors */}
      {priority.factors.length > 0 && (
        <div className="p-3.5 bg-slate-50/80 rounded-2xl border border-slate-200/80 space-y-2">
          <div className="text-[10px] font-bold text-slate-700 uppercase tracking-wider">
            Contributing Priority Factors
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {priority.factors.map((factor, idx) => (
              <div
                key={idx}
                className="text-[11px] p-2 bg-white rounded-xl border border-slate-200 flex items-start gap-2 shadow-xs"
              >
                <span className="text-amber-700 font-mono font-bold shrink-0">
                  +{factor.points_contributed.toFixed(0)}pt
                </span>
                <span className="text-slate-700">{factor.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Recommendations List */}
      <div className="space-y-2.5">
        <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
          Recommended Advisory Next Steps ({recommendations.length})
        </div>

        {recommendations.length === 0 ? (
          <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-200 text-center text-xs text-slate-500">
            No active advisory actions required for this inspection session.
          </div>
        ) : (
          <div className="space-y-2.5">
            {recommendations.map((rec) => (
              <div
                key={rec.code}
                className="p-4 bg-slate-50/60 rounded-2xl border border-slate-200/80 hover:bg-white hover:border-slate-300 transition space-y-2.5 shadow-xs"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    {getCategoryIcon(rec.category)}
                    <span className="text-xs font-bold text-slate-900">{rec.title}</span>
                  </div>
                  <span className="text-[9px] font-mono font-bold uppercase px-2 py-0.5 rounded-lg bg-slate-200/80 text-slate-700">
                    {rec.category.replace('_', ' ')}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">{rec.description}</p>

                {rec.related_rule && (
                  <div className="text-[10px] text-sky-700 font-semibold">
                    Statutory Context: {rec.related_rule}
                  </div>
                )}

                <div className="flex items-center justify-between pt-1 border-t border-slate-200/80">
                  <span className="text-[10px] text-slate-500 italic">
                    Decision-Support Guidance (Non-binding)
                  </span>
                  {onActionClick && (
                    <button
                      onClick={() => onActionClick(rec)}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-sky-700 hover:bg-sky-800 text-white rounded-xl text-xs font-bold transition shadow-xs cursor-pointer"
                    >
                      {rec.action_label} <ArrowRight className="h-3 w-3" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Mandatory Disclaimer */}
      <div className="pt-2 border-t border-slate-100 text-[10px] text-slate-500 italic flex items-center gap-1.5">
        <Info className="h-3 w-3 text-slate-400 shrink-0" />
        {priority.disclaimer}
      </div>
    </div>
  );
}

export default ActionRecommendationsCard;

