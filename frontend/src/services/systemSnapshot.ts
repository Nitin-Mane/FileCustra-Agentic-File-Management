import { SystemSnapshot } from '../types';

export const phaseOneSystemSnapshot: SystemSnapshot = {
  runtime: {
    sidecarStatus: 'READY',
    privacyMode: 'OFFLINE_LOCKED',
    hardwareSummary: 'DirectML / CPU fallback ready',
    modelRuntime: 'Magika route prepared, Gemma local lane queued',
    indexedFiles: 5,
    queuedTasks: 3,
  },
  drives: [
    {
      letter: 'C:\\',
      name: 'System Drive',
      usedGb: 452.4,
      totalGb: 1024.0,
      freeGb: 571.6,
      color: 'var(--accent-aqua)',
      type: 'Local Fixed NVMe',
      health: 'Healthy',
    },
    {
      letter: 'D:\\',
      name: 'Development Drive',
      usedGb: 1120.8,
      totalGb: 2048.0,
      freeGb: 927.2,
      color: 'var(--accent-violet)',
      type: 'Project Storage',
      health: 'Healthy',
    },
    {
      letter: 'E:\\',
      name: 'Archive Drive',
      usedGb: 2840.0,
      totalGb: 4096.0,
      freeGb: 1256.0,
      color: 'var(--accent-mint)',
      type: 'External Backup',
      health: 'Good',
    },
  ],
  hardware: [
    {
      id: 'cpu',
      label: 'Processor',
      value: '16 logical threads',
      detail: 'Balanced analysis queue for hashing, metadata, and parser workers',
      utilizationPct: 38,
      status: 'GOOD',
    },
    {
      id: 'gpu',
      label: 'GPU / Accelerator',
      value: 'DirectML ready',
      detail: 'Local model inference lane prepared for Gemma and embeddings',
      utilizationPct: 24,
      status: 'GOOD',
    },
    {
      id: 'ram',
      label: 'Memory',
      value: '32 GB installed',
      detail: 'Parser workers and vector cache run with bounded concurrency',
      utilizationPct: 46,
      status: 'GOOD',
    },
    {
      id: 'runtime',
      label: 'Runtime',
      value: 'Python sidecar + Tauri shell',
      detail: 'JSON-RPC health checks active over local process boundary',
      utilizationPct: 18,
      status: 'GOOD',
    },
  ],
  security: [
    {
      id: 'privacy-lock',
      label: 'Privacy Lock',
      state: 'Enabled',
      detail: 'Processing stays local; cloud sync and telemetry remain off.',
      enabled: true,
    },
    {
      id: 'dry-run',
      label: 'Dry-run required',
      state: 'Required',
      detail: 'Every move, copy, or rename must be previewed before execution.',
      enabled: true,
    },
    {
      id: 'journal',
      label: 'Rollback journal',
      state: 'Prepared',
      detail: 'Operation logs are reserved for restore and verification workflows.',
      enabled: true,
    },
    {
      id: 'network',
      label: 'Network policy',
      state: 'Blocked during analysis',
      detail: 'Model downloads are explicit; folder analysis does not require network access.',
      enabled: true,
    },
  ],
  settings: [
    {
      id: 'scan-depth',
      label: 'Scan depth',
      value: 'Nested folders enabled',
      detail: 'Subfolders are included in the read-only discovery pass.',
    },
    {
      id: 'model-lane',
      label: 'Model lane',
      value: 'Balanced local inference',
      detail: 'Use CPU fallback when GPU capacity is reserved or unavailable.',
    },
    {
      id: 'motion',
      label: 'Motion',
      value: 'Adaptive',
      detail: 'Animations respect reduced-motion preferences.',
    },
    {
      id: 'retention',
      label: 'Journal retention',
      value: '30 days',
      detail: 'Rollback records are kept locally for recent sessions.',
    },
  ],
  phaseOneMilestones: [
    {
      id: 'p01-01',
      title: 'Product shell',
      description: 'Readable startup sequence, privacy promise, and first dashboard path.',
      status: 'DONE',
    },
    {
      id: 'p01-02',
      title: 'Backend pulse',
      description: 'Sidecar reports runtime health, drives, and workspace phase status.',
      status: 'ACTIVE',
    },
    {
      id: 'p01-03',
      title: 'Safe scan path',
      description: 'Discovery starts read-only analysis before dry-run or execution.',
      status: 'NEXT',
    },
  ],
};

export const loadSystemSnapshot = async (): Promise<SystemSnapshot> => {
  try {
    const response = await fetch('/system-snapshot.json', { cache: 'no-store' });
    if (response.ok) {
      const raw = await response.json();
      if (raw.drives && raw.drives.length) {
        return {
          ...phaseOneSystemSnapshot,
          drives: raw.drives.map((d: any) => ({
            letter: d.letter,
            name: d.name,
            usedGb: d.used_gb,
            totalGb: d.total_gb,
            freeGb: d.free_gb,
            color: d.color === 'aqua' ? 'var(--accent-aqua)' : d.color === 'violet' ? 'var(--accent-violet)' : 'var(--accent-mint)',
            type: d.type || 'Local Storage',
            health: d.health || 'available',
          })),
          hardware: raw.hardware.map((h: any) => ({
            id: h.id,
            label: h.label,
            value: h.value,
            detail: h.detail,
            utilizationPct: h.utilization_pct,
            status: h.status as any,
          })),
          runtime: {
            sidecarStatus: raw.runtime.sidecar_status || 'READY',
            privacyMode: raw.runtime.privacy_mode || 'OFFLINE_LOCKED',
            hardwareSummary: raw.runtime.hardware_summary || 'Intel UHD Graphics + 16-Core CPU',
            modelRuntime: raw.runtime.model_runtime || 'Magika route prepared',
            indexedFiles: raw.runtime.indexed_files || 51,
            queuedTasks: raw.runtime.queued_tasks || 3,
          },
        };
      }
    }
  } catch (e) {
    console.warn('Unable to load live system-snapshot.json, using fallback snapshot', e);
  }
  return phaseOneSystemSnapshot;
};

