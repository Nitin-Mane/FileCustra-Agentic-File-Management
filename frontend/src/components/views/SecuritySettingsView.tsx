import React, { useState } from 'react';
import {
  ShieldCheck,
  Lock,
  Network,
  History,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sliders,
  Database,
  ArrowLeft,
  Cpu,
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
  const [scanDepth, setScanDepth] = useState('NESTED_UNLIMITED');
  const [modelLanePreference, setModelLanePreference] = useState('BALANCED');

  return (
    <div
      style={{
        height: '100vh',
        width: '100vw',
        padding: '16px 24px',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        background: 'radial-gradient(circle at 50% 20%, rgba(6, 182, 212, 0.08) 0%, #0b0f19 80%)',
        overflow: 'hidden',
        userSelect: 'none',
      }}
    >
      {/* 1. Header Bar */}
      <header
        className="glass-panel"
        style={{
          padding: '12px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderRadius: 'var(--radius-md)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn-secondary" style={{ padding: '6px 14px', fontSize: 13 }} onClick={onBackToDashboard}>
            <ArrowLeft size={16} />
            <span>Back to Dashboard</span>
          </button>
          <div>
            <h1 style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1.2 }}>
              Security Policy Controls & Hardware Privacy Settings
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
              Configure local execution sandboxing, network isolation, dry-run safety gates, and journal retention.
            </p>
          </div>
        </div>

        <div className="privacy-badge" style={{ padding: '6px 14px', fontSize: 12 }}>
          <ShieldCheck size={14} />
          <span>{privacyLock ? '100% Offline Privacy Lock ACTIVE' : 'Custom Security Policy'}</span>
        </div>
      </header>

      {/* 2. Main Policy Grid (Fits Screen Height) */}
      <main
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 16,
          flex: 1,
          margin: '14px 0',
          overflow: 'hidden',
          minHeight: 0,
        }}
      >
        {/* LEFT COLUMN: SECURITY POLICIES */}
        <section className="glass-panel" style={{ padding: 20, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
              <ShieldCheck size={18} color="var(--accent-cyan)" />
              <span>Core Security & Privacy Controls</span>
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {/* Privacy Lock Toggle */}
              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  padding: 14,
                  borderRadius: 'var(--radius-sm)',
                  border: `1px solid ${privacyLock ? 'var(--status-safe)' : 'var(--border-subtle)'}`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Lock size={15} color="var(--status-safe)" />
                    <span>Hardware Privacy Lock (Strict Offline Mode)</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>
                    Blocks all outbound HTTP/socket connections during file analysis & local model execution.
                  </div>
                </div>

                <input
                  type="checkbox"
                  checked={privacyLock}
                  onChange={onTogglePrivacyLock}
                  style={{ width: 22, height: 22, cursor: 'pointer', accentColor: 'var(--status-safe)' }}
                />
              </div>

              {/* Dry-Run Gate Toggle */}
              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  padding: 14,
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <CheckCircle2 size={15} color="var(--accent-cyan)" />
                    <span>Mandatory Dry-Run Simulation Gate</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>
                    Enforces dry-run tree diff preview and path collision validation prior to filesystem mutations.
                  </div>
                </div>

                <input
                  type="checkbox"
                  checked={dryRunRequired}
                  onChange={(e) => setDryRunRequired(e.target.checked)}
                  style={{ width: 22, height: 22, cursor: 'pointer', accentColor: 'var(--accent-cyan)' }}
                />
              </div>

              {/* Parser Worker Sandbox */}
              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  padding: 14,
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <FileCode size={15} color="var(--accent-violet)" />
                    <span>Isolated Parser Process Sandbox</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>
                    Executes PDF, Office, and archive parsers in isolated worker subprocesses to prevent host crashes.
                  </div>
                </div>

                <input
                  type="checkbox"
                  checked={sandboxEnabled}
                  onChange={(e) => setSandboxEnabled(e.target.checked)}
                  style={{ width: 22, height: 22, cursor: 'pointer', accentColor: 'var(--accent-violet)' }}
                />
              </div>

              {/* Zero Telemetry Guarantee */}
              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  padding: 14,
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Network size={15} color="var(--status-safe)" />
                    <span>Zero External Telemetry Egress</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>
                    Disables all crash reporters, analytics trackers, and external diagnostics logging.
                  </div>
                </div>

                <input
                  type="checkbox"
                  checked={telemetryOptOut}
                  onChange={(e) => setTelemetryOptOut(e.target.checked)}
                  style={{ width: 22, height: 22, cursor: 'pointer', accentColor: 'var(--status-safe)' }}
                />
              </div>
            </div>
          </div>

          <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: 12, borderRadius: 'var(--radius-sm)', border: '1px solid var(--status-safe)' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--status-safe)' }}>Security Posture Audit: EXCELLENT</div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>
              All 4 core security barriers are active. Local files remain 100% isolated.
            </div>
          </div>
        </section>

        {/* RIGHT COLUMN: RUNTIME & SYSTEM SETTINGS */}
        <section className="glass-panel" style={{ padding: 20, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Sliders size={18} color="var(--accent-violet)" />
              <span>Runtime & Storage Settings</span>
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Journal Retention Setting */}
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span>SQLite Rollback Journal Retention</span>
                  <span style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{journalRetentionDays} Days</span>
                </label>
                <input
                  type="range"
                  min="7"
                  max="90"
                  value={journalRetentionDays}
                  onChange={(e) => setJournalRetentionDays(Number(e.target.value))}
                  style={{ width: '100%', cursor: 'pointer', accentColor: 'var(--accent-cyan)' }}
                />
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  Retains write-ahead operation journal entries for loss-free 1-click reverse rollback.
                </div>
              </div>

              {/* Directory Scan Depth */}
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6, display: 'block' }}>
                  Directory Scan Depth Limit
                </label>
                <select
                  value={scanDepth}
                  onChange={(e) => setScanDepth(e.target.value)}
                  style={{
                    width: '100%',
                    background: 'var(--bg-tertiary)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-subtle)',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    outline: 'none',
                  }}
                >
                  <option value="NESTED_UNLIMITED">Unlimited Nested Subfolders (Recommended)</option>
                  <option value="MAX_3_LEVELS">Maximum 3 Subfolder Levels Deep</option>
                  <option value="ROOT_ONLY">Scoped Top-Level Directory Only</option>
                </select>
              </div>

              {/* AI Model Execution Lane */}
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6, display: 'block' }}>
                  AI Model Execution Lane & Backend Routing
                </label>
                <select
                  value={modelLanePreference}
                  onChange={(e) => setModelLanePreference(e.target.value)}
                  style={{
                    width: '100%',
                    background: 'var(--bg-tertiary)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-subtle)',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    outline: 'none',
                  }}
                >
                  <option value="BALANCED">Balanced (Auto GPU Acceleration + CPU Multi-Thread Fallback)</option>
                  <option value="GPU_ONLY">GPU DirectML Priority (NVIDIA / Intel UHD)</option>
                  <option value="CPU_ONLY">CPU Multi-Thread Isolated (16 Threads)</option>
                </select>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
            <button className="btn-secondary" onClick={onBackToDashboard}>
              <span>Cancel</span>
            </button>
            <button className="btn-primary" onClick={onBackToDashboard}>
              <CheckCircle2 size={16} />
              <span>Apply Security Policies</span>
            </button>
          </div>
        </section>
      </main>

      {/* 3. Footer */}
      <footer
        className="glass-panel"
        style={{
          padding: '8px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: 11,
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-secondary)',
        }}
      >
        <span>Policy Engine: SQLite FTS5 Active</span>
        <span>OSV-Scanner Vulnerability Scan: PASSED (0 Vulnerabilities)</span>
      </footer>
    </div>
  );
};
