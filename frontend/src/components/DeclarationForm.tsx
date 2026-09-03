'use client';

import React, { useState, useEffect } from 'react';
import { Declaration } from '@/types';
import { CheckCircle2, AlertCircle, Save, UserCheck, Sparkles } from 'lucide-react';

interface DeclarationFormProps {
  declaration?: Declaration | null;
  onSave: (data: Partial<Declaration>) => Promise<void>;
  onSelectField?: (fieldName: string) => void;
  activeFieldName?: string | null;
}

export default function DeclarationForm({
  declaration,
  onSave,
  onSelectField,
  activeFieldName,
}: DeclarationFormProps) {
  const [formData, setFormData] = useState<Partial<Declaration>>({});
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  useEffect(() => {
    if (declaration) {
      setFormData({
        commodity_name: declaration.commodity_name || '',
        manufacturer_name: declaration.manufacturer_name || '',
        packer_name: declaration.packer_name || '',
        importer_name: declaration.importer_name || '',
        address: declaration.address || '',
        net_quantity: declaration.net_quantity || '',
        mrp: declaration.mrp || '',
        unit_sale_price: declaration.unit_sale_price || '',
        manufacturing_date: declaration.manufacturing_date || '',
        packing_date: declaration.packing_date || '',
        expiry_date: declaration.expiry_date || '',
        best_before: declaration.best_before || '',
        country_of_origin: declaration.country_of_origin || '',
        consumer_care: declaration.consumer_care || '',
        consumer_care_phone: declaration.consumer_care_phone || '',
        consumer_care_email: declaration.consumer_care_email || '',
        is_imported: declaration.is_imported || false,
      });
    }
  }, [declaration]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
    setSaveSuccess(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await onSave({
        ...formData,
        is_human_verified: true,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } finally {
      setIsSaving(false);
    }
  };

  const confidences = declaration?.field_confidences || {};

  const renderConfidenceBadge = (fieldName: string) => {
    const conf = confidences[fieldName];
    if (conf === undefined || conf === null) return null;
    const pct = Math.round(conf * 100);
    const colorClass =
      pct >= 85
        ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
        : pct >= 60
        ? 'bg-amber-100 text-amber-800 border-amber-300'
        : 'bg-rose-100 text-rose-800 border-rose-300';

    return (
      <span
        className={`text-[10px] font-mono px-1.5 py-0.5 rounded border font-semibold flex items-center gap-1 ${colorClass}`}
        title={`OCR Confidence: ${pct}%`}
      >
        <Sparkles className="h-2.5 w-2.5" />
        {pct}%
      </span>
    );
  };

  return (
    <div className="bg-white rounded-xl shadow border border-slate-200 p-5 flex flex-col h-full">
      {/* Header with Verification Status */}
      <div className="flex justify-between items-center pb-4 border-b border-slate-200">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            Statutory Declarations (LMPC Rule 6)
          </h3>
          <p className="text-xs text-slate-500">
            Review optical extractions and perform human verification if adjustments are needed.
          </p>
        </div>

        <div>
          {declaration?.is_human_verified ? (
            <span className="bg-emerald-50 text-emerald-700 border border-emerald-300 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 shadow-sm">
              <UserCheck className="h-3.5 w-3.5 text-emerald-600" />
              Human Verified
            </span>
          ) : (
            <span className="bg-amber-50 text-amber-700 border border-amber-300 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 shadow-sm">
              <AlertCircle className="h-3.5 w-3.5 text-amber-600" />
              OCR Extracted (Pending Review)
            </span>
          )}
        </div>
      </div>

      {/* Form Fields */}
      <form onSubmit={handleSubmit} className="space-y-4 pt-4 flex-1 overflow-y-auto pr-1">
        {/* Commodity Name */}
        <div
          className={`p-2.5 rounded-lg border transition-colors ${
            activeFieldName === 'commodity' || activeFieldName === 'commodity_name'
              ? 'border-amber-400 bg-amber-50/50'
              : 'border-slate-200 hover:border-slate-300'
          }`}
          onFocus={() => onSelectField && onSelectField('commodity')}
        >
          <div className="flex justify-between items-center mb-1">
            <label className="text-xs font-bold text-slate-700">
              1. Commodity Name <span className="text-slate-400 font-normal">(Rule 6(1)(b))</span>
            </label>
            {renderConfidenceBadge('commodity_name')}
          </div>
          <input
            type="text"
            name="commodity_name"
            value={formData.commodity_name || ''}
            onChange={handleChange}
            placeholder="e.g. Premium Basmati Rice"
            className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500 focus:outline-none"
          />
        </div>

        {/* Manufacturer Name & Address */}
        <div
          className={`p-2.5 rounded-lg border transition-colors ${
            activeFieldName === 'manufacturer' || activeFieldName === 'manufacturer_name'
              ? 'border-amber-400 bg-amber-50/50'
              : 'border-slate-200 hover:border-slate-300'
          }`}
          onFocus={() => onSelectField && onSelectField('manufacturer')}
        >
          <div className="flex justify-between items-center mb-1">
            <label className="text-xs font-bold text-slate-700">
              2. Manufacturer / Packer / Importer <span className="text-slate-400 font-normal">(Rule 6(1)(a))</span>
            </label>
            {renderConfidenceBadge('manufacturer_name')}
          </div>
          <input
            type="text"
            name="manufacturer_name"
            value={formData.manufacturer_name || ''}
            onChange={handleChange}
            placeholder="e.g. Royal Agro Foods Pvt Ltd"
            className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500 focus:outline-none mb-2"
          />
          <textarea
            name="address"
            rows={2}
            value={formData.address || ''}
            onChange={handleChange}
            placeholder="Complete manufacturing / registered address with PIN code..."
            className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500 focus:outline-none"
          />
        </div>

        {/* Net Quantity & MRP (Side by Side) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Net Quantity */}
          <div
            className={`p-2.5 rounded-lg border transition-colors ${
              activeFieldName === 'net_quantity' || activeFieldName === 'quantity'
                ? 'border-amber-400 bg-amber-50/50'
                : 'border-slate-200 hover:border-slate-300'
            }`}
            onFocus={() => onSelectField && onSelectField('net_quantity')}
          >
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-bold text-slate-700">
                3. Net Quantity <span className="text-slate-400 font-normal">(Rule 6(1)(c))</span>
              </label>
              {renderConfidenceBadge('net_quantity')}
            </div>
            <input
              type="text"
              name="net_quantity"
              value={formData.net_quantity || ''}
              onChange={handleChange}
              placeholder="e.g. 5 kg, 1 l, 500 g"
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500 focus:outline-none"
            />
          </div>

          {/* MRP */}
          <div
            className={`p-2.5 rounded-lg border transition-colors ${
              activeFieldName === 'mrp' || activeFieldName === 'price'
                ? 'border-amber-400 bg-amber-50/50'
                : 'border-slate-200 hover:border-slate-300'
            }`}
            onFocus={() => onSelectField && onSelectField('mrp')}
          >
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-bold text-slate-700">
                4. Max Retail Price <span className="text-slate-400 font-normal">(Rule 6(1)(e))</span>
              </label>
              {renderConfidenceBadge('mrp')}
            </div>
            <input
              type="text"
              name="mrp"
              value={formData.mrp || ''}
              onChange={handleChange}
              placeholder="e.g. MRP Rs. 450.00 (incl. of all taxes)"
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500 focus:outline-none"
            />
          </div>
        </div>

        {/* USP & Dates */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Unit Sale Price */}
          <div
            className={`p-2.5 rounded-lg border transition-colors ${
              activeFieldName === 'unit_sale_price' || activeFieldName === 'usp'
                ? 'border-amber-400 bg-amber-50/50'
                : 'border-slate-200 hover:border-slate-300'
            }`}
            onFocus={() => onSelectField && onSelectField('unit_sale_price')}
          >
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-bold text-slate-700">
                5. Unit Sale Price <span className="text-slate-400 font-normal">(Rule 6(11))</span>
              </label>
              {renderConfidenceBadge('unit_sale_price')}
            </div>
            <input
              type="text"
              name="unit_sale_price"
              value={formData.unit_sale_price || ''}
              onChange={handleChange}
              placeholder="e.g. Rs. 90.00 / kg"
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500 focus:outline-none"
            />
          </div>

          {/* Mfg Date */}
          <div
            className={`p-2.5 rounded-lg border transition-colors ${
              activeFieldName === 'manufacturing_date' || activeFieldName === 'date'
                ? 'border-amber-400 bg-amber-50/50'
                : 'border-slate-200 hover:border-slate-300'
            }`}
            onFocus={() => onSelectField && onSelectField('manufacturing_date')}
          >
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-bold text-slate-700">
                6. Mfg / Pkg Date <span className="text-slate-400 font-normal">(Rule 6(1)(d))</span>
              </label>
              {renderConfidenceBadge('manufacturing_date')}
            </div>
            <input
              type="text"
              name="manufacturing_date"
              value={formData.manufacturing_date || ''}
              onChange={handleChange}
              placeholder="MM/YYYY (e.g. 08/2026)"
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Expiry Date & Country of Origin */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Expiry Date */}
          <div
            className={`p-2.5 rounded-lg border transition-colors ${
              activeFieldName === 'expiry_date' || activeFieldName === 'expiry'
                ? 'border-amber-400 bg-amber-50/50'
                : 'border-slate-200 hover:border-slate-300'
            }`}
            onFocus={() => onSelectField && onSelectField('expiry_date')}
          >
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-bold text-slate-700">
                7. Expiry / Best Before <span className="text-slate-400 font-normal">(Rule 6(1)(d))</span>
              </label>
              {renderConfidenceBadge('expiry_date')}
            </div>
            <input
              type="text"
              name="expiry_date"
              value={formData.expiry_date || ''}
              onChange={handleChange}
              placeholder="MM/YYYY or Best Before 12 Months"
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500 focus:outline-none"
            />
          </div>

          {/* Country of Origin */}
          <div
            className={`p-2.5 rounded-lg border transition-colors ${
              activeFieldName === 'country_of_origin' || activeFieldName === 'origin'
                ? 'border-amber-400 bg-amber-50/50'
                : 'border-slate-200 hover:border-slate-300'
            }`}
            onFocus={() => onSelectField && onSelectField('country_of_origin')}
          >
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-bold text-slate-700">
                8. Country of Origin <span className="text-slate-400 font-normal">(Rule 6(1)(g))</span>
              </label>
              {renderConfidenceBadge('country_of_origin')}
            </div>
            <input
              type="text"
              name="country_of_origin"
              value={formData.country_of_origin || ''}
              onChange={handleChange}
              placeholder="e.g. India"
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Consumer Care */}
        <div
          className={`p-2.5 rounded-lg border transition-colors ${
            activeFieldName === 'consumer_care' || activeFieldName === 'consumer'
              ? 'border-amber-400 bg-amber-50/50'
              : 'border-slate-200 hover:border-slate-300'
          }`}
          onFocus={() => onSelectField && onSelectField('consumer_care')}
        >
          <div className="flex justify-between items-center mb-1">
            <label className="text-xs font-bold text-slate-700">
              9. Consumer Helpline & Email <span className="text-slate-400 font-normal">(Rule 6(1)(f))</span>
            </label>
            {renderConfidenceBadge('consumer_care')}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <input
              type="text"
              name="consumer_care_phone"
              value={formData.consumer_care_phone || ''}
              onChange={handleChange}
              placeholder="Helpline: 1800-XXX-XXXX"
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500 focus:outline-none"
            />
            <input
              type="text"
              name="consumer_care_email"
              value={formData.consumer_care_email || ''}
              onChange={handleChange}
              placeholder="Email: care@company.in"
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Actions & Submit */}
        <div className="pt-3 border-t border-slate-200 flex items-center justify-between">
          <div>
            {saveSuccess && (
              <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4" /> Changes verified & saved!
              </span>
            )}
          </div>

          <button
            type="submit"
            disabled={isSaving}
            className="bg-brand-900 hover:bg-brand-800 text-white font-semibold text-xs px-5 py-2.5 rounded-lg shadow transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <Save className="h-4 w-4" />
            {isSaving ? 'Saving...' : 'Save & Verify Declarations'}
          </button>
        </div>
      </form>
    </div>
  );
}

