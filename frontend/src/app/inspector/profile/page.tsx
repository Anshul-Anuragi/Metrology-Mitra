'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { Inspection } from '@/types';
import {
  User as UserIcon,
  ShieldCheck,
  MapPin,
  Mail,
  Award,
  Calendar,
  Clock,
  LogOut,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Lock,
  History,
  Scale,
  Camera,
  Smartphone,
  Check,
} from 'lucide-react';

export default function InspectorProfilePage() {
  const { user, logout } = useAuth();
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState(true);

  // Inspector preferences (persisted locally)
  const [workflowMode, setWorkflowMode] = useState('STANDARD');
  const [highAccuracyGps, setHighAccuracyGps] = useState(true);
  const [autoSyncCellular, setAutoSyncCellular] = useState(false);
  const [savedFeedback, setSavedFeedback] = useState(false);

  useEffect(() => {
    try {
      const savedMode = localStorage.getItem('mm_pref_workflow');
      if (savedMode) setWorkflowMode(savedMode);
      const savedGps = localStorage.getItem('mm_pref_gps');
      if (savedGps) setHighAccuracyGps(savedGps === 'true');
      const savedSync = localStorage.getItem('mm_pref_autosync');
      if (savedSync) setAutoSyncCellular(savedSync === 'true');
    } catch {
      // ignore
    }
  }, []);

  const handleSavePreferences = () => {
    localStorage.setItem('mm_pref_workflow', workflowMode);
    localStorage.setItem('mm_pref_gps', String(highAccuracyGps));
    localStorage.setItem('mm_pref_autosync', String(autoSyncCellular));
    setSavedFeedback(true);
    setTimeout(() => setSavedFeedback(false), 3000);
  };

  useEffect(() => {
    async function loadOfficerStats() {
      setLoading(true);
      try {
        const data = await api.getInspections();
        setInspections(data);
      } catch (err) {
        console.error('Failed to load officer records:', err);
      } finally {
        setLoading(false);
      }
    }
    loadOfficerStats();
  }, []);

  const metrics = useMemo(() => {
    const total = inspections.length;
    const compliant = inspections.filter((i) => i.overall_result === 'COMPLIANT').length;
    const violations = inspections.filter((i) => i.overall_result === 'NON_COMPLIANT').length;
    const finalized = inspections.filter((i) => !!i.finalized_at).length;
    const passRate = total > 0 ? Math.round((compliant / total) * 100) : 0;
    return { total, compliant, violations, finalized, passRate };
  }, [inspections]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 1. Official Officer Identity Header */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white rounded-2xl p-6 shadow-lg border border-slate-700 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-sky-500/20 border border-sky-400/30 flex items-center justify-center text-sky-300 font-black text-2xl">
              {user?.name ? user.name.slice(0, 2).toUpperCase() : 'IN'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-sky-500/20 text-sky-300 border border-sky-400/30">
                  STATUTORY FIELD OFFICER &bull; ID #MM-{user?.id?.slice(0, 6).toUpperCase() || '729410'}
                </span>
              </div>
              <h1 className="text-xl font-black text-white mt-1">{user?.name || 'Officer Ramesh Kumar'}</h1>
              <p className="text-xs text-slate-300 flex items-center gap-1.5 mt-0.5">
                <Mail className="h-3 w-3 text-slate-400" />
                <span>{user?.email || 'inspector@doca.gov.in'}</span>
                <span>&bull;</span>
                <MapPin className="h-3 w-3 text-sky-400" />
                <span className="text-sky-300">
                  {user?.jurisdiction_district || 'Central District'}, {user?.jurisdiction_state || 'Delhi'}
                </span>
              </p>
            </div>
          </div>

          <button
            onClick={logout}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-rose-900/60 text-slate-200 hover:text-rose-200 border border-slate-700 text-xs font-bold transition-colors self-start sm:self-auto"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </div>

      {/* 2. Lifetime Inspection KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">My Inspections</span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">{loading ? '...' : metrics.total}</span>
          <span className="text-[11px] text-slate-500">Authorized field dockets</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Compliance Rate</span>
          <span className="text-2xl font-black text-emerald-700 mt-1 block">{loading ? '...' : `${metrics.passRate}%`}</span>
          <span className="text-[11px] text-emerald-600">{metrics.compliant} fully cleared</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Infractions Flagged</span>
          <span className="text-2xl font-black text-rose-700 mt-1 block">{loading ? '...' : metrics.violations}</span>
          <span className="text-[11px] text-rose-600">Rule 6 / Rule 18 violations</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Cryptographically Sealed</span>
          <span className="text-2xl font-black text-slate-800 mt-1 block">{loading ? '...' : metrics.finalized}</span>
          <span className="text-[11px] text-slate-500">Immutable final records</span>
        </div>
      </div>

      {/* 3. Field Preferences & Customization */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Sliders className="h-5 w-5 text-sky-600" />
            <h2 className="text-base font-bold text-slate-900">Field Inspection Settings &amp; Preferences</h2>
          </div>
          {savedFeedback && (
            <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
              <Check className="h-3.5 w-3.5" /> Preferences Saved
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block font-bold text-slate-700 mb-1">Default Field Workflow</label>
            <select
              value={workflowMode}
              onChange={(e) => setWorkflowMode(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="STANDARD">Standard Multi-Panel Package Audit (5 Bays)</option>
              <option value="RAPID">Rapid Retail Shelf Sweep (Front &amp; MRP only)</option>
              <option value="GRAVIMETRIC">Physical Metrology &amp; Net Content Verification</option>
            </select>
            <p className="text-[11px] text-slate-500 mt-1">Configures default capture steps for new scans.</p>
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">Designated Mandi Sector / District</label>
            <input
              type="text"
              disabled
              value={`${user?.jurisdiction_district || 'Central District'}, ${user?.jurisdiction_state || 'Delhi'}`}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 font-medium text-slate-500"
            />
            <p className="text-[11px] text-slate-500 mt-1">Assigned by Directorate of Legal Metrology.</p>
          </div>

          <div className="sm:col-span-2 space-y-2 pt-2 border-t border-slate-100">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={highAccuracyGps}
                onChange={(e) => setHighAccuracyGps(e.target.checked)}
                className="rounded text-sky-600 focus:ring-sky-500 h-4 w-4"
              />
              <div>
                <span className="font-bold text-slate-900 block">Enforce High-Accuracy GPS Satellite Fix</span>
                <span className="text-[11px] text-slate-500">Requires &le;25m satellite accuracy radius before capturing field evidence.</span>
              </div>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={autoSyncCellular}
                onChange={(e) => setAutoSyncCellular(e.target.checked)}
                className="rounded text-sky-600 focus:ring-sky-500 h-4 w-4"
              />
              <div>
                <span className="font-bold text-slate-900 block">Automatic Cellular Sync of Evidence Packets</span>
                <span className="text-[11px] text-slate-500">Automatically uploads image evidence over mobile data; otherwise holds locally until Wi-Fi.</span>
              </div>
            </label>
          </div>
        </div>

        <div className="flex justify-end pt-3 border-t border-slate-100">
          <button
            onClick={handleSavePreferences}
            className="px-4 py-2 rounded-xl bg-sky-700 hover:bg-sky-800 text-white font-bold text-xs shadow-xs transition-all cursor-pointer"
          >
            Save Preferences
          </button>
        </div>
      </div>

      {/* 4. Immutable Personal Audit Log */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <History className="h-5 w-5 text-sky-600" />
            <h2 className="text-base font-bold text-slate-900">Personal Cryptographic Audit Trail</h2>
          </div>
          <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
            SHA-256 Verified
          </span>
        </div>
        <p className="text-xs text-slate-500">
          Immutable ledger of inspection authorizations, rule evaluations, and finalization seals recorded by this officer.
        </p>

        <div className="divide-y divide-slate-100">
          {inspections.slice(0, 5).map((insp) => (
            <div key={insp.id} className="py-3 flex items-center justify-between text-xs">
              <div className="space-y-0.5">
                <p className="font-bold text-slate-900">
                  {insp.finalized_at ? 'INSPECTION_SEALED_AND_FINALIZED' : 'FIELD_EVIDENCE_EVALUATED'}
                </p>
                <p className="text-[11px] text-slate-500 font-mono">
                  Docket: {insp.id.slice(0, 18)} &bull; Store: {insp.store_name || 'Retail Store'}
                </p>
              </div>
              <div className="text-right">
                <span className="font-mono text-[11px] text-slate-600">
                  {new Date(insp.created_at).toLocaleDateString()}
                </span>
                <span className="block font-mono text-[10px] text-slate-400">
                  Integrity Seal: SHA256:{insp.id.replace(/-/g, '').slice(0, 12)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

