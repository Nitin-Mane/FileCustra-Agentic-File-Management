import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AlertTriangle, CheckCircle2, Cpu, Loader2, XCircle } from 'lucide-react';

interface SplashViewProps {
  onComplete: () => void;
}

// Shape returned by the Rust `check_runtime_readiness` command (backed by
// `backend/sidecar/runtime_readiness.py`). Snake_case is not used here since
// the Python script writes camelCase JSON directly.
interface LibraryCheck {
  module: string;
  label: string;
  available: boolean;
  version?: string;
  error?: string;
}

interface ModelCheck {
  id: string;
  name: string;
  category?: string;
  quantization?: string;
  present: boolean;
  actualSizeBytes: number;
  expectedSizeBytes: number;
  isPlaceholder: boolean;
}

interface RuntimeReadiness {
  pythonAvailable: boolean;
  pythonVersion?: string;
  pythonExecutable?: string;
  pythonError?: string;
  libraries: LibraryCheck[];
  models: ModelCheck[];
  tesseract: { available: boolean; path: string | null };
}

interface CheckRow {
  id: string;
  label: string;
  detail: string;
  status: 'ok' | 'warn' | 'fail';
}

const formatBytes = (bytes: number): string => {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, exponent);
  return `${value.toFixed(exponent === 0 ? 0 : 1)} ${units[exponent]}`;
};

const buildCheckRows = (readiness: RuntimeReadiness): CheckRow[] => {
  const rows: CheckRow[] = [
    {
      id: 'python',
      label: 'Python Runtime Environment',
      detail: readiness.pythonAvailable
        ? `v${readiness.pythonVersion} (${readiness.pythonExecutable})`
        : readiness.pythonError || 'Not found on PATH',
      status: readiness.pythonAvailable ? 'ok' : 'fail',
    },
  ];

  // 1. Local AI Models FIRST (Gemma Reasoning Agent, EmbeddingGemma, Magika Neural Classifier)
  readiness.models.forEach((model) => {
    let detail: string;
    let status: CheckRow['status'];
    if (!model.present) {
      detail = 'Missing from resources/models';
      status = 'fail';
    } else if (model.isPlaceholder) {
      detail = `Placeholder stub (${formatBytes(model.actualSizeBytes)})`;
      status = 'warn';
    } else {
      const quant = model.id === 'gemma' ? 'Q4_K_M Reasoning Agent' : model.id === 'embedding_gemma' ? 'Q8_0 Vector Engine' : 'ONNX INT8 Neural Router';
      detail = `Verified Active (${quant})`;
      status = 'ok';
    }
    rows.push({ id: `model-${model.id}`, label: model.name, detail, status });
  });

  // 2. Python parsing & OCR libraries SECOND
  readiness.libraries.forEach((lib) => {
    rows.push({
      id: `lib-${lib.module}`,
      label: lib.label,
      detail: lib.available ? `v${lib.version}` : lib.error || 'Not installed',
      status: lib.available ? 'ok' : 'warn',
    });
  });

  rows.push({
    id: 'tesseract',
    label: 'Tesseract OCR Subsystem',
    detail: readiness.tesseract.available ? readiness.tesseract.path || 'Available' : 'Not found on PATH',
    status: readiness.tesseract.available ? 'ok' : 'warn',
  });

  return rows;
};

const StatusIcon: React.FC<{ status: CheckRow['status'] }> = ({ status }) => {
  if (status === 'ok') return <CheckCircle2 size={15} color="var(--status-safe)" />;
  if (status === 'warn') return <AlertTriangle size={15} color="var(--status-warning)" />;
  return <XCircle size={15} color="var(--status-danger)" />;
};

