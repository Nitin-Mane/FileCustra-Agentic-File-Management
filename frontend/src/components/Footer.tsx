import React from 'react';
import { Database, Zap, HardDrive } from 'lucide-react';
import { Badge } from './ui/Badge';

interface FooterProps {
  sidecarConnected: boolean;
  totalFiles: number;
  analyzedFiles: number;
  dbStatus: string;
}

export const Footer: React.FC<FooterProps> = ({ sidecarConnected, totalFiles, analyzedFiles, dbStatus }) => {
  return (
    <footer className="app-footer">
      <div className="footer-status-group">
        <div className="status-indicator">
          <Badge color={sidecarConnected ? 'safe' : 'danger'} size="sm">
            <span>Python 3.10 Sidecar IPC: {sidecarConnected ? 'Connected (JSON-RPC 2.0)' : 'Disconnected'}</span>
          </Badge>
        </div>

        <div className="status-indicator" style={{ marginLeft: 16 }}>
          <Database size={13} color="var(--accent-cyan)" />
          <span>SQLite + FTS5: {dbStatus}</span>
        </div>
      </div>

      <div className="footer-status-group">
        <div className="status-indicator">
          <Badge color="violet" size="sm">
            <Zap size={11} />
            <span>Magika Router Ready</span>
          </Badge>
        </div>

        <div className="status-indicator" style={{ marginLeft: 16 }}>
          <HardDrive size={13} color="var(--text-secondary)" />
          <span>Session Scan: {analyzedFiles} / {totalFiles} Files</span>
        </div>
      </div>
    </footer>
  );
};
