import React from 'react';
import { FileText, Image, FileCode, Sheet, FileCheck, CheckCircle2 } from 'lucide-react';
import { FileItem } from '../../types';
import { Badge } from './Badge';

export interface FileRowProps {
  file: FileItem;
  onSelect?: (file: FileItem) => void;
}

const getFileIcon = (mime: string, ext: string) => {
  if (ext === 'pdf') return <FileText size={16} color="var(--accent-coral)" />;
  if (['png', 'jpg', 'webp', 'svg'].includes(ext)) return <Image size={16} color="var(--accent-aqua)" />;
  if (['py', 'rs', 'ts', 'js', 'json'].includes(ext)) return <FileCode size={16} color="var(--accent-violet)" />;
  if (['xlsx', 'csv'].includes(ext)) return <Sheet size={16} color="var(--accent-mint)" />;
  return <FileCheck size={16} color="var(--accent-cyan)" />;
};

const formatSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export const FileRow: React.FC<FileRowProps> = ({ file, onSelect }) => {
  return (
    <div
      onClick={() => onSelect && onSelect(file)}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 14px',
        borderRadius: 'var(--radius-sm)',
        background: 'var(--bg-tertiary)',
        border: '1px solid var(--border-subtle)',
        cursor: onSelect ? 'pointer' : 'default',
        transition: 'all var(--transition-fast)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {getFileIcon(file.mimeType, file.extension)}
        <div>
          <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>{file.name}</div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {file.path}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Badge color="cyan" size="sm">
          {file.magikaType}
        </Badge>
        {file.ocrExtracted && (
          <Badge color="violet" size="sm">
            OCR Extracted
          </Badge>
        )}
        <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
          {formatSize(file.sizeBytes)}
        </span>
      </div>
    </div>
  );
};
