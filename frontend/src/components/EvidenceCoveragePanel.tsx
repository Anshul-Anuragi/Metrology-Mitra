'use client';

import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Layers,
  Shield,
  FileCheck,
  Scale,
  Barcode,
  Building2,
  Calendar,
  Phone,
  Tag,
  Package,
} from 'lucide-react';
import { Declaration, EvidenceCompleteness } from '@/types';

interface EvidenceCoveragePanelProps {
  declaration?: Declaration | null;
  completeness?: EvidenceCompleteness | null;
  hasImages: boolean;
  hasBarcode: boolean;
  hasPhysicalVerification: boolean;
}

export default function EvidenceCoveragePanel({
  declaration,
  completeness,
  hasImages,
  hasBarcode,
  hasPhysicalVerification,
}: EvidenceCoveragePanelProps) {
  // Determine presence of each of the 9 statutory evidence areas
  const evidenceAreas = [
    {
      id: 'identity',
      title: 'Product Identity / Commodity',
      citation: 'Rule 6(1)(b)',
      status: declaration?.commodity_name ? 'AVAILABLE' : 'MISSING',
      value: declaration?.commodity_name || 'Not detected',
      icon: Package,
    },
    {
      id: 'manufacturer',
      title: 'Manufacturer / Packer / Importer',
      citation: 'Rule 6(1)(a)',
      status: declaration?.manufacturer_name || declaration?.packer_name ? 'AVAILABLE' : 'MISSING',
      value: declaration?.manufacturer_name || declaration?.packer_name || 'Not detected',
      icon: Building2,
    },
    {
      id: 'quantity',
      title: 'Net Quantity Declaration',
      citation: 'Rule 6(1)(c)',
      status: declaration?.net_quantity ? 'AVAILABLE' : 'MISSING',
      value: declaration?.net_quantity || 'Not detected',
      icon: Scale,
    },
    {
      id: 'mrp',
      title: 'Maximum Retail Price (MRP)',
      citation: 'Rule 6(1)(e)',
      status: declaration?.mrp ? 'AVAILABLE' : 'MISSING',
      value: declaration?.mrp ? `${declaration.mrp}${declaration.unit_sale_price ? ` (USP: ${declaration.unit_sale_price})` : ''}` : 'Not detected',
      icon: Tag,
    },
    {
      id: 'date',
      title: 'Date Declaration (Mfg / Pkg / Exp)',
      citation: 'Rule 6(1)(d)',
      status: declaration?.manufacturing_date || declaration?.packing_date || declaration?.expiry_date ? 'AVAILABLE' : 'MISSING',
      value: declaration?.expiry_date ? `Exp: ${declaration.expiry_date}` : declaration?.manufacturing_date ? `Mfg: ${declaration.manufacturing_date}` : 'Not detected',
      icon: Calendar,
    },
    {
      id: 'consumer_care',
      title: 'Consumer Care Contact',
      citation: 'Rule 6(1)(f)',
      status: declaration?.consumer_care || declaration?.consumer_care_phone || declaration?.consumer_care_email ? 'AVAILABLE' : 'MISSING',
      value: declaration?.consumer_care_phone || declaration?.consumer_care_email || declaration?.consumer_care || 'Not detected',
      icon: Phone,
    },
    {
      id: 'barcode',
      title: 'Barcode / GTIN Identification',
      citation: 'Catalog Cross-Check',
      status: hasBarcode ? 'AVAILABLE' : 'NOT_RECORDED',
      value: hasBarcode ? 'Optical barcode detected' : 'No optical barcode',
      icon: Barcode,
    },
    {
      id: 'pdp',
      title: 'Mandatory Declaration Panel (PDP)',
      citation: 'Rule 7 & Sched II',
      status: declaration?.pdp_area_sq_cm ? 'AVAILABLE' : hasImages ? 'PARTIAL' : 'NOT_RECORDED',
      value: declaration?.pdp_area_sq_cm ? `${declaration.pdp_area_sq_cm} sq.cm measured` : hasImages ? 'Surface captured (Area uncalibrated)' : 'Surface not recorded',
      icon: FileCheck,
    },
    {
      id: 'physical_verification',
      title: 'Physical Quantity Verification',
      citation: 'Rule 19 Sched VI',
      status: hasPhysicalVerification ? 'AVAILABLE' : 'NOT_RECORDED',
      value: hasPhysicalVerification ? 'Gravimetric measurement attached' : 'Measurement not recorded',
      icon: Scale,
    },
  ];

  const availableCount = evidenceAreas.filter((a) => a.status === 'AVAILABLE').length;
  const partialCount = evidenceAreas.filter((a) => a.status === 'PARTIAL').length;
  const missingCount = evidenceAreas.filter((a) => a.status === 'MISSING').length;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'AVAILABLE':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-300 px-2 py-0.5 rounded">
            <CheckCircle2 className="h-3 w-3 text-emerald-600" /> Available
          </span>
        );
      case 'PARTIAL':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-300 px-2 py-0.5 rounded">
            <AlertTriangle className="h-3 w-3 text-amber-600" /> Partial
          </span>
        );
      case 'MISSING':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-rose-700 bg-rose-50 border border-rose-300 px-2 py-0.5 rounded">
            <XCircle className="h-3 w-3 text-rose-600" /> Missing
          </span>
        );
      case 'NOT_RECORDED':
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-medium text-slate-500 bg-slate-100 border border-slate-300 px-2 py-0.5 rounded">
            <HelpCircle className="h-3 w-3 text-slate-400" /> Not recorded
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-sky-600" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
            Inspection Evidence Coverage
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-bold bg-sky-50 text-sky-800 px-2.5 py-0.5 rounded-full border border-sky-200">
            {availableCount} / 9 Areas Available
          </span>
        </div>
      </div>

      {/* Summary Meter */}
      <div className="space-y-1.5">
        <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden flex">
          <div
            className="bg-emerald-500 h-full transition-all duration-500"
            style={{ width: `${(availableCount / 9) * 100}%` }}
            title={`Available: ${availableCount}`}
          />
          <div
            className="bg-amber-400 h-full transition-all duration-500"
            style={{ width: `${(partialCount / 9) * 100}%` }}
            title={`Partial: ${partialCount}`}
          />
          <div
            className="bg-rose-400 h-full transition-all duration-500"
            style={{ width: `${(missingCount / 9) * 100}%` }}
            title={`Missing: ${missingCount}`}
          />
        </div>
        <div className="flex justify-between text-[10px] text-slate-400">
          <span>{Math.round((availableCount / 9) * 100)}% coverage score</span>
          <span>{9 - availableCount} areas pending or missing</span>
        </div>
      </div>

      {/* Grid of Evidence Areas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 pt-1">
        {evidenceAreas.map((area) => {
          const Icon = area.icon;
          return (
            <div
              key={area.id}
              className="p-2.5 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-slate-50 transition flex flex-col justify-between"
            >
              <div className="flex items-start justify-between gap-1.5 mb-1.5">
                <div className="flex items-center gap-1.5 min-w-0">
                  <Icon className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                  <span className="text-xs font-bold text-slate-800 truncate" title={area.title}>
                    {area.title}
                  </span>
                </div>
                {getStatusBadge(area.status)}
              </div>
              <div className="text-[11px] text-slate-600 truncate font-mono" title={area.value}>
                {area.value}
              </div>
              <div className="text-[9px] text-slate-400 mt-1 flex justify-between">
                <span>{area.citation}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Mandatory Statutory Disclaimer */}
      <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200 text-[10px] text-slate-500 leading-relaxed">
        <span className="font-semibold text-slate-700">Legal Boundary Note:</span> Operational evidence coverage indicates what evidentiary items have been detected and made available for review. It is not a statutory verdict.
      </div>
    </div>
  );
}

