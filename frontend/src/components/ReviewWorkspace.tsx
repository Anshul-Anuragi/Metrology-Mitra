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
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-white shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Inspector Review & Adjudication Workspace
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Human-in-the-loop statutory verification & official case record finalization
          </p>
        </div>
        {isCompleted ? (
          <span className="px-3 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs font-semibold rounded-full flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            LOCKED (COMPLETED)
          </span>
        ) : (
          <span className="px-3 py-1 bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-semibold rounded-full">
            ADJUDICATION IN PROGRESS
          </span>
        )}
      </div>

      {errorMsg && (
        <div className="bg-rose-950/60 border border-rose-500/40 rounded-lg p-3 text-rose-300 text-xs mb-4">
          {errorMsg}
        </div>
      )}

      {/* Blocking Reasons Alert */}
      {!workspaceData.can_finalize && workspaceData.blocking_reasons.length > 0 && !isCompleted && (
        <div className="bg-amber-950/40 border border-amber-500/30 rounded-lg p-3 mb-4">
          <div className="text-xs font-semibold text-amber-300 mb-1 flex items-center gap-1.5">
            <svg className="w-4 h-4 text-amber-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Finalization Guardrail: Action Required Before Finalization
          </div>
          <ul className="list-disc list-inside text-xs text-amber-200/80 space-y-0.5">
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
            <label className="block text-xs font-medium text-slate-300 mb-2">
              Select Adjudication Action:
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                type="button"
                onClick={() => {
                  setReviewAction('CONFIRM');
                  setShowCorrectionForm(false);
                }}
                className={`p-3 rounded-lg border text-left transition ${
                  reviewAction === 'CONFIRM'
                    ? 'bg-emerald-950 border-emerald-500 text-emerald-200'
                    : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="text-xs font-semibold">✓ Confirm Extracted</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Approve OCR extractions as accurate</div>
              </button>

              <button
                type="button"
                onClick={() => {
                  setReviewAction('CORRECT');
                  setShowCorrectionForm(true);
                }}
                className={`p-3 rounded-lg border text-left transition ${
                  reviewAction === 'CORRECT'
                    ? 'bg-blue-950 border-blue-500 text-blue-200'
                    : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="text-xs font-semibold">✏️ Field Correction</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Override OCR fields manually</div>
              </button>

              <button
                type="button"
                onClick={() => {
                  setReviewAction('REQUEST_RETAKE');
                  setShowCorrectionForm(false);
                }}
                className={`p-3 rounded-lg border text-left transition ${
                  reviewAction === 'REQUEST_RETAKE'
                    ? 'bg-rose-950 border-rose-500 text-rose-200'
                    : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="text-xs font-semibold">📸 Request Retake</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Flag illegible label for recapture</div>
              </button>

              <button
                type="button"
                onClick={() => {
                  setReviewAction('MARK_UNRESOLVED');
                  setShowCorrectionForm(false);
                }}
                className={`p-3 rounded-lg border text-left transition ${
                  reviewAction === 'MARK_UNRESOLVED'
                    ? 'bg-purple-950 border-purple-500 text-purple-200'
                    : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="text-xs font-semibold">⚖️ Escalate / Unresolved</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Refer to Senior Legal Metrology Officer</div>
              </button>
            </div>
          </div>

          {/* Manual Correction Fields */}
          {(showCorrectionForm || reviewAction === 'CORRECT') && (
            <div className="bg-slate-950/90 border border-slate-800 rounded-lg p-4 space-y-3">
              <div className="text-xs font-semibold text-slate-300 border-b border-slate-800 pb-2">
                Field Correction Overrides (Applies Human Verification):
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Commodity Name</label>
                  <input
                    type="text"
                    value={overrides.commodity_name || ''}
                    onChange={(e) => setOverrides({ ...overrides, commodity_name: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Manufacturer Name</label>
                  <input
                    type="text"
                    value={overrides.manufacturer_name || ''}
                    onChange={(e) => setOverrides({ ...overrides, manufacturer_name: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Declared Net Quantity (e.g. 500 g)</label>
                  <input
                    type="text"
                    value={overrides.net_quantity || ''}
                    onChange={(e) => setOverrides({ ...overrides, net_quantity: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Declared MRP (e.g. MRP Rs. 250.00 incl. of all taxes)</label>
                  <input
                    type="text"
                    value={overrides.mrp || ''}
                    onChange={(e) => setOverrides({ ...overrides, mrp: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Unit Sale Price (USP) (e.g. Rs. 0.50/g)</label>
                  <input
                    type="text"
                    value={overrides.unit_sale_price || ''}
                    onChange={(e) => setOverrides({ ...overrides, unit_sale_price: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Expiry / Best Before Date (e.g. 12/2026)</label>
                  <input
                    type="text"
                    value={overrides.expiry_date || ''}
                    onChange={(e) => setOverrides({ ...overrides, expiry_date: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Officer Inspection Findings & Review Notes:
            </label>
            <textarea
              rows={2}
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder="Record statutory observations, physical package verification notes, or reasons for correction..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="submit"
              disabled={loadingReview}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition disabled:opacity-50"
            >
              {loadingReview ? 'Saving Adjudication...' : 'Submit Review Decision & Re-Evaluate'}
            </button>

            <button
              type="button"
              disabled={!workspaceData.can_finalize || loadingFinalize}
              onClick={() => setShowFinalizeModal(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Finalize Inspection
            </button>
          </div>
        </form>
      ) : (
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 text-xs text-slate-300 flex items-center justify-between">
          <div>
            <div className="font-semibold text-white">Case Record Finalized</div>
            <div className="text-slate-400 mt-0.5">
              This inspection has been completed and permanently locked. Mutations are prohibited under Rule 36(1) audit guidelines.
            </div>
          </div>
          <span className="px-3 py-1 bg-emerald-950 border border-emerald-500/40 text-emerald-300 font-semibold rounded text-[11px]">
            SEALED CASE
          </span>
        </div>
      )}

      {/* Finalization Modal */}
      {showFinalizeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 text-white shadow-2xl space-y-4">
            <div className="flex items-center gap-2.5 text-amber-400 font-semibold text-sm">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Confirm Official Finalization & Mutation Lock
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Finalizing will officially seal this compliance inspection and transition its status to <strong className="text-white">COMPLETED</strong>. All future modifications to declarations, images, or evaluation rules will be permanently rejected (<code className="text-cyan-300">HTTP 409 Conflict</code>).
            </p>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Final Closing Remarks:
              </label>
              <textarea
                rows={2}
                value={finalizationNotes}
                onChange={(e) => setFinalizationNotes(e.target.value)}
                placeholder="Optional closing notes for final record..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowFinalizeModal(false)}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs rounded-lg transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={loadingFinalize}
                onClick={handleFinalize}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-xs font-semibold rounded-lg transition disabled:opacity-50"
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

