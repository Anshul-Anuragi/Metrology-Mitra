'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import {
  GravimetricTestCreate,
  GravimetricTestResponse,
  SampleUnitWeightInput,
} from '@/types';
import {
  Scale,
  Plus,
  Trash2,
  FileCheck2,
  Download,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RefreshCw,
  Layers,
} from 'lucide-react';

export default function GravimetricPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  // Test form state
  const [nominalQty, setNominalQty] = useState<number>(500);
  const [unit, setUnit] = useState<string>('g');
  const [tareWeight, setTareWeight] = useState<number>(12.5);
  const [samples, setSamples] = useState<SampleUnitWeightInput[]>([
    { unit_number: 1, gross_weight: 512.5, tare_weight: 12.5 },
    { unit_number: 2, gross_weight: 511.8, tare_weight: 12.5 },
    { unit_number: 3, gross_weight: 513.2, tare_weight: 12.5 },
    { unit_number: 4, gross_weight: 509.4, tare_weight: 12.5 },
    { unit_number: 5, gross_weight: 514.0, tare_weight: 12.5 },
  ]);

  const [testResult, setTestResult] = useState<GravimetricTestResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [authLoading, user]);

  const handleAddSample = () => {
    const nextNum = samples.length + 1;
    setSamples([
      ...samples,
      { unit_number: nextNum, gross_weight: nominalQty + tareWeight, tare_weight: tareWeight },
    ]);
  };

  const handleRemoveSample = (index: number) => {
    if (samples.length <= 1) return;
    const updated = samples.filter((_, i) => i !== index).map((s, i) => ({
      ...s,
      unit_number: i + 1,
    }));
    setSamples(updated);
  };

  const handleSampleChange = (index: number, field: keyof SampleUnitWeightInput, val: number) => {
    const updated = [...samples];
    updated[index] = { ...updated[index], [field]: val };
    setSamples(updated);
  };

  const handleSubmitTest = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload: GravimetricTestCreate = {
        nominal_quantity_value: nominalQty,
        nominal_quantity_unit: unit,
        declared_tare_weight: tareWeight,
        samples: samples,
      };
      const res = await api.createGravimetricTest(payload);
      setTestResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to evaluate gravimetric test.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!testResult) return;
    try {
      const filename = `Gravimetric_Test_${testResult.id.slice(0, 8)}.pdf`;
      await api.downloadGravimetricPdf(testResult.id, filename);
    } catch (err: any) {
      setError('Failed to download test report PDF.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <Scale className="h-6 w-6 text-brand-900" />
            Physical Gravimetric Net-Weight & MPE Testing
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Rule 24 & Schedule IV Table 2 Maximum Permissible Errors (MPE) verification on calibrated physical weighing equipment.
          </p>
        </div>

        {testResult && (
          <button
            onClick={handleDownloadPdf}
            className="px-4 py-2.5 bg-indigo-700 hover:bg-indigo-800 text-white rounded-xl shadow font-bold text-xs flex items-center gap-2 self-start sm:self-auto transition"
          >
            <Download className="h-4 w-4" />
            Download Gravimetric Test Memo PDF
          </button>
        )}
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Form / Sample Input Table + Live Evaluation Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Sample Entry Form */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-6">
          <form onSubmit={handleSubmitTest} className="space-y-6">
            {/* Parameters */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Declared Nominal Qty ($Q_n$) *
                </label>
                <input
                  type="number"
                  step="any"
                  value={nominalQty}
                  onChange={(e) => setNominalQty(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-bold focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Unit of Measure *</label>
                <select
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-medium focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
                >
                  <option value="g">Grams (g)</option>
                  <option value="kg">Kilograms (kg)</option>
                  <option value="ml">Millilitres (ml)</option>
                  <option value="l">Litres (L)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Container Tare Weight *
                </label>
                <input
                  type="number"
                  step="any"
                  value={tareWeight}
                  onChange={(e) => setTareWeight(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-medium focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
                  required
                />
              </div>
            </div>

            {/* Sample Table */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <Layers className="h-4 w-4 text-indigo-700" />
                  Sample Packages Scale Weighing Log ({samples.length} units)
                </h3>
                <button
                  type="button"
                  onClick={handleAddSample}
                  className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold flex items-center gap-1 transition"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Add Sample Unit
                </button>
              </div>

              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
                  <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                    <tr>
                      <th className="px-4 py-2.5">Sample #</th>
                      <th className="px-4 py-2.5">Gross Weight ({unit})</th>
                      <th className="px-4 py-2.5">Tare Weight ({unit})</th>
                      <th className="px-4 py-2.5">Net Weight ({unit})</th>
                      <th className="px-4 py-2.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {samples.map((s, idx) => {
                      const net = Math.max(0, (s.gross_weight || 0) - (s.tare_weight ?? tareWeight));
                      return (
                        <tr key={idx} className="hover:bg-slate-50/50">
                          <td className="px-4 py-2 font-bold text-slate-900">Unit #{s.unit_number}</td>
                          <td className="px-4 py-2">
                            <input
                              type="number"
                              step="any"
                              value={s.gross_weight}
                              onChange={(e) =>
                                handleSampleChange(idx, 'gross_weight', parseFloat(e.target.value) || 0)
                              }
                              className="w-28 px-2 py-1 bg-slate-50 border border-slate-300 rounded font-semibold text-xs focus:bg-white focus:outline-none"
                            />
                          </td>
                          <td className="px-4 py-2">
                            <input
                              type="number"
                              step="any"
                              value={s.tare_weight ?? tareWeight}
                              onChange={(e) =>
                                handleSampleChange(idx, 'tare_weight', parseFloat(e.target.value) || 0)
                              }
                              className="w-28 px-2 py-1 bg-slate-50 border border-slate-300 rounded text-xs focus:bg-white focus:outline-none"
                            />
                          </td>
                          <td className="px-4 py-2 font-black text-indigo-900">
                            {net.toFixed(2)} {unit}
                          </td>
                          <td className="px-4 py-2 text-right">
                            <button
                              type="button"
                              onClick={() => handleRemoveSample(idx)}
                              disabled={samples.length <= 1}
                              className="p-1 hover:bg-rose-50 text-slate-400 hover:text-rose-600 rounded transition disabled:opacity-30"
                              title="Delete row"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 bg-brand-900 hover:bg-brand-800 text-white font-black rounded-xl shadow transition flex items-center justify-center gap-2 text-xs uppercase tracking-wider"
            >
              <FileCheck2 className="h-4 w-4" />
              {submitting ? 'Evaluating Schedule IV MPE...' : 'Evaluate Schedule IV MPE Compliance'}
            </button>
          </form>
        </div>

        {/* Right Col: Schedule IV Verdict & Statistical Summary */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <Scale className="h-4 w-4 text-indigo-700" />
              Schedule IV Lot Evaluation Summary
            </h2>

            {testResult ? (
              <div className="space-y-4 text-xs">
                {/* Verdict Badge */}
                <div
                  className={`p-4 rounded-xl border flex items-center gap-3 ${
                    testResult.lot_decision === 'PASSED_MPE'
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
                      : 'bg-rose-50 border-rose-200 text-rose-950'
                  }`}
                >
                  {testResult.lot_decision === 'PASSED_MPE' ? (
                    <CheckCircle2 className="h-6 w-6 text-emerald-600 shrink-0" />
                  ) : (
                    <XCircle className="h-6 w-6 text-rose-600 shrink-0" />
                  )}
                  <div>
                    <span className="text-[10px] font-bold uppercase block text-slate-500">
                      Lot Acceptance Verdict
                    </span>
                    <span className="font-black text-sm">{testResult.lot_decision}</span>
                  </div>
                </div>

                {/* Key Stats */}
                <div className="grid grid-cols-2 gap-2 text-center">
                  <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg">
                    <span className="text-[10px] text-slate-500 font-bold uppercase block">Mean Net Content</span>
                    <span className="font-black text-slate-900 text-sm">
                      {testResult.sample_mean_net_quantity} {testResult.nominal_quantity_unit}
                    </span>
                  </div>
                  <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg">
                    <span className="text-[10px] text-slate-500 font-bold uppercase block">Statutory MPE</span>
                    <span className="font-black text-indigo-700 text-sm">
                      ±{testResult.mpe_value} {testResult.nominal_quantity_unit}
                    </span>
                  </div>
                  <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg">
                    <span className="text-[10px] text-slate-500 font-bold uppercase block">Std Dev ($s$)</span>
                    <span className="font-black text-slate-900 text-sm">{testResult.sample_std_dev}</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg">
                    <span className="text-[10px] text-slate-500 font-bold uppercase block">Defective Units</span>
                    <span
                      className={`font-black text-sm ${
                        testResult.defective_units_count > 0 ? 'text-rose-700' : 'text-emerald-700'
                      }`}
                    >
                      {testResult.defective_units_count} unit(s)
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                  <span className="text-[10px] text-slate-500 font-bold uppercase block">Applicable Standard</span>
                  <p className="text-[11px] font-semibold text-slate-800">{testResult.statutory_standard}</p>
                  <p className="text-[10px] text-slate-500">{testResult.mpe_description}</p>
                </div>

                {/* Disclaimer */}
                <div className="p-3 bg-amber-50/80 border border-amber-200 rounded-xl text-[10px] text-amber-900 flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                  <span>
                    <strong>Metrology Notice:</strong> Recorded gross and tare weights must be obtained from verified/calibrated physical metrology weighing equipment.
                  </span>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-xs text-slate-400">
                <Scale className="h-8 w-8 text-slate-300 mx-auto mb-2" />
                <p>Enter sample gross weights and click Evaluate to compute Schedule IV MPE statistics.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

