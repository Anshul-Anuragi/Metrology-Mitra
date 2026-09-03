'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { InspectionBatch } from '@/types';
import {
  Boxes,
  PlusCircle,
  Search,
  ArrowRight,
  Building2,
  MapPin,
  RefreshCw,
  AlertTriangle,
  FileCheck2,
} from 'lucide-react';

export default function BatchesPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [batches, setBatches] = useState<InspectionBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New batch modal state
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [lotSize, setLotSize] = useState(500);
  const [sampleSize, setSampleSize] = useState(10);
  const [storeName, setStoreName] = useState('');
  const [district, setDistrict] = useState('New Delhi');
  const [state, setState] = useState('Delhi');
  const [submitting, setSubmitting] = useState(false);

  const fetchBatches = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listBatches();
      setBatches(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load batch inspection lots.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push('/login');
      } else {
        fetchBatches();
      }
    }
  }, [authLoading, user]);

  const handleCreateBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const created = await api.createBatch({
        name,
        lot_size: lotSize,
        sample_size: sampleSize,
        store_name: storeName,
        district,
        state,
      });
      setShowModal(false);
      setName('');
      await fetchBatches();
      router.push(`/batches/${created.id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to create batch lot.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <Boxes className="h-6 w-6 text-brand-900" />
            Batch & Lot Inspections (Schedule IV)
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Statistical sampling compliance inspections for wholesale depots, warehouses, and distribution centers.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchBatches}
            className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors text-xs font-semibold flex items-center gap-1.5"
            title="Refresh List"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="bg-brand-900 hover:bg-brand-800 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow transition-colors flex items-center gap-1.5"
          >
            <PlusCircle className="h-4 w-4" />
            New Lot Inspection
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Batches Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-xs text-slate-500 flex flex-col items-center justify-center">
            <RefreshCw className="h-8 w-8 text-sky-600 animate-spin mb-3" />
            <span>Loading batch inspection lots...</span>
          </div>
        ) : batches.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-500 flex flex-col items-center justify-center">
            <Boxes className="h-10 w-10 text-slate-300 mb-3" />
            <p className="font-semibold text-slate-700 text-sm">No batch lots found</p>
            <p className="text-slate-400 mt-1 max-w-sm">
              Click &quot;New Lot Inspection&quot; to initiate a Schedule IV multi-sample statistical inspection.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-4 py-3.5">Lot / Batch Name</th>
                  <th className="px-4 py-3.5">Establishment</th>
                  <th className="px-4 py-3.5">Lot Size</th>
                  <th className="px-4 py-3.5">Sample Target</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Date Created</th>
                  <th className="px-4 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {batches.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-3.5">
                      <div className="font-bold text-slate-900">{b.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">ID: {b.id.slice(0, 16)}...</div>
                    </td>
                    <td className="px-4 py-3.5 text-slate-600">
                      <div className="flex items-center gap-1 font-medium">
                        <Building2 className="h-3.5 w-3.5 text-slate-400" />
                        {b.store_name || 'Unspecified'}
                      </div>
                      <div className="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5">
                        <MapPin className="h-3 w-3" />
                        {b.district || 'N/A'}, {b.state || 'N/A'}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 font-bold text-slate-700">{b.lot_size} units</td>
                    <td className="px-4 py-3.5 font-bold text-indigo-700">{b.sample_size} samples</td>
                    <td className="px-4 py-3.5">
                      <span className="text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 px-2.5 py-0.5 rounded-full">
                        {b.status}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-slate-500 whitespace-nowrap">
                      {new Date(b.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3.5 text-right whitespace-nowrap">
                      <a
                        href={`/batches/${b.id}`}
                        className="inline-flex items-center gap-1 bg-brand-50 hover:bg-brand-100 text-brand-900 font-bold px-3 py-1.5 rounded-lg border border-brand-200 transition-colors"
                      >
                        Manage Lot <ArrowRight className="h-3.5 w-3.5" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* New Batch Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full p-6 border border-slate-200 animate-in fade-in zoom-in duration-150">
            <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
              <Boxes className="h-5 w-5 text-brand-900" />
              Create Schedule IV Lot Inspection
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Initialize a statistical multi-package lot verification session.
            </p>

            <form onSubmit={handleCreateBatch} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Lot / Batch Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Warehouse Lot B-204 (Edible Oil 1L)"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Total Lot Size (units) *</label>
                  <input
                    type="number"
                    min={1}
                    required
                    value={lotSize}
                    onChange={(e) => setLotSize(parseInt(e.target.value) || 1)}
                    className="w-full text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Target Sample Size *</label>
                  <input
                    type="number"
                    min={1}
                    required
                    value={sampleSize}
                    onChange={(e) => setSampleSize(parseInt(e.target.value) || 1)}
                    className="w-full text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Establishment / Depot Name</label>
                <input
                  type="text"
                  placeholder="e.g. Reliance Retail Mega Depot"
                  value={storeName}
                  onChange={(e) => setStoreName(e.target.value)}
                  className="w-full text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">District</label>
                  <input
                    type="text"
                    value={district}
                    onChange={(e) => setDistrict(e.target.value)}
                    className="w-full text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">State</label>
                  <input
                    type="text"
                    value={state}
                    onChange={(e) => setState(e.target.value)}
                    className="w-full text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-brand-900 hover:bg-brand-800 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 disabled:opacity-50"
                >
                  <FileCheck2 className="h-4 w-4" />
                  {submitting ? 'Creating...' : 'Initialize Lot'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

