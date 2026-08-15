import { SystemSnapshot } from '../types';
import { phaseOneSystemSnapshot } from './systemSnapshot';

type RawRuntimeSnapshot = {
  sidecar_status?: string;
  privacy_mode?: string;
  hardware_summary?: string;
  model_runtime?: string;
  indexed_files?: number;
  queued_tasks?: number;
};

type RawDriveSnapshot = {
  letter?: string;
  name?: string;
  used_gb?: number;
  total_gb?: number;
  free_gb?: number;
  color?: string;
  type?: string;
  health?: string;
};

type RawHardwareMetric = {
  id?: string;
  label?: string;
  value?: string;
  detail?: string;
  utilization_pct?: number;
  status?: string;
};

type RawSecurityControl = {
  id?: string;
  label?: string;
  state?: string;
  detail?: string;
  enabled?: boolean;
};

type RawSettingsControl = {
  id?: string;
  label?: string;
  value?: string;
  detail?: string;
};

type RawSystemSnapshot = {
  runtime?: RawRuntimeSnapshot;
  drives?: RawDriveSnapshot[];
  hardware?: RawHardwareMetric[];
  security?: RawSecurityControl[];
  settings?: RawSettingsControl[];
};

const colorMap: Record<string, string> = {
  aqua: 'var(--accent-aqua)',
  violet: 'var(--accent-violet)',
  mint: 'var(--accent-mint)',
  coral: 'var(--accent-coral)',
};

const normalizeStatus = (status?: string) => {
  if (status === 'WARN' || status === 'ACTION') {
    return status;
  }
  return 'GOOD';
};

const normalizeRuntimeStatus = (status?: string) => {
  if (status === 'BOOTING' || status === 'DEGRADED') {
    return status;
  }
  return 'READY';
};

export const normalizeSystemSnapshot = (raw: RawSystemSnapshot): SystemSnapshot => ({
  ...phaseOneSystemSnapshot,
  runtime: {
    sidecarStatus: normalizeRuntimeStatus(raw.runtime?.sidecar_status),
    privacyMode: raw.runtime?.privacy_mode === 'ONLINE_ALLOWED' ? 'ONLINE_ALLOWED' : 'OFFLINE_LOCKED',
    hardwareSummary: raw.runtime?.hardware_summary || phaseOneSystemSnapshot.runtime.hardwareSummary,
    modelRuntime: raw.runtime?.model_runtime || phaseOneSystemSnapshot.runtime.modelRuntime,
    indexedFiles: raw.runtime?.indexed_files ?? phaseOneSystemSnapshot.runtime.indexedFiles,
    queuedTasks: raw.runtime?.queued_tasks ?? phaseOneSystemSnapshot.runtime.queuedTasks,
  },
  drives: raw.drives?.length
    ? raw.drives.map((drive, index) => ({
        letter: drive.letter || `Drive ${index + 1}`,
        name: drive.name || 'Attached Storage',
        usedGb: drive.used_gb ?? 0,
        totalGb: drive.total_gb ?? 0,
        freeGb: drive.free_gb ?? 0,
        color: colorMap[drive.color || ''] || drive.color || 'var(--accent-aqua)',
        type: drive.type || 'Local Volume',
        health: drive.health || 'available',
      }))
    : phaseOneSystemSnapshot.drives,
  hardware: raw.hardware?.length
    ? raw.hardware.map((item) => ({
        id: item.id || item.label || 'hardware',
        label: item.label || 'Hardware',
        value: item.value || 'Unavailable',
        detail: item.detail || 'Runtime data unavailable.',
        utilizationPct: item.utilization_pct,
        status: normalizeStatus(item.status),
      }))
    : phaseOneSystemSnapshot.hardware,
  security: raw.security?.length
    ? raw.security.map((item) => ({
        id: item.id || item.label || 'security',
        label: item.label || 'Security control',
        state: item.state || 'Unknown',
        detail: item.detail || 'No detail available.',
        enabled: item.enabled ?? false,
      }))
    : phaseOneSystemSnapshot.security,
  settings: raw.settings?.length
    ? raw.settings.map((item) => ({
        id: item.id || item.label || 'setting',
        label: item.label || 'Setting',
        value: item.value || 'Unset',
        detail: item.detail || 'No detail available.',
      }))
    : phaseOneSystemSnapshot.settings,
});

export const loadRuntimeSystemSnapshot = async (): Promise<SystemSnapshot> => {
  const response = await fetch('/system-snapshot.json', { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Runtime snapshot unavailable: ${response.status}`);
  }
  const raw = (await response.json()) as RawSystemSnapshot;
  return normalizeSystemSnapshot(raw);
};
