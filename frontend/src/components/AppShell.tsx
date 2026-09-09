'use client';

import React, { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import OfflineSyncBadge from '@/components/OfflineSyncBadge';
import {
  ShieldCheck,
  ClipboardList,
  PlusCircle,
  BarChart3,
  LogOut,
  Boxes,
  Gavel,
  Scale,
  Building2,
  AlertOctagon,
  Briefcase,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Search,
  CheckSquare,
  Shield,
  Home,
  Camera,
  FileText,
  User as UserIcon,
} from 'lucide-react';

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const { user, logout, isInspector, isSupervisor } = useAuth();
  const pathname = usePathname();

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [seedingDemo, setSeedingDemo] = useState(false);
  const [demoFeedback, setDemoFeedback] = useState<string | null>(null);

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // Handle login page: completely isolate from AppShell chrome (sidebar, header, nav)
  if (pathname === '/login') {
    return <>{children}</>;
  }

  const handleSeedDemoPresets = async () => {
    setSeedingDemo(true);
    setDemoFeedback(null);
    try {
      const res = await api.seedDemoPresets();
      setDemoFeedback(res.message);
      // Reload current route data if on inspections
      if (pathname === '/inspections') {
        window.location.reload();
      }
      setTimeout(() => setDemoFeedback(null), 6000);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to seed controlled demo presets.');
    } finally {
      setSeedingDemo(false);
    }
  };

  const navPrimary = [
    {
      name: 'Command Desk',
      href: '/inspector',
      icon: Home,
      exact: true,
      active: pathname === '/inspector',
      badge: null,
      visible: isInspector,
    },
    {
      name: 'Inspections',
      href: '/inspector/inspections',
      icon: ClipboardList,
      exact: true,
      active: pathname === '/inspector/inspections' || pathname === '/inspections',
      badge: null,
    },
    {
      name: 'Field Scan',
      href: '/inspector/scan',
      icon: Camera,
      exact: true,
      active: pathname === '/inspector/scan' || pathname === '/inspections/new',
      badge: 'Capture',
      visible: isInspector,
    },
    {
      name: 'Reports & Hub',
      href: '/inspector/reports',
      icon: FileText,
      exact: true,
      active: pathname === '/inspector/reports',
      badge: null,
      visible: isInspector,
    },
    {
      name: 'Officer Profile',
      href: '/inspector/profile',
      icon: UserIcon,
      exact: true,
      active: pathname === '/inspector/profile',
      badge: null,
      visible: isInspector,
    },
    {
      name: 'Review Queue',
      href: '/inspections/triage',
      icon: CheckSquare,
      exact: true,
      active: pathname === '/inspections/triage',
      badge: null,
    },
    {
      name: 'Investigation Dossiers',
      href: '/dossiers',
      icon: Briefcase,
      exact: false,
      active: pathname.startsWith('/dossiers'),
      badge: null,
    },
    {
      name: 'Supervisor Analytics',
      href: '/analytics',
      icon: BarChart3,
      exact: false,
      active: pathname.startsWith('/analytics'),
      badge: null,
      visible: isSupervisor,
    },
  ].filter((item) => item.visible !== false);

  const navStatutory = [
    {
      name: 'Rule 19 Batch Lots',
      href: '/batches',
      icon: Boxes,
      active: pathname.startsWith('/batches'),
    },
    {
      name: 'Gravimetric MPE',
      href: '/gravimetric',
      icon: Scale,
      active: pathname === '/gravimetric',
    },
    {
      name: 'Rule 27 Packer Registry',
      href: '/registrations',
      icon: Building2,
      active: pathname === '/registrations',
    },
    {
      name: 'Section 15 Seizures',
      href: '/seizures',
      icon: AlertOctagon,
      active: pathname === '/seizures',
    },
    {
      name: 'Section 48 Compounding',
      href: '/enforcement',
      icon: Gavel,
      active: pathname === '/enforcement',
    },
  ];

  const getRouteMetadata = () => {
    if (pathname === '/inspector') {
      return {
        title: 'Inspector Command Center',
        subtitle: 'Personalized field inspection workload, sync state, and recidivist radar',
      };
    }
    if (pathname === '/inspector/inspections' || pathname === '/inspections') {
      return {
        title: 'Inspection Workspace',
        subtitle: 'Field inspection repository and deterministic compliance adjudication',
      };
    }
    if (pathname === '/inspector/scan' || pathname === '/inspections/new') {
      return {
        title: 'Field Scan & Multi-Panel Evidence Capture',
        subtitle: 'Guided 5-step statutory packaging capture & vision diagnostics',
      };
    }
    if (pathname === '/inspector/reports') {
      return {
        title: 'Statutory Reports & Enforcement Hub',
        subtitle: 'Generate and export legally admissible certificates and Panchnamas',
      };
    }
    if (pathname === '/inspector/profile') {
      return {
        title: 'Officer Profile & Cryptographic Audit',
        subtitle: 'Statutory officer credentials, jurisdiction, and immutable audit ledger',
      };
    }
    if (pathname.startsWith('/inspections/triage')) {
      return {
        title: 'Officer Review Queue',
        subtitle: 'Adjudication queue for cases with low confidence or optical quality flags',
      };
    }
    if (pathname.startsWith('/inspections/')) {
      return {
        title: 'Inspection Workstation',
        subtitle: 'Multi-angle visual perception and deterministic statutory rule evaluation',
      };
    }
    if (pathname.startsWith('/dossiers')) {
      return {
        title: 'Investigation Dossiers',
        subtitle: 'Formal digital case dossiers under Legal Metrology Act, 2009',
      };
    }
    if (pathname.startsWith('/analytics')) {
      return {
        title: 'Supervisor Intelligence & Analytics',
        subtitle: 'Jurisdictional compliance rates, officer workload, and violation trends',
      };
    }
    if (pathname.startsWith('/batches')) {
      return {
        title: 'Rule 19 Batch Sampling Lots',
        subtitle: 'Statistical sampling and maximum permissible error (MPE) lot verification',
      };
    }
    if (pathname.startsWith('/gravimetric')) {
      return {
        title: 'Gravimetric Net-Weight Verification',
        subtitle: 'Tare, gross, and net quantity determination with digital scale integration',
      };
    }
    if (pathname.startsWith('/registrations')) {
      return {
        title: 'Rule 27 Manufacturer & Packer Registry',
        subtitle: 'Statutory verification of registered manufacturers, packers, and importers',
      };
    }
    if (pathname.startsWith('/seizures')) {
      return {
        title: 'Section 15 Seizures & Panchnama',
        subtitle: 'Formal seizure records, panchnama documentation, and custody chains',
      };
    }
    if (pathname.startsWith('/enforcement')) {
      return {
        title: 'Section 48 Compounding Register',
        subtitle: 'Statutory compounding notices, hearings, and penalty settlements',
      };
    }
    return {
      title: 'MetrologyMitra Workstation',
      subtitle: 'Legal Metrology (Packaged Commodities) Rules, 2011 Operating System',
    };
  };

  const routeMeta = getRouteMetadata();

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col antialiased">
      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-slate-950/70 z-40 lg:hidden backdrop-blur-xs"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      <div className="flex flex-1 w-full relative">
        {/* LEFT SIDEBAR (Desktop & Mobile Drawer - Modern Translucent Light Executive Styling) */}
        <aside
          className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col bg-white/90 backdrop-blur-xl border-r border-slate-200/80 text-slate-700 transition-all duration-300 ease-in-out shadow-sm ${
            sidebarCollapsed ? 'w-20' : 'w-64'
          } ${
            mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          }`}
        >
          {/* Brand Header */}
          <div className="h-16 px-4 flex items-center justify-between border-b border-slate-200/80 bg-white/60 backdrop-blur-sm">
            <a
              href="/inspections"
              className={`flex items-center gap-2.5 overflow-hidden transition-all ${
                sidebarCollapsed ? 'justify-center w-full' : ''
              }`}
            >
              <div className="p-2 bg-sky-50 border border-sky-200/80 rounded-xl shrink-0 shadow-2xs">
                <ShieldCheck className="h-5 w-5 text-sky-600" />
              </div>
              {!sidebarCollapsed && (
                <div className="leading-tight truncate">
                  <div className="font-black tracking-tight text-slate-900 text-sm flex items-center gap-1.5">
                    MetrologyMitra
                    <span className="text-[9px] bg-sky-100 text-sky-800 px-1.5 py-0.5 rounded font-mono font-semibold border border-sky-200">
                      SIH26034
                    </span>
                  </div>
                  <div className="text-[9px] font-medium text-slate-400 tracking-wider uppercase truncate">
                    Inspection Intelligence
                  </div>
                </div>
              )}
            </a>

            {/* Desktop Collapse Toggle */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="hidden lg:flex p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition cursor-pointer"
              title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {sidebarCollapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </button>

            {/* Mobile Close Button */}
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation Links Scroll Container */}
          <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6 scrollbar-thin scrollbar-thumb-slate-200">
            {/* Primary Workspace Section */}
            <div>
              {!sidebarCollapsed && (
                <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                  Primary Workspace
                </div>
              )}
              <div className="space-y-1">
                {navPrimary.map((item) => {
                  const Icon = item.icon;
                  return (
                    <a
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                        item.active
                          ? 'bg-sky-50 text-sky-800 border border-sky-200/80 shadow-xs font-bold'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                      } ${sidebarCollapsed ? 'justify-center' : ''}`}
                      title={sidebarCollapsed ? item.name : undefined}
                    >
                      <Icon
                        className={`h-4 w-4 shrink-0 ${
                          item.active ? 'text-sky-600' : 'text-slate-400'
                        }`}
                      />
                      {!sidebarCollapsed && (
                        <span className="truncate flex-1">{item.name}</span>
                      )}
                      {!sidebarCollapsed && item.badge && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-sky-600 text-white">
                          {item.badge}
                        </span>
                      )}
                    </a>
                  );
                })}
              </div>
            </div>

            {/* Statutory Modules Section */}
            <div>
              {!sidebarCollapsed && (
                <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                  Statutory Modules (LMPC)
                </div>
              )}
              <div className="space-y-1">
                {navStatutory.map((item) => {
                  const Icon = item.icon;
                  return (
                    <a
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                        item.active
                          ? 'bg-sky-50 text-sky-800 border border-sky-200/80 shadow-xs font-bold'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                      } ${sidebarCollapsed ? 'justify-center' : ''}`}
                      title={sidebarCollapsed ? item.name : undefined}
                    >
                      <Icon
                        className={`h-4 w-4 shrink-0 ${
                          item.active ? 'text-sky-600' : 'text-slate-400'
                        }`}
                      />
                      {!sidebarCollapsed && (
                        <span className="truncate flex-1">{item.name}</span>
                      )}
                    </a>
                  );
                })}
              </div>
            </div>

            {/* Demo Presets Trigger in Sidebar */}
            <div className="pt-2">
              <button
                type="button"
                onClick={handleSeedDemoPresets}
                disabled={seedingDemo}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold transition border border-indigo-200/80 bg-indigo-50/70 text-indigo-700 hover:bg-indigo-100/80 disabled:opacity-50 shadow-2xs cursor-pointer ${
                  sidebarCollapsed ? 'justify-center' : ''
                }`}
                title="Seed 7 controlled benchmark cases (Compliant, MRP, Exemption, etc.)"
              >
                <Sparkles
                  className={`h-4 w-4 text-indigo-600 shrink-0 ${
                    seedingDemo ? 'animate-spin' : ''
                  }`}
                />
                {!sidebarCollapsed && (
                  <span className="truncate">
                    {seedingDemo ? 'Seeding Presets...' : 'Load 7 Demo Presets'}
                  </span>
                )}
              </button>
            </div>
          </div>

          {/* Sidebar Footer: Officer Badge & Sync */}
          {user && (
            <div className="p-3 border-t border-slate-200/80 bg-slate-50/80 space-y-2">
              <div
                className={`flex items-center gap-2.5 ${
                  sidebarCollapsed ? 'justify-center' : 'justify-between'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <div className="h-8 w-8 rounded-full bg-sky-100 border border-sky-200 flex items-center justify-center text-xs font-bold text-sky-700 shrink-0">
                    {user.name.charAt(0)}
                  </div>
                  {!sidebarCollapsed && (
                    <div className="truncate">
                      <div className="text-xs font-bold text-slate-900 truncate">
                        {user.name}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono flex items-center gap-1">
                        <span className="px-1 py-0.2 bg-slate-200/70 rounded text-slate-700">
                          {user.role}
                        </span>
                        {user.jurisdiction_state && (
                          <span className="truncate">• {user.jurisdiction_state}</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {!sidebarCollapsed && (
                  <button
                    onClick={logout}
                    title="Log Out"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition shrink-0 cursor-pointer"
                  >
                    <LogOut className="h-4 w-4" />
                  </button>
                )}
              </div>

              {!sidebarCollapsed && (
                <div className="pt-1 flex items-center justify-between border-t border-slate-200/80">
                  <OfflineSyncBadge />
                </div>
              )}
            </div>
          )}
        </aside>

        {/* MAIN BODY AREA */}
        <div
          className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${
            sidebarCollapsed ? 'lg:pl-20' : 'lg:pl-64'
          }`}
        >
          {/* TOP HEADER */}
          <header className="h-16 bg-white border-b border-slate-200 px-4 sm:px-6 lg:px-8 flex items-center justify-between sticky top-0 z-30 shadow-xs">
            {/* Left: Mobile hamburger & route metadata */}
            <div className="flex items-center gap-3 min-w-0">
              <button
                onClick={() => setMobileMenuOpen(true)}
                className="lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100"
                aria-label="Open sidebar"
              >
                <Menu className="h-5 w-5" />
              </button>

              <div className="min-w-0">
                <h1 className="text-sm sm:text-base font-black text-slate-900 truncate tracking-tight">
                  {routeMeta.title}
                </h1>
                <p className="text-[11px] text-slate-500 truncate hidden sm:block">
                  {routeMeta.subtitle}
                </p>
              </div>
            </div>

            {/* Right: Operational Status Pill, Global Actions */}
            <div className="flex items-center gap-2 sm:gap-3 shrink-0">
              {/* Statutory Deterministic Engine Badge */}
              <div
                className="hidden md:flex items-center gap-1.5 px-3 py-1 bg-slate-100 border border-slate-200 rounded-full text-[11px] font-semibold text-slate-700"
                title="LMPC 2011 deterministic legal rules evaluated without generative distortion"
              >
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="font-mono">LMPC 2011 Engine Active</span>
              </div>

              {/* Quick "+ New Inspection" Action */}
              {isInspector && pathname !== '/inspections/new' && (
                <a
                  href="/inspections/new"
                  className="bg-brand-900 hover:bg-brand-800 text-white font-bold text-xs px-3 sm:px-3.5 py-1.5 rounded-lg shadow-xs transition flex items-center gap-1.5"
                >
                  <PlusCircle className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">New Inspection</span>
                </a>
              )}
            </div>
          </header>

          {/* Feedback banner for demo fixtures if triggered from sidebar */}
          {demoFeedback && (
            <div className="mx-4 sm:mx-6 lg:mx-8 mt-4 p-3 bg-indigo-50 border border-indigo-200 rounded-xl text-xs text-indigo-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-600 shrink-0" />
                <span><strong>Demo Fixtures:</strong> {demoFeedback}</span>
              </div>
              <button
                onClick={() => setDemoFeedback(null)}
                className="text-indigo-400 hover:text-indigo-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* MAIN PAGE CONTAINER */}
          <main className="flex-1 w-full max-w-[1600px] mx-auto p-4 sm:p-6 lg:p-8 mb-16 lg:mb-0">
            {children}
          </main>

          {/* MOBILE BOTTOM NAVIGATION BAR (ScanShield Parity & Field Ergonomics) */}
          {isInspector && (
            <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-slate-200 lg:hidden shadow-lg">
              <div className="grid grid-cols-5 items-center h-16 px-1">
                <a
                  href="/inspector"
                  className={`flex flex-col items-center justify-center gap-1 py-1 text-[10px] font-bold ${
                    pathname === '/inspector' ? 'text-sky-600' : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  <Home className="h-5 w-5" />
                  <span>Home</span>
                </a>

                <a
                  href="/inspector/inspections"
                  className={`flex flex-col items-center justify-center gap-1 py-1 text-[10px] font-bold ${
                    pathname === '/inspector/inspections' || pathname === '/inspections'
                      ? 'text-sky-600'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  <ClipboardList className="h-5 w-5" />
                  <span>History</span>
                </a>

                <a
                  href="/inspector/scan"
                  className="flex flex-col items-center justify-center -mt-5"
                >
                  <div className="w-12 h-12 rounded-full bg-sky-600 text-white flex items-center justify-center shadow-lg shadow-sky-600/30 border-2 border-white hover:bg-sky-500 transition-transform active:scale-95">
                    <Camera className="h-6 w-6" />
                  </div>
                  <span className="text-[10px] font-extrabold text-sky-700 mt-0.5">Scan</span>
                </a>

                <a
                  href="/inspector/reports"
                  className={`flex flex-col items-center justify-center gap-1 py-1 text-[10px] font-bold ${
                    pathname === '/inspector/reports' ? 'text-sky-600' : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  <FileText className="h-5 w-5" />
                  <span>Reports</span>
                </a>

                <a
                  href="/inspector/profile"
                  className={`flex flex-col items-center justify-center gap-1 py-1 text-[10px] font-bold ${
                    pathname === '/inspector/profile' ? 'text-sky-600' : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  <UserIcon className="h-5 w-5" />
                  <span>Profile</span>
                </a>
              </div>
            </nav>
          )}

          {/* GLOBAL FOOTER */}
          <footer className="bg-white border-t border-slate-200 py-3.5 px-4 sm:px-6 lg:px-8 text-center text-[11px] text-slate-500">
            <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
              <div className="flex items-center gap-1.5 text-slate-600 font-medium">
                <Shield className="h-3.5 w-3.5 text-sky-600" />
                <span>Legal Metrology Inspection Operating System (SIH26034)</span>
              </div>
              <p className="text-slate-400">
                Department of Consumer Affairs • Government of India • Deterministic Statutory Compliance Engine
              </p>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}

