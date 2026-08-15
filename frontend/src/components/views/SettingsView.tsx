import React, { useState } from 'react';
import { Settings, ShieldCheck, Database, Trash2, Cpu, Lock, Check } from 'lucide-react';

interface SettingsViewProps {
  privacyLock: boolean;
  onTogglePrivacyLock: () => void;
  onResetMemory: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  privacyLock,
  onTogglePrivacyLock,
  onResetMemory,
}) => {
  const [telemetry, setTelemetry] = useState(false);

  return (
    <div className="view-container">
      <div style={{ marginBottom: 20 }}>
        <h2 className="heading-lg">Personalization Memory & Security Control Panel</h2>
        <p className="subheading">
          Transparent configuration for learned user preferences, Hardware Privacy Lock, local SQLite memory, and vulnerability diagnostics.
        </p>
      </div>

      {/* Security & Privacy Lock */}
      <div className="glass-panel" style={{ padding: 20, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ padding: 10, borderRadius: 'var(--radius-sm)', background: 'var(--status-safe-bg)' }}>
              <ShieldCheck size={20} color="var(--status-safe)" />
            </div>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 600 }}>Hardware Privacy Lock (Strict Offline Execution)</h3>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                When enabled, Tauri core blocks all outbound socket and HTTP network connections during analysis and file operations.
              </p>
            </div>
          </div>

          <button
            className={privacyLock ? 'btn-primary' : 'btn-secondary'}
            onClick={onTogglePrivacyLock}
          >
            {privacyLock ? 'Privacy Lock ACTIVE' : 'Enable Privacy Lock'}
          </button>
        </div>
      </div>

      {/* Local Learned Personalization Memory */}
      <div className="glass-panel" style={{ padding: 20, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>Learned Personalization Signals</h3>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Compact local feedback history recorded to SQLite `user_preferences` table.
            </p>
          </div>

          <button className="btn-danger" onClick={onResetMemory}>
            <Trash2 size={16} />
            <span>Reset Learned Memory</span>
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Preferred Naming Strategy</div>
            <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, color: 'var(--accent-cyan)' }}>snake_case_lowercase</div>
          </div>

          <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Target Folder Depth Limit</div>
            <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, color: 'var(--accent-violet)' }}>3 Levels Deep</div>
          </div>

          <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Protected Path Rules</div>
            <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, color: 'var(--status-safe)' }}>.git, node_modules</div>
          </div>
        </div>
      </div>

      {/* Telemetry & Audit */}
      <div className="glass-panel" style={{ padding: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>Anonymous Error Diagnostics</h3>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Disabled by default. Zero file names, paths, or file contents are ever transmitted.
            </p>
          </div>

          <input
            type="checkbox"
            checked={telemetry}
            onChange={(e) => setTelemetry(e.target.checked)}
            style={{ width: 20, height: 20, cursor: 'pointer' }}
          />
        </div>
      </div>
    </div>
  );
};
