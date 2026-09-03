'use client';

import React, { useState } from 'react';
import { useAuth } from '@/lib/auth';
import { ShieldCheck, Lock, Mail, AlertCircle, ArrowRight } from 'lucide-react';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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
        setError('Invalid credentials or backend service unreachable.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFillTestCreds = (roleEmail: string) => {
    setEmail(roleEmail);
    setPassword('Password@123');
  };

  return (
    <div className="flex items-center justify-center min-h-[75vh] px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex p-3 bg-brand-50 rounded-2xl mb-3 border border-brand-100">
            <ShieldCheck className="h-10 w-10 text-brand-900" />
          </div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">MetrologyMitra</h2>
          <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider font-semibold">
            Legal Metrology Packaged Commodities Compliance
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Department of Consumer Affairs • Government of India
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-5 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-start gap-2.5">
            <AlertCircle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Official Email Address
            </label>
            <div className="relative">
              <Mail className="h-4 w-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="officer.name@doca.gov.in"
                className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl focus:bg-white focus:ring-2 focus:ring-sky-500 focus:border-sky-500 focus:outline-none transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="h-4 w-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl focus:bg-white focus:ring-2 focus:ring-sky-500 focus:border-sky-500 focus:outline-none transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-900 hover:bg-brand-800 text-white font-bold text-xs py-3 px-4 rounded-xl shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
          >
            {loading ? 'Authenticating...' : 'Sign In to Portal'}
            <ArrowRight className="h-4 w-4" />
          </button>
        </form>

        {/* Quick Demo Credentials */}
        <div className="mt-8 pt-6 border-t border-slate-100 text-center">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
            Quick Fill Demo Profiles (Password@123)
          </p>
          <div className="flex flex-wrap gap-1.5 justify-center">
            <button
              type="button"
              onClick={() => handleFillTestCreds('p11.insp@doca.gov.in')}
              className="text-[11px] bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1 rounded-lg transition-colors font-medium border border-slate-200"
            >
              Inspector
            </button>
            <button
              type="button"
              onClick={() => handleFillTestCreds('p11.sup@doca.gov.in')}
              className="text-[11px] bg-sky-50 hover:bg-sky-100 text-sky-800 px-2.5 py-1 rounded-lg transition-colors font-medium border border-sky-200"
            >
              Supervisor
            </button>
            <button
              type="button"
              onClick={() => handleFillTestCreds('p11.admin@doca.gov.in')}
              className="text-[11px] bg-indigo-50 hover:bg-indigo-100 text-indigo-800 px-2.5 py-1 rounded-lg transition-colors font-medium border border-indigo-200"
            >
              Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

