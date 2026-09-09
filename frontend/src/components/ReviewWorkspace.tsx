'use client';

import React, { useState } from 'react';
import { Declaration, ReviewWorkspaceResponse } from '@/types';
import { api } from '@/lib/api';

interface ReviewWorkspaceProps {
  inspectionId: string;
  workspaceData: ReviewWorkspaceResponse;
  onReviewSubmitted?: (updated: ReviewWorkspaceResponse) => void;
  onFinalized?: () => void;
}

export const ReviewWorkspace: React.FC<ReviewWorkspaceProps> = ({
  inspectionId,
  workspaceData,
  onReviewSubmitted,
  onFinalized,
}) => {
  const [reviewAction, setReviewAction] = useState<'CONFIRM' | 'CORRECT' | 'REQUEST_RETAKE' | 'MARK_UNRESOLVED'>('CONFIRM');
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [showCorrectionForm, setShowCorrectionForm] = useState<boolean>(false);
  const [overrides, setOverrides] = useState<Partial<Declaration>>({
    commodity_name: workspaceData.declaration?.commodity_name || '',
    manufacturer_name: workspaceData.declaration?.manufacturer_name || '',
    address: workspaceData.declaration?.address || '',
    net_quantity: workspaceData.declaration?.net_quantity || '',
    mrp: workspaceData.declaration?.mrp || '',
    unit_sale_price: workspaceData.declaration?.unit_sale_price || '',
    expiry_date: workspaceData.declaration?.expiry_date || '',
  });

  const [loadingReview, setLoadingReview] = useState<boolean>(false);
  const [loadingFinalize, setLoadingFinalize] = useState<boolean>(false);
  const [showFinalizeModal, setShowFinalizeModal] = useState<boolean>(false);
  const [finalizationNotes, setFinalizationNotes] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const isCompleted = workspaceData.status === 'COMPLETED';

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isCompleted) return;
    setLoadingReview(true);
    setErrorMsg(null);
    try {
      const payload = {
        review_action: reviewAction,
        review_notes: reviewNotes,
        declaration_overrides: reviewAction === 'CORRECT' ? overrides : undefined,
      };
      const res = await api.submitReview(inspectionId, payload);
      if (onReviewSubmitted) onReviewSubmitted(res);
    } catch (err: any) {
      console.error('Failed to submit review', err);
      setErrorMsg(err?.response?.data?.detail || 'Failed to submit review.');
    } finally {
      setLoadingReview(false);
    }
  };

  const handleFinalize = async () => {
    if (isCompleted) return;
    setLoadingFinalize(true);
    setErrorMsg(null);
    try {
      await api.finalizeInspection(inspectionId, { finalization_notes: finalizationNotes });
      setShowFinalizeModal(false);
      if (onFinalized) onFinalized();
    } catch (err: any) {
      console.error('Failed to finalize inspection', err);
      setErrorMsg(err?.response?.data?.detail || 'Failed to finalize inspection.');
    } finally {
      setLoadingFinalize(false);
    }
  };

  return (
    <div className="bg-white/85 backdrop-blur-md rounded-3xl border border-slate-200/90 p-6 text-slate-900 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-3 gap-2">
        <div>
          <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
            <svg className="w-5 h-5 text-sky-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Inspector Review &amp; Adjudication Workspace</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Human-in-the-loop statutory verification &amp; official case record finalization
          </p>
        </div>
        {isCompleted ? (
          <span className="px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold rounded-full flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-600" />
            LOCKED (COMPLETED)
          </span>
        ) : (
          <span className="px-3 py-1 bg-amber-50 border border-amber-200 text-amber-800 text-xs font-bold rounded-full">
            ADJUDICATION IN PROGRESS
          </span>
        )}
      </div>

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-3 text-rose-700 text-xs">
          {errorMsg}
        </div>
      )}

      {/* Blocking Reasons Alert */}
      {!workspaceData.can_finalize && workspaceData.blocking_reasons.length > 0 && !isCompleted && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-3.5">
          <div className="text-xs font-bold text-amber-800 mb-1 flex items-center gap-1.5">
            <svg className="w-4 h-4 text-amber-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Finalization Guardrail: Action Required Before Finalization
          </div>
          <ul className="list-disc list-inside text-xs text-amber-700 space-y-0.5">
            {workspaceData.blocking_reasons.map((r, idx) => (
              <li key={idx}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Review Form */}
      {!isCompleted ? (
        <form onSubmit={handleSubmitReview} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wider">
              Select Adjudication Action:
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                type="button"
                onClick={() => {
                  setReviewAction('CONFIRM');
                  setShowCorrectionForm(false);
                }}
                className={`p-3 rounded-2xl border text-left transition cursor-pointer ${
                  reviewAction === 'CONFIRM'
                    ? 'bg-sky-50 border-sky-300 text-sky-900 ring-1 ring-sky-300'
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <div className="text-xs font-bold">✓ Confirm Extracted</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Approve OCR extractions as accurate</div>
              </button>

              <button
                type="button"
                onClick={() => {
                  setReviewAction('CORRECT');
                  setShowCorrectionForm(true);
                }}
                className={`p-3 rounded-2xl border text-left transition cursor-pointer ${
                  reviewAction === 'CORRECT'
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-900 ring-1 ring-indigo-300'
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <div className="text-xs font-bold">✏️ Field Correction</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Override OCR fields manually</div>
              </button>

              <button
                type="button"
                onClick={() => {
                  setReviewAction('REQUEST_RETAKE');
                  setShowCorrectionForm(false);
                }}
                className={`p-3 rounded-2xl border text-left transition cursor-pointer ${
                  reviewAction === 'REQUEST_RETAKE'
                    ? 'bg-amber-50 border-amber-300 text-amber-900 ring-1 ring-amber-300'
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <div className="text-xs font-bold">📸 Request Retake</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Flag illegible label for recapture</div>
              </button>

              <button
                type="button"
                onClick={() => {
                  setReviewAction('MARK_UNRESOLVED');
                  setShowCorrectionForm(false);
                }}
                className={`p-3 rounded-2xl border text-left transition cursor-pointer ${
                  reviewAction === 'MARK_UNRESOLVED'
                    ? 'bg-purple-50 border-purple-300 text-purple-900 ring-1 ring-purple-300'
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <div className="text-xs font-bold">⚖️ Escalate / Unresolved</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Refer to Senior Legal Metrology Officer</div>
              </button>
            </div>
          </div>

          {/* Manual Correction Fields */}
          {(showCorrectionForm || reviewAction === 'CORRECT') && (
            <div className="bg-slate-50/80 border border-slate-200 rounded-2xl p-4 space-y-3">
              <div className="text-xs font-bold text-slate-800 border-b border-slate-200 pb-2">
                Field Correction Overrides (Applies Human Verification):
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Commodity Name</label>
                  <input
                    type="text"
                    value={overrides.commodity_name || ''}
                    onChange={(e) => setOverrides({ ...overrides, commodity_name: e.target.value })}
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-900 focus:border-sky-500 outline-hidden"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Manufacturer Name</label>
                  <input
                    type="text"
                    value={overrides.manufacturer_name || ''}
                    onChange={(e) => setOverrides({ ...overrides, manufacturer_name: e.target.value })}
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-900 focus:border-sky-500 outline-hidden"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Declared Net Quantity (e.g. 500 g)</label>
                  <input
                    type="text"
                    value={overrides.net_quantity || ''}
                    onChange={(e) => setOverrides({ ...overrides, net_quantity: e.target.value })}
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-900 focus:border-sky-500 outline-hidden"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Declared MRP (e.g. MRP Rs. 250.00 incl. of all taxes)</label>
                  <input
                    type="text"
                    value={overrides.mrp || ''}
                    onChange={(e) => setOverrides({ ...overrides, mrp: e.target.value })}
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-900 focus:border-sky-500 outline-hidden"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Unit Sale Price (USP) (e.g. Rs. 0.50/g)</label>
                  <input
                    type="text"
                    value={overrides.unit_sale_price || ''}
                    onChange={(e) => setOverrides({ ...overrides, unit_sale_price: e.target.value })}
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-900 focus:border-sky-500 outline-hidden"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Expiry / Best Before Date (e.g. 12/2026)</label>
                  <input
                    type="text"
                    value={overrides.expiry_date || ''}
                    onChange={(e) => setOverrides({ ...overrides, expiry_date: e.target.value })}
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-900 focus:border-sky-500 outline-hidden"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Officer Inspection Findings &amp; Review Notes:
            </label>
            <textarea
              rows={2}
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder="Record statutory observations, physical package verification notes, or reasons for correction..."
              className="w-full bg-white border border-slate-200 rounded-2xl px-3 py-2 text-xs text-slate-900 focus:outline-hidden focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="submit"
              disabled={loadingReview}
              className="px-4 py-2.5 bg-sky-700 hover:bg-sky-800 text-white text-xs font-bold rounded-xl transition shadow-xs disabled:opacity-50 cursor-pointer"
            >
              {loadingReview ? 'Saving Adjudication...' : 'Submit Review Decision & Re-Evaluate'}
            </button>

            <button
              type="button"
              disabled={!workspaceData.can_finalize || loadingFinalize}
              onClick={() => setShowFinalizeModal(true)}
              className="px-4 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold rounded-xl transition shadow-xs disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 cursor-pointer"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span>Finalize Inspection</span>
            </button>
          </div>
        </form>
      ) : (
        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 text-xs text-emerald-900 flex items-center justify-between">
          <div>
            <div className="font-bold text-emerald-950">Case Record Finalized</div>
            <div className="text-emerald-800 mt-0.5">
              This inspection has been completed and permanently locked. Mutations are prohibited under Rule 36(1) audit guidelines.
            </div>
          </div>
          <span className="px-3 py-1 bg-white border border-emerald-300 text-emerald-800 font-bold rounded-full text-[11px] shadow-2xs">
            SEALED CASE
          </span>
        </div>
      )}

      {/* Finalization Modal */}
      {showFinalizeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="bg-white border border-slate-200 rounded-3xl max-w-md w-full p-6 text-slate-900 shadow-2xl space-y-4">
            <div className="flex items-center gap-2.5 text-amber-700 font-bold text-sm">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Confirm Official Finalization &amp; Mutation Lock
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Finalizing will officially seal this compliance inspection and transition its status to <strong className="text-slate-900">COMPLETED</strong>. All future modifications to declarations, images, or evaluation rules will be permanently rejected.
            </p>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Final Closing Remarks:
              </label>
              <textarea
                rows={2}
                value={finalizationNotes}
                onChange={(e) => setFinalizationNotes(e.target.value)}
                placeholder="Optional closing notes for final record..."
                className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-3 py-2 text-xs text-slate-900 focus:bg-white focus:border-sky-500 outline-hidden"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowFinalizeModal(false)}
                className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-xs font-bold text-slate-700 rounded-xl transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={loadingFinalize}
                onClick={handleFinalize}
                className="px-4 py-2 bg-sky-700 hover:bg-sky-800 text-white text-xs font-bold rounded-xl transition shadow-xs disabled:opacity-50 cursor-pointer"
              >
                {loadingFinalize ? 'Finalizing...' : 'Confirm & Permanently Seal'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

