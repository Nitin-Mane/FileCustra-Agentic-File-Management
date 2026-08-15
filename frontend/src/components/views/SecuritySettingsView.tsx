import React, { useState } from 'react';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Cpu,
  Database,
  FileCode,
  History,
  Lock,
  Network,
  RotateCcw,
  ShieldCheck,
  Sliders,
} from 'lucide-react';

interface SecuritySettingsViewProps {
  onBackToDashboard: () => void;
  privacyLock: boolean;
  onTogglePrivacyLock: () => void;
}

export const SecuritySettingsView: React.FC<SecuritySettingsViewProps> = ({
  onBackToDashboard,
  privacyLock,
  onTogglePrivacyLock,
}) => {
  const [dryRunRequired, setDryRunRequired] = useState(true);
  const [sandboxEnabled, setSandboxEnabled] = useState(true);
  const [telemetryOptOut, setTelemetryOptOut] = useState(true);
  const [journalRetentionDays, setJournalRetentionDays] = useState(30);
  const [scanDepth, setScanDepth] = useState('MAX_20_LEVELS');
  const [modelLanePreference, setModelLanePreference] = useState('BALANCED');

  const activeSecurityCount = [privacyLock, dryRunRequired, sandboxEnabled, telemetryOptOut].filter(Boolean).length;

  return (
    <div className="template-shell security-template-shell">
      <main className="template-main security-template-main">
        <header className="template-page-header security-page-header">
          <div>
            <button className="template-back-button" onClick={onBackToDashboard} type="button">
              <ArrowLeft size={16} />
              Dashboard
            </button>
            <span className="template-live-kicker">
              <i />
              Security Configuration
            </span>
            <h1>Advanced Security System Configuration</h1>
            <p>Configure local privacy posture, dry-run safety, parser isolation settings, and rollback retention.</p>
          </div>
          <span className={`template-security-score ${activeSecurityCount === 4 ? 'safe' : 'warn'}`}>
            <ShieldCheck size={16} />
            {activeSecurityCount}/4 local controls enabled
          </span>
        </header>

        <section className="security-template-grid">
          <div className="template-glass-card security-control-stack">
            <div className="template-card-head">
              <div>
                <span>Core Security</span>
                <strong>Privacy and mutation barriers</strong>
              </div>
              <span className="template-state-pill safe">user controlled</span>
            </div>

            <label className={`security-toggle-row ${privacyLock ? 'active' : ''}`}>
              <div>
                <Lock size={17} />
                <span>Hardware Privacy Lock</span>
                <small>Local-first mode. Network enforcement must be verified by backend policy before release.</small>
              </div>
              <input type="checkbox" checked={privacyLock} onChange={onTogglePrivacyLock} />
            </label>

            <label className={`security-toggle-row ${dryRunRequired ? 'active' : ''}`}>
              <div>
                <CheckCircle2 size={17} />
                <span>Mandatory Dry-Run Gate</span>
                <small>Current workflow requires plan review before native file movement.</small>
              </div>
              <input type="checkbox" checked={dryRunRequired} onChange={(event) => setDryRunRequired(event.target.checked)} />
            </label>

            <label className={`security-toggle-row ${sandboxEnabled ? 'active' : ''}`}>
              <div>
                <FileCode size={17} />
                <span>Parser Sandbox Preference</span>
                <small>UI preference prepared. Full parser worker sandboxing is still a roadmap item.</small>
              </div>
              <input type="checkbox" checked={sandboxEnabled} onChange={(event) => setSandboxEnabled(event.target.checked)} />
            </label>

            <label className={`security-toggle-row ${telemetryOptOut ? 'active' : ''}`}>
              <div>
                <Network size={17} />
                <span>Zero External Telemetry</span>
                <small>No telemetry integration is enabled in the current local app flow.</small>
              </div>
              <input type="checkbox" checked={telemetryOptOut} onChange={(event) => setTelemetryOptOut(event.target.checked)} />
            </label>
          </div>

          <div className="template-glass-card security-runtime-stack">
            <div className="template-card-head">
              <div>
                <span>Runtime Settings</span>
                <strong>Scan depth, model lane, journals</strong>
              </div>
              <span className="template-state-pill warn">partly wired</span>
            </div>

            <div className="security-setting-block">
              <label>
                <span>Rollback journal retention</span>
                <strong>{journalRetentionDays} days</strong>
              </label>
              <input
                max="90"
                min="7"
                onChange={(event) => setJournalRetentionDays(Number(event.target.value))}
                type="range"
                value={journalRetentionDays}
              />
              <small>Journal files are created by native execution. Automated retention cleanup is not wired yet.</small>
            </div>

            <div className="security-setting-block">
              <label>
                <span>Directory scan depth</span>
              </label>
              <select value={scanDepth} onChange={(event) => setScanDepth(event.target.value)}>
                <option value="MAX_20_LEVELS">Up to 20 levels, current flow default</option>
                <option value="MAX_10_LEVELS">Up to 10 levels</option>
                <option value="ROOT_ONLY">Root folder only</option>
              </select>
              <small>Folder flow currently calls Tauri scan with maxDepth 20.</small>
            </div>

            <div className="security-setting-block">
              <label>
                <span>Model execution lane</span>
              </label>
              <select value={modelLanePreference} onChange={(event) => setModelLanePreference(event.target.value)}>
                <option value="BALANCED">Balanced local runtime, use available libraries</option>
                <option value="CPU_ONLY">CPU-only preference</option>
                <option value="GPU_READY">GPU-ready when verified by runtime readiness</option>
              </select>
              <small>Real model activation depends on manifest, file presence, checksum, and runtime readiness.</small>
            </div>

            <div className="security-status-grid">
              <article>
                <Database size={17} />
                <span>Native journal</span>
                <strong>Available after execution</strong>
              </article>
              <article>
                <RotateCcw size={17} />
                <span>Rollback</span>
                <strong>Journal backed</strong>
              </article>
              <article>
                <Cpu size={17} />
                <span>Models</span>
                <strong>Readiness checked on startup</strong>
              </article>
              <article>
                <History size={17} />
                <span>OSV scan</span>
                <strong>Not connected</strong>
              </article>
            </div>
          </div>

          <div className="template-glass-card security-template-note">
            <AlertTriangle size={19} />
            <div>
              <strong>Implementation boundary</strong>
              <p>
                This page is now template-aligned and functional as UI state. Privacy lock and workflow navigation are wired,
                while parser sandboxing, OSV scan, network enforcement, and model integrity enforcement still need backend policy integration.
              </p>
            </div>
          </div>
        </section>

        <footer className="security-template-footer">
          <span>Safe-core status: Tauri executes approved MOVE plans and rollback journals.</span>
          <div>
            <button className="flow-secondary-button" onClick={onBackToDashboard} type="button">Cancel</button>
            <button className="flow-primary-button" onClick={onBackToDashboard} type="button">
              <CheckCircle2 size={16} />
              Apply Local Preferences
            </button>
          </div>
        </footer>
      </main>
    </div>
  );
};
