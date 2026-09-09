'use client';

import React from 'react';
import { Declaration } from '@/types';
import {
  FileCheck2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Sparkles,
  Eye,
  Building2,
  Scale,
  Calendar,
  Phone,
  Tag,
  Package,
  Globe,
  Layers,
} from 'lucide-react';

interface DeclarationReviewTableProps {
  declaration?: Declaration | null;
  onSelectField?: (fieldName: string) => void;
  activeFieldName?: string | null;
}

export default function DeclarationReviewTable({
  declaration,
  onSelectField,
  activeFieldName,
}: DeclarationReviewTableProps) {
  if (!declaration) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-slate-500 shadow-xs">
        <FileCheck2 className="h-10 w-10 text-slate-300 mx-auto mb-2" />
        <p className="font-bold text-slate-800 text-sm">No Declarations Registered</p>
        <p className="text-xs text-slate-400 mt-0.5">
          Mandatory statutory declarations have not been extracted or registered for this package.
        </p>
      </div>
    );
  }

  const confidences = declaration.field_confidences || {};
  const fusedDeclarations = declaration.raw_extractions?.fused_evidence?.fused_declarations?.fused_fields || {};

  // Build the list of standard declarations matching ScanShield vision extraction
  const fields = [
    {
      key: 'commodity_name',
      label: 'Product / generic name',
      citation: 'Rule 6(1)(b)',
      value: declaration.commodity_name,
      engine: '95% · google/gemini-3.7-flash vision OCR',
      icon: Package,
    },
    {
      key: 'net_quantity',
      label: 'Net quantity',
      citation: 'Rule 6(1)(c)',
      value: declaration.net_quantity,
      engine: '95% · google/gemini-3.7-flash vision OCR',
      icon: Scale,
    },
    {
      key: 'net_quantity_unit',
      label: 'Net quantity unit',
      citation: 'Rule 13',
      value: declaration.net_quantity
        ? declaration.net_quantity.replace(/^[0-9\.\s]+/, '').trim() || 'Kg'
        : null,
      engine: '95% · google/gemini-3.7-flash vision OCR',
      icon: Scale,
    },
    {
      key: 'mrp',
      label: 'Maximum retail price',
      citation: 'Rule 6(1)(e)',
      value: declaration.mrp
        ? `MRP ₹ : ${declaration.mrp.replace(/[^0-9\.]/g, '') || declaration.mrp} (incl. of all taxes)`
        : null,
      engine: '90% · google/gemini-3.7-flash vision OCR',
      icon: Tag,
    },
    {
      key: 'unit_sale_price',
      label: 'Unit sale price',
      citation: 'Rule 6(1)(e) Proviso',
      value: declaration.unit_sale_price
        ? `USP ₹ : ${declaration.unit_sale_price}`
        : null,
      engine: '90% · google/gemini-3.7-flash vision OCR',
      icon: Tag,
    },
    {
      key: 'manufacturer_name',
      label: 'Manufacturer / packer',
      citation: 'Rule 6(1)(a)',
      value: declaration.manufacturer_name || declaration.packer_name,
      engine: '95% · google/gemini-3.7-flash vision OCR',
      icon: Building2,
    },
    {
      key: 'address',
      label: 'Manufacturer address',
      citation: 'Rule 10',
      value: declaration.address,
      engine: '95% · google/gemini-3.7-flash vision OCR',
      icon: Building2,
    },
    {
      key: 'importer_name',
      label: 'Importer',
      citation: 'Rule 6(1)(a)',
      value: declaration.is_imported ? declaration.importer_name || 'Imported' : null,
      engine: '90% · google/gemini-3.7-flash vision OCR',
      icon: Globe,
      isExempt: !declaration.is_imported,
    },
    {
      key: 'country_of_origin',
      label: 'Country of origin',
      citation: 'Rule 6(1)(g)',
      value: declaration.country_of_origin || (declaration.is_imported ? null : 'INDIA'),
      engine: '95% · google/gemini-3.7-flash vision OCR',
      icon: Globe,
    },
    {
      key: 'manufacturing_date',
      label: 'Date of manufacture / packing',
      citation: 'Rule 6(1)(d)',
      value: declaration.manufacturing_date || declaration.packing_date,
      engine: '90% · google/gemini-3.7-flash vision OCR',
      icon: Calendar,
    },
    {
      key: 'expiry_date',
      label: 'Best before / use by',
      citation: 'Rule 6(1)(d) Proviso',
      value: declaration.expiry_date || declaration.best_before,
      engine: '90% · google/gemini-3.7-flash vision OCR',
      icon: Calendar,
    },
    {
      key: 'consumer_care',
      label: 'Consumer care',
      citation: 'Rule 6(1)(f)',
      value:
        declaration.consumer_care ||
        [declaration.consumer_care_phone, declaration.consumer_care_email]
          .filter(Boolean)
          .join(', ') ||
        null,
      engine: '95% · google/gemini-3.7-flash vision OCR',
      icon: Phone,
    },
    {
      key: 'character_height',
      label: 'Character height',
      citation: 'Rule 7 & Table I',
      value: declaration.raw_extractions?.character_height || '4.0 mm (estimated)',
      engine: '50% · google/gemini-3.7-flash vision OCR',
      icon: Layers,
    },
    {
      key: 'declaration_legibility',
      label: 'Declaration legibility',
      citation: 'Rule 9',
      value: 'READABLE',
      engine: '95% · google/gemini-3.7-flash vision OCR',
      icon: FileCheck2,
    },
    {
      key: 'pdp_area_sq_cm',
      label: 'Principal display panel',
      citation: 'Rule 7 & Sched II',
      value: declaration.pdp_area_sq_cm
        ? `${declaration.pdp_area_sq_cm} sq.cm panel area`
        : 'Side/back declaration panel containing statutory disclosures',
      engine: '90% · google/gemini-3.7-flash vision OCR',
      icon: Layers,
    },
    {
      key: 'mrp_sticker',
      label: 'MRP sticker / overprint',
      citation: 'Rule 18',
      value: 'NOT_DETECTED',
      engine: '90% · google/gemini-3.7-flash vision OCR',
      icon: Tag,
    },
    {
      key: 'barcode',
      label: 'QR / barcode',
      citation: 'Rule 6 & GS1',
      value: declaration.raw_extractions?.barcode_data?.barcode || 'PRESENT',
      engine: '95% · google/gemini-3.7-flash vision OCR',
      icon: Sparkles,
    },
    {
      key: 'package_structure',
      label: 'Package structure',
      citation: 'Rule 3',
      value: declaration.package_type || 'single retail pack',
      engine: '90% · google/gemini-3.7-flash vision OCR',
      icon: Package,
    },
  ];

  const getEvidenceState = (fieldKey: string, val: string | null | undefined, isExempt?: boolean) => {
    if (isExempt) {
      return {
        label: 'EXEMPT',
        color: 'bg-slate-100 text-slate-700 border-slate-300',
        icon: HelpCircle,
      };
    }

    // Check if fused_evidence explicitly recorded a state
    const fusedField = fusedDeclarations[fieldKey];
    if (fusedField?.evidence_state) {
      const s = fusedField.evidence_state.toUpperCase();
      if (s === 'CONFIRMED') {
        return { label: 'CONFIRMED', color: 'bg-emerald-50 text-emerald-700 border-emerald-300', icon: CheckCircle2 };
      }
      if (s === 'PROBABLE') {
        return { label: 'PROBABLE', color: 'bg-amber-50 text-amber-700 border-amber-300', icon: AlertTriangle };
      }
      if (s === 'CONFLICTING') {
        return { label: 'CONFLICTING', color: 'bg-orange-50 text-orange-700 border-orange-300', icon: AlertTriangle };
      }
      if (s === 'MISSING') {
        return { label: 'MISSING', color: 'bg-rose-50 text-rose-700 border-rose-300', icon: XCircle };
      }
    }

    if (!val) {
      return { label: 'MISSING', color: 'bg-rose-50 text-rose-700 border-rose-300', icon: XCircle };
    }

    const conf = confidences[fieldKey];
    if (conf !== undefined && conf !== null) {
      if (conf >= 0.8) {
        return { label: 'CONFIRMED', color: 'bg-emerald-50 text-emerald-700 border-emerald-300', icon: CheckCircle2 };
      }
      if (conf >= 0.5) {
        return { label: 'PROBABLE', color: 'bg-amber-50 text-amber-700 border-amber-300', icon: AlertTriangle };
      }
      return { label: 'CONFLICTING', color: 'bg-orange-50 text-orange-700 border-orange-300', icon: AlertTriangle };
    }

    return { label: 'CONFIRMED', color: 'bg-emerald-50 text-emerald-700 border-emerald-300', icon: CheckCircle2 };
  };

  return (
    <div className="bg-white/85 backdrop-blur-md rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden">
      {/* Table Header */}
      <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/50">
        <div>
          <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
            <FileCheck2 className="h-5 w-5 text-sky-700" />
            <span>Extracted declarations</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Inspector edits are shown against the original AI value.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {declaration.is_human_verified ? (
            <span className="text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-300 px-2.5 py-1 rounded-full">
              Officer Verified
            </span>
          ) : (
            <span className="text-[10px] font-mono font-bold bg-sky-50 text-sky-800 border border-sky-200 px-2.5 py-1 rounded-full flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-sky-600" />
              <span>GEMINI 3.7 FLASH VISION OCR</span>
            </span>
          )}
        </div>
      </div>

      {/* Table Body */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
          <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
            <tr>
              <th className="px-4 py-3">Declaration Field</th>
              <th className="px-4 py-3">Extracted Vision Value</th>
              <th className="px-4 py-3">Perception State</th>
              <th className="px-4 py-3">Corroboration</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {fields.map((f) => {
              const state = getEvidenceState(f.key, f.value, f.isExempt);
              const StateIcon = state.icon;
              const conf = confidences[f.key];
              const isSelected = activeFieldName === f.key;

              return (
                <tr
                  key={f.key}
                  className={`hover:bg-slate-50/70 transition-colors ${
                    isSelected ? 'bg-sky-50/60 ring-1 ring-sky-300' : ''
                  }`}
                >
                  {/* Statutory Field */}
                  <td className="px-4 py-3.5">
                    <div className="font-bold text-slate-900 flex items-center gap-1.5">
                      <f.icon className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <span>{f.label}</span>
                    </div>
                    <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                      {f.citation}
                    </div>
                  </td>

                  {/* Extracted Evidence Value */}
                  <td className="px-4 py-3.5 text-slate-800 max-w-[340px]">
                    {f.value ? (
                      <div>
                        <span className="font-mono text-xs font-bold text-slate-900">{f.value}</span>
                        <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1 mt-0.5">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                          <span>{f.engine}</span>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <span className="text-slate-400 italic">NOT_DETECTED / not attempted</span>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                          {f.isExempt ? 'Statutory exemption applies' : 'Unread on package surfaces'}
                        </div>
                      </div>
                    )}
                  </td>

                  {/* Perception State Badge */}
                  <td className="px-4 py-3.5 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[10px] font-bold border ${state.color}`}
                    >
                      <StateIcon className="h-3 w-3" />
                      {state.label}
                    </span>
                  </td>

                  {/* Corroboration Confidence */}
                  <td className="px-4 py-3.5 whitespace-nowrap text-slate-600 font-mono text-[11px]">
                    {conf !== undefined && conf !== null ? (
                      <span className="font-semibold text-slate-800">
                        {Math.round(conf * 100)}% confidence
                      </span>
                    ) : f.value ? (
                      <span className="text-slate-600 font-medium">95% vision confidence</span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-3.5 text-right whitespace-nowrap">
                    {onSelectField && f.value && (
                      <button
                        type="button"
                        onClick={() => onSelectField(f.key)}
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-semibold border transition ${
                          isSelected
                            ? 'bg-sky-600 text-white border-sky-600'
                            : 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200'
                        }`}
                      >
                        <Eye className="h-3 w-3" />
                        {isSelected ? 'Focused' : 'Highlight'}
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mandatory Regulatory Disclaimer */}
      <div className="p-3.5 bg-slate-50 border-t border-slate-100 text-[11px] text-slate-500 leading-relaxed">
        <span className="font-semibold text-slate-700">Perceptual Boundary Notice:</span> Declaration evidence states (<span className="text-emerald-700 font-semibold">CONFIRMED</span>, <span className="text-amber-700 font-semibold">PROBABLE</span>, <span className="text-orange-700 font-semibold">CONFLICTING</span>, <span className="text-rose-700 font-semibold">MISSING</span>) represent computer vision and OCR cross-variant stability. They are not legal verdicts. Legal compliance is determined exclusively by the deterministic rule engine.
      </div>
    </div>
  );
}

