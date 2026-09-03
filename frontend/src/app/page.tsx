'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { ShieldCheck, ArrowRight } from 'lucide-react';

export default function HomePage() {
  const { user, loading, isInspector, isSupervisor } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push('/login');
      } else if (isInspector) {
        router.push('/inspections');
      } else if (isSupervisor) {
        router.push('/analytics');
      }
    }
  }, [user, loading, isInspector, isSupervisor, router]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <ShieldCheck className="h-16 w-16 text-sky-600 mb-4 animate-pulse" />
      <h1 className="text-3xl font-black text-slate-900 mb-2">
        Legal Metrology Compliance System
      </h1>
      <p className="text-slate-600 max-w-md mb-6 text-sm">
        Automated multi-angle compliance inspection of packaged commodities under Legal Metrology (Packaged Commodities) Rules, 2011.
      </p>
      <a
        href="/login"
        className="bg-brand-900 hover:bg-brand-800 text-white font-semibold px-6 py-3 rounded-xl shadow flex items-center gap-2 text-sm transition-all"
      >
        Sign in to Portal <ArrowRight className="h-4 w-4" />
      </a>
    </div>
  );
}

