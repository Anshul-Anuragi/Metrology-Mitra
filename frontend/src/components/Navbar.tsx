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
} from 'lucide-react';

export default function Navbar() {
  const { user, logout, isInspector, isSupervisor } = useAuth();
  const pathname = usePathname();

  if (!user && pathname === '/login') {
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
              <a href={isInspector ? '/inspections' : '/analytics'} className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
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
              <a
                href="/inspections"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  pathname === '/inspections'
                    ? 'bg-brand-800 text-white'
                    : 'text-slate-200 hover:bg-brand-800/60 hover:text-white'
                }`}
              >
                <ClipboardList className="h-4 w-4" />
                Inspections
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
                  New Inspection
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

          {/* User Profile & Logout */}
          {user ? (
            <div className="flex items-center space-x-4">
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

