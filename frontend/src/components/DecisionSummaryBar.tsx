'use client';

import React from 'react';
import { Inspection, ComplianceResult, ComplianceCheck, Violation } from '@/types';
import {
  ShieldCheck,
  ShieldAlert,
  Clock,
  CheckCircle2,
  Lock,
  Building2,
  MapPin,
  Calendar,
  User as UserIcon,
  Package,
  FileText,
  History,
  RotateCw,
  ArrowLeft,
  Scale,
  ExternalLink,
} from 'lucide-react';

interface DecisionSummaryBarProps {
  inspection: Inspection;
  checks: ComplianceCheck[];
  violations: Violation[];
  onReevaluate?: () => void;
  isReevaluating?: boolean;
  onJumpToSection?: (sectionId: string) => void;
}

export default function DecisionSummaryBar({
  inspection,
  checks = [],
  violations = [],
  onReevaluate,
  isReevaluating = false,
  onJumpToSection,
}: DecisionSummaryBarProps) {
  const verdict = inspection.statutory_verdict || inspection.overall_result;
  const isCompleted = inspection.status === 'COMPLETED';

  const passedChecks = checks.filter((c) => c.result === 'PASS').length;
  const failedChecks = checks.filter((c) => c.result === 'FAIL').length;
  const reviewChecks = checks.filter((c) => c.result === 'REVIEW').length;
  const totalChecks = checks.length;

  const getVerdictBadge = (res: ComplianceResult | undefined | null) => {
    switch (res) {
      case 'COMPLIANT':
        return (
          <span className="inline-flex items-center gap-1.5 bg-emerald-500/10 text-emerald-700 border border-emerald-500/30 px-3 py-1 rounded-full text-xs font-black tracking-wide">
            <ShieldCheck className="h-4 w-4 text-emerald-600" /> COMPLIANT
          </span>
        );
      case 'NON_COMPLIANT':
        return (
          <span className="inline-flex items-center gap-1.5 bg-rose-500/10 text-rose-700 border border-rose-500/30 px-3 py-1 rounded-full text-xs font-black tracking-wide">
            <ShieldAlert className="h-4 w-4 text-rose-600" /> NON-COMPLIANT
          </span>
        );
      case 'NEEDS_REVIEW':
        return (
          <span className="inline-flex items-center gap-1.5 bg-amber-500/10 text-amber-800 border border-amber-500/30 px-3 py-1 rounded-full text-xs font-black tracking-wide">
            <Clock className="h-4 w-4 text-amber-600" /> NEEDS REVIEW
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 bg-slate-100 text-slate-700 border border-slate-300 px-3 py-1 rounded-full text-xs font-bold tracking-wide">
            PENDING
          </span>
        );
    }
  };

  const getLifecycleBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-800 border border-emerald-300 font-bold px-2.5 py-1 rounded-lg text-xs">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> COMPLETED
          </span>
        );
      case 'REVIEW_REQUIRED':
        return (
          <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-800 border border-amber-300 font-bold px-2.5 py-1 rounded-lg text-xs">
            <Clock className="h-3.5 w-3.5 text-amber-600" /> REVIEW REQUIRED
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1 bg-sky-50 text-sky-800 border border-sky-300 font-bold px-2.5 py-1 rounded-lg text-xs">
            <RotateCw className="h-3.5 w-3.5 text-sky-600 animate-spin" /> PROCESSING
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 bg-slate-100 text-slate-700 border border-slate-300 font-semibold px-2.5 py-1 rounded-lg text-xs">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* 1. Header Card (Translucent Modern Light Workstation Header) */}
      <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 p-6 rounded-3xl shadow-sm text-slate-900">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-2">
            {/* Top Navigation & ID Pill */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <a
                href="/inspections"
                className="font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1 transition-colors"
              >
                <ArrowLeft className="h-3.5 w-3.5" /> Back to Inspections
              </a>
              <span className="text-slate-300">•</span>
              <span className="font-mono font-bold text-sky-800 bg-sky-50 px-2.5 py-0.5 rounded-lg border border-sky-200">
                #INS-{inspection.id.slice(0, 8).toUpperCase()}
              </span>
              <span className="text-slate-300">•</span>
              {getLifecycleBadge(inspection.status)}
              {getVerdictBadge(verdict)}
            </div>

            {/* Commodity Name / Inspection Title */}
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
                <Package className="h-6 w-6 text-sky-600 shrink-0" />
                <span>
                  {inspection.declaration?.commodity_name ||
                    inspection.store_name ||
                    'Packaged Retail Commodity'}
                </span>
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Statutory Inspection Case under Legal Metrology (Packaged Commodities) Rules, 2011
              </p>
            </div>

            {/* Metadata Badges Strip */}
            <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 text-xs text-slate-600 pt-1">
              <div className="flex items-center gap-1.5">
                <Building2 className="h-3.5 w-3.5 text-slate-400" />
                <span className="font-semibold text-slate-800">
                  {inspection.store_name || 'Retail Establishment'}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-slate-400" />
                <span>
                  {inspection.district || 'District N/A'}, {inspection.state || 'DL'}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-slate-400" />
                <span>
                  {new Date(inspection.created_at).toLocaleString('en-IN', {
                    timeZone: 'Asia/Kolkata',
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  })}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <UserIcon className="h-3.5 w-3.5 text-slate-400" />
                <span>
                  Officer: {inspection.inspector?.name || 'Assigned Officer'}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex flex-wrap items-center gap-2 lg:self-start shrink-0">
            {onJumpToSection && (
              <>
                <button
                  type="button"
                  onClick={() => onJumpToSection('reports')}
                  className="px-3.5 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200/90 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
                >
                  <FileText className="h-3.5 w-3.5 text-sky-600" />
                  Generate Report
                </button>
                <button
                  type="button"
                  onClick={() => onJumpToSection('replay')}
                  className="px-3.5 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200/90 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
                >
                  <History className="h-3.5 w-3.5 text-indigo-600" />
                  Audit Trail
                </button>
              </>
            )}

            {!isCompleted && onReevaluate && (
              <button
                type="button"
                onClick={onReevaluate}
                disabled={isReevaluating}
                className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 transition shadow-xs disabled:opacity-50 cursor-pointer"
              >
                <RotateCw className={`h-3.5 w-3.5 ${isReevaluating ? 'animate-spin' : ''}`} />
                {isReevaluating ? 'Evaluating...' : 'Re-Evaluate Rules'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 2. Finalized / In-Progress Banner (Translucent Soft Tint) */}
      {isCompleted ? (
        <div className="bg-emerald-50/80 backdrop-blur-sm border border-emerald-200/90 rounded-2xl p-4.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-emerald-950 shadow-2xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-100/90 rounded-xl border border-emerald-300/80 text-emerald-700 shadow-2xs shrink-0">
              <Lock className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <div className="font-bold text-emerald-950 text-sm flex items-center gap-2">
                <span>INSPECTION FINALIZED</span>
                <span className="text-[10px] bg-emerald-200/70 text-emerald-900 border border-emerald-300 px-2 py-0.5 rounded font-mono font-bold">
                  HTTP 409 MUTATION LOCKED
                </span>
              </div>
              <p className="text-emerald-800/90 text-xs mt-0.5">
                This inspection has been finalized by an authorized Legal Metrology officer. The inspection record is locked against modifications.
              </p>
            </div>
          </div>
          {inspection.finalized_at && (
            <div className="text-[11px] font-mono text-emerald-800 shrink-0 self-start sm:self-auto bg-emerald-100/80 px-3 py-1 rounded-lg border border-emerald-200">
              Finalized: {new Date(inspection.finalized_at).toLocaleDateString()}
            </div>
          )}
        </div>
      ) : (
        <div className="bg-sky-50/80 backdrop-blur-sm border border-sky-200/90 rounded-2xl p-4 flex items-center justify-between gap-3 text-sky-950 text-xs shadow-2xs">
          <div className="flex items-center gap-2.5">
            <span className="h-2.5 w-2.5 rounded-full bg-sky-500 animate-pulse" />
            <div>
              <span className="font-bold text-sky-950">INSPECTION IN PROGRESS:</span>
              <span className="text-sky-800/90 ml-1.5">
                This inspection remains active and editable according to authorized field officer review workflow.
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 3. Statutory Decision Summary Card (Translucent Modern Light Gradient) */}
      <div
        className={`rounded-3xl p-6 border shadow-sm text-slate-900 transition-all ${
          verdict === 'COMPLIANT'
            ? 'bg-gradient-to-r from-emerald-50/90 via-white to-emerald-50/40 border-emerald-200/90'
            : verdict === 'NON_COMPLIANT'
            ? 'bg-gradient-to-r from-rose-50/90 via-white to-rose-50/40 border-rose-200/90'
            : 'bg-gradient-to-r from-amber-50/90 via-white to-amber-50/40 border-amber-200/90'
        }`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="text-[10px] uppercase font-bold tracking-widest text-slate-400">
              Statutory Decision
            </div>
            <div className="text-2xl sm:text-3xl font-black tracking-tight flex items-center gap-2.5">
              {verdict === 'COMPLIANT' && (
                <>
                  <ShieldCheck className="h-8 w-8 text-emerald-600 shrink-0" />
                  <span className="text-emerald-700">COMPLIANT</span>
                </>
              )}
              {verdict === 'NON_COMPLIANT' && (
                <>
                  <ShieldAlert className="h-8 w-8 text-rose-600 shrink-0" />
                  <span className="text-rose-700">NON-COMPLIANT</span>
                </>
              )}
              {verdict === 'NEEDS_REVIEW' && (
                <>
                  <Clock className="h-8 w-8 text-amber-600 shrink-0" />
                  <span className="text-amber-800">NEEDS REVIEW</span>
                </>
              )}
              {!['COMPLIANT', 'NON_COMPLIANT', 'NEEDS_REVIEW'].includes(verdict as string) && (
                <>
                  <RotateCw className="h-8 w-8 text-slate-400 shrink-0" />
                  <span className="text-slate-700">PENDING EVALUATION</span>
                </>
              )}
            </div>

            <p className="text-xs text-slate-600 max-w-2xl leading-relaxed">
              {verdict === 'COMPLIANT' &&
                `${passedChecks} of ${totalChecks} statutory checks verified. Package satisfies all mandatory Legal Metrology (Packaged Commodities) Rules, 2011 provisions.`}
              {verdict === 'NON_COMPLIANT' &&
                `Deterministic rule evaluation identified ${failedChecks} statutory violation(s) across ${totalChecks} evaluated provisions. Review the specific findings below.`}
              {verdict === 'NEEDS_REVIEW' &&
                'Evidence is insufficient or conflicting for a deterministic disposition; routed for human officer adjudication under the zero-false-certainty safety invariant.'}
              {!['COMPLIANT', 'NON_COMPLIANT', 'NEEDS_REVIEW'].includes(verdict as string) &&
                'Evidence collection in progress. Rule matrix will evaluate upon image registration.'}
            </p>
          </div>

          <div className="bg-white/90 backdrop-blur-xs p-4 rounded-2xl border border-slate-200/80 text-xs space-y-1 shrink-0 shadow-2xs">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">
              Legal Corpus
            </div>
            <div className="font-mono font-bold text-sky-700 text-xs">
              SIH-OFFICIAL-LEGAL-DATASET-2011
            </div>
            <div className="text-[10px] text-slate-500">
              Deterministic rule evaluation • Zero generative distortion
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

