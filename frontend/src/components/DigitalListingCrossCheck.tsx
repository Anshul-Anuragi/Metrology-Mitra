'use client';

import React, { useState } from 'react';
import { Declaration, DigitalListingCrossCheckResponse, DigitalListingInput } from '@/types';
import { api } from '@/lib/api';

interface DigitalListingCrossCheckProps {
  inspectionId: string;
  physicalDeclaration?: Declaration | null;
  onCrossCheckCompleted?: (res: DigitalListingCrossCheckResponse) => void;
}

export const DigitalListingCrossCheck: React.FC<DigitalListingCrossCheckProps> = ({
  inspectionId,
  physicalDeclaration,
  onCrossCheckCompleted,
}) => {
  const [listingData, setListingData] = useState<DigitalListingInput>({
    title: physicalDeclaration?.commodity_name || '',
    price: physicalDeclaration?.mrp ? parseFloat(physicalDeclaration.mrp.replace(/[^0-9.]/g, '')) || undefined : undefined,
    net_quantity: physicalDeclaration?.net_quantity || '',
    country_of_origin: physicalDeclaration?.country_of_origin || 'India',
    manufacturer_name: physicalDeclaration?.manufacturer_name || '',
    listing_url: '',
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DigitalListingCrossCheckResponse | null>(null);

  const handleCrossCheck = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.submitDigitalListing(inspectionId, listingData);
      setResult(res);
      if (onCrossCheckCompleted) onCrossCheckCompleted(res);
    } catch (err) {
      console.error('Failed to submit digital listing cross-check', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-6 text-slate-900 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-5">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
            E-Commerce Digital Marketplace Cross-Check
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Rule 6(10) Mandatory Declarations &amp; Physical Package Cross-Verification
          </p>
        </div>
        <span className="px-2.5 py-1 bg-purple-50 text-purple-700 border border-purple-200 text-[10px] font-bold rounded-full uppercase tracking-wider">
          Rule 6(10) E-Commerce
        </span>
      </div>

      {/* Input Form */}
      <form onSubmit={handleCrossCheck} className="space-y-4 mb-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Marketplace Listing Title / Commodity
            </label>
            <input
              type="text"
              value={listingData.title || ''}
              onChange={(e) => setListingData({ ...listingData, title: e.target.value })}
              placeholder="e.g. Premium Basmati Rice 1kg"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:border-purple-600 focus:ring-2 focus:ring-purple-600/20 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Listed Selling Price / MRP (₹)
            </label>
            <input
              type="number"
              step="0.01"
              value={listingData.price !== undefined ? listingData.price : ''}
              onChange={(e) => setListingData({ ...listingData, price: parseFloat(e.target.value) || undefined })}
              placeholder="e.g. 240.00"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:border-purple-600 focus:ring-2 focus:ring-purple-600/20 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Listed Net Quantity
            </label>
            <input
              type="text"
              value={listingData.net_quantity || ''}
              onChange={(e) => setListingData({ ...listingData, net_quantity: e.target.value })}
              placeholder="e.g. 1 kg"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:border-purple-600 focus:ring-2 focus:ring-purple-600/20 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Listed Country of Origin
            </label>
            <input
              type="text"
              value={listingData.country_of_origin || ''}
              onChange={(e) => setListingData({ ...listingData, country_of_origin: e.target.value })}
              placeholder="e.g. India"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:border-purple-600 focus:ring-2 focus:ring-purple-600/20 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Listed Manufacturer / Brand Name
            </label>
            <input
              type="text"
              value={listingData.manufacturer_name || ''}
              onChange={(e) => setListingData({ ...listingData, manufacturer_name: e.target.value })}
              placeholder="e.g. Rice Exporters Ltd"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:border-purple-600 focus:ring-2 focus:ring-purple-600/20 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Marketplace Product URL
            </label>
            <input
              type="url"
              value={listingData.listing_url || ''}
              onChange={(e) => setListingData({ ...listingData, listing_url: e.target.value })}
              placeholder="https://ecom-marketplace.in/item/123"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:border-purple-600 focus:ring-2 focus:ring-purple-600/20 transition-all"
            />
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-purple-700 hover:bg-purple-800 text-white text-xs font-bold rounded-xl transition shadow-xs disabled:opacity-50 flex items-center gap-1.5 cursor-pointer"
          >
            {loading ? 'Cross-Checking...' : 'Run E-Commerce Cross-Check'}
          </button>
        </div>
      </form>

      {/* Results Comparison View */}
      {result && (
        <div className="border-t border-slate-100 pt-5">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Cross-Check Comparison Report
            </h4>
            <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold border ${
              result.has_contradictions
                ? 'bg-rose-50 border-rose-200 text-rose-800'
                : 'bg-emerald-50 border-emerald-200 text-emerald-800'
            }`}>
              {result.has_contradictions ? 'CONTRADICTIONS DETECTED' : 'DECLARATIONS MATCH'}
            </span>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-slate-200">
            <table className="w-full text-left text-xs text-slate-800 overflow-hidden">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200 text-[11px] font-semibold">
                <tr>
                  <th className="p-3">Field</th>
                  <th className="p-3">Physical Package Declaration</th>
                  <th className="p-3">Digital Marketplace Listing</th>
                  <th className="p-3">Finding / Statutory Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {result.items.map((item, idx) => (
                  <tr key={idx} className={item.is_contradiction ? 'bg-rose-50/50 hover:bg-rose-50/80 transition' : 'bg-white hover:bg-slate-50/80 transition'}>
                    <td className="p-3 font-semibold text-slate-900 capitalize">
                      {item.field_name.replace(/_/g, ' ')}
                    </td>
                    <td className="p-3 text-slate-700 font-mono text-[11px]">
                      {item.physical_value || '—'}
                    </td>
                    <td className="p-3 text-slate-700 font-mono text-[11px]">
                      {item.listing_value || '—'}
                    </td>
                    <td className="p-3">
                      <span className={`inline-flex items-center gap-1 text-xs ${
                        item.is_contradiction ? 'text-rose-700 font-bold' : 'text-emerald-700 font-bold'
                      }`}>
                        {item.is_contradiction ? '⚠️' : '✓'} {item.finding}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

