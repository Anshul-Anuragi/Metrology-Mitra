'use client';

import React, { useRef, useState, useEffect } from 'react';
import { Evidence, BoundingBox } from '@/types';
import { ZoomIn, ZoomOut, RotateCcw, Eye, Layers } from 'lucide-react';

interface ImageBBoxViewerProps {
  imageUrl: string;
  evidenceItems?: Evidence[];
  selectedFieldName?: string | null;
  onSelectEvidence?: (evidence: Evidence) => void;
}

export default function ImageBBoxViewer({
  imageUrl,
  evidenceItems = [],
  selectedFieldName,
  onSelectEvidence,
}: ImageBBoxViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  const [naturalDimensions, setNaturalDimensions] = useState<{ width: number; height: number } | null>(null);
  const [displayedDimensions, setDisplayedDimensions] = useState<{ width: number; height: number }>({ width: 0, height: 0 });
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [showBoxes, setShowBoxes] = useState<boolean>(true);
  const [hoveredEvidenceId, setHoveredEvidenceId] = useState<string | null>(null);

  const backendOrigin = process.env.NEXT_PUBLIC_BACKEND_ORIGIN || 'http://localhost:8000';
  const fullImageUrl = imageUrl.startsWith('http') ? imageUrl : `${backendOrigin}${imageUrl}`;

  const handleImageLoad = () => {
    if (imgRef.current) {
      setNaturalDimensions({
        width: imgRef.current.naturalWidth,
        height: imgRef.current.naturalHeight,
      });
      setDisplayedDimensions({
        width: imgRef.current.clientWidth,
        height: imgRef.current.clientHeight,
      });
    }
  };

  useEffect(() => {
    const handleResize = () => {
      if (imgRef.current) {
        setDisplayedDimensions({
          width: imgRef.current.clientWidth,
          height: imgRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const scaleX = naturalDimensions && naturalDimensions.width > 0 ? displayedDimensions.width / naturalDimensions.width : 1;
  const scaleY = naturalDimensions && naturalDimensions.height > 0 ? displayedDimensions.height / naturalDimensions.height : 1;

  // Filter evidence items with bounding box coordinates
  const bboxItems = evidenceItems.filter((ev) => ev.bounding_box && ev.bounding_box.width > 0);

  return (
    <div className="bg-slate-900 rounded-xl overflow-hidden shadow-lg border border-slate-700 flex flex-col h-full">
      {/* Viewer Toolbar */}
      <div className="bg-slate-800/90 px-4 py-2.5 border-b border-slate-700 flex justify-between items-center text-xs text-slate-300">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-sky-400" />
          <span className="font-semibold text-white">Visual Evidence & OCR Bounding Boxes</span>
          <span className="bg-slate-700 text-slate-300 px-2 py-0.5 rounded text-[11px]">
            {bboxItems.length} regions detected
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowBoxes(!showBoxes)}
            className={`px-2.5 py-1 rounded flex items-center gap-1 transition-colors ${
              showBoxes ? 'bg-sky-600 text-white' : 'bg-slate-700 text-slate-400'
            }`}
            title="Toggle Bounding Boxes"
          >
            <Eye className="h-3.5 w-3.5" />
            <span className="text-[11px]">{showBoxes ? 'Hide Boxes' : 'Show Boxes'}</span>
          </button>
          <button
            onClick={() => setZoomLevel((z) => Math.min(z + 0.25, 2.5))}
            className="p-1.5 rounded bg-slate-700 hover:bg-slate-600 text-white transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setZoomLevel((z) => Math.max(z - 0.25, 0.75))}
            className="p-1.5 rounded bg-slate-700 hover:bg-slate-600 text-white transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setZoomLevel(1)}
            className="p-1.5 rounded bg-slate-700 hover:bg-slate-600 text-white transition-colors"
            title="Reset Zoom"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Interactive Image & Overlay Area */}
      <div
        ref={containerRef}
        className="relative flex-1 overflow-auto p-4 flex items-center justify-center bg-slate-950 min-h-[420px]"
      >
        <div
          className="relative inline-block transition-transform duration-150"
          style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center' }}
        >
          {/* Main Package Image */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            ref={imgRef}
            src={fullImageUrl}
            alt="Package Inspection Visual"
            onLoad={handleImageLoad}
            className="max-h-[550px] w-auto object-contain rounded border border-slate-700 select-none shadow-md"
          />

          {/* SVG Bounding Boxes Overlay */}
          {showBoxes && naturalDimensions && displayedDimensions.width > 0 && (
            <svg
              className="absolute top-0 left-0 w-full h-full pointer-events-auto"
              viewBox={`0 0 ${displayedDimensions.width} ${displayedDimensions.height}`}
            >
              {bboxItems.map((ev) => {
                const bbox = ev.bounding_box as BoundingBox;
                const scaledX = bbox.x * scaleX;
                const scaledY = bbox.y * scaleY;
                const scaledW = bbox.width * scaleX;
                const scaledH = bbox.height * scaleY;

                // Check if this box corresponds to the active selected field
                const isFieldActive =
                  selectedFieldName &&
                  ev.description?.toLowerCase().includes(selectedFieldName.toLowerCase());
                const isHovered = hoveredEvidenceId === ev.id;

                const isBarcode = ev.description?.toLowerCase().includes('barcode');
                const strokeColor = isFieldActive
                  ? '#F59E0B' // Amber / Golden for active selection
                  : isBarcode
                  ? '#A855F7' // Purple / Violet for Barcode
                  : isHovered
                  ? '#38BDF8' // Sky blue on hover
                  : '#10B981'; // Emerald green default

                const fillColor = isFieldActive
                  ? 'rgba(245, 158, 11, 0.25)'
                  : isBarcode
                  ? 'rgba(168, 85, 247, 0.2)'
                  : isHovered
                  ? 'rgba(56, 189, 248, 0.2)'
                  : 'rgba(16, 185, 129, 0.12)';

                return (
                  <g
                    key={ev.id}
                    className="cursor-pointer transition-all"
                    onMouseEnter={() => setHoveredEvidenceId(ev.id)}
                    onMouseLeave={() => setHoveredEvidenceId(null)}
                    onClick={() => onSelectEvidence && onSelectEvidence(ev)}
                  >
                    <rect
                      x={scaledX}
                      y={scaledY}
                      width={scaledW}
                      height={scaledH}
                      fill={fillColor}
                      stroke={strokeColor}
                      strokeWidth={isFieldActive || isHovered ? 2.5 : 1.5}
                      rx={3}
                    />
                    {/* Bounding box label pill */}
                    {(isFieldActive || isHovered) && (
                      <foreignObject
                        x={Math.max(0, scaledX)}
                        y={Math.max(0, scaledY - 24)}
                        width={240}
                        height={24}
                      >
                        <div className="bg-slate-900/95 text-white text-[10px] font-mono px-2 py-0.5 rounded shadow border border-slate-700 truncate w-fit max-w-[230px]">
                          {ev.description || 'OCR Token Region'}
                        </div>
                      </foreignObject>
                    )}
                  </g>
                );
              })}
            </svg>
          )}
        </div>
      </div>

      {/* Footer Info */}
      <div className="bg-slate-800/80 px-4 py-2 border-t border-slate-700 flex justify-between text-[11px] text-slate-400">
        <span>Natural: {naturalDimensions ? `${naturalDimensions.width} × ${naturalDimensions.height}px` : 'Loading...'}</span>
        <span>Zoom: {Math.round(zoomLevel * 100)}%</span>
      </div>
    </div>
  );
}

