import React from 'react';
import { Activity, ShieldAlert, Cpu, Sparkles, FileText, Image, FileCode, FileSpreadsheet, CheckCircle2, ArrowRight, ArrowLeft, Layers, FileCheck } from 'lucide-react';

interface ConstellationViewProps {
  onProceedToStep3?: () => void;
  onBack?: () => void;
}

export const ConstellationView: React.FC<ConstellationViewProps> = ({ onProceedToStep3, onBack }) => {
  const fileClusters = [
    { label: 'PDF Documents & Financial Scans', count: 2, icon: FileText, color: 'var(--accent-violet)', ocrCount: 2, risk: 'LOW' },
    { label: 'Python & Engineering Code', count: 1, icon: FileCode, color: 'var(--accent-cyan)', ocrCount: 0, risk: 'SAFE' },
    { label: 'PNG Images & Diagrams', count: 1, icon: Image, color: 'var(--accent-aqua)', ocrCount: 0, risk: 'SAFE' },
    { label: 'Spreadsheets & Excel Payroll', count: 1, icon: FileSpreadsheet, color: 'var(--status-safe)', ocrCount: 0, risk: 'SAFE' },
  ];

  return (
    <div className="view-container phase-home" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Step Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          {onBack && (
            <button className="btn-ghost" onClick={onBack} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 8, padding: '4px 10px' }}>
              <ArrowLeft size={14} />
              <span>Back to Folder Selection (Step 1)</span>
            </button>
          )}
          <h2 className="heading-lg" style={{ margin: 0 }}>Step 2: File Types & Structural Formatting Analysis</h2>
          <p className="subheading" style={{ margin: '4px 0 0 0' }}>
            Google Magika deep learning file type breakdown, extension mismatch detection, and OCR extraction matrix.
          </p>
        </div>

        {onProceedToStep3 && (
          <button className="btn-primary btn-lg" onClick={onProceedToStep3}>
            <span>Proceed to Execution Engine Mode (Step 3)</span>
            <ArrowRight size={18} />
          </button>
        )}
      </div>

      {/* Realtime Stream Graphic */}
      <div className="glass-panel" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Activity size={20} color="var(--accent-cyan)" />
            <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              Magika Classification & Structure Matrix
            </h3>
          </div>
          <span className="badge badge-safe">100% Offline Magika Classifier Active</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          {fileClusters.map((cluster) => {
            const Icon = cluster.icon;
            return (
              <div
                key={cluster.label}
                style={{
                  padding: 16,
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 10,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Icon size={20} color={cluster.color} />
                  <span className="badge badge-cyan" style={{ fontSize: 10 }}>{cluster.count} Files</span>
                </div>

                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                  {cluster.label}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-secondary)' }}>
                  <span>OCR Extracted: {cluster.ocrCount}</span>
                  <span style={{ color: 'var(--status-safe)', fontWeight: 600 }}>Risk: {cluster.risk}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Structural Formatting Rules & Mismatch Alerts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        
        {/* Extension Mismatch Warnings */}
        <div className="glass-panel" style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ShieldAlert size={18} color="var(--status-safe)" />
            <h4 style={{ fontSize: 14, fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              Extension Mismatch Audit
            </h4>
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0 }}>
            Google Magika verifies byte headers to catch spoofed or misnamed file extensions before organization.
          </p>

          <div style={{ padding: 12, borderRadius: 'var(--radius-sm)', background: 'rgba(34, 197, 94, 0.08)', border: '1px solid rgba(34, 197, 94, 0.2)', fontSize: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <CheckCircle2 size={16} color="var(--status-safe)" />
            <span>0 Spoofed Extensions Detected. All byte signatures match file extensions.</span>
          </div>
        </div>

        {/* Target Formatting Preferences */}
        <div className="glass-panel" style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Layers size={18} color="var(--accent-violet)" />
            <h4 style={{ fontSize: 14, fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              Target Folder Structure Strategy
            </h4>
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0 }}>
            Configure how file types and formats should be grouped into destination subfolders.
          </p>

          <div style={{ display: 'flex', gap: 8 }}>
            <span className="badge badge-cyan">Domain + Category</span>
            <span className="badge badge-violet">Chronological Year</span>
            <span className="badge badge-mint">Magika Type</span>
          </div>
        </div>

      </div>
    </div>
  );
};
