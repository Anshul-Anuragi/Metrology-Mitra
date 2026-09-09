'use client';

import React, { useState } from 'react';
import {
  Package,
  Camera,
  Layers,
  Sparkles,
  Scale,
  ShieldCheck,
  ShieldAlert,
  Clock,
  ChevronDown,
  ChevronUp,
  Info,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react';
import { ComplianceResult } from '@/types';

interface DecisionPipelineVisualizerProps {
  imagesCount: number;
  tokensCount?: number;
  checksCount: number;
  passedChecksCount: number;
  verdict: ComplianceResult | string;
  hasBarcode?: boolean;
  hasGravimetric?: boolean;
}

export default function DecisionPipelineVisualizer({
  imagesCount,
  tokensCount,
  checksCount,
  passedChecksCount,
  verdict,
  hasBarcode = false,
  hasGravimetric = false,
}: DecisionPipelineVisualizerProps) {
  const [showExplainer, setShowExplainer] = useState(false);

  const steps = [
    {
      step: '1',
      title: 'PACKAGE',
      subtitle: 'Retail Unit',
      desc: 'Physical packaging & establishment premises',
      status: 'Captured',
      icon: Package,
      active: true,
      badge: 'Master Unit',
    },
    {
      step: '2',
      title: 'EVIDENCE',
      subtitle: `${imagesCount} Photo${imagesCount === 1 ? '' : 's'}`,
      desc: hasBarcode ? 'Images + Barcode detected' : 'Images captured',
      status: imagesCount > 0 ? 'Verified' : 'Pending',
      icon: Camera,
      active: imagesCount > 0,
      badge: `${imagesCount} Source${imagesCount === 1 ? '' : 's'}`,
    },
    {
      step: '3',
      title: 'FUSION',
      subtitle: 'Multi-Modal',
      desc: 'OCR consensus & cross-variant stability',
      status: 'Corroborated',
      icon: Layers,
      active: true,
      badge: 'Consensus',
    },
    {
      step: '4',
      title: 'LEGAL RULES',
      subtitle: `${checksCount} Checks`,
      desc: 'LMPC 2011 deterministic rule engine',
      status: 'Evaluated',
      icon: Scale,
      active: checksCount > 0,
      badge: `${passedChecksCount}/${checksCount} Pass`,
    },
    {
      step: '5',
      title: 'DECISION',
      subtitle: verdict,
      desc: 'Statutory verdict under officer supervision',
      status: verdict,
      icon:
        verdict === 'COMPLIANT'
          ? ShieldCheck
          : verdict === 'NON_COMPLIANT'
          ? ShieldAlert
          : Clock,
      active: true,
      badge: 'Finalized',
    },
  ];

  return (
    <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-6 text-slate-900 shadow-sm space-y-4">
      {/* Top Header & Toggle */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-sky-600" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Inspection Evidence → Rule → Decision Pipeline
          </h2>
        </div>
        <button
          type="button"
          onClick={() => setShowExplainer(!showExplainer)}
          className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1 transition cursor-pointer"
        >
          <span>How MatrologyMitra Decides</span>
          {showExplainer ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
        </button>
      </div>

      {/* Horizontal Pipeline Steps */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
        {steps.map((s, idx) => {
          const Icon = s.icon;
          const isVerdict = idx === 4;

          return (
            <div
              key={s.step}
              className={`p-3.5 rounded-2xl border transition-all flex flex-col justify-between shadow-2xs ${
                isVerdict
                  ? verdict === 'COMPLIANT'
                    ? 'bg-emerald-50/90 border-emerald-300 text-emerald-950'
                    : verdict === 'NON_COMPLIANT'
                    ? 'bg-rose-50/90 border-rose-300 text-rose-950'
                    : 'bg-amber-50/90 border-amber-300 text-amber-950'
                  : 'bg-slate-50/80 hover:bg-slate-100/70 border-slate-200/80 text-slate-800'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold text-slate-400">
                  0{s.step}
                </span>
                <span
                  className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded shadow-2xs ${
                    isVerdict
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : 'bg-white text-slate-700 border border-slate-200'
                  }`}
                >
                  {s.badge}
                </span>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-1.5 font-bold text-xs text-slate-900">
                  <Icon
                    className={`h-3.5 w-3.5 ${
                      isVerdict
                        ? verdict === 'COMPLIANT'
                          ? 'text-emerald-600'
                          : verdict === 'NON_COMPLIANT'
                          ? 'text-rose-600'
                          : 'text-amber-600'
                        : 'text-sky-600'
                    }`}
                  />
                  <span>{s.title}</span>
                </div>
                <div className="text-[11px] font-semibold text-slate-600 truncate">
                  {s.subtitle}
                </div>
                <div className="text-[10px] text-slate-500 leading-tight">
                  {s.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Expandable "HOW MATROLOGYMITRA DECIDES" Methodology Drawer */}
      {showExplainer && (
        <div className="mt-4 p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-3 animate-fadeIn">
          <div className="font-bold text-slate-800 flex items-center gap-2">
            <Info className="h-4 w-4 text-sky-600" />
            <span>Deterministic Legal Metrology Adjudication Architecture</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-slate-700">
            <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-1 shadow-2xs">
              <div className="font-bold text-sky-700">1. Evidence Capture</div>
              <p className="text-[11px] text-slate-500">
                Multi-surface package photography with camera pre-flight gating and SHA-256 byte-level cryptographic fingerprinting.
              </p>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-1 shadow-2xs">
              <div className="font-bold text-sky-700">2. Optical Quality Gate</div>
              <p className="text-[11px] text-slate-500">
                Automated Laplacian blur and specular glare diagnostics to detect irrecoverable image defects before analysis.
              </p>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-1 shadow-2xs">
              <div className="font-bold text-sky-700">3. Multi-Variant Consensus</div>
              <p className="text-[11px] text-slate-500">
                Multiple deterministic preprocessing variants (local contrast, binarization) run in parallel to corroborate tokens.
              </p>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-1 shadow-2xs">
              <div className="font-bold text-sky-700">4. Declaration Fusion</div>
              <p className="text-[11px] text-slate-500">
                Perception consensus tags declarations as CONFIRMED, PROBABLE, CONFLICTING, or MISSING without collapsing uncertainty.
              </p>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-1 shadow-2xs">
              <div className="font-bold text-emerald-700">5. Rule Applicability</div>
              <p className="text-[11px] text-slate-500">
                Determines statutory scope under Rule 3 and Rule 26 exclusions (wholesale, institutional, weight exemptions).
              </p>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-1 shadow-2xs">
              <div className="font-bold text-emerald-700">6. Deterministic LMPC Rules</div>
              <p className="text-[11px] text-slate-500">
                Rules 6, 7, 18, 19 evaluated against the official Legal Metrology dataset without generative AI distortion.
              </p>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-1 shadow-2xs">
              <div className="font-bold text-amber-700">7. Officer Review &amp; Routing</div>
              <p className="text-[11px] text-slate-500">
                Any ambiguity, missing declarations, or optical flags are routed to authorized officer adjudication (NEEDS_REVIEW).
              </p>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-1 shadow-2xs">
              <div className="font-bold text-indigo-700">8. Mutation Lock &amp; Audit</div>
              <p className="text-[11px] text-slate-500">
                Finalized inspection is permanently locked (HTTP 409) with full cryptographic SHA-256 audit trail preserved.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

