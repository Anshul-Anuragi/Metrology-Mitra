'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { PackerRegistration, RegistrationVerifyResponse } from '@/types';
import {
  Building2,
  CheckCircle2,
  FileCheck,
  PlusCircle,
  Search,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from 'lucide-react';

export default function RegistrationsPage() {
  const [registrations, setRegistrations] = useState<PackerRegistration[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [stateFilter, setStateFilter] = useState<string>('');
  
  // Verification lookup states
  const [lookupQuery, setLookupQuery] = useState<string>('');
  const [verifyResult, setVerifyResult] = useState<RegistrationVerifyResponse | null>(null);
  const [verifying, setVerifying] = useState<boolean>(false);

  // New Registration Modal states
  const [showModal, setShowModal] = useState<boolean>(false);
  const [regNumber, setRegNumber] = useState<string>('');
  const [entityName, setEntityName] = useState<string>('');
  const [regAddress, setRegAddress] = useState<string>('');
  const [jurisdiction, setJurisdiction] = useState<string>('CENTRAL_DIRECTOR');
  const [stateName, setStateName] = useState<string>('Delhi');
  const [issuingAuth, setIssuingAuth] = useState<string>('Director of Legal Metrology, GoI');
  const [categories, setCategories] = useState<string>('Food, Grains, Edible Oils');
  const [validFrom, setValidFrom] = useState<string>('2023-01-01');
  const [validTo, setValidTo] = useState<string>('2028-12-31');
  const [saving, setSaving] = useState<boolean>(false);

  const fetchRegistrations = async () => {
    try {
      setLoading(true);
      const data = await api.getPackerRegistrations({
        q: searchTerm || undefined,
        state: stateFilter || undefined,
      });
      setRegistrations(data);
    } catch (err) {
      console.error('Failed to fetch registrations', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRegistrations();
  }, [searchTerm, stateFilter]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lookupQuery.trim()) return;
    setVerifying(true);
    try {
      const res = await api.verifyPackerRegistration({
        registration_number: lookupQuery.includes('-') ? lookupQuery : undefined,
        entity_name: !lookupQuery.includes('-') ? lookupQuery : undefined,
      });
      setVerifyResult(res);
    } catch (err) {
      console.error('Verification failed', err);
    } finally {
      setVerifying(false);
    }
  };

  const handleCreateRegistration = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.createPackerRegistration({
        registration_number: regNumber,
        entity_name: entityName,
        registered_address: regAddress,
        jurisdiction_level: jurisdiction,
        state: stateName,
        issuing_authority: issuingAuth,
        registered_categories: categories.split(',').map((s) => s.trim()),
        valid_from: validFrom,
        valid_to: validTo || undefined,
        is_active: true,
      });
      setShowModal(false);
      fetchRegistrations();
    } catch (err) {
      console.error('Failed to create registration', err);
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
            <h1 className="text-2xl font-bold text-slate-900">Rule 27 Pre-Packer Registry</h1>
            <span className="text-xs bg-indigo-50 text-indigo-700 font-semibold px-2.5 py-0.5 rounded-full border border-indigo-200">
              LMPC Rules, 2011
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Authoritative statutory registry of manufacturers, packers, and importers under Rule 27.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-xl transition shadow-sm self-start sm:self-auto"
        >
          <PlusCircle className="h-4 w-4" />
          Register Pre-Packer
        </button>
      </div>

      {/* Verification Lookup Tool */}
      <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white p-6 rounded-2xl shadow-md space-y-4">
        <div className="flex items-center gap-2">
          <FileCheck className="h-5 w-5 text-sky-400" />
          <h2 className="text-base font-bold">Rule 27 Pre-Packer Registry Verification</h2>
        </div>
        <p className="text-xs text-slate-300">
          Enter a printed Registration Number (e.g., <span className="font-mono text-sky-300">DL-LM-REG-2023-089</span>) or Entity Name to verify statutory compliance.
        </p>

        <form onSubmit={handleVerify} className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={lookupQuery}
            onChange={(e) => setLookupQuery(e.target.value)}
            placeholder="Search Registration No. or Manufacturer Name..."
            className="flex-1 px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm placeholder:text-slate-400 focus:outline-none focus:border-sky-400"
          />
          <button
            type="submit"
            disabled={verifying}
            className="px-6 py-2.5 bg-sky-500 hover:bg-sky-600 text-white font-bold text-sm rounded-xl transition flex items-center justify-center gap-2"
          >
            <Search className="h-4 w-4" />
            {verifying ? 'Verifying...' : 'Verify Registry'}
          </button>
        </form>

        {verifyResult && (
          <div className="mt-4 p-4 bg-slate-800/80 border border-slate-700 rounded-xl space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-200">Verification Result:</span>
              <span
                className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] border ${
                  verifyResult.is_compliant
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                    : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                }`}
              >
                {verifyResult.verification_status}
              </span>
            </div>
            <p className="text-slate-300">{verifyResult.rationale}</p>
            {verifyResult.registered_address && (
              <p className="text-slate-400">
                <strong>Registered Premises:</strong> {verifyResult.registered_address} ({verifyResult.state})
              </p>
            )}
            <p className="text-[10px] text-slate-400 pt-2 border-t border-slate-700">{verifyResult.disclaimer}</p>
          </div>
        )}
      </div>

      {/* Registry Table & Filters */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50">
          <div className="flex items-center gap-2 flex-1 max-w-md">
            <Search className="h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filter registered pre-packers..."
              className="w-full bg-transparent text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">State:</span>
            <input
              type="text"
              value={stateFilter}
              onChange={(e) => setStateFilter(e.target.value)}
              placeholder="All States"
              className="px-2.5 py-1 bg-white border border-slate-300 rounded-lg text-xs"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm">Loading registered pre-packers...</div>
        ) : registrations.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-sm">No pre-packer registrations found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100/70 text-slate-600 font-bold uppercase text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Registration No.</th>
                  <th className="py-3 px-4">Entity Name</th>
                  <th className="py-3 px-4">Registered Premises</th>
                  <th className="py-3 px-4">Jurisdiction</th>
                  <th className="py-3 px-4">State</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {registrations.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50 transition">
                    <td className="py-3 px-4 font-mono font-bold text-indigo-700">{r.registration_number}</td>
                    <td className="py-3 px-4 font-semibold text-slate-900">{r.entity_name}</td>
                    <td className="py-3 px-4 text-slate-600 max-w-xs truncate">{r.registered_address}</td>
                    <td className="py-3 px-4 text-slate-700 font-medium">{r.jurisdiction_level}</td>
                    <td className="py-3 px-4 text-slate-700">{r.state}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-bold text-[10px] ${
                          r.is_active
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        {r.is_active ? 'ACTIVE' : 'INACTIVE'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Register Pre-Packer */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 text-xs">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Building2 className="h-5 w-5 text-indigo-600" />
              New Pre-Packer Registration (Rule 27)
            </h3>

            <form onSubmit={handleCreateRegistration} className="space-y-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Registration Number</label>
                <input
                  type="text"
                  required
                  value={regNumber}
                  onChange={(e) => setRegNumber(e.target.value)}
                  placeholder="e.g. DL-LM-REG-2024-001"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Entity Name</label>
                <input
                  type="text"
                  required
                  value={entityName}
                  onChange={(e) => setEntityName(e.target.value)}
                  placeholder="e.g. Desi Agro Foods Pvt. Ltd."
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Registered Premises Address</label>
                <textarea
                  required
                  rows={2}
                  value={regAddress}
                  onChange={(e) => setRegAddress(e.target.value)}
                  placeholder="Full physical factory/depot address"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Jurisdiction Level</label>
                  <select
                    value={jurisdiction}
                    onChange={(e) => setJurisdiction(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg bg-slate-50"
                  >
                    <option value="CENTRAL_DIRECTOR">Central (Director)</option>
                    <option value="STATE_CONTROLLER">State (Controller)</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">State</label>
                  <input
                    type="text"
                    required
                    value={stateName}
                    onChange={(e) => setStateName(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Valid From</label>
                  <input
                    type="date"
                    required
                    value={validFrom}
                    onChange={(e) => setValidFrom(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Valid To</label>
                  <input
                    type="date"
                    value={validTo}
                    onChange={(e) => setValidTo(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg"
                  />
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
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold transition shadow-sm"
                >
                  {saving ? 'Saving...' : 'Save Registration'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

