'use client';

import React from 'react';
import {
  Layers,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Barcode,
  Sparkles,
  ShieldAlert,
  Cpu,
} from 'lucide-react';

interface EvidenceFusionCardProps {
  fusedEvidence?: {
    original_image_hash?: string;
    overall_evidence_quality?: string;
    requires_human_review?: boolean;
    human_review_reasons?: string[];
    preprocessing_summary?: {
      total_variants_generated?: number;
      variant_names?: string[];
      selection_strategy?: string;
    };
    ocr_consensus?: {
      consensus?: {
        primary_variant?: string;
        stable_token_count?: number;
        unstable_token_count?: number;
        stability_ratio?: number;
        mean_confidence_across_variants?: number;
      };
    };
    barcode_quorum?: {
      winning_barcode?: string;
      winning_format?: string;
      quorum_count?: number;
      total_variants_evaluated?: number;
      catalog_verification?: {
        matched?: boolean;
        commodity_name?: string;
        standard_mrp?: number;
      };
    };
    fused_declarations?: {
      confirmed_count?: number;
      probable_count?: number;
      conflicting_count?: number;
      missing_count?: number;
      fused_fields?: Record<
        string,
        {
          field_name: string;
          statutory_rule: string;
          evidence_state: string;
          fused_value?: string;
          aggregate_confidence: number;
          supporting_variants?: string[];
          conflicting_variants?: string[];
          review_reason?: string;
        }
      >;
    };
  } | null;
}

