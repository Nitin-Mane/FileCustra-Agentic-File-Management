import React from 'react';
import { ShieldCheck, HardDrive, Cpu, Sparkles } from 'lucide-react';
import { Badge } from './ui/Badge';

interface HeaderProps {
  scopedFolder: string;
  hardwareDevice: string;
  privacyLock: boolean;
}

export const Header: React.FC<HeaderProps> = ({ scopedFolder, hardwareDevice, privacyLock }) => {
  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-logo">FC</div>
        <div>
          <h1 className="brand-title">FileCustra</h1>
        </div>
        {scopedFolder && (
          <div style={{ marginLeft: 16, display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)' }}>
            <HardDrive size={14} color="var(--accent-cyan)" />
            <span>Scoped: </span>
            <code style={{ background: 'var(--bg-tertiary)', padding: '2px 8px', borderRadius: 4, color: 'var(--accent-cyan)' }}>
              {scopedFolder}
            </code>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* FileCustra Native Local SDK Status Pill */}
        <Badge color="cyan" size="md">
          <ShieldCheck size={13} />
          <span>FileCustra Native SDK (100% Offline Safe)</span>
        </Badge>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)' }}>
          <Cpu size={14} color="var(--accent-violet)" />
          <span>{hardwareDevice}</span>
        </div>

        {privacyLock && (
          <Badge color="safe" size="md">
            <ShieldCheck size={14} />
            <span>100% Offline Privacy Lock</span>
          </Badge>
        )}
      </div>
    </header>
  );
};
