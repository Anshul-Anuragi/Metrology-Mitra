'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { ImageType } from '@/types';
import {
  PlusCircle,
  MapPin,
  Camera,
  Upload,
  Sparkles,
  Trash2,
  AlertCircle,
  Building2,
  Navigation,
} from 'lucide-react';

interface UploadQueueItem {
  file: File;
  previewUrl: string;
  imageType: ImageType;
}

export default function NewInspectionPage() {
  const { user } = useAuth();
  const router = useRouter();

  // Store metadata
  const [storeName, setStoreName] = useState('');
  const [storeAddress, setStoreAddress] = useState('');
  const [district, setDistrict] = useState('');
  const [state, setState] = useState('DL');
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [gpsStatus, setGpsStatus] = useState<string | null>(null);

  // Images queue
  const [imagesQueue, setImagesQueue] = useState<UploadQueueItem[]>([]);
  const [selectedImageType, setSelectedImageType] = useState<ImageType>('LABEL');

  // Processing state
  const [processingStage, setProcessingStage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Geolocation trigger
  const handleGetLocation = () => {
    setGpsStatus('Acquiring satellite GPS fix...');
    if (!navigator.geolocation) {
      setGpsStatus('Geolocation not supported on this device/browser.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude);
        setLongitude(position.coords.longitude);
        setGpsStatus(`GPS Captured: ${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`);
      },
      (err) => {
        setGpsStatus(`GPS unavailable (${err.message}). Continuing manually.`);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  // Image selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const previewUrl = URL.createObjectURL(file);
      setImagesQueue((prev) => [
        ...prev,
        {
          file,
          previewUrl,
          imageType: selectedImageType,
        },
      ]);
      e.target.value = ''; // Reset input
    }
  };

  const handleRemoveImage = (index: number) => {
    setImagesQueue((prev) => {
      const copy = [...prev];
      URL.revokeObjectURL(copy[index].previewUrl);
      copy.splice(index, 1);
      return copy;
    });
  };

  // Run full workflow
  const handleRunPipeline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (imagesQueue.length === 0) {
      setError('Please add at least one package photograph (Label, Front, or Back) before running the pipeline.');
      return;
    }

    setError(null);
    try {
      // Step 1: Create Inspection
      setProcessingStage('1/3: Initializing official inspection session...');
      const createdInsp = await api.createInspection({
        store_name: storeName.trim() || 'Retail Outlet',
        store_address: storeAddress.trim() || undefined,
        district: district.trim() || undefined,
        state: state.trim() || 'DL',
        gps_latitude: latitude || undefined,
        gps_longitude: longitude || undefined,
      });

      // Step 2: Upload Images
      setProcessingStage(`2/3: Uploading ${imagesQueue.length} package photographs...`);
      for (let i = 0; i < imagesQueue.length; i++) {
        const item = imagesQueue[i];
        await api.uploadImage(createdInsp.id, item.file, item.imageType, i + 1);
      }

      // Step 3: Run Full Pipeline (OCR -> Extraction -> Legal Rule Engine -> Violations -> Evidence)
      setProcessingStage('3/3: Running Tesseract OCR & Deterministic LMPC Rule Engine...');
      await api.runPipeline(createdInsp.id);

      // Route to inspection workspace
      router.push(`/inspections/${createdInsp.id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'An error occurred during pipeline execution.');
      setProcessingStage(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
          <PlusCircle className="h-6 w-6 text-brand-900" />
          New Packaged Commodity Inspection
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Capture retail establishment metadata and package photographs for automated LMPC 2011 statutory compliance analysis.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Flow Form */}
      <form onSubmit={handleRunPipeline} className="space-y-6">
        {/* STEP 1: Store & Geolocation */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 pb-3 border-b border-slate-100">
            <Building2 className="h-4 w-4 text-brand-900" />
            Step 1: Retail Store & Geolocation Metadata
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Store / Establishment Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Central Mega Mart, Super Bazaar"
                value={storeName}
                onChange={(e) => setStoreName(e.target.value)}
                className="w-full text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">State / UT Code</label>
              <input
                type="text"
                required
                maxLength={2}
                placeholder="e.g. DL, MH, KA, TN, UP"
                value={state}
                onChange={(e) => setState(e.target.value.toUpperCase())}
                className="w-full text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none uppercase font-mono font-bold"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">District</label>
              <input
                type="text"
                placeholder="e.g. Central Delhi, Pune, Bengaluru Urban"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="w-full text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Store Address / Locality</label>
              <input
                type="text"
                placeholder="Market, Shop No, Street address"
                value={storeAddress}
                onChange={(e) => setStoreAddress(e.target.value)}
                className="w-full text-xs px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl focus:bg-white focus:ring-1 focus:ring-sky-500 focus:outline-none"
              />
            </div>
          </div>

          {/* GPS Coordinates Button */}
          <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
            <div className="text-xs text-slate-600 flex items-center gap-2">
              <MapPin className="h-4 w-4 text-sky-600 shrink-0" />
              <span>
                {latitude && longitude
                  ? `Lat: ${latitude.toFixed(6)}, Lng: ${longitude.toFixed(6)}`
                  : gpsStatus || 'GPS coordinates not captured.'}
              </span>
            </div>

            <button
              type="button"
              onClick={handleGetLocation}
              className="bg-white hover:bg-slate-100 text-slate-800 text-xs font-semibold px-3.5 py-2 rounded-lg border border-slate-300 flex items-center gap-1.5 shadow-sm transition-colors"
            >
              <Navigation className="h-3.5 w-3.5 text-sky-600" />
              Use My Location
            </button>
          </div>
        </div>

        {/* STEP 2: Package Photographs */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
          <div className="flex justify-between items-center pb-3 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <Camera className="h-4 w-4 text-brand-900" />
              Step 2: Multi-Angle Package Photographs ({imagesQueue.length})
            </h2>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Angle Type:</span>
              <select
                value={selectedImageType}
                onChange={(e) => setSelectedImageType(e.target.value as ImageType)}
                className="text-xs px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none font-semibold text-slate-800"
              >
                <option value="LABEL">Principal Label Panel</option>
                <option value="FRONT">Front Face</option>
                <option value="BACK">Back Face</option>
                <option value="SIDE">Side Panel</option>
                <option value="OTHER">Other Angle</option>
              </select>
            </div>
          </div>

          {/* Upload Dropzone / Button */}
          <div className="border-2 border-dashed border-slate-300 hover:border-sky-500 rounded-2xl p-6 text-center bg-slate-50/60 transition-colors">
            <input
              type="file"
              accept="image/*"
              capture="environment"
              id="package-file-input"
              onChange={handleFileSelect}
              className="hidden"
            />
            <label
              htmlFor="package-file-input"
              className="cursor-pointer flex flex-col items-center justify-center space-y-2"
            >
              <div className="p-3 bg-white rounded-full shadow-sm border border-slate-200">
                <Upload className="h-6 w-6 text-sky-600" />
              </div>
              <div className="text-xs font-bold text-slate-800">
                Click to Take Photo or Select Package Image
              </div>
              <p className="text-[11px] text-slate-400">
                Select JPEG, PNG, or WEBP. Upload multiple angles for thorough declaration extraction.
              </p>
            </label>
          </div>

          {/* Image Queue Thumbnails */}
          {imagesQueue.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              {imagesQueue.map((item, index) => (
                <div
                  key={index}
                  className="relative group bg-slate-100 rounded-xl overflow-hidden border border-slate-200 shadow-sm"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={item.previewUrl}
                    alt={`Upload preview ${index + 1}`}
                    className="h-32 w-full object-cover"
                  />
                  <div className="p-2 bg-white flex justify-between items-center text-[11px]">
                    <span className="font-bold text-slate-700 uppercase font-mono">{item.imageType}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveImage(index)}
                      className="text-rose-600 hover:text-rose-800 p-1 rounded"
                      title="Remove image"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* STEP 3: Automated Pipeline Execution */}
        <div className="bg-brand-900 text-white p-6 rounded-2xl shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-sky-400" />
              Automated Statutory Compliance Pipeline
            </h3>
            <p className="text-xs text-slate-300 mt-1">
              Executes image preprocessing, Tesseract 5 OCR extraction, and deterministic LMPC 2011 rule evaluation.
            </p>
          </div>

          <button
            type="submit"
            disabled={processingStage !== null}
            className="w-full sm:w-auto bg-sky-500 hover:bg-sky-400 text-brand-950 font-black text-xs px-6 py-3.5 rounded-xl shadow-md transition-all flex items-center justify-center gap-2 shrink-0 disabled:opacity-50"
          >
            {processingStage ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin h-4 w-4 border-2 border-brand-950 border-t-transparent rounded-full" />
                {processingStage}
              </span>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Run Automated Compliance Pipeline
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