export default function EvidenceFusionCard({ fusedEvidence }: EvidenceFusionCardProps) {
  if (!fusedEvidence) {
    return null;
  }

  const quality = fusedEvidence.overall_evidence_quality || 'UNKNOWN';
  const prep = fusedEvidence.preprocessing_summary;
  const ocr = fusedEvidence.ocr_consensus?.consensus;
  const barcode = fusedEvidence.barcode_quorum;
  const decls = fusedEvidence.fused_declarations;
  const fields = decls?.fused_fields ? Object.values(decls.fused_fields) : [];

  const qualityBadge = {
    HIGH: 'bg-emerald-50 text-emerald-800 border-emerald-300',
    MODERATE: 'bg-blue-50 text-blue-800 border-blue-300',
    DEGRADED: 'bg-amber-50 text-amber-800 border-amber-300',
    INSUFFICIENT: 'bg-rose-50 text-rose-800 border-rose-300',
    UNKNOWN: 'bg-slate-100 text-slate-700 border-slate-300',
  }[quality] || 'bg-slate-100 text-slate-700 border-slate-300';

  return (
    <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-6 shadow-sm space-y-4 text-slate-900">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-indigo-50 border border-indigo-200/80 rounded-xl text-indigo-600 shadow-2xs">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              Multi-Variant Perception &amp; Evidence Fusion
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                Phase 4.3 Engine
              </span>
            </h3>
            <p className="text-[11px] text-slate-500">
              Corroborated across {prep?.total_variants_generated || 1} deterministic image derivatives with in-memory provenance
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-lg border ${qualityBadge}`}>
            Quality: {quality}
          </span>
          {fusedEvidence.requires_human_review && (
            <span className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-amber-50 text-amber-800 border border-amber-300 flex items-center gap-1">
              <AlertTriangle className="h-3 w-3 text-amber-600" />
              Human Review Directives
            </span>
          )}
        </div>
      </div>

      {/* Review Directives Alert Banner */}
      {fusedEvidence.requires_human_review && fusedEvidence.human_review_reasons && fusedEvidence.human_review_reasons.length > 0 && (
        <div className="p-3.5 bg-amber-50/80 border border-amber-200 rounded-2xl space-y-1">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-900">
            <ShieldAlert className="h-3.5 w-3.5 text-amber-600 shrink-0" />
            Inspection Review Directives:
          </div>
          <ul className="text-[11px] text-amber-800 pl-5 list-disc space-y-0.5">
            {fusedEvidence.human_review_reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Metrics Row: Preprocessing Derivatives, OCR Stability, Barcode Quorum */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Preprocessing Derivatives */}
        <div className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-4 space-y-1.5 shadow-2xs">
          <div className="text-[11px] font-semibold text-slate-600 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Cpu className="h-3.5 w-3.5 text-sky-600" />
              Derivatives Generated
            </span>
            <span className="font-mono text-sky-700 font-bold">{prep?.total_variants_generated || 0}</span>
          </div>
          <div className="flex flex-wrap gap-1 pt-1">
            {(prep?.variant_names || []).map((name) => (
              <span
                key={name}
                className="text-[9px] font-mono px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-700 shadow-2xs"
              >
                {name}
              </span>
            ))}
          </div>
        </div>

        {/* OCR Stability */}
        <div className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-4 space-y-1.5 shadow-2xs">
          <div className="text-[11px] font-semibold text-slate-600 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
              OCR Token Stability
            </span>
            <span className="font-mono text-indigo-700 font-bold">
              {ocr ? `${Math.round((ocr.stability_ratio || 0) * 100)}%` : 'N/A'}
            </span>
          </div>
          <div className="space-y-1 pt-1">
            <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-indigo-600 h-1.5 rounded-full"
                style={{ width: `${Math.round((ocr?.stability_ratio || 0) * 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>Stable: {ocr?.stable_token_count || 0}</span>
              <span>Primary: {ocr?.primary_variant || 'RAW'}</span>
            </div>
          </div>
        </div>

        {/* Barcode Quorum */}
        <div className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-4 space-y-1.5 shadow-2xs">
          <div className="text-[11px] font-semibold text-slate-600 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Barcode className="h-3.5 w-3.5 text-amber-600" />
              Barcode Quorum
            </span>
            <span className="font-mono text-amber-700 font-bold">
              {barcode?.winning_barcode ? `${barcode.quorum_count}/${barcode.total_variants_evaluated} votes` : 'None'}
            </span>
          </div>
          <div className="text-[10px] text-slate-700 pt-1 flex items-center justify-between font-mono">
            <span className="truncate max-w-[140px]">{barcode?.winning_barcode || 'No barcode detected'}</span>
            {barcode?.catalog_verification?.matched ? (
              <span className="text-emerald-700 font-bold flex items-center gap-0.5">
                <CheckCircle2 className="h-3 w-3 text-emerald-600" /> Catalog Matched
              </span>
            ) : (
              <span className="text-slate-400">No catalog match</span>
            )}
          </div>
        </div>
      </div>

      {/* Corroborated Statutory Declarations Matrix */}
      {fields.length > 0 && (
        <div className="space-y-2 pt-1">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
            <span>Fused Statutory Declarations ({decls?.confirmed_count || 0} Confirmed, {decls?.probable_count || 0} Probable):</span>
            <span className="text-[10px] text-slate-400 font-normal">
              Statutory adjudication performed exclusively by deterministic legal rule engine
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {fields.filter(f => f.evidence_state !== 'MISSING').map((f) => {
              const stateBadge = {
                CONFIRMED: 'bg-emerald-50 text-emerald-800 border-emerald-300',
                PROBABLE: 'bg-blue-50 text-blue-800 border-blue-300',
                CONFLICTING: 'bg-rose-50 text-rose-800 border-rose-300',
                UNREADABLE: 'bg-slate-100 text-slate-700 border-slate-300',
              }[f.evidence_state] || 'bg-slate-100 text-slate-700 border-slate-300';

              return (
                <div
                  key={f.field_name}
                  className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-3 flex flex-col justify-between space-y-1 shadow-2xs"
                >
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-[11px] font-bold text-slate-800 capitalize">
                      {f.field_name.replace(/_/g, ' ')}
                    </span>
                    <span className={`text-[9px] font-mono px-2 py-0.5 rounded border ${stateBadge}`}>
                      {f.evidence_state} ({Math.round(f.aggregate_confidence * 100)}%)
                    </span>
                  </div>
                  <div className="text-xs text-slate-900 font-mono font-semibold truncate" title={f.fused_value || ''}>
                    {f.fused_value || '—'}
                  </div>
                  {f.supporting_variants && f.supporting_variants.length > 0 && (
                    <div className="text-[9px] text-slate-500 font-mono flex gap-1 items-center">
                      <span>Corroborated by:</span>
                      <span className="text-slate-700 font-semibold">{f.supporting_variants.join(', ')}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

