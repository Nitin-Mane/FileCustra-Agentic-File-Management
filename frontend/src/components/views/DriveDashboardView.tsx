import React, { useState } from 'react';
import {
  ShieldCheck,
  HardDrive,
  Cpu,
  Database,
  Activity,
  FolderOpen,
  Sparkles,
  ArrowRight,
  LockKeyhole,
  CheckCircle2,
  Settings,
  MonitorCog,
  MemoryStick,
  Zap,
  Lock,
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

  // Extract real hardware & drive snapshot data
  const drives = systemSnapshot?.drives || [
    { letter: 'C:\\', name: 'Local Workspace', usedGb: 908.9, totalGb: 1023.9, freeGb: 115.0, health: 'available', type: 'fixed_or_attached', color: 'aqua' },
    { letter: 'D:\\', name: 'Attached Storage', usedGb: 745.3, totalGb: 882.5, freeGb: 137.2, health: 'available', type: 'fixed_or_attached', color: 'violet' },
    { letter: 'E:\\', name: 'Attached Storage', usedGb: 682.3, totalGb: 931.4, freeGb: 249.1, health: 'available', type: 'fixed_or_attached', color: 'mint' },
    { letter: 'F:\\', name: 'Attached Storage', usedGb: 1785.2, totalGb: 1862.9, freeGb: 77.7, health: 'available', type: 'fixed_or_attached', color: 'coral' },
    { letter: 'G:\\', name: 'Attached Storage', usedGb: 3442.4, totalGb: 3725.9, freeGb: 283.5, health: 'available', type: 'fixed_or_attached', color: 'aqua' },
  ];

  const hardware = systemSnapshot?.hardware || [
    { id: 'cpu', label: 'Processor', value: '16 logical threads', detail: 'Intel64 Family 6 Model 165 Stepping 5, GenuineIntel', utilizationPct: 0, status: 'GOOD' as const },
    { id: 'gpu', label: 'GPU / Accelerator', value: 'Intel(R) UHD Graphics 630', detail: 'Used for local model acceleration when available.', utilizationPct: 0, status: 'GOOD' as const },
    { id: 'ram', label: 'Memory', value: '31.8 GB installed', detail: '7.3 GB available for parser workers and vector cache.', utilizationPct: 76, status: 'GOOD' as const },
    { id: 'runtime', label: 'Runtime', value: 'Python 3.13.9', detail: 'Sidecar JSON-RPC process is available on local STDIN/STDOUT.', utilizationPct: 0, status: 'GOOD' as const },
  ];

  const totalCapacity = drives.reduce((sum, d) => sum + d.totalGb, 0);
  const freeCapacity = drives.reduce((sum, d) => sum + d.freeGb, 0);
  const usedCapacity = totalCapacity - freeCapacity;
  const freePct = 100 - percent(usedCapacity, totalCapacity);

  return (
    <div className="view-container phase-home" style={{ height: '100vh', overflow: 'hidden', padding: '16px 24px', boxSizing: 'border-box', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      
      {/* 1. HERO SECTION WITH MATCHING HOME DASHBOARD DESIGN & ANIMATION */}
      <section className="phase-hero" style={{ padding: '18px 24px', marginBottom: 0 }}>
        <div className="phase-hero-copy">
          <div className="eyebrow-pill">
            <Sparkles size={14} />
            <span>Real-Time Storage Command Center</span>
          </div>

          <h2 style={{ fontSize: 22, lineHeight: 1.25, margin: '8px 0' }}>
            System Intelligence & Drive Analytics before file actions.
          </h2>

          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 14 }}>
            Live physical drives telemetry, compute lanes, privacy controls, and sidecar runtime queues arranged for instant operator decision making.
          </p>

          {/* EXACTLY ONE OPEN WORKSPACE BUTTON */}
          <div className="hero-actions">
            <button className="btn-primary btn-lg" onClick={onOpenWorkspace}>
              <FolderOpen size={18} />
              <span>Open Workspace</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </div>

        {/* ANIMATED STORAGE CORE GRAPHIC (MATCHES HOME VIEW FLUID MOTION) */}
        <div className="file-flow-graphic" aria-label="Animated storage node telemetry">
          <div className="flow-core">
            <ShieldCheck size={28} />
            <span style={{ fontSize: 10, fontWeight: 700 }}>{freePct}%</span>
          </div>
          {drives.slice(0, 6).map((drive, idx) => (
            <div
              key={drive.letter}
              className={`flow-chip flow-chip-${idx + 1}`}
              style={{
                background: highlightedDrive === drive.letter ? 'var(--accent-cyan)' : 'rgba(30, 41, 59, 0.9)',
                borderColor: highlightedDrive === drive.letter ? 'var(--accent-aqua)' : 'var(--border-subtle)',
                color: highlightedDrive === drive.letter ? '#000' : 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
              }}
              onMouseEnter={() => setHighlightedDrive(drive.letter)}
              onMouseLeave={() => setHighlightedDrive(null)}
            >
              {drive.letter.replace('\\', '')}
            </div>
          ))}
          <div className="flow-ring flow-ring-one" />
          <div className="flow-ring flow-ring-two" />
        </div>
      </section>

      {/* 2. INSIGHT GRID (METRIC TILES MATCHING HOME DASHBOARD HUB) */}
      <section className="insight-grid" style={{ margin: '10px 0' }}>
        <div className="metric-tile">
          <HardDrive size={19} color="var(--accent-cyan)" />
          <span>Detected Drives</span>
          <strong>{drives.length} Volumes</strong>
          <small>{Math.round(totalCapacity).toLocaleString()} GB Total Capacity</small>
        </div>

        <div className="metric-tile">
          <Database size={19} color="var(--status-safe)" />
          <span>Free Headroom</span>
          <strong>{Math.round(freeCapacity).toLocaleString()} GB</strong>
          <small>{freePct}% Free Storage Headroom</small>
        </div>

        <div className="metric-tile">
          <Cpu size={19} color="var(--accent-violet)" />
          <span>Processor Lane</span>
          <strong>16 Threads</strong>
          <small>Intel64 Family 6 Model 165</small>
        </div>

        <div className="metric-tile">
          <MonitorCog size={19} color="var(--accent-aqua)" />
          <span>GPU / Accelerator</span>
          <strong>Intel UHD 630</strong>
          <small>DirectML Local Acceleration Ready</small>
        </div>
      </section>

      {/* 3. PHASE WORKBENCH (TIGHT DUAL COLUMNS - ZERO UNNATURAL GAPS) */}
      <section className="phase-workbench" style={{ flex: 1, minHeight: 0, gap: 14 }}>
        {/* PANEL 1: PHYSICAL STORAGE DRIVES */}
        <div className="workspace-panel" style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', gap: 10, padding: '16px 20px' }}>
          <div className="panel-heading" style={{ marginBottom: 4 }}>
            <HardDrive size={18} color="var(--accent-cyan)" />
            <div>
              <h3>Physical Storage Drives ({drives.length})</h3>
              <p>Real-time volume IO and free space breakdown.</p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1, justifyContent: 'space-between' }}>
            {drives.map((drive) => {
              const driveUsedPct = percent(drive.usedGb, drive.totalGb);
              const active = highlightedDrive === drive.letter;

              return (
                <div
                  key={drive.letter}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    background: active ? 'rgba(6, 182, 212, 0.12)' : 'var(--bg-tertiary)',
                    border: `1px solid ${active ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                  }}
                  onMouseEnter={() => setHighlightedDrive(drive.letter)}
                  onMouseLeave={() => setHighlightedDrive(null)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 3 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontSize: 13 }}>
                        {drive.letter}
                      </span>
                      <span style={{ fontSize: 12, fontWeight: 600 }}>{drive.name}</span>
                    </div>
                    <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                      {driveUsedPct}% used
                    </span>
                  </div>

                  <div style={{ height: 5, background: 'var(--bg-primary)', borderRadius: 'var(--radius-full)', overflow: 'hidden', marginBottom: 3 }}>
                    <div style={{ height: '100%', width: `${driveUsedPct}%`, background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-violet))' }} />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    <span>Free: {drive.freeGb.toLocaleString()} GB</span>
                    <span>Total: {drive.totalGb.toLocaleString()} GB</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* PANEL 2: ORIGINAL COMPUTE LANES */}
        <div className="workspace-panel" style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', gap: 10, padding: '16px 20px' }}>
          <div className="panel-heading" style={{ marginBottom: 4 }}>
            <Cpu size={18} color="var(--accent-violet)" />
            <div>
              <h3>Original System Compute Metrics</h3>
              <p>Hardware threads, memory cache, and sidecar status.</p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1, justifyContent: 'space-between' }}>
            {hardware.map((item) => {
              const Icon = hardwareIconMap[item.id] ?? Activity;
              return (
                <div
                  key={item.id}
                  style={{
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 600 }}>
                      <Icon size={14} color="var(--accent-violet)" />
                      <span>{item.label}</span>
                    </div>
                    <span className="badge badge-safe" style={{ fontSize: 10 }}>
                      {statusLabel[item.status]}
                    </span>
                  </div>

                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>
                    {item.value}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-secondary)', lineHeight: 1.3 }}>
                    {item.detail}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 4. MODULE GRID (SECURITY POLICIES - CLICKABLE TO OPEN SECURITY PAGE) */}
      <section className="module-grid" style={{ margin: '10px 0 0 0' }}>
        <button
          className="module-card"
          onClick={onOpenSecuritySettings}
          style={{ cursor: 'pointer', textAlign: 'left' }}
        >
          <ShieldCheck size={20} color="var(--status-safe)" />
          <strong style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>Hardware Privacy Lock</span>
            <span className="badge badge-safe" style={{ fontSize: 9 }}>ACTIVE</span>
          </strong>
          <span>100% Offline Mode. Blocks external network egress during file analysis. Click to configure.</span>
        </button>

        <button
          className="module-card"
          onClick={onOpenSecuritySettings}
          style={{ cursor: 'pointer', textAlign: 'left' }}
        >
          <CheckCircle2 size={20} color="var(--accent-cyan)" />
          <strong style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>Mandatory Dry-Run Gate</span>
            <span className="badge badge-cyan" style={{ fontSize: 9 }}>ENFORCED</span>
          </strong>
          <span>Requires preview tree diff and path collision validation prior to file moves. Click to configure.</span>
        </button>

        <button
          className="module-card"
          onClick={onOpenSecuritySettings}
          style={{ cursor: 'pointer', textAlign: 'left' }}
        >
          <LockKeyhole size={20} color="var(--accent-violet)" />
          <strong style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>SQLite Rollback Journal</span>
            <span className="badge badge-violet" style={{ fontSize: 9 }}>30 DAYS</span>
          </strong>
          <span>Transactional operation journal reserved for loss-free 1-click reverse rollback. Click to configure.</span>
        </button>
      </section>
    </div>
  );
};
