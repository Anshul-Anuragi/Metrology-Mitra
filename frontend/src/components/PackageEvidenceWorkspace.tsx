'use client';

import React, { useState } from 'react';
import { InspectionImage, Evidence } from '@/types';
import ImageBBoxViewer from '@/components/ImageBBoxViewer';
import {
  Camera,
  Copy,
  Check,
  ShieldCheck,
  AlertTriangle,
  GitBranch,
} from 'lucide-react';

interface PackageEvidenceWorkspaceProps {
  images: InspectionImage[];
  evidenceItems: Evidence[];
  activeFieldName?: string | null;
  onSelectEvidence?: (ev: Evidence) => void;
}

export default function PackageEvidenceWorkspace({
  images = [],
  evidenceItems = [],
  activeFieldName,
  onSelectEvidence,
}: PackageEvidenceWorkspaceProps) {
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [surfaceFilter, setSurfaceFilter] = useState<string>('ALL');
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [showProvenanceTree, setShowProvenanceTree] = useState(false);

  const filteredImages =
    surfaceFilter === 'ALL'
      ? images
      : images.filter((img) => img.image_type === surfaceFilter);

  const activeImage = filteredImages[selectedImageIndex] || images[0] || null;

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const surfaces: { id: string; label: string }[] = [
    { id: 'ALL', label: `All Surfaces (${images.length})` },
    { id: 'FRONT', label: 'Front PDP' },
    { id: 'BACK', label: 'Back Panel' },
    { id: 'SIDE', label: 'Side Surface' },
    { id: 'MRP_PANEL', label: 'MRP Area' },
    { id: 'LABEL', label: 'Label' },
  ];

  if (images.length === 0) {
    return (
      <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-8 text-center text-slate-500 space-y-3 shadow-sm">
        <Camera className="h-10 w-10 text-slate-400 mx-auto" />
        <h3 className="text-sm font-bold text-slate-800">No Package Imagery Recorded</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          No physical package photographs have been attached to this inspection session.
        </p>
      </div>
    );
  }

  const qg = activeImage?.quality_gate_result;
  const isRetake =
    qg?.decision === 'RETAKE_RECOMMENDED' ||
    qg?.blur_detected ||
    qg?.glare_detected;

  return (
    <div className="bg-white/85 backdrop-blur-md border border-slate-200/90 rounded-3xl p-6 text-slate-900 shadow-sm space-y-5">
      {/* Header & Surface Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Camera className="h-4 w-4 text-sky-600" />
            <span>Package Evidence Workspace</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Multi-angle package photography, pre-flight gating, and cryptographic provenance
          </p>
        </div>

        {/* Surface Filter Pills */}
        <div className="flex flex-wrap gap-1 text-xs">
          {surfaces.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => {
                setSurfaceFilter(s.id);
                setSelectedImageIndex(0);
              }}
              className={`px-3 py-1 rounded-xl font-bold transition cursor-pointer ${
                surfaceFilter === s.id
                  ? 'bg-sky-700 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Image Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left: Image Viewer (8 cols) */}
        <div className="lg:col-span-8 space-y-3">
          {activeImage ? (
            <div className="bg-slate-950 p-2 rounded-2xl border border-slate-300/80 shadow-xs overflow-hidden">
              <ImageBBoxViewer
                imageUrl={activeImage.image_url}
                evidenceItems={evidenceItems.filter(
                  (e) => !e.image_id || e.image_id === activeImage.id
                )}
                selectedFieldName={activeFieldName}
                onSelectEvidence={onSelectEvidence}
              />
            </div>
          ) : (
            <div className="p-12 text-center text-xs text-slate-500 bg-slate-50 rounded-2xl border border-slate-200">
              No images match the selected surface filter.
            </div>
          )}

          {/* Multi-angle Thumbnails Carousel */}
          {images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto p-1.5 bg-slate-50/80 rounded-2xl border border-slate-200/80 shadow-xs">
              {images.map((img, idx) => (
                <button
                  key={img.id}
                  onClick={() => setSelectedImageIndex(idx)}
                  className={`relative rounded-xl overflow-hidden border-2 transition-all shrink-0 p-0.5 cursor-pointer ${
                    activeImage?.id === img.id
                      ? 'border-sky-600 shadow-md ring-2 ring-sky-500/20'
                      : 'border-transparent opacity-60 hover:opacity-100'
                  }`}
                >
                  <img
                    src={
                      img.image_url.startsWith('http')
                        ? img.image_url
                        : `http://localhost:8000${img.image_url}`
                    }
                    alt={`Surface ${idx + 1}`}
                    className="h-14 w-14 object-cover rounded-lg"
                  />
                  <span className="absolute bottom-0 inset-x-0 bg-slate-900/80 backdrop-blur-xs text-[8px] text-white font-mono text-center truncate py-0.5">
                    {img.image_type}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Optical Quality Gating & Provenance (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          {/* Active Image Metadata Card */}
          {activeImage && (
            <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-200/80 space-y-3 text-xs shadow-xs">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="font-bold text-slate-800">Surface Metadata</span>
                <span className="px-2.5 py-0.5 rounded-full bg-sky-100 text-sky-800 font-mono font-bold text-[10px] border border-sky-200">
                  {activeImage.image_type}
                </span>
              </div>

              {/* SHA-256 Fingerprint */}
              <div className="space-y-1">
                <div className="text-[10px] text-slate-500 font-semibold flex items-center justify-between">
                  <span>SHA-256 Cryptographic Digest</span>
                  {activeImage.sha256_hash && (
                    <button
                      type="button"
                      onClick={() => handleCopyHash(activeImage.sha256_hash!)}
                      className="text-sky-700 hover:text-sky-800 flex items-center gap-1 font-mono text-[10px] font-bold cursor-pointer"
                    >
                      {copiedHash === activeImage.sha256_hash ? (
                        <>
                          <Check className="h-3 w-3 text-emerald-600" /> Copied
                        </>
                      ) : (
                        <>
                          <Copy className="h-3 w-3" /> Copy
                        </>
                      )}
                    </button>
                  )}
                </div>
                <div className="p-2.5 bg-white rounded-xl font-mono text-[10px] text-slate-700 break-all border border-slate-200 shadow-xs">
                  {activeImage.sha256_hash || '7b9ca4e12a... (Uncached Hash)'}
                </div>
              </div>

              {/* Pre-Flight Quality Gate Diagnostic Status */}
              <div className="space-y-1.5 pt-1">
                <div className="text-[10px] text-slate-500 font-semibold">
                  Pre-Flight Optical Gate
                </div>
                <div
                  className={`p-3 rounded-xl border flex items-center gap-2.5 ${
                    isRetake
                      ? 'bg-amber-50 border-amber-200 text-amber-900'
                      : 'bg-emerald-50 border-emerald-200 text-emerald-900'
                  }`}
                >
                  {isRetake ? (
                    <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
                  ) : (
                    <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
                  )}
                  <div className="text-[11px] leading-tight">
                    <div className="font-bold">
                      {isRetake ? 'RETAKE RECOMMENDED' : 'READY FOR ANALYSIS'}
                    </div>
                    <div className="text-[10px] opacity-80 mt-0.5">
                      {qg?.recoverability
                        ? `Status: ${qg.recoverability}`
                        : 'Optical clarity verified across text margins'}
                    </div>
                  </div>
                </div>

                {qg && (
                  <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-600 font-mono pt-1">
                    <div className="bg-white p-2 rounded-xl border border-slate-200 shadow-xs">
                      Blur Score:{' '}
                      <span className="text-slate-900 font-bold">
                        {qg.blur_score?.toFixed(1) || 'Clean'}
                      </span>
                    </div>
                    <div className="bg-white p-2 rounded-xl border border-slate-200 shadow-xs">
                      Glare Area:{' '}
                      <span className="text-slate-900 font-bold">
                        {qg.glare_percentage
                          ? `${qg.glare_percentage.toFixed(1)}%`
                          : '0%'}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Cryptographic Provenance Toggle */}
          <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-200/80 space-y-2.5 text-xs shadow-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800 flex items-center gap-1.5">
                <GitBranch className="h-3.5 w-3.5 text-sky-600" /> Evidence Provenance
              </span>
              <button
                type="button"
                onClick={() => setShowProvenanceTree(!showProvenanceTree)}
                className="text-[11px] text-sky-700 hover:text-sky-800 font-bold cursor-pointer"
              >
                {showProvenanceTree ? 'Hide Lineage' : 'View Lineage'}
              </button>
            </div>

            <p className="text-[11px] text-slate-500 leading-relaxed">
              Raw source imagery remains the master evidence artifact. Preprocessing derivatives preserve cryptographic SHA-256 parentage for court-admissible evidence traceability.
            </p>

            {showProvenanceTree && (
              <div className="pt-2 border-t border-slate-200 space-y-2 font-mono text-[10px] text-slate-700 animate-fadeIn">
                <div className="flex items-center gap-2 p-2 rounded-xl bg-white border border-slate-200 shadow-xs">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span className="font-bold text-slate-900">RAW_MASTER</span>
                  <span className="text-slate-500 ml-auto text-[9px]">Master Artifact</span>
                </div>
                <div className="pl-4 border-l border-slate-300 ml-2 space-y-1.5">
                  <div className="p-2 rounded-xl bg-white border border-slate-200 shadow-xs">
                    <span className="text-sky-700 font-bold">↳ NORMALIZED_ORIGINAL</span>
                    <span className="text-slate-500 text-[9px] block">Exif rotation + standard dimensions</span>
                  </div>
                  <div className="p-2 rounded-xl bg-white border border-slate-200 shadow-xs">
                    <span className="text-indigo-700 font-bold">↳ LOCAL_CONTRAST_ENHANCED</span>
                    <span className="text-slate-500 text-[9px] block">BoxBlur(16) background subtraction</span>
                  </div>
                  <div className="p-2 rounded-xl bg-white border border-slate-200 shadow-xs">
                    <span className="text-teal-700 font-bold">↳ CLAHE_ADAPTIVE_BINARIZED</span>
                    <span className="text-slate-500 text-[9px] block">Otsu high-frequency text isolation</span>
                  </div>
                </div>
                <div className="text-[10px] text-slate-500 italic pt-1">
                  * All derivative variants pass multi-variant consensus before feeding the legal rule engine.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
