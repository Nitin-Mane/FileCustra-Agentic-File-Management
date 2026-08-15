import React, { useState } from 'react';
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Database,
  FolderOpen,
  HardDrive,
  HelpCircle,
  LockKeyhole,
  MemoryStick,
  MonitorCog,
  RefreshCw,
  Settings,
  ShieldCheck,
  Sparkles,
  Terminal,
} from 'lucide-react';
import { SystemSnapshot, HardwareMetric } from '../../types';

interface DriveDashboardViewProps {
  onOpenWorkspace: () => void;
  onOpenSecuritySettings?: () => void;
  systemSnapshot?: SystemSnapshot;
}

const hardwareIconMap: Record<string, React.ElementType> = {
  cpu: Cpu,
  gpu: MonitorCog,
  ram: MemoryStick,
  runtime: Activity,
};

const statusLabel: Record<HardwareMetric['status'], string> = {
  GOOD: 'Ready',
  WARN: 'Watch',
  ACTION: 'Action',
};

const percent = (used: number, total: number) => (total === 0 ? 0 : Math.round((used / total) * 100));

export const DriveDashboardView: React.FC<DriveDashboardViewProps> = ({
  onOpenWorkspace,
  onOpenSecuritySettings,
  systemSnapshot,
}) => {
  const [highlightedDrive, setHighlightedDrive] = useState<string | null>(null);
  const [snapshotReloadTick, setSnapshotReloadTick] = useState(0);
  const isLiveSnapshot = Boolean(systemSnapshot);

  const drives = systemSnapshot?.drives || [
    { letter: 'C:\\', name: 'System Drive', usedGb: 452.4, totalGb: 1024.0, freeGb: 571.6, health: 'Fallback', type: 'Local Fixed NVMe', color: 'var(--accent-aqua)' },
    { letter: 'D:\\', name: 'Development Drive', usedGb: 1120.8, totalGb: 2048.0, freeGb: 927.2, health: 'Fallback', type: 'Project Storage', color: 'var(--accent-violet)' },
    { letter: 'E:\\', name: 'Archive Drive', usedGb: 2840.0, totalGb: 4096.0, freeGb: 1256.0, health: 'Fallback', type: 'External Backup', color: 'var(--accent-mint)' },
  ];

  const hardware = systemSnapshot?.hardware || [
    { id: 'cpu', label: 'Processor', value: 'Unavailable', detail: 'Live system snapshot was not loaded.', utilizationPct: 0, status: 'WARN' as const },
    { id: 'gpu', label: 'GPU / Accelerator', value: 'Not checked', detail: 'Acceleration status requires runtime snapshot.', utilizationPct: 0, status: 'WARN' as const },
    { id: 'ram', label: 'Memory', value: 'Not checked', detail: 'Memory capacity requires runtime snapshot.', utilizationPct: 0, status: 'WARN' as const },
    { id: 'runtime', label: 'Runtime', value: 'Fallback mode', detail: 'Dashboard is using static fallback telemetry.', utilizationPct: 0, status: 'WARN' as const },
  ];

  const totalCapacity = drives.reduce((sum, d) => sum + d.totalGb, 0);
  const freeCapacity = drives.reduce((sum, d) => sum + d.freeGb, 0);
  const usedCapacity = totalCapacity - freeCapacity;
  const freePct = 100 - percent(usedCapacity, totalCapacity);
  const activeDrive = drives.find((drive) => drive.letter === highlightedDrive) || drives[0];

  return (
    <div className="template-shell dashboard-template-shell">
      <aside className="template-sidebar" aria-label="FileCustra dashboard navigation">
        <div className="template-brand">
          <div className="template-brand-mark">
            <ShieldCheck size={22} />
          </div>
          <div>
            <strong>FileCustra</strong>
            <span>Local-First Secure</span>
          </div>
        </div>

        <nav className="template-nav">
          <button className="active" type="button">
            <Database size={17} />
            Dashboard
          </button>
          <button type="button" onClick={onOpenWorkspace}>
            <FolderOpen size={17} />
            Workspace
          </button>
          <button type="button">
            <Terminal size={17} />
            Logs
          </button>
          <button type="button" onClick={onOpenSecuritySettings}>
            <ShieldCheck size={17} />
            Security
          </button>
        </nav>

        <button className="template-primary-nav-action" onClick={onOpenWorkspace} type="button">
          <FolderOpen size={16} />
          Open Workspace
        </button>

        <div className="template-sidebar-footer">
          <button type="button" onClick={onOpenSecuritySettings}>
            <Settings size={16} />
            Settings
          </button>
          <button type="button">
            <HelpCircle size={16} />
            Help
          </button>
        </div>
      </aside>

      <main className="template-main dashboard-template-main">
        <header className="template-page-header">
          <div>
            <span className="template-live-kicker">
              <i />
              {isLiveSnapshot ? 'Live System Snapshot' : 'Fallback Snapshot'}
            </span>
            <h1>Command Center</h1>
            <p>Storage, compute, privacy, and backend readiness before file actions.</p>
          </div>
          <div className="template-header-actions">
            <span className="template-agent-chip">
              <Activity size={15} />
              Runtime: {systemSnapshot?.runtime.sidecarStatus || 'Fallback'}
            </span>
            <button type="button" onClick={() => setSnapshotReloadTick((tick) => tick + 1)}>
              <RefreshCw size={16} />
              Refresh View
            </button>
          </div>
        </header>

        <section className="template-dashboard-grid" key={snapshotReloadTick}>
          <div className="template-glass-card template-storage-orbit">
            <div className="template-card-head">
              <div>
                <span>Storage Orbital</span>
                <strong>Physical volumes and headroom</strong>
              </div>
              <span className="template-state-pill">{drives.length} drives</span>
            </div>

            <div className="template-orbit-stage" aria-label="Storage headroom visualization">
              <div className="template-orbit-core">
                <ShieldCheck size={28} />
                <strong>{freePct}%</strong>
                <span>free</span>
              </div>
              {drives.slice(0, 8).map((drive, index) => (
                <button
                  key={drive.letter}
                  className={`template-drive-node template-drive-node-${(index % 8) + 1} ${highlightedDrive === drive.letter ? 'active' : ''}`}
                  onMouseEnter={() => setHighlightedDrive(drive.letter)}
                  onFocus={() => setHighlightedDrive(drive.letter)}
                  onMouseLeave={() => setHighlightedDrive(null)}
                  onBlur={() => setHighlightedDrive(null)}
                  type="button"
                >
                  {drive.letter.replace('\\', '')}
                </button>
              ))}
              <div className="template-orbit-ring one" />
              <div className="template-orbit-ring two" />
            </div>

            {activeDrive && (
              <div className="template-active-drive">
                <span>{activeDrive.letter} {activeDrive.name}</span>
                <strong>{Math.round(activeDrive.freeGb).toLocaleString()} GB free</strong>
                <small>{activeDrive.type} | {percent(activeDrive.usedGb, activeDrive.totalGb)}% used</small>
              </div>
            )}
          </div>

          <div className="template-glass-card template-readiness-panel">
            <div className="template-card-head">
              <div>
                <span>Backend Readiness</span>
                <strong>Functional safety gates</strong>
              </div>
              <span className={`template-state-pill ${isLiveSnapshot ? 'safe' : 'warn'}`}>
                {isLiveSnapshot ? 'live' : 'fallback'}
              </span>
            </div>

            <div className="template-readiness-list">
              <div>
                <ShieldCheck size={18} />
                <span>Privacy mode</span>
                <strong>{systemSnapshot?.runtime.privacyMode || 'OFFLINE_LOCKED'}</strong>
              </div>
              <div>
                <Database size={18} />
                <span>Indexed files</span>
                <strong>{systemSnapshot?.runtime.indexedFiles ?? 0}</strong>
              </div>
              <div>
                <Activity size={18} />
                <span>Queued tasks</span>
                <strong>{systemSnapshot?.runtime.queuedTasks ?? 0}</strong>
              </div>
              <div>
                <Sparkles size={18} />
                <span>Model runtime</span>
                <strong>{systemSnapshot?.runtime.modelRuntime || 'Readiness not checked'}</strong>
              </div>
            </div>
          </div>

          <div className="template-metric-row">
            <article>
              <HardDrive size={19} />
              <span>Detected Drives</span>
              <strong>{drives.length} Volumes</strong>
              <small>{Math.round(totalCapacity).toLocaleString()} GB total</small>
            </article>
            <article>
              <Database size={19} />
              <span>Free Headroom</span>
              <strong>{Math.round(freeCapacity).toLocaleString()} GB</strong>
              <small>{freePct}% available</small>
            </article>
            <article>
              <Cpu size={19} />
              <span>Processor Lane</span>
              <strong>{hardware.find((item) => item.id === 'cpu')?.value || 'Not checked'}</strong>
              <small>{hardware.find((item) => item.id === 'cpu')?.detail || 'Runtime snapshot required'}</small>
            </article>
            <article>
              <MonitorCog size={19} />
              <span>GPU / Accelerator</span>
              <strong>{hardware.find((item) => item.id === 'gpu')?.value || 'Not checked'}</strong>
              <small>{hardware.find((item) => item.id === 'gpu')?.detail || 'Runtime snapshot required'}</small>
            </article>
          </div>

          <div className="template-glass-card template-drive-list">
            <div className="template-card-head">
              <div>
                <span>Volume Table</span>
                <strong>Drive usage breakdown</strong>
              </div>
            </div>
            <div className="template-table-list">
              {drives.map((drive) => {
                const driveUsedPct = percent(drive.usedGb, drive.totalGb);
                const active = highlightedDrive === drive.letter;
                return (
                  <button
                    key={drive.letter}
                    className={active ? 'active' : ''}
                    onMouseEnter={() => setHighlightedDrive(drive.letter)}
                    onFocus={() => setHighlightedDrive(drive.letter)}
                    onMouseLeave={() => setHighlightedDrive(null)}
                    onBlur={() => setHighlightedDrive(null)}
                    type="button"
                  >
                    <span>{drive.letter}</span>
                    <strong>{drive.name}</strong>
                    <i><b style={{ width: `${driveUsedPct}%` }} /></i>
                    <small>{drive.freeGb.toLocaleString()} GB free / {drive.totalGb.toLocaleString()} GB total</small>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="template-glass-card template-hardware-list">
            <div className="template-card-head">
              <div>
                <span>Compute Lanes</span>
                <strong>Processor, GPU, memory, runtime</strong>
              </div>
            </div>
            <div className="template-hardware-grid">
              {hardware.map((item) => {
                const Icon = hardwareIconMap[item.id] ?? Activity;
                return (
                  <article key={item.id}>
                    <Icon size={18} />
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                    <small>{item.detail}</small>
                    <em>{statusLabel[item.status]}</em>
                  </article>
                );
              })}
            </div>
          </div>

          <div className="template-module-row">
            <button onClick={onOpenSecuritySettings} type="button">
              <LockKeyhole size={21} />
              <strong>Hardware Privacy Lock</strong>
              <span>Configure offline policy and processing boundaries.</span>
            </button>
            <button onClick={onOpenSecuritySettings} type="button">
              <CheckCircle2 size={21} />
              <strong>Mandatory Dry-Run Gate</strong>
              <span>Preview and verify planned moves before execution.</span>
            </button>
            <button onClick={onOpenSecuritySettings} type="button">
              <Database size={21} />
              <strong>Rollback Journal</strong>
              <span>Native move transactions create rollback records.</span>
            </button>
            <button className="primary" onClick={onOpenWorkspace} type="button">
              <FolderOpen size={21} />
              <strong>Open Workspace</strong>
              <span>Select a folder and start a real backend scan.</span>
              <ArrowRight size={17} />
            </button>
          </div>
        </section>
      </main>
    </div>
  );
};
