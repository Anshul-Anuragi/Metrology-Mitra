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
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-white shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Reference-Assisted Numeral Height Assistant
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Rule 7 & Schedule II Table 1 Principal Display Panel (PDP) Numeral Height Assessment
          </p>
        </div>
        <span className="px-2.5 py-1 bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-semibold rounded-full uppercase tracking-wider">
          Decision-Support Prototype
        </span>
      </div>

      {/* Mandatory Statutory Prototype Notice */}
      <div className="bg-amber-950/40 border border-amber-500/30 rounded-lg p-3 text-amber-300 text-xs mb-4 flex items-start gap-2">
        <svg className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <strong>Statutory Compliance Guardrail:</strong> Uncalibrated camera images cannot provide certified physical millimeter dimensions. Without reference scale calibration, optical estimation is strictly advisory and outputs <span className="font-semibold text-amber-200">REVIEW</span> for manual physical gauge verification by the inspecting officer.
        </div>
      </div>

      {/* Form Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        {/* PDP Area */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Principal Display Panel (PDP) Area ($A$ in cm²)
          </label>
          <input
            type="number"
            min="1"
            max="10000"
            value={pdpArea}
            onChange={(e) => setPdpArea(parseFloat(e.target.value) || 1)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
          />
          <div className="text-[11px] text-slate-400 mt-1">
            Schedule II Tier: Min Height = <strong className="text-indigo-300">{currentThreshold.toFixed(1)} mm</strong>
          </div>
        </div>

        {/* Pixel Height */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Measured Numeral Bounding Box (Pixels)
          </label>
          <input
            type="number"
            min="1"
            max="2000"
            value={pixelHeight}
            onChange={(e) => setPixelHeight(parseFloat(e.target.value) || 1)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
          />
          <div className="text-[11px] text-slate-400 mt-1">
            Raw optical numeral height on captured sensor
          </div>
        </div>

        {/* Reference Scale Calibration */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs font-medium text-slate-300">
              Reference Scale Calibration
            </label>
            <label className="flex items-center gap-1.5 text-xs text-slate-400 cursor-pointer">
              <input
                type="checkbox"
                checked={isCalibrated}
                onChange={(e) => setIsCalibrated(e.target.checked)}
                className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-0"
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
                className="w-1/2 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                placeholder="mm / px"
              />
              <select
                value={scaleSource}
                onChange={(e) => setScaleSource(e.target.value)}
                className="w-1/2 bg-slate-950 border border-slate-800 rounded-lg px-2 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
              >
                <option value="REFERENCE_OBJECT">Reference Object (Coin/Card)</option>
                <option value="AR_MARKER">AR / Grid Target</option>
                <option value="DEVICE_SENSOR">Hardware Sensor Calibration</option>
              </select>
            </div>
          ) : (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-amber-400">
              No calibrated scale. Measurement will record as unverified image estimation.
            </div>
          )}
        </div>

        {/* Blown/Moulded Package Type */}
        <div className="flex flex-col justify-center">
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={isBlownOrMoulded}
              onChange={(e) => setIsBlownOrMoulded(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-0"
            />
            Blown, formed, moulded, or perforated container (Schedule II Higher Tier)
          </label>
          <div className="text-[11px] text-slate-500 mt-1">
            Applies higher statutory minimum heights per Rule 7 Schedule II Table 1
          </div>
        </div>
      </div>

      {/* Live Estimation Preview */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 mb-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div className="text-xs text-slate-400">Live Statutory Assessment:</div>
          <div className="text-sm font-semibold text-white mt-0.5 flex items-center gap-2">
            <span>
              Estimated Physical Height: {estimatedPhysicalHeight !== null ? `${estimatedPhysicalHeight.toFixed(2)} mm` : 'Uncalibrated (Scale Required)'}
            </span>
            <span className="text-slate-500">|</span>
            <span className="text-indigo-300">
              Prescribed Statutory Min: {currentThreshold.toFixed(1)} mm
            </span>
          </div>
        </div>

        <button
          onClick={handleCalculateAndSave}
          disabled={loading}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition disabled:opacity-50 shrink-0"
        >
          {loading ? 'Evaluating...' : 'Record & Link Evidence'}
        </button>
      </div>

      {/* Evaluated Result Badge */}
      {measurementResult && (
        <div className={`p-3 rounded-lg border text-xs ${
          measurementResult.result === 'PASS'
            ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300'
            : 'bg-amber-950/60 border-amber-500/40 text-amber-300'
        }`}>
          <div className="font-semibold flex items-center gap-1.5">
            <span>Result: {measurementResult.result}</span>
            <span className="text-slate-400 font-normal">({measurementResult.reason})</span>
          </div>
        </div>
      )}
    </div>
  );
};

