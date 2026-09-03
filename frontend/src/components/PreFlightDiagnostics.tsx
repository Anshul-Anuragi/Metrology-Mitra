'use client';

import React, { useState } from 'react';
import { ImageQualityDiagnostics } from '@/types';
import { api } from '@/lib/api';

interface PreFlightDiagnosticsProps {
  inspectionId: string;
  imageId: string;
  initialDiagnostics?: ImageQualityDiagnostics | null;
  sha256Hash?: string | null;
  onRetakeRequested?: () => void;
}

export const PreFlightDiagnostics: React.FC<PreFlightDiagnosticsProps> = ({
  inspectionId,
  imageId,
  initialDiagnostics,
  sha256Hash,
  onRetakeRequested,
}) => {
  const [diagnostics, setDiagnostics] = useState<ImageQualityDiagnostics | null>(
    initialDiagnostics || null
  );
  const [loading, setLoading] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);

  const runQualityGate = async () => {
    setLoading(true);
    try {
      const res = await api.runQualityGate(inspectionId, imageId);
      setDiagnostics(res);
    } catch (err) {
      console.error('Failed to run quality gate', err);
    } finally {
      setLoading(false);
    }
  };

  const copyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const activeHash = diagnostics?.sha256_hash || sha256Hash;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-white shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse" />
            Image Pre-Flight Diagnostics & Evidence Gate
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Automated quality assessment & byte-level integrity verification
          </p>
        </div>
        <button
          onClick={runQualityGate}
          disabled={loading}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-xs font-medium rounded-lg transition disabled:opacity-50 flex items-center gap-1.5"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Assessing...
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Run Quality Gate
            </>
          )}
        </button>
      </div>

      {/* Decision Banner */}
      {diagnostics && (
        <div className="mb-4">
          {diagnostics.gate_decision === 'READY_FOR_ANALYSIS' && (
            <div className="bg-emerald-950/60 border border-emerald-500/40 rounded-lg p-3 text-emerald-300 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-emerald-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                <span><strong>READY FOR ANALYSIS:</strong> Image meets optical sharpness and exposure standards.</span>
              </div>
              <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 font-semibold rounded text-[10px] tracking-wide">
                PASSED GATE
              </span>
            </div>
          )}

          {diagnostics.gate_decision === 'RETAKE_RECOMMENDED' && (
            <div className="bg-rose-950/60 border border-rose-500/40 rounded-lg p-3 text-rose-300 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-rose-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span><strong>RETAKE RECOMMENDED:</strong> Image quality may impede statutory declaration extraction.</span>
              </div>
              {onRetakeRequested && (
                <button
                  onClick={onRetakeRequested}
                  className="px-2.5 py-1 bg-rose-600 hover:bg-rose-500 text-white font-medium rounded text-[11px] transition"
                >
                  Capture Retake
                </button>
              )}
            </div>
          )}

          {diagnostics.gate_decision === 'MANUAL_REVIEW' && (
            <div className="bg-amber-950/60 border border-amber-500/40 rounded-lg p-3 text-amber-300 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-amber-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span><strong>MANUAL REVIEW:</strong> Minor optical anomalies detected. Inspector verification advised.</span>
              </div>
              <span className="px-2 py-0.5 bg-amber-500/20 text-amber-300 font-semibold rounded text-[10px]">
                OFFICER REVIEW
              </span>
            </div>
          )}
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
          <div className="text-[11px] text-slate-400 font-medium">Sharpness (Laplacian)</div>
          <div className="text-base font-bold text-white mt-1">
            {diagnostics ? diagnostics.blur_score.toFixed(1) : '—'}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Status: {diagnostics ? diagnostics.blur_status : 'Pending'}
          </div>
        </div>

        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
          <div className="text-[11px] text-slate-400 font-medium">Specular Glare</div>
          <div className="text-base font-bold text-white mt-1">
            {diagnostics ? `${(diagnostics.glare_ratio * 100).toFixed(1)}%` : '—'}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Status: {diagnostics ? diagnostics.glare_status : 'Pending'}
          </div>
        </div>

        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
          <div className="text-[11px] text-slate-400 font-medium">Luminance / Exposure</div>
          <div className="text-base font-bold text-white mt-1">
            {diagnostics && diagnostics.exposure_mean !== undefined ? `${diagnostics.exposure_mean.toFixed(0)} / 255` : '—'}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Status: {diagnostics?.exposure_status || 'Normal'}
          </div>
        </div>

        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
          <div className="text-[11px] text-slate-400 font-medium">Resolution</div>
          <div className="text-base font-bold text-white mt-1">
            {diagnostics ? `${diagnostics.width} × ${diagnostics.height}` : '—'}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Status: {diagnostics ? diagnostics.resolution_status : 'Optimal'}
          </div>
        </div>
      </div>

      {/* Actionable Reasons */}
      {diagnostics?.actionable_reasons && diagnostics.actionable_reasons.length > 0 && (
        <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 mb-4">
          <div className="text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Actionable Quality Observations:
          </div>
          <ul className="list-disc list-inside text-xs text-slate-400 space-y-1">
            {diagnostics.actionable_reasons.map((reason, idx) => (
              <li key={idx}>{reason}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Evidence Integrity Hash (SHA-256) */}
      {activeHash && (
        <div className="bg-slate-950/90 border border-slate-800 rounded-lg p-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2 overflow-hidden">
            <svg className="w-4 h-4 text-cyan-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <div className="truncate">
              <div className="text-[10px] text-slate-400 font-medium">Evidence Integrity Hash (SHA-256 Byte-Level Fingerprint):</div>
              <code className="text-xs font-mono text-cyan-300 truncate block">
                {activeHash}
              </code>
            </div>
          </div>
          <button
            onClick={() => copyHash(activeHash)}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] rounded transition shrink-0"
          >
            {copiedHash ? '✓ Copied' : 'Copy Hash'}
          </button>
        </div>
      )}
    </div>
  );
};
