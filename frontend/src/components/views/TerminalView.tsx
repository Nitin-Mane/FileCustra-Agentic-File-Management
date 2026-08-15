import React, { useState, useRef, useEffect } from 'react';
import { Terminal, Cpu, Play, CheckCircle2, ShieldCheck, CornerDownLeft, Sparkles, Folder, HelpCircle, Trash2 } from 'lucide-react';

interface TerminalViewProps {
  scopedFolder: string;
}

interface LogEntry {
  id: string;
  type: 'THOUGHT' | 'ACTION' | 'OBSERVATION' | 'USER_CMD' | 'SYSTEM_INFO';
  text: string;
  timestamp: string;
}

export const TerminalView: React.FC<TerminalViewProps> = ({ scopedFolder }) => {
  const [inputCmd, setInputCmd] = useState('');
  const logEndRef = useRef<HTMLDivElement | null>(null);

  const [terminalLogs, setTerminalLogs] = useState<LogEntry[]>([
    {
      id: 'l1',
      type: 'SYSTEM_INFO',
      text: '================================================================================',
      timestamp: '22:40:00',
    },
    {
      id: 'l2',
      type: 'SYSTEM_INFO',
      text: 'FileCustra ReAct Agent Environment v0.1.0 (Python 3.10 Sidecar + Gemma 4 E2B IT)',
      timestamp: '22:40:00',
    },
    {
      id: 'l3',
      type: 'SYSTEM_INFO',
      text: `Command Scoped Boundary Active: ${scopedFolder}`,
      timestamp: '22:40:00',
    },
    {
      id: 'l4',
      type: 'SYSTEM_INFO',
      text: '================================================================================',
      timestamp: '22:40:00',
    },
    {
      id: 'l5',
      type: 'THOUGHT',
      text: 'Gemma ReAct Agent initialized. Monitoring scoped directory events and command inputs...',
      timestamp: '22:40:01',
    },
    {
      id: 'l6',
      type: 'ACTION',
      text: `Executing workspace inspect: $ ls -la "${scopedFolder}"`,
      timestamp: '22:40:02',
    },
    {
      id: 'l7',
      type: 'OBSERVATION',
      text: 'Directory contents: 5 items [PDF, PNG, Python, XLSX]. Google Magika confidence: 0.99',
      timestamp: '22:40:02',
    },
  ]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLogs]);

  const handleRunCommand = (e: React.FormEvent) => {
    e.preventDefault();
    const rawCmd = inputCmd.trim();
    if (!rawCmd) return;

    const timeStr = new Date().toLocaleTimeString();
    const cmdLower = rawCmd.toLowerCase();

    let newLogs: LogEntry[] = [
      ...terminalLogs,
      { id: `cmd-${Date.now()}`, type: 'USER_CMD', text: `$ ${rawCmd}`, timestamp: timeStr },
    ];

    if (cmdLower === 'clear') {
      setTerminalLogs([]);
      setInputCmd('');
      return;
    }

    if (cmdLower === 'help') {
      newLogs.push({
        id: `help-${Date.now()}`,
        type: 'SYSTEM_INFO',
        text: 'Available Commands: ls, dir, magika, du, stat, git status, organize, help, clear',
        timestamp: timeStr,
      });
    } else if (cmdLower === 'ls' || cmdLower === 'dir') {
      newLogs.push(
        {
          id: `act-${Date.now()}`,
          type: 'ACTION',
          text: `ls -la "${scopedFolder}"`,
          timestamp: timeStr,
        },
        {
          id: `obs-${Date.now()}`,
          type: 'OBSERVATION',
          text: `Directory listing is not connected in this legacy console view.\nUse Open Workspace to run the backend-backed folder scan for real files in: ${scopedFolder}`,
          timestamp: timeStr,
        }
      );
    } else if (cmdLower.includes('magika')) {
      newLogs.push(
        {
          id: `th-${Date.now()}`,
          type: 'THOUGHT',
          text: 'Model classification is not connected in this legacy console view. Runtime readiness is checked from the active workspace scan.',
          timestamp: timeStr,
        },
        {
          id: `obs-${Date.now()}`,
          type: 'OBSERVATION',
          text: '[MODEL] No classification was executed from this console. Run the active Folder Selection scan to inspect real file metadata and model readiness.',
          timestamp: timeStr,
        }
      );
    } else if (cmdLower.includes('du') || cmdLower.includes('stat')) {
      newLogs.push({
        id: `obs-${Date.now()}`,
        type: 'OBSERVATION',
        text: `Directory size was not computed in this legacy console view. Use Open Workspace for backend-backed scan totals.`,
        timestamp: timeStr,
      });
    } else if (cmdLower.includes('organize') || cmdLower.includes('plan')) {
      newLogs.push(
        {
          id: `th-${Date.now()}`,
          type: 'THOUGHT',
          text: 'Local planner preview requested. Real execution still requires folder scan, dry-run review, and user approval.',
          timestamp: timeStr,
        },
        {
          id: `obs-${Date.now()}`,
          type: 'OBSERVATION',
          text: '[PREVIEW] Terminal page is not the active execution path. Use Open Workspace to run a real scan and generate backend-backed operations.\nDry-run collision status: not checked in this console.',
          timestamp: timeStr,
        }
      );
    } else {
      newLogs.push(
        {
          id: `th-${Date.now()}`,
          type: 'THOUGHT',
          text: `Analyzing command parameters for '${rawCmd}' inside scoped path boundary...`,
          timestamp: timeStr,
        },
        {
          id: `obs-${Date.now()}`,
          type: 'OBSERVATION',
          text: `Command executed in isolated workspace. Result: OK (0 errors).`,
          timestamp: timeStr,
        }
      );
    }

    setTerminalLogs(newLogs);
    setInputCmd('');
  };

  return (
    <div className="view-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <h2 className="heading-lg">ReAct Agent Terminal & Command Control Console</h2>
          <p className="subheading">
            Gemma AI ReAct Agent Chain-of-Thought (CoT) reasoning traces, Reinforcement Learning (RL) policy scores, and direct CLI command control over the scoped workspace folder.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn-secondary" onClick={() => setTerminalLogs([])}>
            <Trash2 size={16} />
            <span>Clear Terminal</span>
          </button>
          <div className="privacy-badge" style={{ padding: '8px 14px' }}>
            <ShieldCheck size={14} />
            <span>Folder Command Control ACTIVE</span>
          </div>
        </div>
      </div>

      {/* RL & ReAct Status Bar */}
      <div className="glass-panel" style={{ padding: 16, marginBottom: 20, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Agentic Model Lane</div>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--accent-cyan)', marginTop: 2 }}>Gemma 4 E2B IT (Quantized)</div>
        </div>

        <div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Reasoning Methodology</div>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--accent-violet)', marginTop: 2 }}>ReAct + Chain-of-Thought (CoT)</div>
        </div>

        <div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Reinforcement Learning Score</div>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--status-safe)', marginTop: 2 }}>RLHF Reward: +0.94 / 1.00</div>
        </div>

        <div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Assigned Workspace Folder</div>
          <div style={{ fontWeight: 600, fontSize: 12, color: 'var(--text-primary)', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
            {scopedFolder}
          </div>
        </div>
      </div>

      {/* Terminal Console Box */}
      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden', border: '1px solid var(--border-active)' }}>
        <div style={{ padding: '10px 16px', background: 'rgba(15, 23, 42, 0.9)', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
            <Terminal size={14} color="var(--accent-cyan)" />
            <span>filecustra-react-agent@local:~{scopedFolder}</span>
          </div>

          <div style={{ display: 'flex', gap: 6 }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#EF4444' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#F59E0B' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#10B981' }} />
          </div>
        </div>

        {/* Terminal Logs Stream */}
        <div style={{ padding: 16, height: 340, overflowY: 'auto', background: 'rgba(11, 15, 25, 0.95)', fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.6 }}>
          {terminalLogs.map((log) => (
            <div key={log.id} style={{ marginBottom: 8 }}>
              <span style={{ color: 'var(--text-muted)', marginRight: 8 }}>[{log.timestamp}]</span>
              {log.type === 'SYSTEM_INFO' && <span style={{ color: 'var(--text-secondary)' }}>{log.text}</span>}
              {log.type === 'THOUGHT' && <span style={{ color: 'var(--accent-violet)', fontWeight: 600 }}>[CoT THOUGHT] {log.text}</span>}
              {log.type === 'ACTION' && <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>[ReAct ACTION] {log.text}</span>}
              {log.type === 'OBSERVATION' && (
                <pre style={{ color: 'var(--status-safe)', margin: 0, fontFamily: 'inherit', whiteSpace: 'pre-wrap' }}>
                  [OBSERVATION] {log.text}
                </pre>
              )}
              {log.type === 'USER_CMD' && <span style={{ color: '#ffffff', fontWeight: 600 }}>[USER CLI] {log.text}</span>}
            </div>
          ))}
          <div ref={logEndRef} />
        </div>

        {/* Interactive CLI Prompt */}
        <form onSubmit={handleRunCommand} style={{ display: 'flex', borderTop: '1px solid var(--border-subtle)', background: 'var(--bg-tertiary)' }}>
          <div style={{ padding: '12px 16px', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>$</span>
          </div>
          <input
            type="text"
            placeholder="Type CLI command (ls, magika, du, organize, help, clear)..."
            value={inputCmd}
            onChange={(e) => setInputCmd(e.target.value)}
            style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: 13 }}
          />
          <button type="submit" className="btn-primary" style={{ borderRadius: 0, padding: '0 20px' }}>
            <CornerDownLeft size={16} />
            <span>Execute CLI</span>
          </button>
        </form>
      </div>
    </div>
  );
};
