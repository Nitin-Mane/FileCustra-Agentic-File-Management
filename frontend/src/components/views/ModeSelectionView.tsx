import React from 'react';
import { Sparkles, HelpCircle, ArrowRight, ArrowLeft, ShieldCheck, Cpu, Bot, Route } from 'lucide-react';

interface ModeSelectionViewProps {
  onSelectMode: (mode: 'AUTONOMOUS' | 'GUIDED_INTERACTIVE') => void;
  onBack: () => void;
  scopedFolder: string;
  totalFiles: number;
}

export const ModeSelectionView: React.FC<ModeSelectionViewProps> = ({
  onSelectMode,
  onBack,
  scopedFolder,
  totalFiles,
}) => {
  return (
    <div className="view-container phase-home" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      
      {/* Header & Breadcrumb Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <button className="btn-ghost" onClick={onBack} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 8, padding: '4px 10px' }}>
            <ArrowLeft size={14} />
            <span>Back to File Types & Formatting</span>
          </button>
          <h2 className="heading-lg" style={{ margin: 0 }}>Step 3: Select Agentic Execution Engine</h2>
          <p className="subheading" style={{ margin: '4px 0 0 0' }}>
            Choose how Gemma Reinforcement Learning & Chain-of-Thought reasoning should structure your workspace.
          </p>
        </div>

        <div className="eyebrow-pill">
          <ShieldCheck size={14} />
          <span>Read-Only Preview Required</span>
        </div>
      </div>

      {/* Workspace Context Chip */}
      <div className="glass-panel" style={{ padding: '12px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Cpu size={18} color="var(--accent-cyan)" />
          <div>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
              Active Corpus Target
            </span>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
              {scopedFolder}
            </div>
          </div>
        </div>
        <span className="badge badge-cyan" style={{ fontSize: 12 }}>{totalFiles} Scanned Files</span>
      </div>

      {/* TWO ETHICAL PROFESSIONAL ENGINE SELECTION CARDS */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, margin: '8px 0' }}>
        
        {/* OPTION 1: AUTONOMOUS INTELLIGENT AGENT ENGINE */}
        <div
          className="glass-panel module-card"
          style={{
            padding: 24,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)',
            cursor: 'pointer',
            transition: 'all var(--transition-normal)',
            position: 'relative',
            overflow: 'hidden',
          }}
          onClick={() => onSelectMode('AUTONOMOUS')}
        >
          <div style={{ position: 'absolute', top: 0, right: 0, width: 120, height: 120, background: 'radial-gradient(circle, rgba(6, 182, 212, 0.15) 0%, transparent 70%)', pointerEvents: 'none' }} />
          
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ width: 44, height: 44, borderRadius: 'var(--radius-md)', background: 'rgba(6, 182, 212, 0.12)', border: '1px solid var(--accent-cyan)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Sparkles size={24} color="var(--accent-cyan)" />
              </div>
              <span className="badge badge-cyan" style={{ fontSize: 10 }}>RECOMMENDED</span>
            </div>

            <h3 style={{ fontSize: 18, fontWeight: 700, margin: '0 0 8px 0', color: 'var(--text-primary)' }}>
              Autonomous Intelligent Agent Engine
            </h3>

            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 16 }}>
              Self-optimizing Reinforcement Learning (RLHF/RLAIF) heuristic strategy planner with Chain-of-Thought (CoT) reasoning loops. Automatically clusters files by Magika type, project semantics, and creation timelines.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12, color: 'var(--text-secondary)', marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Route size={14} color="var(--accent-cyan)" />
                <span>4 Parallel Strategy Topologies (Chronological, Format, Semantic, Project)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <ShieldCheck size={14} color="var(--status-safe)" />
                <span>Zero-Loss Dry-Run Technical Execution Plan</span>
              </div>
            </div>
          </div>

          <button className="btn-primary btn-lg" style={{ width: '100%', justifyContent: 'center' }}>
            <span>Launch Autonomous Engine</span>
            <ArrowRight size={18} />
          </button>
        </div>

        {/* OPTION 2: GUIDED INTERACTIVE AGENT ASSISTANT */}
        <div
          className="glass-panel module-card"
          style={{
            padding: 24,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)',
            cursor: 'pointer',
            transition: 'all var(--transition-normal)',
            position: 'relative',
            overflow: 'hidden',
          }}
          onClick={() => onSelectMode('GUIDED_INTERACTIVE')}
        >
          <div style={{ position: 'absolute', top: 0, right: 0, width: 120, height: 120, background: 'radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%)', pointerEvents: 'none' }} />

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ width: 44, height: 44, borderRadius: 'var(--radius-md)', background: 'rgba(139, 92, 246, 0.12)', border: '1px solid var(--accent-violet)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Bot size={24} color="var(--accent-violet)" />
              </div>
              <span className="badge badge-violet" style={{ fontSize: 10 }}>INTERACTIVE DIALOGUE</span>
            </div>

            <h3 style={{ fontSize: 18, fontWeight: 700, margin: '0 0 8px 0', color: 'var(--text-primary)' }}>
              Guided Interactive Agent Assistant
            </h3>

            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 16 }}>
              Step-by-step 5-question structured intent dialogue to customize precise organization rules. Interactive prompt refinement ensures customized folder hierarchies tailored to your exact workflow requirements.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12, color: 'var(--text-secondary)', marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <HelpCircle size={14} color="var(--accent-violet)" />
                <span>5 Focused Intent Questions (Domain, Format, Archival, Rules)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <ShieldCheck size={14} color="var(--status-safe)" />
                <span>Custom Rule Synthesis into Gemma Technical Plan</span>
              </div>
            </div>
          </div>

          <button className="btn-secondary btn-lg" style={{ width: '100%', justifyContent: 'center', borderColor: 'var(--accent-violet)' }}>
            <span>Launch Guided Interactive Assistant</span>
            <ArrowRight size={18} />
          </button>
        </div>

      </div>

      {/* Footer Safety Note */}
      <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', marginTop: 4 }}>
        🔒 Both execution modes generate a dry-run technical plan model for your approval before any physical file operations are committed.
      </div>
    </div>
  );
};
