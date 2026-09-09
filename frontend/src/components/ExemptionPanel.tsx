'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { ExemptionEvaluationResponse } from '@/types';
import { ShieldCheck, Info, CheckCircle2, AlertTriangle, Scale, HelpCircle } from 'lucide-react';

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
  const [isAgricultural, setIsAgricultural] = useState<boolean>(false);
  const [isInstitutional, setIsInstitutional] = useState<boolean>(false);
  const [hasInstitutionalMarking, setHasInstitutionalMarking] = useState<boolean>(false);
  const [isTobacco, setIsTobacco] = useState<boolean>(false);
  const [multiPieceCount, setMultiPieceCount] = useState<number>(2);
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
        is_agricultural_farm_produce: isAgricultural,
        is_institutional_consumer: isInstitutional,
        has_institutional_marking: hasInstitutionalMarking,
        is_tobacco_product: isTobacco,
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

  const getStatusBadge = () => {
    if (!evalResult) return null;
    switch (evalResult.assessment_status) {
      case 'EXEMPTION_ELIGIBLE':
        return (
          <span className="px-2.5 py-0.5 rounded-full font-bold text-[10px] border bg-emerald-50 text-emerald-700 border-emerald-300 flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Eligible Subject to Verification ({evalResult.exemption_rule})
          </span>
        );
      case 'NEEDS_REVIEW':
        return (
          <span className="px-2.5 py-0.5 rounded-full font-bold text-[10px] border bg-amber-50 text-amber-700 border-amber-300 flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            Needs Factual Review (Incomplete Evidence)
          </span>
        );
      case 'SPECIAL_PACKAGING_PROVISION':
        return (
          <span className="px-2.5 py-0.5 rounded-full font-bold text-[10px] border bg-sky-50 text-sky-700 border-sky-300 flex items-center gap-1">
            <Info className="h-3 w-3" />
            Special Packaging Provision ({evalResult.package_type})
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full font-bold text-[10px] border bg-slate-100 text-slate-700 border-slate-300">
            Standard Retail / Not Exempt
          </span>
        );
    }
  };

  return (
    <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4 text-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <h3 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-indigo-700" />
          Rule 26 Statutory Exemptions & Packaging Classification
        </h3>
        {getStatusBadge()}
      </div>

      <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-xl flex items-start gap-2 text-slate-600 text-[11px]">
        <Info className="h-4 w-4 text-sky-600 shrink-0 mt-0.5" />
        <p>
          <strong>Statutory Principle:</strong> Package classification is an assessment input. Eligibility for an exemption requires supporting statutory facts/evidence and does not automatically confer legal compliance.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Package Classification</label>
          <select
            value={packageType}
            onChange={(e) => {
              setPackageType(e.target.value);
              setEvalResult(null);
            }}
            className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:outline-none font-medium"
          >
            <option value="STANDARD">Standard Retail Package</option>
            <option value="SMALL_PACK">Small Package (&le; 10g / &le; 10ml) — Rule 26(a)</option>
            <option value="INSTITUTIONAL">Institutional / Industrial Consumer — Rule 26(c)</option>
            <option value="AGRICULTURAL_BULK">Agricultural Bulk Produce (&gt; 50kg) — Rule 26(b)</option>
            <option value="FAST_FOOD">Fast Food Takeout — Rule 26(d)</option>
            <option value="MULTI_PIECE">Multi-Piece Package — Rule 21</option>
            <option value="COMBINATION">Combination Package — Rule 22</option>
          </select>
        </div>

        {/* Factual Evidence Checkboxes depending on Package Type */}
        {packageType === 'SMALL_PACK' && (
          <div className="flex items-center gap-2 pt-5">
            <input
              type="checkbox"
              id="tobaccoCheck"
              checked={isTobacco}
              onChange={(e) => setIsTobacco(e.target.checked)}
              className="rounded text-rose-600 focus:ring-rose-500"
            />
            <label htmlFor="tobaccoCheck" className="text-[11px] font-medium text-slate-700">
              Tobacco product (exemption denied under Rule 26(a) proviso)
            </label>
          </div>
        )}

        {packageType === 'AGRICULTURAL_BULK' && (
          <div className="flex items-center gap-2 pt-5">
            <input
              type="checkbox"
              id="agriCheck"
              checked={isAgricultural}
              onChange={(e) => setIsAgricultural(e.target.checked)}
              className="rounded text-indigo-600 focus:ring-indigo-500"
            />
            <label htmlFor="agriCheck" className="text-[11px] font-medium text-slate-700">
              Verified as raw agricultural farm produce (Rule 26(b))
            </label>
          </div>
        )}

        {packageType === 'INSTITUTIONAL' && (
          <div className="space-y-1.5 pt-2">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="instCheck"
                checked={isInstitutional}
                onChange={(e) => setIsInstitutional(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              <label htmlFor="instCheck" className="text-[11px] font-medium text-slate-700">
                Direct institutional consumer supply (Rule 2(p))
              </label>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="instMarkingCheck"
                checked={hasInstitutionalMarking}
                onChange={(e) => setHasInstitutionalMarking(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              <label htmlFor="instMarkingCheck" className="text-[11px] font-medium text-slate-700">
                Marked &apos;Not for retail sale&apos; on package
              </label>
            </div>
          </div>
        )}

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
      </div>

      <button
        type="button"
        onClick={handleEvaluateExemption}
        disabled={loading}
        className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold rounded-xl transition flex items-center justify-center gap-1.5"
      >
        <Scale className="h-3.5 w-3.5 text-indigo-700" />
        {loading ? 'Evaluating...' : inspectionId ? 'Apply Assessment & Re-evaluate Rules' : 'Evaluate Statutory Exemption'}
      </button>

      {error && <p className="text-rose-600 text-[11px]">{error}</p>}

      {evalResult && (
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-[11px]">
          <p className="text-slate-800 font-medium">{evalResult.rationale}</p>
          
          {evalResult.missing_statutory_facts && evalResult.missing_statutory_facts.length > 0 && (
            <div className="p-2 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 text-[10px] space-y-1">
              <strong>Pending Factual Verifications:</strong>
              <ul className="list-disc pl-4 space-y-0.5">
                {evalResult.missing_statutory_facts.map((fact, idx) => (
                  <li key={idx}>{fact}</li>
                ))}
              </ul>
            </div>
          )}

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
