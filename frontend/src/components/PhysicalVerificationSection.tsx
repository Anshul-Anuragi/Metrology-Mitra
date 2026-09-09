'use client';

import React from 'react';
import { Declaration } from '@/types';
import {
  Scale,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Info,
  Layers,
  HelpCircle,
} from 'lucide-react';

interface PhysicalVerificationSectionProps {
  declaration?: Declaration | null;
}

export default function PhysicalVerificationSection({
  declaration,
}: PhysicalVerificationSectionProps) {
  const measurementData = declaration?.measurement_data;
  const declaredQtyStr = declaration?.net_quantity || 'Not declared';

  // Parse numeric declared quantity if available
  const matchQty = declaredQtyStr.match(/(\d+(?:\.\d+)?)\s*(g|kg|ml|l|m|cm|units?)/i);
  const declaredValue = matchQty ? parseFloat(matchQty[1]) : null;
  const declaredUnit = matchQty ? matchQty[2].toLowerCase() : '';

  // Extract recorded measurement data if present
  const measuredValue = measurementData?.measured_net_quantity ?? measurementData?.net_weight_g ?? null;
  const tareWeight = measurementData?.tare_weight_g ?? null;
  const grossWeight = measurementData?.gross_weight_g ?? null;

  const hasMeasurement = measuredValue !== null && measuredValue !== undefined;

  let difference: number | null = null;
  let percentDiff: number | null = null;
  if (hasMeasurement && declaredValue !== null) {
    // normalize kg to g if needed
    const normDeclared = declaredUnit === 'kg' || declaredUnit === 'l' ? declaredValue * 1000 : declaredValue;
    const normMeasured = measuredValue;
    difference = normMeasured - normDeclared;
    percentDiff = (difference / normDeclared) * 100;
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <Scale className="h-4 w-4 text-brand-900" />
          <h3 className="text-sm font-bold text-slate-900">
            Physical Quantity &amp; Gravimetric Verification
          </h3>
        </div>
        <span className="text-[10px] font-mono font-bold bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded border border-slate-200">
          RULE 19 &amp; SIXTH SCHEDULE
        </span>
      </div>

      {hasMeasurement ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
              <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                Declared Net Quantity
              </div>
              <div className="text-base font-black text-slate-900 font-mono mt-0.5">
                {declaredQtyStr}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">Printed on package PDP</div>
            </div>

            <div className="p-3 bg-sky-50/60 rounded-xl border border-sky-200">
              <div className="text-[10px] text-sky-800 uppercase tracking-wider font-semibold">
                Measured Net Quantity
              </div>
              <div className="text-base font-black text-sky-950 font-mono mt-0.5">
                {measuredValue} g
              </div>
              <div className="text-[10px] text-sky-700 mt-0.5">Field digital scale reading</div>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
              <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                Difference (Δ)
              </div>
              <div
                className={`text-base font-black font-mono mt-0.5 ${
                  difference !== null && difference >= 0 ? 'text-emerald-700' : 'text-rose-700'
                }`}
              >
                {difference !== null ? `${difference >= 0 ? '+' : ''}${difference.toFixed(1)} g` : 'N/A'}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                {percentDiff !== null ? `${percentDiff >= 0 ? '+' : ''}${percentDiff.toFixed(2)}% deviation` : ''}
              </div>
            </div>

            <div className="p-3 bg-emerald-50/60 rounded-xl border border-emerald-200">
              <div className="text-[10px] text-emerald-800 uppercase tracking-wider font-semibold">
                Sixth Schedule Result
              </div>
              <div className="text-sm font-black text-emerald-950 flex items-center gap-1 mt-0.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" /> PASS
              </div>
              <div className="text-[10px] text-emerald-700 mt-0.5">Within permissible error</div>
            </div>
          </div>

          {(grossWeight !== null || tareWeight !== null) && (
            <div className="flex flex-wrap gap-4 text-xs text-slate-600 p-2.5 bg-slate-50 rounded-lg border border-slate-200 font-mono">
              {grossWeight !== null && <div>Gross Weight: <span className="font-bold text-slate-900">{grossWeight} g</span></div>}
              {tareWeight !== null && <div>Tare Weight: <span className="font-bold text-slate-900">{tareWeight} g</span></div>}
            </div>
          )}
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-800">
                <HelpCircle className="h-4 w-4 text-slate-400" />
                <span>Physical Measurement Not Recorded</span>
              </div>
              <p className="text-xs text-slate-500 max-w-xl leading-relaxed">
                No physical gravimetric measurement is attached to this inspection record. For retail inspections requiring net-content audit, field officers perform scale tare and net-content determination.
              </p>
            </div>
            <a
              href="/gravimetric"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-900 hover:bg-brand-800 text-white rounded-lg text-xs font-bold transition shrink-0 shadow-xs"
            >
              Open Gravimetric Tool <ArrowRight className="h-3.5 w-3.5" />
            </a>
          </div>

          <div className="text-[11px] font-mono text-slate-500 bg-white p-2.5 rounded-lg border border-slate-200 flex items-center justify-between">
            <span>Declared Net Quantity: <strong className="text-slate-900">{declaredQtyStr}</strong></span>
            <span className="text-slate-400">Tolerance Tier: Sched VI Table 1</span>
          </div>
        </div>
      )}

      {/* Statutory Disclaimer */}
      <div className="text-[10px] text-slate-400 italic">
        * Determination of Net Quantity follows Sixth Schedule procedures: sample average (x̄ ≥ Qn), and individual pack deficit cannot exceed maximum permissible negative error (MPE).
      </div>
    </div>
  );
}

