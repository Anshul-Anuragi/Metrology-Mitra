'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import {
  DossierPriority,
  DossierStatus,
  InvestigationDossier,
  InvestigationDossierCreate,
} from '@/types';
import {
  Briefcase,
  PlusCircle,
  Search,
  Filter,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Shield,
  FileText,
  Building2,
  Eye,
  RefreshCw,
  FolderOpen,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';

export default function DossiersPage() {
  const { user, isSupervisor, isAdmin } = useAuth();
  const router = useRouter();

  const [dossiers, setDossiers] = useState<InvestigationDossier[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');

  // New Dossier Modal
  const [showModal, setShowModal] = useState<boolean>(false);
  const [newTitle, setNewTitle] = useState<string>('');
  const [newDescription, setNewDescription] = useState<string>('');
  const [newTargetEntity, setNewTargetEntity] = useState<string>('');
  const [newPriority, setNewPriority] = useState<DossierPriority>('NORMAL');
  const [newTags, setNewTags] = useState<string>('MARKET_SURVEILLANCE');
  const [submitting, setSubmitting] = useState<boolean>(false);

  const fetchDossiers = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: any = {};
      if (statusFilter !== 'ALL') params.status = statusFilter;
      if (priorityFilter !== 'ALL') params.priority = priorityFilter;
      if (search.trim()) params.search = search.trim();

      const data = await api.getDossiers(params);
      setDossiers(data);
    } catch (err: any) {
      console.error('Failed to load dossiers', err);
      setError(err?.response?.data?.detail || 'Failed to load investigation dossiers.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDossiers();
  }, [statusFilter, priorityFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchDossiers();
  };

  const handleCreateDossier = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      setSubmitting(true);
      const payload: InvestigationDossierCreate = {
        title: newTitle.trim(),
        description: newDescription.trim() || undefined,
        target_entity_name: newTargetEntity.trim() || undefined,
        priority: newPriority,
        tags: newTags
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      };

      const created = await api.createDossier(payload);
      setShowModal(false);
      // Reset modal form
      setNewTitle('');
      setNewDescription('');
      setNewTargetEntity('');
      setNewPriority('NORMAL');
      setNewTags('MARKET_SURVEILLANCE');
      // Navigate to the newly created dossier workspace
      router.push(`/dossiers/${created.id}`);
    } catch (err: any) {
      console.error('Failed to create dossier', err);
      alert(err?.response?.data?.detail || 'Failed to create investigation dossier.');
    } finally {
      setSubmitting(false);
    }
  };

  // Status badge styling helper
  const getStatusBadge = (status: DossierStatus) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-sky-100 text-sky-800 border-sky-300';
      case 'EVALUATION':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'NOTICE_REVIEW':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'COMPOUNDING_REVIEW':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'CLOSED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  // Priority badge styling helper
  const getPriorityBadge = (priority: DossierPriority) => {
    switch (priority) {
      case 'URGENT':
        return 'bg-red-600 text-white font-bold';
      case 'HIGH':
        return 'bg-orange-500 text-white font-semibold';
      case 'NORMAL':
        return 'bg-blue-600 text-white';
      case 'LOW':
        return 'bg-slate-500 text-white';
      default:
        return 'bg-slate-400 text-white';
    }
  };

  // Calculate metrics
  const totalCount = dossiers.length;
  const activeCount = dossiers.filter((d) => d.status === 'ACTIVE').length;
  const evaluationCount = dossiers.filter((d) => d.status === 'EVALUATION').length;
  const noticeCount = dossiers.filter((d) => d.status === 'NOTICE_REVIEW').length;
  const compoundingCount = dossiers.filter((d) => d.status === 'COMPOUNDING_REVIEW').length;
  const closedCount = dossiers.filter((d) => d.status === 'CLOSED').length;

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      {/* Header */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Briefcase className="h-7 w-7 text-brand-800" />
                <h1 className="text-2xl font-bold text-slate-900">
                  Market Surveillance Investigation Dossiers
                </h1>
              </div>
              <p className="text-sm text-slate-500 mt-1">
                Multi-inspection operational case containers for supervisory coordination and evidence synthesis.
              </p>
            </div>

            {(isSupervisor || isAdmin) && (
              <button
                onClick={() => setShowModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-800 hover:bg-brand-900 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors cursor-pointer"
              >
                <PlusCircle className="h-4 w-4" />
                New Investigation Dossier
              </button>
            )}
          </div>

          {/* Legal Boundary Advisory Banner */}
          <div className="mt-5 p-4 rounded-lg bg-amber-50 border border-amber-200/80 flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-amber-700 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-amber-900 leading-relaxed">
              <strong className="font-semibold">STATUTORY / ARCHITECTURAL BOUNDARY: </strong>
              Investigation Dossiers are strictly operational administrative containers grouping individual inspection records for market surveillance coordination. Dossiers <strong>do not alter</strong> individual statutory compliance verdicts, <strong>do not establish</strong> collective guilt or conspiracy, and <strong>do not determine</strong> prosecution or director liability. Each inspection remains an independent legal record.
            </div>
          </div>

          {/* Metrics Overview Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-6">
            <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
              <div className="text-xs text-slate-500 font-medium">Total Dossiers</div>
              <div className="text-xl font-bold text-slate-900 mt-1">{totalCount}</div>
            </div>
            <div className="bg-sky-50 border border-sky-100 rounded-lg p-3 shadow-xs">
              <div className="text-xs text-sky-700 font-medium">Active</div>
              <div className="text-xl font-bold text-sky-900 mt-1">{activeCount}</div>
            </div>
            <div className="bg-purple-50 border border-purple-100 rounded-lg p-3 shadow-xs">
              <div className="text-xs text-purple-700 font-medium">Evaluation</div>
              <div className="text-xl font-bold text-purple-900 mt-1">{evaluationCount}</div>
            </div>
            <div className="bg-amber-50 border border-amber-100 rounded-lg p-3 shadow-xs">
              <div className="text-xs text-amber-700 font-medium">Notice Review</div>
              <div className="text-xl font-bold text-amber-900 mt-1">{noticeCount}</div>
            </div>
            <div className="bg-rose-50 border border-rose-100 rounded-lg p-3 shadow-xs">
              <div className="text-xs text-rose-700 font-medium">Compounding Review</div>
              <div className="text-xl font-bold text-rose-900 mt-1">{compoundingCount}</div>
            </div>
            <div className="bg-emerald-50 border border-emerald-100 rounded-lg p-3 shadow-xs">
              <div className="text-xs text-emerald-700 font-medium">Closed</div>
              <div className="text-xl font-bold text-emerald-900 mt-1">{closedCount}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        {/* Filters and Search Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs mb-6">
          <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
            <div className="relative flex-1">
              <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by title, dossier number, or target entity name..."
                className="w-full pl-9 pr-4 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div className="flex flex-wrap gap-3 items-center">
              <div className="flex items-center gap-1.5 text-xs text-slate-600">
                <Filter className="h-3.5 w-3.5 text-slate-400" />
                <span>Status:</span>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="text-xs border border-slate-300 rounded-md py-1.5 px-2 bg-white text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="EVALUATION">EVALUATION</option>
                  <option value="NOTICE_REVIEW">NOTICE_REVIEW</option>
                  <option value="COMPOUNDING_REVIEW">COMPOUNDING_REVIEW</option>
                  <option value="CLOSED">CLOSED</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-slate-600">
                <span>Priority:</span>
                <select
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                  className="text-xs border border-slate-300 rounded-md py-1.5 px-2 bg-white text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="ALL">All Priorities</option>
                  <option value="URGENT">URGENT</option>
                  <option value="HIGH">HIGH</option>
                  <option value="NORMAL">NORMAL</option>
                  <option value="LOW">LOW</option>
                </select>
              </div>

              <button
                type="submit"
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-md transition-colors"
              >
                Apply
              </button>

              <button
                type="button"
                onClick={() => {
                  setSearch('');
                  setStatusFilter('ALL');
                  setPriorityFilter('ALL');
                }}
                className="p-1.5 text-slate-400 hover:text-slate-600"
                title="Reset filters"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
            </div>
          </form>
        </div>

        {/* Error State */}
        {error && (
          <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm mb-6 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        {/* Dossiers Grid */}
        {loading ? (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-200">
            <RefreshCw className="h-8 w-8 text-brand-600 animate-spin mx-auto mb-3" />
            <p className="text-sm text-slate-500 font-medium">Loading investigation dossiers...</p>
          </div>
        ) : dossiers.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-200 shadow-xs">
            <FolderOpen className="h-12 w-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">No investigation dossiers found</h3>
            <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
              {search || statusFilter !== 'ALL' || priorityFilter !== 'ALL'
                ? 'No dossiers match your current filter criteria. Try clearing filters.'
                : 'Create a dossier to group related market surveillance inspections for supervisor review.'}
            </p>
            {(isSupervisor || isAdmin) && (
              <button
                onClick={() => setShowModal(true)}
                className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-brand-800 hover:bg-brand-900 text-white text-xs font-semibold rounded-lg shadow-sm cursor-pointer"
              >
                <PlusCircle className="h-3.5 w-3.5" />
                Create New Dossier
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {dossiers.map((dossier) => (
              <div
                key={dossier.id}
                className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between"
              >
                <div>
                  {/* Top Bar: Number & Priority */}
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">
                      {dossier.dossier_number}
                    </span>
                    <span
                      className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded ${getPriorityBadge(
                        dossier.priority
                      )}`}
                    >
                      {dossier.priority}
                    </span>
                  </div>

                  {/* Title */}
                  <h3 className="text-base font-bold text-slate-900 line-clamp-1 mb-1" title={dossier.title}>
                    {dossier.title}
                  </h3>

                  {/* Target Entity Name */}
                  <div className="flex items-center gap-1.5 text-xs text-slate-600 mb-3">
                    <Building2 className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                    <span className="font-medium truncate" title={dossier.target_entity_name || 'No target entity designated'}>
                      {dossier.target_entity_name || 'No target entity designated'}
                    </span>
                  </div>

                  {/* Description */}
                  {dossier.description && (
                    <p className="text-xs text-slate-500 line-clamp-2 mb-3">
                      {dossier.description}
                    </p>
                  )}

                  {/* Status & Inspections Count */}
                  <div className="flex items-center gap-2 mb-4">
                    <span
                      className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${getStatusBadge(
                        dossier.status
                      )}`}
                    >
                      {dossier.status.replace('_', ' ')}
                    </span>

                    <span className="text-xs font-medium text-slate-600 bg-slate-50 px-2.5 py-1 rounded-full border border-slate-200">
                      {dossier.inspections?.length || 0} inspections linked
                    </span>
                  </div>

                  {/* Tags */}
                  {dossier.tags && dossier.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {dossier.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Footer Bar */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between mt-2">
                  <div className="text-[11px] text-slate-400">
                    Lead: {dossier.lead_supervisor?.name || 'Assigned Supervisor'}
                  </div>

                  <Link
                    href={`/dossiers/${dossier.id}`}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-700 hover:text-brand-900 hover:underline"
                  >
                    Open Workspace
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* New Dossier Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 border border-slate-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Briefcase className="h-5 w-5 text-brand-800" />
                <h3 className="text-lg font-bold text-slate-900">Create Investigation Dossier</h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-semibold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateDossier} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Dossier Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Edible Oil MRP Discrepancy — North Region Surveillance"
                  className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-brand-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Description / Operational Scope
                </label>
                <textarea
                  rows={2}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Brief note on rationale, target markets, or suspected declaration irregularities..."
                  className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-brand-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Target Entity Name (Informational Descriptor)
                </label>
                <input
                  type="text"
                  value={newTargetEntity}
                  onChange={(e) => setNewTargetEntity(e.target.value)}
                  placeholder="e.g. National FMCG Foods Private Limited"
                  className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-brand-500 focus:outline-none"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Note: Strictly operational text descriptor. Does not establish corporate liability without Section 49 record.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Priority</label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value as DossierPriority)}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 bg-white focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  >
                    <option value="LOW">LOW</option>
                    <option value="NORMAL">NORMAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="URGENT">URGENT</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Tags (comma-separated)</label>
                  <input
                    type="text"
                    value={newTags}
                    onChange={(e) => setNewTags(e.target.value)}
                    placeholder="EDIBLE_OIL, MRP_OVERCHARGE"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg font-medium cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 text-sm bg-brand-800 hover:bg-brand-900 text-white font-semibold rounded-lg shadow-sm disabled:opacity-50 cursor-pointer"
                >
                  {submitting ? 'Creating...' : 'Create Dossier'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

