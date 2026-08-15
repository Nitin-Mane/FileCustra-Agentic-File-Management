import React from 'react';
import { ShieldCheck, HardDrive, Cpu, Lock, ArrowRight, CheckCircle2 } from 'lucide-react';

interface WelcomeViewProps {
  onContinue: () => void;
}

export const WelcomeView: React.FC<WelcomeViewProps> = ({ onContinue }) => {
  return (
    <div
      style={{
        height: '100vh',
        width: '100vw',
        background: 'radial-gradient(circle at 10% 20%, rgba(6, 182, 212, 0.08) 0%, transparent 50%), radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 50%), #0b0f19',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
        overflowY: 'auto',
      }}
    >
      <div className="glass-panel" style={{ width: 780, maxWidth: '95vw', padding: 36, border: '1px solid var(--border-active)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div className="brand-logo" style={{ width: 44, height: 44, fontSize: 20 }}>FC</div>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.02em' }}>Welcome to FileCustra</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>Private-First Agentic File Management System</p>
          </div>
        </div>

        {/* Security Banner */}
        <div
          className="glass-panel"
          style={{
            padding: 18,
            marginBottom: 24,
            background: 'rgba(16, 185, 129, 0.08)',
            borderLeft: '4px solid var(--status-safe)',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <ShieldCheck size={32} color="var(--status-safe)" />
          <div>
            <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--status-safe)' }}>
              Your files stay 100% on this device
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>
              FileCustra runs local AI reasoning (Google Magika, EmbeddingGemma, Gemma 4 E2B IT). Zero file names, paths, or file contents are ever uploaded to cloud servers.
            </div>
          </div>
        </div>

        {/* Core Principles Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 28 }}>
          <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, fontSize: 14, marginBottom: 6, color: 'var(--accent-cyan)' }}>
              <Lock size={16} /> 100% Read-Only First
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Analysis is purely read-only. No AI model directly mutates or deletes your files.
            </p>
          </div>

          <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, fontSize: 14, marginBottom: 6, color: 'var(--accent-violet)' }}>
              <HardDrive size={16} /> Dry-Run Mandatory
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Inspect visual tree diffs and path collision checks before any filesystem modification.
            </p>
          </div>

          <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, fontSize: 14, marginBottom: 6, color: 'var(--status-safe)' }}>
              <CheckCircle2 size={16} /> 1-Click Rollback
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Write-ahead transaction journal guarantees 100% loss-free reverse undo.
            </p>
          </div>
        </div>

        {/* CTA Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn-primary" style={{ padding: '12px 28px', fontSize: 15 }} onClick={onContinue}>
            <span>Continue to Drives Dashboard</span>
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};
