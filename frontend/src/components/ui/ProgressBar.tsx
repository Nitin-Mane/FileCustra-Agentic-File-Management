import React from 'react';

export interface ProgressBarProps {
  progressPct: number;
  height?: number;
  colorGradient?: string;
  showLabel?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progressPct,
  height = 6,
  colorGradient = 'linear-gradient(90deg, var(--accent-cyan), var(--accent-violet))',
  showLabel = false,
}) => {
  const normalized = Math.min(100, Math.max(0, progressPct));

  return (
    <div style={{ width: '100%' }}>
      {showLabel && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px', color: 'var(--text-secondary)' }}>
          <span>Progress</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
            {normalized}%
          </span>
        </div>
      )}
      <div
        style={{
          width: '100%',
          height: `${height}px`,
          background: 'var(--bg-primary)',
          borderRadius: 'var(--radius-full)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${normalized}%`,
            background: colorGradient,
            borderRadius: 'var(--radius-full)',
            transition: 'width var(--transition-normal)',
          }}
        />
      </div>
    </div>
  );
};
