'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { SeizureRecord } from '@/types';
import {
  AlertOctagon,
  Download,
  FileSpreadsheet,
  FileText,
  PlusCircle,
  ShieldAlert,
  Users,
} from 'lucide-react';

export default function SeizuresPage() {
  const [seizures, setSeizures] = useState<SeizureRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showModal, setShowModal] = useState<boolean>(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  // Form states
  const [premisesName, setPremisesName] = useState<string>('');
  const [premisesAddress, setPremisesAddress] = useState<string>('');
  const [statutoryGrounds, setStatutoryGrounds] = useState<string>(
    'Non-compliance with mandatory declarations under Rule 6 and Section 15(1)(b) of Legal Metrology Act, 2009'
  );
  const [witness1Name, setWitness1Name] = useState<string>('');
  const [witness1Address, setWitness1Address] = useState<string>('');
  const [witness1Phone, setWitness1Phone] = useState<string>('');
  const [witness2Name, setWitness2Name] = useState<string>('');
  const [witness2Address, setWitness2Address] = useState<string>('');
  const [witness2Phone, setWitness2Phone] = useState<string>('');
  
  // Inventory items
  const [commodityName, setCommodityName] = useState<string>('Refined Soybean Oil 1L');
  const [brandName, setBrandName] = useState<string>('Kisan Pure');
  const [batchLot, setBatchLot] = useState<string>('LOT-2024-K09');
  const [netQty, setNetQty] = useState<string>('1 L');
  const [totalSeized, setTotalSeized] = useState<number>(50);
  const [sampleDrawn, setSampleDrawn] = useState<number>(3);
  const [sampleSealTag, setSampleSealTag] = useState<string>('DOCA-SEAL-8890');
  const [saving, setSaving] = useState<boolean>(false);

  const fetchSeizures = async () => {
    try {
      setLoading(true);
      const data = await api.getSeizureRecords();
      setSeizures(data);
    } catch (err) {
      console.error('Failed to fetch seizures', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSeizures();
  }, []);

  const handleDownloadPdf = async (seizure: SeizureRecord) => {
    try {
      setDownloadingId(seizure.id);
      await api.downloadPanchnamaPdf(seizure.id, `Panchnama_${seizure.seizure_memo_number}.pdf`);
    } catch (err) {
      console.error('Failed to download PDF', err);
    } finally {
      setDownloadingId(null);
    }
  };

  const handleCreateSeizure = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.createSeizureRecord({
        premises_name: premisesName,
        premises_address: premisesAddress,
        statutory_grounds: statutoryGrounds,
        witness_1: { name: witness1Name, address: witness1Address, phone: witness1Phone || undefined },
        witness_2: { name: witness2Name, address: witness2Address, phone: witness2Phone || undefined },
        items: [
          {
            commodity_name: commodityName,
            brand_name: brandName,
            batch_lot_number: batchLot,
            declared_net_quantity: netQty,
            total_packages_seized: totalSeized,
            sample_packages_taken: sampleDrawn,
            sample_seal_tag_number: sampleSealTag,
          },
        ],
      });
      setShowModal(false);
      fetchSeizures();
    } catch (err) {
      console.error('Failed to create seizure record', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900">Section 15 Seizures & Panchnama</h1>
            <span className="text-xs bg-rose-50 text-rose-700 font-semibold px-2.5 py-0.5 rounded-full border border-rose-200">
              Sec 15, Legal Metrology Act, 2009
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Statutory records of search, seizure, sample custody, and independent witness Panchnamas.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-rose-700 hover:bg-rose-800 text-white font-medium text-sm rounded-xl transition shadow-sm self-start sm:self-auto"
        >
          <PlusCircle className="h-4 w-4" />
          Execute Seizure & Panchnama
        </button>
      </div>

      {/* Seizure Records Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm">Loading statutory seizure records...</div>
        ) : seizures.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-sm space-y-2">
            <AlertOctagon className="h-8 w-8 text-slate-300 mx-auto" />
            <p>No seizure records executed yet.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {seizures.map((s) => (
              <div key={s.id} className="p-5 hover:bg-slate-50 transition space-y-3 text-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-rose-800 text-sm">{s.seizure_memo_number}</span>
                    <span className="px-2.5 py-0.5 bg-rose-50 text-rose-700 font-bold text-[10px] rounded-full border border-rose-200">
                      {s.status}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDownloadPdf(s)}
                    disabled={downloadingId === s.id}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold rounded-lg transition"
                  >
                    <Download className="h-3.5 w-3.5 text-rose-700" />
                    {downloadingId === s.id ? 'Generating PDF...' : 'Form VI Panchnama PDF'}
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <div>
                    <span className="text-[10px] text-slate-400 font-semibold block">PREMISES:</span>
                    <span className="font-semibold text-slate-900">{s.premises_name}</span>
                    <p className="text-[11px] text-slate-500 truncate">{s.premises_address}</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-semibold block">INDEPENDENT WITNESSES:</span>
                    <p className="text-[11px] text-slate-800">1. {s.witness_1_name}</p>
                    <p className="text-[11px] text-slate-800">2. {s.witness_2_name}</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-semibold block">SHA-256 EVIDENCE SEAL:</span>
                    <span className="font-mono text-[10px] text-slate-600 truncate block">
                      {s.sha256_seal_hash ? `${s.sha256_seal_hash.slice(0, 24)}...` : 'N/A'}
                    </span>
                  </div>
                </div>

                {s.items && s.items.length > 0 && (
                  <div className="pt-2">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                      Seized Commodities & Test Samples
                    </span>
                    <div className="space-y-1">
                      {s.items.map((item) => (
                        <div
                          key={item.id}
                          className="flex items-center justify-between p-2 bg-white rounded-lg border border-slate-200 text-[11px]"
                        >
                          <span className="font-semibold text-slate-900">
                            {item.commodity_name} {item.brand_name ? `(${item.brand_name})` : ''}
                          </span>
                          <div className="flex items-center gap-4 text-slate-600">
                            <span>Seized: <b>{item.total_packages_seized} pkgs</b></span>
                            <span>Samples: <b>{item.sample_packages_taken} pkgs</b></span>
                            {item.sample_seal_tag_number && (
                              <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded border">
                                Seal: {item.sample_seal_tag_number}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal: New Seizure & Panchnama */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 space-y-4 text-xs max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-rose-700" />
              Execute Statutory Seizure & Panchnama (Section 15)
            </h3>

            <form onSubmit={handleCreateSeizure} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Premises / Shop Name</label>
                  <input
                    type="text"
                    required
                    value={premisesName}
                    onChange={(e) => setPremisesName(e.target.value)}
                    placeholder="e.g. Metro Supermarket Hub"
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Premises Address</label>
                  <input
                    type="text"
                    required
                    value={premisesAddress}
                    onChange={(e) => setPremisesAddress(e.target.value)}
                    placeholder="Physical location address"
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Statutory Grounds</label>
                <input
                  type="text"
                  required
                  value={statutoryGrounds}
                  onChange={(e) => setStatutoryGrounds(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                />
              </div>

              {/* Witnesses */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                <span className="font-bold text-slate-900 flex items-center gap-1.5 text-xs">
                  <Users className="h-4 w-4 text-indigo-600" />
                  Independent Witnesses (Panchas — 2 Required by Law)
                </span>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <input
                      type="text"
                      required
                      placeholder="Witness 1 Name"
                      value={witness1Name}
                      onChange={(e) => setWitness1Name(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                    />
                    <input
                      type="text"
                      required
                      placeholder="Witness 1 Address"
                      value={witness1Address}
                      onChange={(e) => setWitness1Address(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                    />
                  </div>
                  <div className="space-y-2">
                    <input
                      type="text"
                      required
                      placeholder="Witness 2 Name"
                      value={witness2Name}
                      onChange={(e) => setWitness2Name(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                    />
                    <input
                      type="text"
                      required
                      placeholder="Witness 2 Address"
                      value={witness2Address}
                      onChange={(e) => setWitness2Address(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                    />
                  </div>
                </div>
              </div>

              {/* Seized Item */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                <span className="font-bold text-slate-900 text-xs">Seized Commodity Details</span>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    required
                    placeholder="Commodity Name"
                    value={commodityName}
                    onChange={(e) => setCommodityName(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                  />
                  <input
                    type="text"
                    placeholder="Brand Name"
                    value={brandName}
                    onChange={(e) => setBrandName(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                  />
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[10px] text-slate-500 mb-0.5">Total Seized Pkgs</label>
                    <input
                      type="number"
                      required
                      min={1}
                      value={totalSeized}
                      onChange={(e) => setTotalSeized(parseInt(e.target.value) || 1)}
                      className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-500 mb-0.5">Samples Drawn</label>
                    <input
                      type="number"
                      min={0}
                      value={sampleDrawn}
                      onChange={(e) => setSampleDrawn(parseInt(e.target.value) || 0)}
                      className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-500 mb-0.5">Seal Tag No.</label>
                    <input
                      type="text"
                      value={sampleSealTag}
                      onChange={(e) => setSampleSealTag(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-300 rounded-lg font-mono"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-xl hover:bg-slate-100 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-5 py-2 bg-rose-700 hover:bg-rose-800 text-white rounded-xl font-bold transition shadow-sm"
                >
                  {saving ? 'Recording...' : 'Record Seizure & Panchnama'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

