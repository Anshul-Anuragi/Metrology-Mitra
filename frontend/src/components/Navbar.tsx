'use client';

import React from 'react';
import Link from 'next/navigation';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import {
  ShieldCheck,
  ClipboardList,
  PlusCircle,
  BarChart3,
  LogOut,
  User as UserIcon,
  Boxes,
  Gavel,
  Scale,
  Building2,
  AlertOctagon,
  Briefcase,
} from 'lucide-react';
import OfflineSyncBadge from '@/components/OfflineSyncBadge';

export default function Navbar() {
  const { user, logout, isInspector, isSupervisor } = useAuth();
  const pathname = usePathname();

  if (pathname === '/login') {
    return null;
  }

  return (
    <header className="bg-brand-900 text-white shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Brand / Logo */}
          <div className="flex items-center space-x-3">
            <ShieldCheck className="h-8 w-8 text-sky-400" />
            <div>
              <a href={isInspector ? '/inspector' : '/analytics'} className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                MetrologyMitra
                <span className="text-xs bg-sky-500/20 text-sky-300 font-medium px-2 py-0.5 rounded border border-sky-400/30">
                  LMPC 2011
                </span>
              </a>
              <p className="text-[10px] text-slate-300 tracking-wider">
                DEPT OF CONSUMER AFFAIRS • GOVT OF INDIA
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          {user && (
            <nav className="hidden md:flex items-center space-x-2">
              {isInspector && (
                <a
                  href="/inspector"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                    pathname === '/inspector'
                      ? 'bg-brand-800 text-white'
                      : 'text-slate-200 hover:bg-brand-800/60 hover:text-white'
                  }`}
                >
                  Desk
                </a>
              )}

              <a
                href="/inspector/inspections"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  pathname === '/inspector/inspections' || pathname === '/inspections'
                    ? 'bg-brand-800 text-white'
                    : 'text-slate-200 hover:bg-brand-800/60 hover:text-white'
                }`}
              >
                <ClipboardList className="h-4 w-4" />
                Inspections
              </a>

              <a
                href="/batches"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  pathname.startsWith('/batches')
                    ? 'bg-brand-800 text-white'
                    : 'text-slate-200 hover:bg-brand-800/60 hover:text-white'
                }`}
              >
                <Boxes className="h-4 w-4" />
                Lots
              </a>

              <a
                href="/gravimetric"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  pathname === '/gravimetric'
                    ? 'bg-brand-800 text-white'
                    : 'text-slate-200 hover:bg-brand-800/60 hover:text-white'
                }`}
              >
                <Scale className="h-4 w-4" />
                Net-Weight
              </a>

              <a
                href="/registrations"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  pathname === '/registrations'
                    ? 'bg-brand-800 text-white'
                    : 'text-slate-200 hover:bg-brand-800/60 hover:text-white'
                }`}
              >
                <Building2 className="h-4 w-4" />
                Rule 27 Registry
              </a>

              <a
                href="/seizures"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  pathname === '/seizures'
                    ? 'bg-brand-800 text-white'
                    : 'text-slate-200 hover:bg-brand-800/60 hover:text-white'
                }`}
              >
                <AlertOctagon className="h-4 w-4" />
                Seizures
              </a>

              <a
                href="/enforcement"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  pathname === '/enforcement'
                    ? 'bg-brand-800 text-white'
                    : 'text-slate-200 hover:bg-brand-800/60 hover:text-white'
                }`}
              >
                <Gavel className="h-4 w-4" />
                Enforcement
              </a>

              <a
                href="/dossiers"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  pathname.startsWith('/dossiers')
                    ? 'bg-brand-800 text-white'
                    : 'text-slate-200 hover:bg-brand-800/60 hover:text-white'
                }`}
              >
                <Briefcase className="h-4 w-4" />
                Dossiers
              </a>

              {isInspector && (
                <a
                  href="/inspections/new"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                    pathname === '/inspections/new'
                      ? 'bg-sky-600 text-white font-semibold shadow-sm'
                      : 'bg-sky-500 text-white hover:bg-sky-600'
                  }`}
                >
                  <PlusCircle className="h-4 w-4" />
                  New
                </a>
              )}

              {isSupervisor && (
                <a
                  href="/analytics"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                    pathname === '/analytics'
                      ? 'bg-brand-800 text-white'
                      : 'text-slate-200 hover:bg-brand-800/60 hover:text-white'
                  }`}
                >
                  <BarChart3 className="h-4 w-4" />
                  Supervisor Analytics
                </a>
              )}
            </nav>
          )}

          {/* User Profile & Offline Badge */}
          {user ? (
            <div className="flex items-center space-x-3">
              <OfflineSyncBadge />
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-xs font-semibold text-white">{user.name}</span>
                <span className="text-[10px] text-sky-300 font-mono font-medium">
                  {user.role} {user.jurisdiction_state ? `• ${user.jurisdiction_state}` : ''}
                </span>
              </div>
              <button
                onClick={logout}
                title="Log Out"
                className="p-2 rounded-md text-slate-300 hover:text-white hover:bg-brand-800 transition-colors"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          ) : (
            <div>
              <a
                href="/login"
                className="text-sm bg-sky-500 hover:bg-sky-600 text-white font-medium px-4 py-2 rounded-md transition-colors"
              >
                Sign In
              </a>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