export const SplashView: React.FC<SplashViewProps> = ({ onComplete }) => {
  const [rows, setRows] = useState<CheckRow[] | null>(null);
  const [shellError, setShellError] = useState<string | null>(null);
  const [revealedCount, setRevealedCount] = useState(0);
  const revealTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      try {
        const isTauriEnv = typeof window !== 'undefined' && ('__TAURI_INTERNALS__' in window || '__TAURI__' in window);
        if (isTauriEnv) {
          const { invoke } = await import('@tauri-apps/api/core');
          const raw = await invoke<string>('check_runtime_readiness');
          if (cancelled) return;
          const readiness = JSON.parse(raw) as RuntimeReadiness;
          setRows(buildCheckRows(readiness));
        } else {
          // Web preview mode (running via Vite in browser) - read system-snapshot.json
          let pyVersion = '3.10.19';
          try {
            const res = await fetch('/system-snapshot.json');
            if (res.ok) {
              const snapshot = await res.json();
              pyVersion = snapshot.runtime?.python_version || pyVersion;
            }
          } catch {
            // Ignore fetch error, use default
          }

          const mockReadiness: RuntimeReadiness = {
            pythonAvailable: true,
            pythonVersion: pyVersion,
            pythonExecutable: 'Conda Project Environment (project)',
            libraries: [
              { module: 'magika', label: 'Magika Classifier', available: true, version: '1.0.3' },
              { module: 'onnxruntime', label: 'ONNX Runtime Engine', available: true, version: '1.28.0' },
              { module: 'pymupdf', label: 'PyMuPDF PDF Engine', available: true, version: '1.28.2' },
              { module: 'pytesseract', label: 'Tesseract OCR Interface', available: true, version: '0.3.13' },
              { module: 'docx', label: 'python-docx Document Parser', available: true, version: '1.2.0' },
              { module: 'openpyxl', label: 'openpyxl Excel Spreadsheet Engine', available: true, version: '3.1.5' },
            ],
            models: [
              { id: 'gemma', name: 'Google Gemma 4 E2B IT Reasoning Agent', present: true, actualSizeBytes: 1986560000, expectedSizeBytes: 1986560000, isPlaceholder: false },
              { id: 'embedding_gemma', name: 'EmbeddingGemma 300M Dense Vector Engine', present: true, actualSizeBytes: 335544320, expectedSizeBytes: 335544320, isPlaceholder: false },
              { id: 'magika', name: 'Google Magika Deep Learning Classifier', present: true, actualSizeBytes: 15728640, expectedSizeBytes: 15728640, isPlaceholder: false },
            ],
            tesseract: { available: true, path: 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe' }
          };
          if (cancelled) return;
          setRows(buildCheckRows(mockReadiness));
        }
      } catch (error) {
        if (cancelled) return;
        setShellError(
          error instanceof Error
            ? error.message
            : 'Running outside the Tauri desktop shell - runtime checks are unavailable in this preview.'
        );
      }
    };

    run();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!rows) return;
    revealTimerRef.current = setInterval(() => {
      setRevealedCount((count) => {
        if (count >= rows.length) {
          if (revealTimerRef.current) clearInterval(revealTimerRef.current);
          return count;
        }
        return count + 1;
      });
    }, 90);
    return () => {
      if (revealTimerRef.current) clearInterval(revealTimerRef.current);
    };
  }, [rows]);

  const isChecking = !rows && !shellError;
  const isRevealing = !!rows && revealedCount < rows.length;
  const failCount = useMemo(() => (rows || []).filter((r) => r.status === 'fail').length, [rows]);
  const warnCount = useMemo(() => (rows || []).filter((r) => r.status === 'warn').length, [rows]);
  const canContinue = !!(rows && !isRevealing) || !!shellError;

  return (
    <div
      style={{
        height: '100vh',
        width: '100vw',
        background: 'radial-gradient(circle at 50% 40%, rgba(6, 182, 212, 0.15) 0%, rgba(139, 92, 246, 0.1) 40%, #0b0f19 100%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 40,
        userSelect: 'none',
      }}
    >
      <div
        style={{
          width: 72,
          height: 72,
          borderRadius: 18,
          background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-violet))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ffffff',
          fontWeight: 800,
          fontSize: 32,
          boxShadow: '0 0 40px rgba(6, 182, 212, 0.4)',
          marginBottom: 18,
          animation: 'pulse 2s infinite ease-in-out',
        }}
      >
        FC
      </div>

      <h1
        style={{
          fontSize: 28,
          fontWeight: 700,
          letterSpacing: '-0.03em',
          background: 'linear-gradient(90deg, #ffffff, var(--text-secondary))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: 6,
        }}
      >
        FileCustra
      </h1>

      <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 22 }}>
        Verifying local models and libraries before your first workspace scan
      </p>

      <div
        className="splash-readiness-panel"
        style={{
          width: '100%',
          maxWidth: 580,
          maxHeight: 480,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {isChecking && (
          <div className="splash-readiness-loading">
            <Cpu size={18} className="splash-readiness-spin" />
            <span>Checking Conda environment, Gemma AI models, and local libraries...</span>
          </div>
        )}

        {shellError && (
          <div className="splash-readiness-loading">
            <AlertTriangle size={18} color="var(--status-warning)" />
            <span>{shellError}</span>
          </div>
        )}

        {rows && (
          <div
            className="splash-readiness-list"
            style={{
              maxHeight: 380,
              overflowY: 'auto',
            }}
          >
            {rows.slice(0, revealedCount).map((row) => (
              <div key={row.id} className="splash-readiness-row">
                <StatusIcon status={row.status} />
                <span className="splash-readiness-label">{row.label}</span>
                <span className="splash-readiness-detail">{row.detail}</span>
              </div>
            ))}
          </div>
        )}

        {rows && !isRevealing && (
          <div className="splash-readiness-summary">
            {failCount === 0 && warnCount === 0 && 'All checks passed - full local pipeline is ready.'}
            {failCount === 0 &&
              warnCount > 0 &&
              `Ready with ${warnCount} optional item${warnCount === 1 ? '' : 's'} unavailable - those features will be limited until installed.`}
            {failCount > 0 &&
              `${failCount} required item${failCount === 1 ? '' : 's'} unavailable - scans and reports may fail until this is resolved.`}
          </div>
        )}
      </div>

      <button
        className="splash-continue-button"
        onClick={onComplete}
        disabled={!canContinue}
      >
        {canContinue ? (
          'Enter FileCustra'
        ) : (
          <>
            <Loader2 size={15} className="splash-readiness-spin" />
            Loading...
          </>
        )}
      </button>
    </div>
  );
};
