'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import {
  Gavel,
  CheckCircle2,
  XCircle,
  RotateCcw,
  MinusCircle,
  FileText,
  Shield,
  Clock,
  AlertTriangle,
  Loader2,
  Printer,
} from 'lucide-react';

interface InspectorDecisionSectionProps {
  inspectionId: string;
  status?: string;
  overallResult?: string;
  reviewedBy?: string | null;
  reviewedAt?: string | null;
  reviewNotes?: string | null;
  onDecisionSubmitted?: () => void;
  onOpenReport?: () => void;
}

export default function InspectorDecisionSection({
  inspectionId,
  status,
  overallResult,
  reviewedBy,
  reviewedAt,
  reviewNotes,
  onDecisionSubmitted,
  onOpenReport,
}: InspectorDecisionSectionProps) {
  const [notes, setNotes] = useState(reviewNotes || '');
  const [submittingAction, setSubmittingAction] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [recordedDecision, setRecordedDecision] = useState<{
    action: string;
    timestamp: string;
    notes: string;
  } | null>(
    reviewedAt
      ? {
          action: 'CONFIRMED',
          timestamp: reviewedAt,
          notes: reviewNotes || '',
        }
      : null
  );

  const handleDecision = async (
    action: 'CONFIRM' | 'CORRECT' | 'REQUEST_RETAKE' | 'MARK_UNRESOLVED'
  ) => {
    if (!inspectionId) return;
    setSubmittingAction(action);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      await api.submitReview(inspectionId, {
        review_action: action,
        review_notes: notes.trim() || undefined,
      });

      const now = new Date().toLocaleString();
      setRecordedDecision({
        action,
        timestamp: now,
        notes: notes.trim(),
      });

      const actionLabels: Record<string, string> = {
        CONFIRM: 'Result confirmed by inspector',
        CORRECT: 'AI finding rejected/corrected by inspector',
        REQUEST_RETAKE: 'Rescan requested from field officer',
        MARK_UNRESOLVED: 'Marked not applicable / unresolvable',
      };

      setSuccessMsg(actionLabels[action] || 'Decision recorded successfully.');

      if (onDecisionSubmitted) {
        onDecisionSubmitted();
      }

      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err: any) {
      setErrorMsg(
        err?.response?.data?.detail ||
          'Failed to record inspector decision. Please check network connection.'
      );
    } finally {
      setSubmittingAction(null);
    }
  };

  const isCompleted = status === 'COMPLETED';

  return (
    <div className="bg-white/90 backdrop-blur-md rounded-3xl border border-slate-200/90 shadow-sm p-6 space-y-4">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
            <Gavel className="h-5 w-5 text-sky-700" />
            <span>Inspector decision</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Every decision is written to the audit trail and queued for sync.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono font-bold bg-sky-50 text-sky-800 border border-sky-200 px-2.5 py-1 rounded-full flex items-center gap-1">
            <Shield className="h-3 w-3 text-sky-600" />
            <span>STATUTORY AUDIT LEDGER</span>
          </span>
        </div>
      </div>

      {/* Messages */}
      {errorMsg && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-700 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-2xl text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Observation note textarea */}
      <div className="space-y-1.5">
        <label className="block text-xs font-semibold text-slate-700">
          Observation note (optional)
        </label>
        <textarea
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          disabled={isCompleted || submittingAction !== null}
          placeholder="Enter statutory observation notes, packaging remarks, or justification..."
          className="w-full text-xs p-3 rounded-2xl border border-slate-200 bg-slate-50/70 focus:bg-white focus:border-sky-500 focus:ring-1 focus:ring-sky-500 outline-hidden transition placeholder:text-slate-400 disabled:opacity-60"
        />
      </div>

      {/* 4 Primary Action Buttons */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
        {/* 1. Confirm result */}
        <button
          type="button"
          onClick={() => handleDecision('CONFIRM')}
          disabled={isCompleted || submittingAction !== null}
          className="py-2.5 px-3 bg-sky-700 hover:bg-sky-800 active:bg-sky-900 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center justify-center gap-1.5 disabled:opacity-50 cursor-pointer"
        >
          {submittingAction === 'CONFIRM' ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <CheckCircle2 className="h-3.5 w-3.5" />
          )}
          <span>Confirm result</span>
        </button>

        {/* 2. Reject AI finding */}
        <button
          type="button"
          onClick={() => handleDecision('CORRECT')}
          disabled={isCompleted || submittingAction !== null}
          className="py-2.5 px-3 bg-white hover:bg-rose-50 text-rose-700 hover:text-rose-800 font-bold text-xs rounded-xl border border-rose-200 transition flex items-center justify-center gap-1.5 disabled:opacity-50 cursor-pointer"
        >
          {submittingAction === 'CORRECT' ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <XCircle className="h-3.5 w-3.5" />
          )}
          <span>Reject AI finding</span>
        </button>

        {/* 3. Request rescan */}
        <button
          type="button"
          onClick={() => handleDecision('REQUEST_RETAKE')}
          disabled={isCompleted || submittingAction !== null}
          className="py-2.5 px-3 bg-white hover:bg-amber-50 text-amber-700 hover:text-amber-800 font-bold text-xs rounded-xl border border-amber-200 transition flex items-center justify-center gap-1.5 disabled:opacity-50 cursor-pointer"
        >
          {submittingAction === 'REQUEST_RETAKE' ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <RotateCcw className="h-3.5 w-3.5" />
          )}
          <span>Request rescan</span>
        </button>

        {/* 4. Mark not applicable */}
        <button
          type="button"
          onClick={() => handleDecision('MARK_UNRESOLVED')}
          disabled={isCompleted || submittingAction !== null}
          className="py-2.5 px-3 bg-white hover:bg-slate-100 text-slate-700 font-bold text-xs rounded-xl border border-slate-200 transition flex items-center justify-center gap-1.5 disabled:opacity-50 cursor-pointer"
        >
          {submittingAction === 'MARK_UNRESOLVED' ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <MinusCircle className="h-3.5 w-3.5" />
          )}
          <span>Mark not applicable</span>
        </button>
      </div>

      {/* Decision Status & Printable Report Links */}
      <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          {recordedDecision ? (
            <div className="flex items-center gap-1.5 text-emerald-800 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-xl">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
              <span>
                <strong>Decision recorded:</strong> {recordedDecision.action} on{' '}
                {recordedDecision.timestamp}
              </span>
            </div>
          ) : (
            <span className="text-slate-500 italic flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-slate-400" />
              No decision recorded yet.
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {onOpenReport ? (
            <button
              type="button"
              onClick={onOpenReport}
              className="text-sky-700 hover:text-sky-800 font-bold flex items-center gap-1.5 underline underline-offset-2 cursor-pointer"
            >
              <Printer className="h-3.5 w-3.5" />
              <span>Open printable violation report</span>
            </button>
          ) : (
            <a
              href={`/inspections/${inspectionId}?tab=reports`}
              className="text-sky-700 hover:text-sky-800 font-bold flex items-center gap-1.5 underline underline-offset-2 cursor-pointer"
            >
              <Printer className="h-3.5 w-3.5" />
              <span>Open printable violation report</span>
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

