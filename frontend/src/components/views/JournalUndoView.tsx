import React from 'react';
import { OperationJournalEntry } from '../../types';
import { Undo2, History, CheckCircle2, ShieldCheck, Clock, RotateCcw, ArrowRight } from 'lucide-react';

interface JournalUndoViewProps {
  entries: OperationJournalEntry[];
  onRollback: (entryId: string) => void;
  onStartNewWorkspace?: () => void;
}

export const JournalUndoView: React.FC<JournalUndoViewProps> = ({ entries, onRollback, onStartNewWorkspace }) => {
  return (
    <div className="view-container phase-home" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="eyebrow-pill" style={{ marginBottom: 8 }}>
            <ShieldCheck size={14} />
            <span>Step 5 of 5: Safe Execution & Satisfaction Rollback</span>
          </div>
          <h2 className="heading-lg" style={{ margin: 0 }}>Write-Ahead Operation Journal & 1-Click Rollback</h2>
          <p className="subheading" style={{ margin: '4px 0 0 0' }}>
            All operations executed under full transactional safety. If you are not satisfied with the reorganization result, perform a 1-click reverse rollback.
          </p>
        </div>

        {onStartNewWorkspace && (
          <button className="btn-primary btn-lg" onClick={onStartNewWorkspace}>
            <RotateCcw size={16} />
            <span>Start New Workspace Flow</span>
            <ArrowRight size={18} />
          </button>
        )}
      </div>

      {/* Prominent Satisfaction Rollback Banner */}
      <div className="glass-panel" style={{ padding: 20, borderLeft: '4px solid var(--accent-violet)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <Undo2 size={28} color="var(--accent-violet)" />
          <div>
            <h4 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
              Not Satisfied with the Reorganization?
            </h4>
            <p style={{ margin: '2px 0 0 0', fontSize: 12, color: 'var(--text-secondary)' }}>
              1-Click Instant Reverse Rollback restores every file back to its original pre-execution path with 0 data loss.
            </p>
          </div>
        </div>
      </div>

      {/* Executed Sessions Deck */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '12px 16px', background: 'rgba(31, 41, 55, 0.6)', borderBottom: '1px solid var(--border-subtle)', fontWeight: 600, fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
          <History size={16} color="var(--accent-cyan)" />
          <span>Executed Transaction Journal Batches ({entries.length} Sessions)</span>
        </div>

        <div style={{ padding: 16 }}>
          {entries.length === 0 ? (
            <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
              No execution transactions recorded yet. Complete Step 4 approval to generate a journal entry.
            </div>
          ) : (
            entries.map((entry) => (
              <div
                key={entry.id}
                className="glass-panel"
                style={{ padding: 18, marginBottom: 16, borderLeft: `4px solid ${entry.status === 'COMPLETED' ? 'var(--status-safe)' : 'var(--text-muted)'}` }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Clock size={14} color="var(--text-secondary)" />
                      <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>Batch #{entry.id.substring(0, 8)}</span>
                      <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>• {entry.timestamp}</span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                      {entry.operationCount} File Operations Executed • Status: {entry.status}
                    </div>
                  </div>

                  {entry.status === 'COMPLETED' ? (
                    <button className="btn-danger btn-lg" onClick={() => onRollback(entry.id)}>
                      <Undo2 size={16} />
                      <span>1-Click Reverse Rollback</span>
                    </button>
                  ) : (
                    <span className="badge badge-warning" style={{ padding: '6px 14px', fontSize: 12, fontWeight: 700 }}>
                      ✓ Transaction Successfully Rolled Back
                    </span>
                  )}
                </div>

                <div style={{ background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', padding: 12, fontSize: 12, fontFamily: 'var(--font-mono)' }}>
                  {entry.steps.map((s) => (
                    <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px dashed var(--border-subtle)' }}>
                      <span>{s.operationType}: {s.sourcePath}</span>
                      <span style={{ color: 'var(--accent-cyan)' }}>→ {s.targetPath}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
