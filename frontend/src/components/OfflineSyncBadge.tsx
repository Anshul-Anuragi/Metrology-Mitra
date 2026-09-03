'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { OfflineInspectionItem, OfflineSyncBatchRequest } from '@/types';
import { Wifi, WifiOff, RefreshCw, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function OfflineSyncBadge() {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [syncSuccess, setSyncSuccess] = useState<string | null>(null);

  useEffect(() => {
    setIsOnline(navigator.onLine);

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Check localStorage queue
    checkLocalQueue();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const checkLocalQueue = () => {
    try {
      const raw = localStorage.getItem('metrologymitra_offline_queue');
      if (raw) {
        const list = JSON.parse(raw);
        setPendingCount(Array.isArray(list) ? list.length : 0);
      } else {
        setPendingCount(0);
      }
    } catch {
      setPendingCount(0);
    }
  };

  const handleSyncNow = async () => {
    if (pendingCount === 0 || !isOnline) return;
    setSyncing(true);
    setSyncSuccess(null);
    try {
      const raw = localStorage.getItem('metrologymitra_offline_queue');
      if (!raw) return;
      const list: OfflineInspectionItem[] = JSON.parse(raw);
      if (list.length === 0) return;

      const payload: OfflineSyncBatchRequest = {
        device_id: navigator.userAgent.slice(0, 30),
        offline_inspections: list,
      };

      const res = await api.syncOfflineInspections(payload);
      localStorage.removeItem('metrologymitra_offline_queue');
      setPendingCount(0);
      setSyncSuccess(`Successfully synced ${res.synced_count} offline inspections!`);
      setTimeout(() => setSyncSuccess(null), 4000);
    } catch (err: any) {
      console.error('Offline sync failed:', err);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="flex items-center gap-2 text-xs">
      {/* Online/Offline Status Indicator */}
      <div
        className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold border transition ${
          isOnline
            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
            : 'bg-rose-50 text-rose-700 border-rose-200'
        }`}
        title={isOnline ? 'Online: Live Sync Active' : 'Offline: Local Drafting Mode'}
      >
        {isOnline ? <Wifi className="h-3.5 w-3.5 text-emerald-600" /> : <WifiOff className="h-3.5 w-3.5 text-rose-600" />}
        <span>{isOnline ? 'ONLINE' : 'OFFLINE'}</span>
      </div>

      {/* Pending Sync Count & Sync Trigger */}
      {pendingCount > 0 && (
        <button
          onClick={handleSyncNow}
          disabled={syncing || !isOnline}
          className="flex items-center gap-1.5 px-3 py-1 bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 rounded-full text-[11px] font-bold transition disabled:opacity-50"
        >
          <RefreshCw className={`h-3 w-3 ${syncing ? 'animate-spin' : ''}`} />
          <span>{syncing ? 'Syncing...' : `Sync Queue (${pendingCount})`}</span>
        </button>
      )}

      {syncSuccess && (
        <span className="text-[11px] text-emerald-700 font-bold flex items-center gap-1">
          <CheckCircle2 className="h-3.5 w-3.5" />
          {syncSuccess}
        </span>
      )}
    </div>
  );
}

