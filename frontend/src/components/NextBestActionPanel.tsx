'use client';

import React from 'react';
import { ActionRecommendation, CasePriority, InspectionImage, Declaration } from '@/types';
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
  Camera,
  AlertOctagon,
} from 'lucide-react';

interface NextBestActionPanelProps {
  recommendations?: ActionRecommendation[];
  images?: InspectionImage[];
  declaration?: Declaration | null;
  onActionClick?: (target: string) => void;
}

export default function NextBestActionPanel({
  recommendations = [],
  images = [],
  declaration,
  onActionClick,
}: NextBestActionPanelProps) {
  // Check for optical quality flags in current images
  const opticalFlagImages = images.filter((img) => {
    const qg = img.quality_gate_result;
    return qg && (qg.blur_detected || qg.glare_detected || qg.decision === 'RETAKE_RECOMMENDED');
  });

  const hasOpticalFlag = opticalFlagImages.length > 0;
  const hasPhysicalMeasurement = Boolean(declaration?.measurement_data);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-amber-600" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
            Next Best Action &amp; Officer Guidance
          </h3>
        </div>
        <span className="text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded font-mono">
          ADVISORY ONLY
        </span>
      </div>

      <div className="space-y-3">
        {/* Optical Quality Flag Warning (if present) */}
        {hasOpticalFlag && (
          <div className="p-3 bg-orange-50 border border-orange-200 rounded-xl text-xs space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold text-orange-950">
                <Camera className="h-4 w-4 text-orange-600 shrink-0" />
                <span>Optical Evidence Gating Alert</span>
              </div>
              <span className="text-[10px] font-semibold bg-orange-200 text-orange-900 px-1.5 py-0.2 rounded">
                RETAKE ADVISED
              </span>
            </div>
            <p className="text-[11px] text-orange-900/90 leading-relaxed">
              Specular glare or blur was flagged on {opticalFlagImages.length} package surface(s). Retake under diffused lighting to avoid OCR uncertainty.
            </p>
            {onActionClick && (
              <button
                type="button"
                onClick={() => onActionClick('evidence')}
                className="text-[11px] font-bold text-orange-800 hover:text-orange-900 flex items-center gap-1 transition"
              >
                Inspect Affected Image <ArrowRight className="h-3 w-3" />
              </button>
            )}
          </div>
        )}

        {/* Physical Measurement Missing (if applicable) */}
        {!hasPhysicalMeasurement && (
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold text-slate-800">
                <Scale className="h-4 w-4 text-slate-600 shrink-0" />
                <span>Physical Verification Required</span>
              </div>
              <span className="text-[10px] font-semibold bg-slate-200 text-slate-700 px-1.5 py-0.2 rounded">
                RULE 19 / SCHED VI
              </span>
            </div>
            <div className="text-[11px] text-slate-600 space-y-0.5">
              <div>
                Declared Net Quantity:{' '}
                <span className="font-mono font-bold text-slate-800">
                  {declaration?.net_quantity || 'Not declared'}
                </span>
              </div>
              <div>Physical scale measurement: <span className="italic text-slate-400">Not recorded</span></div>
            </div>
            <p className="text-[10px] text-slate-500">
              Recommended: Perform field or laboratory gravimetric verification to evaluate Maximum Permissible Error (MPE).
            </p>
            {onActionClick && (
              <a
                href="/gravimetric"
                className="inline-flex items-center gap-1 text-[11px] font-bold text-brand-900 hover:text-brand-800 transition pt-1"
              >
                Open Gravimetric Workspace <ArrowRight className="h-3 w-3" />
              </a>
            )}
          </div>
        )}

        {/* Backend Intelligence Recommendations */}
        {recommendations.length > 0 ? (
          <div className="space-y-2 pt-1">
            {recommendations.slice(0, 3).map((rec) => (
              <div
                key={rec.code}
                className="p-3 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition space-y-1.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 font-bold text-xs text-slate-900">
                    <AlertCircle className="h-3.5 w-3.5 text-sky-600 shrink-0" />
                    <span>{rec.title}</span>
                  </div>
                  <span className="text-[9px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                    {rec.category.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  {rec.description}
                </p>
                {rec.action_label && onActionClick && (
                  <button
                    type="button"
                    onClick={() => {
                      if (rec.category === 'VERIFICATION') onActionClick('declarations');
                      else if (rec.category === 'EVIDENCE_COLLECTION') onActionClick('evidence');
                      else onActionClick('rules');
                    }}
                    className="text-[11px] font-bold text-sky-600 hover:text-sky-700 flex items-center gap-1 transition pt-0.5"
                  >
                    <span>{rec.action_label}</span>
                    <ArrowRight className="h-3 w-3" />
                  </button>
                )}
              </div>
            ))}
          </div>
        ) : !hasOpticalFlag && hasPhysicalMeasurement ? (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs space-y-1 text-emerald-900">
            <div className="flex items-center gap-2 font-bold text-emerald-800">
              <CheckCircle className="h-4 w-4 text-emerald-600" />
              <span>Evidence Sufficient</span>
            </div>
            <p className="text-[11px] text-emerald-800/80">
              All mandatory packaging surfaces, declarations, and measurements are recorded. No immediate evidence-collection action is currently indicated.
            </p>
          </div>
        ) : null}
      </div>

      {/* Advisory Microcopy Notice */}
      <div className="text-[10px] text-slate-400 italic pt-1 border-t border-slate-100">
        * All recommendations are automated decision-support signals. Authorized field officers determine investigative workflows.
      </div>
    </div>
  );
}

