'use client';

import React, { useState } from 'react';
import { MeasurementResponse } from '@/types';
import { api } from '@/lib/api';

interface MeasurementAssistantProps {
  inspectionId: string;
  initialPdpArea?: number | null;
  onMeasurementSaved?: (res: MeasurementResponse) => void;
}

export const MeasurementAssistant: React.FC<MeasurementAssistantProps> = ({
  inspectionId,
  initialPdpArea,
  onMeasurementSaved,
}) => {
  const [pdpArea, setPdpArea] = useState<number>(initialPdpArea || 80);
  const [pixelHeight, setPixelHeight] = useState<number>(24);
  const [isCalibrated, setIsCalibrated] = useState<boolean>(true);
  const [pixelScale, setPixelScale] = useState<number>(0.08); // mm per pixel
  const [scaleSource, setScaleSource] = useState<string>('REFERENCE_OBJECT');
  const [isBlownOrMoulded, setIsBlownOrMoulded] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [measurementResult, setMeasurementResult] = useState<MeasurementResponse | null>(null);

  // Compute live Schedule II minimum height threshold
  const getMinHeightThreshold = (area: number, blown: boolean): number => {
    if (area <= 50) return blown ? 1.5 : 1.0;
    if (area <= 100) return blown ? 2.0 : 1.5;
    if (area <= 500) return blown ? 4.0 : 2.0;
    if (area <= 2500) return blown ? 6.0 : 4.0;
    return 6.0;
  };

  const currentThreshold = getMinHeightThreshold(pdpArea, isBlownOrMoulded);
  const estimatedPhysicalHeight = isCalibrated && pixelScale ? pixelHeight * pixelScale : null;

  const handleCalculateAndSave = async () => {
    setLoading(true);
    try {
      const res = await api.recordMeasurement(inspectionId, {
        pdp_area_cm2: pdpArea,
        pixel_height: pixelHeight,
        pixel_scale_mm_per_px: isCalibrated ? pixelScale : undefined,
        scale_source: isCalibrated ? scaleSource : 'UNAVAILABLE',
        scale_confidence: isCalibrated ? 0.9 : 0.0,
        is_blown_or_moulded: isBlownOrMoulded,
      });
      setMeasurementResult(res);
      if (onMeasurementSaved) onMeasurementSaved(res);
    } catch (err) {
      console.error('Failed to record measurement', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-6 text-slate-900 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <span>Reference-Assisted Numeral Height Assistant</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Rule 7 &amp; Schedule II Table 1 Principal Display Panel (PDP) Numeral Height Assessment
          </p>
        </div>
        <span className="px-2.5 py-1 bg-indigo-50 text-indigo-700 border border-indigo-200 text-[10px] font-bold rounded-full uppercase tracking-wider">
          Decision-Support Prototype
        </span>
      </div>

      {/* Mandatory Statutory Prototype Notice */}
      <div className="bg-amber-50/80 border border-amber-200/90 rounded-2xl p-4 text-amber-900 text-xs flex items-start gap-2.5 shadow-xs">
        <svg className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <strong>Statutory Compliance Guardrail:</strong> Uncalibrated camera images cannot provide certified physical millimeter dimensions. Without reference scale calibration, optical estimation is strictly advisory and outputs <span className="font-bold text-amber-950">REVIEW</span> for manual physical gauge verification by the inspecting officer.
        </div>
      </div>

      {/* Form Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* PDP Area */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Principal Display Panel (PDP) Area ($A$ in cm²)
          </label>
          <input
            type="number"
            min="1"
            max="10000"
            value={pdpArea}
            onChange={(e) => setPdpArea(parseFloat(e.target.value) || 1)}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-hidden focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/20 transition-all"
          />
          <div className="text-[11px] text-slate-500 mt-1 font-medium">
            Schedule II Tier: Min Height = <strong className="text-indigo-700">{currentThreshold.toFixed(1)} mm</strong>
          </div>
        </div>

        {/* Pixel Height */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Measured Numeral Bounding Box (Pixels)
          </label>
          <input
            type="number"
            min="1"
            max="2000"
            value={pixelHeight}
            onChange={(e) => setPixelHeight(parseFloat(e.target.value) || 1)}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-hidden focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/20 transition-all"
          />
          <div className="text-[11px] text-slate-500 mt-1 font-medium">
            Raw optical numeral height on captured sensor
          </div>
        </div>

        {/* Reference Scale Calibration */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs font-semibold text-slate-700">
              Reference Scale Calibration
            </label>
            <label className="flex items-center gap-1.5 text-xs text-slate-600 font-medium cursor-pointer">
              <input
                type="checkbox"
                checked={isCalibrated}
                onChange={(e) => setIsCalibrated(e.target.checked)}
                className="rounded border-slate-300 text-indigo-600 focus:ring-0"
              />
              Calibrated Scale Present
            </label>
          </div>
          {isCalibrated ? (
            <div className="flex gap-2">
              <input
                type="number"
                step="0.001"
                min="0.001"
                value={pixelScale}
                onChange={(e) => setPixelScale(parseFloat(e.target.value) || 0.08)}
                className="w-1/2 bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-hidden focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/20 transition-all"
                placeholder="mm / px"
              />
              <select
                value={scaleSource}
                onChange={(e) => setScaleSource(e.target.value)}
                className="w-1/2 bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 text-xs text-slate-700 focus:bg-white focus:outline-hidden focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/20 transition-all"
              >
                <option value="REFERENCE_OBJECT">Reference Object (Coin/Card)</option>
                <option value="AR_MARKER">AR / Grid Target</option>
                <option value="DEVICE_SENSOR">Hardware Sensor Calibration</option>
              </select>
            </div>
          ) : (
            <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-2.5 text-xs text-amber-900 font-medium">
              No calibrated scale. Measurement will record as unverified image estimation.
            </div>
          )}
        </div>

        {/* Blown/Moulded Package Type */}
        <div className="flex flex-col justify-center">
          <label className="flex items-center gap-2 text-xs text-slate-700 font-medium cursor-pointer">
            <input
              type="checkbox"
              checked={isBlownOrMoulded}
              onChange={(e) => setIsBlownOrMoulded(e.target.checked)}
              className="rounded border-slate-300 text-indigo-600 focus:ring-0"
            />
            <span>Blown, formed, moulded, or perforated container</span>
          </label>
          <div className="text-[11px] text-slate-500 mt-1 font-medium">
            Applies higher statutory minimum heights per Rule 7 Schedule II Table 1
          </div>
        </div>
      </div>

      {/* Live Estimation Preview */}
      <div className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
        <div>
          <div className="text-xs font-semibold text-slate-500">Live Statutory Assessment:</div>
          <div className="text-sm font-bold text-slate-900 mt-0.5 flex items-center gap-2">
            <span>
              Estimated Physical Height:{' '}
              {estimatedPhysicalHeight !== null
                ? `${estimatedPhysicalHeight.toFixed(2)} mm`
                : 'Uncalibrated (Scale Required)'}
            </span>
            <span className="text-slate-400 font-normal">|</span>
            <span className="text-indigo-700">
              Prescribed Statutory Min: {currentThreshold.toFixed(1)} mm
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={handleCalculateAndSave}
          disabled={loading}
          className="px-4 py-2 bg-indigo-700 hover:bg-indigo-800 text-white text-xs font-bold rounded-xl transition shadow-xs disabled:opacity-50 shrink-0 cursor-pointer"
        >
          {loading ? 'Evaluating...' : 'Record & Link Evidence'}
        </button>
      </div>

      {/* Evaluated Result Badge */}
      {measurementResult && (
        <div
          className={`p-3.5 rounded-2xl border text-xs shadow-xs ${
            measurementResult.result === 'PASS'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
              : 'bg-amber-50 border-amber-200 text-amber-900'
          }`}
        >
          <div className="font-bold flex items-center gap-1.5">
            <span>Result: {measurementResult.result}</span>
            <span className="text-slate-600 font-medium">({measurementResult.reason})</span>
          </div>
        </div>
      )}
    </div>
  );
};
