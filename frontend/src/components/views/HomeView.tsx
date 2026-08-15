import React from 'react';
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Cpu,
  FileCheck,
  FolderSearch,
  History,
  LockKeyhole,
  Route,
  ShieldCheck,
  Sparkles,
  Terminal,
} from 'lucide-react';
import { NavTab } from '../Sidebar';
import { SystemSnapshot } from '../../types';

interface HomeViewProps {
  scopedFolder: string;
  onNavigate: (tab: NavTab) => void;
  totalFiles: number;
  analyzedFiles: number;
  privacyLock: boolean;
  systemSnapshot?: SystemSnapshot;
}

export const HomeView: React.FC<HomeViewProps> = ({
  scopedFolder,
  onNavigate,
  totalFiles,
  analyzedFiles,
  privacyLock,
  systemSnapshot,
}) => {
  const analysisPct = totalFiles === 0 ? 0 : Math.round((analyzedFiles / totalFiles) * 100);
  const drivesList = systemSnapshot?.drives || [];
  const totalDriveCapacity = drivesList.reduce((sum, drive) => sum + drive.totalGb, 0);
  const freeDriveCapacity = drivesList.reduce((sum, drive) => sum + drive.freeGb, 0);


  return (
    <div className="view-container phase-home">
      <section className="phase-hero">
        <div className="phase-hero-copy">
          <div className="eyebrow-pill">
            <Sparkles size={14} />
            <span>Phase 01 build surface</span>
          </div>

          <h2>Private file intelligence, designed like a focused workspace.</h2>

          <p>
            Scope a folder, inspect contents read-only, and turn the analysis into a dry-run
            organization plan before any file is changed.
          </p>

          <div className="hero-actions">
            <button className="btn-primary btn-lg" onClick={() => onNavigate('discovery')}>
              <FolderSearch size={18} />
              <span>Start Read-Only Scan</span>
              <ArrowRight size={18} />
            </button>

            <button className="btn-secondary btn-lg" onClick={() => onNavigate('auto-ai')}>
              <Route size={18} />
              <span>Open Planner</span>
            </button>
          </div>
        </div>

        <div className="file-flow-graphic" aria-label="Animated file analysis flow">
          <div className="flow-core">
            <ShieldCheck size={30} />
            <span>FC</span>
          </div>
          {['PDF', 'DOCX', 'PY', 'JPG', 'XLSX', 'ZIP'].map((label, index) => (
            <div key={label} className={`flow-chip flow-chip-${index + 1}`}>
              {label}
            </div>
          ))}
          <div className="flow-ring flow-ring-one" />
          <div className="flow-ring flow-ring-two" />
        </div>
      </section>

      <section className="insight-grid">
        <button className="metric-tile" onClick={() => onNavigate('discovery')}>
          <FolderSearch size={19} />
          <span>Scoped Files</span>
          <strong>{totalFiles}</strong>
          <small>{analysisPct}% analyzed</small>
        </button>

        <button className="metric-tile" onClick={() => onNavigate('models')}>
          <Cpu size={19} />
          <span>Runtime Lane</span>
          <strong>{systemSnapshot?.runtime.sidecarStatus || 'READY'}</strong>
          <small>{systemSnapshot?.runtime.modelRuntime || 'Magika route prepared'}</small>
        </button>

        <button className="metric-tile" onClick={() => onNavigate('settings')}>
          <LockKeyhole size={19} />
          <span>Privacy State</span>
          <strong>{privacyLock ? 'Locked' : 'Open'}</strong>
          <small>Local processing policy</small>
        </button>

        <button className="metric-tile" onClick={() => onNavigate('journal-undo')}>
          <History size={19} />
          <span>Undo Journal</span>
          <strong>Ready</strong>
          <small>Dry-run before execution</small>
        </button>
      </section>

      <section className="phase-workbench">
        <div className="workspace-panel">
          <div className="panel-heading">
            <Activity size={18} />
            <div>
              <h3>Live Workspace Pulse</h3>
              <p>Phase 01 frontend and backend shell readiness.</p>
            </div>
          </div>

          <div className="pulse-list">
            {(systemSnapshot?.phaseOneMilestones || []).map((item) => (
              <div key={item.id} className={`pulse-row pulse-${item.status.toLowerCase()}`}>
                <CheckCircle2 size={16} />
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.description}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="workspace-panel">
          <div className="panel-heading">
            <FileCheck size={18} />
            <div>
              <h3>Current Scope</h3>
              <p>Nothing changes until a dry-run plan is reviewed.</p>
            </div>
          </div>

          <code className="scope-path">{scopedFolder}</code>

          <div className="capacity-strip">
            <div>
              <span>Drive Capacity</span>
              <strong>{Math.round(totalDriveCapacity).toLocaleString()} GB</strong>
            </div>
            <div>
              <span>Free Space</span>
              <strong>{Math.round(freeDriveCapacity).toLocaleString()} GB</strong>
            </div>
            <div>
              <span>Queued Work</span>
              <strong>{systemSnapshot?.runtime.queuedTasks || 3}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="module-grid">
        <button className="module-card" onClick={() => onNavigate('constellation')}>
          <Activity size={22} />
          <strong>Constellation Stream</strong>
          <span>Visual analysis states for file types, OCR, risk, and duplicate clusters.</span>
        </button>

        <button className="module-card" onClick={() => onNavigate('terminal')}>
          <Terminal size={22} />
          <strong>Scoped Terminal</strong>
          <span>Command interface stays inside the managed folder boundary.</span>
        </button>

        <button className="module-card" onClick={() => onNavigate('guided-query')}>
          <Sparkles size={22} />
          <strong>Guided Query</strong>
          <span>Five focused questions become explicit organization rules.</span>
        </button>
      </section>
    </div>
  );
};
