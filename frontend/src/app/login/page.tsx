'use client';

import React, { useState } from 'react';
import { useAuth } from '@/lib/auth';
import {
  ShieldCheck,
  Lock,
  Mail,
  AlertCircle,
  ArrowRight,
  Eye,
  EyeOff,
  UserCheck,
  LogOut,
  Scale,
  Shield,
  Sparkles,
} from 'lucide-react';

export default function LoginPage() {
  const { user, login, logout, isInspector, isSupervisor } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg).join(', '));
      } else {
        setError('Invalid officer credentials or authentication gateway unreachable.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFastLogin = async (roleEmail: string) => {
    setEmail(roleEmail);
    setPassword('Password@123');
    setError(null);
    setLoading(true);
    try {
      await login(roleEmail, 'Password@123');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Quick login failed. Please retry.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-sky-50/30 to-slate-100 text-slate-900 flex flex-col justify-between font-sans selection:bg-sky-500 selection:text-white relative">
      {/* Centered Authentication Workstation */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-8 sm:py-12 z-10 w-full max-w-5xl mx-auto">
        {/* Active Session Notification (if officer is already authenticated) */}
        {user && (
          <div className="w-full max-w-xl mb-6 p-4 bg-emerald-50/90 border border-emerald-300/80 rounded-2xl shadow-sm backdrop-blur-md flex flex-col sm:flex-row items-center justify-between gap-3 animate-in fade-in slide-in-from-top-4 duration-300">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-100 border border-emerald-300 text-emerald-800 rounded-xl shrink-0">
                <UserCheck className="h-5 w-5" />
              </div>
              <div>
                <div className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-800">
                  Active Session Authenticated
                </div>
                <div className="text-xs font-bold text-slate-900">
                  Signed in as <span className="text-emerald-700">{user.name}</span> ({user.role})
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
              <a
                href={isInspector ? '/inspector' : '/analytics'}
                className="px-3.5 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold rounded-lg transition flex items-center gap-1 shadow-sm"
              >
                <span>Workstation</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </a>
              <button
                type="button"
                onClick={logout}
                className="px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-700 text-xs font-medium rounded-lg transition flex items-center gap-1 border border-slate-300 shadow-xs cursor-pointer"
              >
                <LogOut className="h-3 w-3" />
                <span>Switch</span>
              </button>
            </div>
          </div>
        )}

        {/* Central Executive Login Card */}
        <div className="w-full max-w-xl bg-white/90 backdrop-blur-xl border border-slate-200/90 rounded-3xl shadow-xl shadow-slate-200/50 overflow-hidden">
          {/* Card Official Dignified Header */}
          <div className="p-6 sm:p-8 pb-6 border-b border-slate-100 bg-slate-50/80">
            {/* National Insignia & Ministry Subtitle */}
            <div className="flex items-center justify-between gap-4 mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-sky-50 border border-sky-200/80 flex items-center justify-center p-1 shrink-0 text-sky-700 shadow-xs">
                  <ShieldCheck className="h-6 w-6 text-sky-700" />
                </div>
                <div>
                  <div className="text-[10px] font-bold text-slate-700 tracking-wider uppercase">
                    भारत सरकार • Government of India
                  </div>
                  <div className="text-[11px] font-semibold text-slate-500">
                    Department of Consumer Affairs • Legal Metrology Division
                  </div>
                </div>
              </div>

              {/* SIH Hackathon Problem Statement Tag */}
              <div className="hidden sm:flex flex-col items-end">
                <span className="text-[9px] uppercase font-bold tracking-wider text-sky-700">
                  SIH 2026
                </span>
                <span className="text-[10px] font-mono font-bold bg-sky-50 text-sky-800 px-2 py-0.5 rounded border border-sky-200">
                  SIH26034
                </span>
              </div>
            </div>

            {/* Platform Title */}
            <div>
              <div className="flex items-baseline gap-2">
                <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900">
                  MetrologyMitra
                </h1>
                <span className="text-xs font-bold text-sky-700 bg-sky-100 px-2 py-0.5 rounded font-mono border border-sky-200">
                  LMPC 2011
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Automated Legal Metrology Compliance Inspection &amp; Statutory Enforcement Portal
              </p>
            </div>
          </div>

          {/* Form & Auth Body */}
          <div className="p-6 sm:p-8 pt-6 space-y-6">
            {/* Error Notification */}
            {error && (
              <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2.5">
                <AlertCircle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{error}</span>
              </div>
            )}

            {/* Login Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Official Officer Email
                </label>
                <div className="relative">
                  <Mail className="h-4 w-4 text-slate-400 absolute left-3.5 top-3.5" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="officer.name@doca.gov.in"
                    className="w-full text-xs sm:text-sm pl-10 pr-3.5 py-3 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-sky-600 focus:ring-2 focus:ring-sky-600/20 focus:outline-none transition-all"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                    Official Password
                  </label>
                  <span className="text-[10px] text-slate-400 font-mono">NIC-Secured</span>
                </div>
                <div className="relative">
                  <Lock className="h-4 w-4 text-slate-400 absolute left-3.5 top-3.5" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full text-xs sm:text-sm pl-10 pr-10 py-3 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-sky-600 focus:ring-2 focus:ring-sky-600/20 focus:outline-none transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-3.5 text-slate-400 hover:text-slate-700 transition cursor-pointer"
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 bg-sky-700 hover:bg-sky-800 text-white font-bold text-xs sm:text-sm rounded-xl shadow-md transition duration-150 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group cursor-pointer"
              >
                {loading ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Authenticating Credentials...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In to Official Workstation</span>
                    <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
                  </>
                )}
              </button>
            </form>

            {/* SIH Judge & Evaluator Fast Access Section */}
            <div className="pt-3 border-t border-slate-100">
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-800">
                  <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                  <span>SIH Judge / Evaluator 1-Click Access</span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">Password: Password@123</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {/* Inspector Role */}
                <button
                  type="button"
                  onClick={() => handleFastLogin('p11.insp@doca.gov.in')}
                  disabled={loading}
                  className="p-2.5 bg-sky-50/70 hover:bg-sky-100/90 border border-sky-200/80 hover:border-sky-300 rounded-xl text-left transition group cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-extrabold uppercase tracking-wide text-sky-800 group-hover:text-sky-900">
                      Field Inspector
                    </span>
                    <ArrowRight className="h-3 w-3 text-sky-600 group-hover:translate-x-0.5 transition-all" />
                  </div>
                  <div className="text-[11px] font-bold text-slate-900 truncate">
                    p11.insp@doca.gov.in
                  </div>
                  <div className="text-[9px] text-slate-500 truncate mt-0.5">
                    Field OCR &amp; Seizures
                  </div>
                </button>

                {/* Supervisor Role */}
                <button
                  type="button"
                  onClick={() => handleFastLogin('p11.sup@doca.gov.in')}
                  disabled={loading}
                  className="p-2.5 bg-indigo-50/70 hover:bg-indigo-100/90 border border-indigo-200/80 hover:border-indigo-300 rounded-xl text-left transition group cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-extrabold uppercase tracking-wide text-indigo-800 group-hover:text-indigo-900">
                      Supervisor
                    </span>
                    <ArrowRight className="h-3 w-3 text-indigo-600 group-hover:translate-x-0.5 transition-all" />
                  </div>
                  <div className="text-[11px] font-bold text-slate-900 truncate">
                    p11.sup@doca.gov.in
                  </div>
                  <div className="text-[9px] text-slate-500 truncate mt-0.5">
                    Triage &amp; Enforcement
                  </div>
                </button>

                {/* Admin Role */}
                <button
                  type="button"
                  onClick={() => handleFastLogin('p11.admin@doca.gov.in')}
                  disabled={loading}
                  className="p-2.5 bg-emerald-50/70 hover:bg-emerald-100/90 border border-emerald-200/80 hover:border-emerald-300 rounded-xl text-left transition group cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-extrabold uppercase tracking-wide text-emerald-800 group-hover:text-emerald-900">
                      Administrator
                    </span>
                    <ArrowRight className="h-3 w-3 text-emerald-600 group-hover:translate-x-0.5 transition-all" />
                  </div>
                  <div className="text-[11px] font-bold text-slate-900 truncate">
                    p11.admin@doca.gov.in
                  </div>
                  <div className="text-[9px] text-slate-500 truncate mt-0.5">
                    Central Registry &amp; Audit
                  </div>
                </button>
              </div>
            </div>

            {/* Statutory Compliance Badges */}
            <div className="pt-2 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-500 border-t border-slate-100">
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="font-mono text-slate-700 font-semibold">21/21 Statutory Rules Active</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Scale className="h-3 w-3 text-sky-600" />
                <span>Deterministic Decision Logic</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Shield className="h-3 w-3 text-indigo-600" />
                <span>SHA-256 Audit Integrity</span>
              </div>
            </div>
          </div>
        </div>

        {/* Statutory Legal Warning Notice below card */}
        <div className="max-w-xl text-center mt-5 px-4">
          <p className="text-[11px] text-slate-500 leading-relaxed">
            <strong className="text-slate-700">Statutory Notice:</strong> This workstation is authorized exclusively for designated Legal Metrology Officers under the{' '}
            <span className="text-slate-700 font-medium">Legal Metrology Act, 2009</span> and{' '}
            <span className="text-slate-700 font-medium">Legal Metrology (Packaged Commodities) Rules, 2011</span>. All access sessions are logged with cryptographic timestamps under Sections 43 and 66 of the Information Technology Act, 2000.
          </p>
        </div>
      </main>

      {/* Clean Minimalist Bottom Footer */}
      <footer className="w-full py-3 px-4 border-t border-slate-200 text-center text-[11px] text-slate-500 bg-white z-10">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            Department of Consumer Affairs • Ministry of Consumer Affairs, Food &amp; Public Distribution • Govt. of India
          </div>
          <div className="font-mono text-[10px] text-slate-400">
            Smart India Hackathon 2026 • Problem Statement SIH26034
          </div>
        </div>
      </footer>
    </div>
  );
}
