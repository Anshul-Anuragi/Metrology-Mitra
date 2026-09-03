'use client';

import React from 'react';
import { BarcodeDataInfo } from '@/types';
import { Barcode, CheckCircle, AlertTriangle, HelpCircle, ShieldAlert, Building2 } from 'lucide-react';

interface MasterCatalogComparisonCardProps {
  barcodeData?: BarcodeDataInfo | null;
}

export default function MasterCatalogComparisonCard({
  barcodeData,
}: MasterCatalogComparisonCardProps) {
  if (!barcodeData || !barcodeData.value) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs text-slate-500 flex items-center gap-3">
        <Barcode className="h-5 w-5 text-slate-400 shrink-0" />
        <div>
          <span className="font-bold text-slate-700">Barcode / Master Catalog:</span> No 1D/2D barcode detected on attached package photographs. Standalone LMPC Rule 6 declarations apply.
        </div>
      </div>
    );
  }

  const match = barcodeData.catalog_match;
  const isMatch = match?.discrepancy === 'MATCH';
  const isMismatch = match?.discrepancy === 'MISMATCH';
  const isNoCatalog = match?.discrepancy === 'NO_CATALOG_MATCH' || !match?.matched;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 space-y-3">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-brand-50 rounded-lg text-brand-900 border border-brand-100">
            <Barcode className="h-4 w-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              Decoded Package Barcode
              <span className="text-[10px] font-mono bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded border border-slate-200">
                {barcodeData.format}
              </span>
            </div>
            <div className="text-xs font-mono font-bold text-sky-700">{barcodeData.value}</div>
          </div>
        </div>

        <div>
          {isMatch ? (
            <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold px-2.5 py-1 rounded-full text-xs">
              <CheckCircle className="h-3.5 w-3.5 text-emerald-600" />
              Catalog Price Matched
            </span>
          ) : isMismatch ? (
            <span className="inline-flex items-center gap-1 bg-rose-50 text-rose-700 border border-rose-200 font-bold px-2.5 py-1 rounded-full text-xs">
              <ShieldAlert className="h-3.5 w-3.5 text-rose-600" />
              Price Discrepancy (Rule 18(2))
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 bg-slate-100 text-slate-600 border border-slate-200 font-semibold px-2.5 py-1 rounded-full text-xs">
              <HelpCircle className="h-3.5 w-3.5 text-slate-400" />
              Uncataloged Barcode
            </span>
          )}
        </div>
      </div>

      {/* Comparison Grid */}
      {match?.matched ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          {/* Controlled Master Catalog Column */}
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-1">
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
              <Building2 className="h-3 w-3" /> Controlled Demo Catalog
            </div>
            <div className="font-bold text-slate-800 truncate">{match.product_name}</div>
            <div className="text-[11px] text-slate-500">Brand: {match.brand_name || 'N/A'}</div>
            <div className="text-sm font-black text-slate-900 mt-1">
              Standard MRP: ₹{match.catalog_mrp ? match.catalog_mrp.toFixed(2) : 'N/A'}
            </div>
          </div>

          {/* Observed Package Column */}
          <div className={`p-3 rounded-lg border space-y-1 ${
            isMismatch ? 'bg-rose-50/50 border-rose-200' : 'bg-emerald-50/50 border-emerald-200'
          }`}>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Observed Package Declaration
            </div>
            <div className="font-bold text-slate-800">Printed Label Extractions</div>
            <div className="text-[11px] text-slate-500">Statutory Label Scan</div>
            <div className={`text-sm font-black mt-1 ${isMismatch ? 'text-rose-600' : 'text-emerald-600'}`}>
              Observed MRP: ₹{match.observed_mrp ? match.observed_mrp.toFixed(2) : 'Not Detected'}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          Barcode is present on the package but not registered in the controlled demo master catalog. Standard Rule 6 mandatory declaration checks apply.
        </div>
      )}

      {/* Discrepancy Finding Summary */}
      {match?.reason && (
        <div className={`text-xs p-2.5 rounded-lg flex items-start gap-2 border ${
          isMismatch ? 'bg-rose-50 text-rose-800 border-rose-200' : 'bg-slate-50 text-slate-700 border-slate-200'
        }`}>
          {isMismatch ? (
            <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
          ) : (
            <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
          )}
          <span>{match.reason}</span>
        </div>
      )}
    </div>
  );
}

