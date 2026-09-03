'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { ExemptionEvaluationResponse } from '@/types';
import { ShieldCheck, Info, CheckCircle2, AlertTriangle, Scale } from 'lucide-react';

interface ExemptionPanelProps {
  inspectionId?: string;
  initialPackageType?: string;
  nominalQty?: number;
  unit?: string;
  onExemptionApplied?: (res: ExemptionEvaluationResponse) => void;
}

export default function ExemptionPanel({
  inspectionId,
  initialPackageType = 'STANDARD',
  nominalQty,
  unit,
  onExemptionApplied,
}: ExemptionPanelProps) {
  const [packageType, setPackageType] = useState<string>(initialPackageType);
  const [isInstitutional, setIsInstitutional] = useState<boolean>(false);
  const [multiPieceCount, setMultiPieceCount] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [evalResult, setEvalResult] = useState<ExemptionEvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleEvaluateExemption = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        package_type: packageType,
        declared_net_quantity_value: nominalQty,
        declared_net_quantity_unit: unit,
        is_institutional_consumer: isInstitutional,
        multi_piece_count: packageType === 'MULTI_PIECE' ? multiPieceCount : undefined,
      };

      let res: ExemptionEvaluationResponse;
      if (inspectionId) {
        res = await api.applyExemptionToInspection(inspectionId, payload);
      } else {
        res = await api.evaluateExemptionRules(payload);
      }

      setEvalResult(res);
      if (onExemptionApplied) {
        onExemptionApplied(res);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to evaluate statutory exemptions.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4 text-xs">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-indigo-700" />
          Rule 26 Statutory Exemptions & Special Packaging
        </h3>
        {evalResult && (
          <span
            className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] border ${
              evalResult.is_exempt
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            {evalResult.is_exempt ? `EXEMPT (${evalResult.exemption_rule})` : 'STANDARD RETAIL'}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Package Classification</label>
          <select
            value={packageType}
            onChange={(e) => setPackageType(e.target.value)}
            className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:outline-none font-medium"
          >
            <option value="STANDARD">Standard Retail Package</option>
            <option value="SMALL_PACK">Small Package (&le; 10g / &le; 10ml) — Rule 26(a)</option>
            <option value="INSTITUTIONAL">Institutional / Industrial Consumer — Rule 26(c)</option>
            <option value="AGRICULTURAL_BULK">Agricultural Bulk (&gt; 50kg) — Rule 26(b)</option>
            <option value="MULTI_PIECE">Multi-Piece Package — Rule 21</option>
            <option value="COMBINATION">Combination Package — Rule 22</option>
          </select>
        </div>

        {packageType === 'MULTI_PIECE' && (
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Individual Piece Count</label>
            <input
              type="number"
              min={2}
              value={multiPieceCount}
              onChange={(e) => setMultiPieceCount(parseInt(e.target.value) || 2)}
              className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:outline-none"
            />
          </div>
        )}

        {packageType === 'INSTITUTIONAL' && (
          <div className="flex items-center gap-2 pt-5">
            <input
              type="checkbox"
              id="instCheck"
              checked={isInstitutional}
              onChange={(e) => setIsInstitutional(e.target.checked)}
              className="rounded text-indigo-600 focus:ring-indigo-500"
            />
            <label htmlFor="instCheck" className="text-[11px] font-medium text-slate-700">
              Contractual institutional use (Rule 2(p))
            </label>
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={handleEvaluateExemption}
        disabled={loading}
        className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold rounded-xl transition flex items-center justify-center gap-1.5"
      >
        <Scale className="h-3.5 w-3.5 text-indigo-700" />
        {loading ? 'Evaluating...' : inspectionId ? 'Apply Exemption & Re-evaluate' : 'Evaluate Exemption Rules'}
      </button>

      {error && <p className="text-rose-600 text-[11px]">{error}</p>}

      {evalResult && (
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5 text-[11px]">
          <p className="text-slate-800 font-medium">{evalResult.rationale}</p>
          {evalResult.exempt_mandatory_declarations.length > 0 && (
            <div className="pt-1 text-[10px] text-emerald-800">
              <strong>Exempt Mandatory Declarations:</strong>{' '}
              {evalResult.exempt_mandatory_declarations.join(', ')}
            </div>
          )}
          <p className="text-[10px] text-slate-500 pt-1 border-t border-slate-200">{evalResult.disclaimer}</p>
        </div>
      )}
    </div>
  );
}

