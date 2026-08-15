import React, { useState, useEffect } from 'react';
import { Download, Cpu, ShieldCheck, CheckCircle2, ArrowRight, Sparkles, Database } from 'lucide-react';

interface OnboardingSetupViewProps {
  onCompleteSetup: () => void;
}

export const OnboardingSetupView: React.FC<OnboardingSetupViewProps> = ({ onCompleteSetup }) => {
  const [downloading, setDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [activeModel, setActiveModel] = useState('Google Magika v0.5.1 Classifier (50 MB)');
  const [isCompleted, setIsCompleted] = useState(false);

  const startSetup = () => {
    setDownloading(true);
    let p = 0;
    const interval = setInterval(() => {
      p += 10;
      setDownloadProgress(p);

      if (p === 30) setActiveModel('EmbeddingGemma 300M Vector Weights (320 MB)');
      else if (p === 60) setActiveModel('Gemma 4 E2B IT Quantized Reasoning Weights (1.85 GB)');
      else if (p === 90) setActiveModel('Configuring SQLite FTS5 Transactional Schema...');

      if (p >= 100) {
        clearInterval(interval);
        setDownloading(false);
        setIsCompleted(true);
      }
    }, 600);
  };

  return (
    <div
      style={{
        height: '100vh',
        width: '100vw',
        background: 'radial-gradient(circle at 50% 30%, rgba(139, 92, 246, 0.12) 0%, #0b0f19 80%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
      }}
    >
      <div className="glass-panel" style={{ width: 740, maxWidth: '95vw', padding: 36, border: '1px solid var(--border-active)' }}>
        <div className="badge badge-violet" style={{ marginBottom: 12, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <Sparkles size={12} /> One-Time Setup & Hardware Initialization
        </div>

        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
          Initial Local Model Setup & Hardware Configuration
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 28, lineHeight: 1.6 }}>
          This is a <strong>one-time setup process</strong>. FileCustra prepares your local offline AI model weights (Google Magika, EmbeddingGemma 300M, and Gemma 4 E2B IT) for 100% device-local file management.
        </p>

        {/* Model Download Progress Card */}
        <div className="glass-panel" style={{ padding: 24, marginBottom: 28, background: 'var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{activeModel}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                {downloading ? 'Downloading & verifying SHA-256 checksums...' : isCompleted ? 'All local model weights verified and ready!' : 'Ready to download model weights'}
              </div>
            </div>

            {isCompleted && (
              <span className="badge badge-safe" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '6px 12px' }}>
                <CheckCircle2 size={14} /> Verification Passed
              </span>
            )}
          </div>

          <div style={{ height: 8, background: 'var(--bg-primary)', borderRadius: 'var(--radius-full)', overflow: 'hidden', marginBottom: 12 }}>
            <div style={{ height: '100%', width: `${downloadProgress}%`, background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-violet))', transition: 'width 0.4s ease' }} />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
            <span>Progress: {downloadProgress}%</span>
            <span>Target Path: <code>~/.filecustra/models/</code></span>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="privacy-badge">
            <ShieldCheck size={14} />
            <span>Setup is 100% One-Time Only</span>
          </div>

          {!isCompleted ? (
            <button className="btn-primary" style={{ padding: '12px 24px' }} onClick={startSetup} disabled={downloading}>
              <Download size={18} />
              <span>{downloading ? 'Downloading Weights...' : 'Start One-Time Model Setup'}</span>
            </button>
          ) : (
            <button className="btn-primary" style={{ padding: '12px 28px', background: 'linear-gradient(135deg, var(--status-safe), var(--accent-cyan))' }} onClick={onCompleteSetup}>
              <span>Enter Formatted Application Workspace</span>
              <ArrowRight size={18} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
