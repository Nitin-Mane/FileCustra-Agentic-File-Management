import React, { useState } from 'react';
import { Sparkles, Calendar, FolderTree, FileType, Network, CheckCircle2, ArrowRight } from 'lucide-react';

interface AutoAiViewProps {
  onGeneratePlan: (topology: string) => void;
}

export const AutoAiView: React.FC<AutoAiViewProps> = ({ onGeneratePlan }) => {
  const [selectedTopology, setSelectedTopology] = useState<string>('PROJECT');

  const topologies = [
    {
      id: 'PROJECT',
      name: 'Project & Domain Based',
      icon: FolderTree,
      color: 'var(--accent-cyan)',
      description: 'Groups files into clear project domain folders (e.g. Finance, Engineering, Research, Marketing) based on content semantics.',
      example: 'Documents/Projects/2026_Q3_Financial_Audit/invoice_01.pdf',
    },
    {
      id: 'CHRONOLOGICAL',
      name: 'Date & Time Chronological',
      icon: Calendar,
      color: 'var(--accent-violet)',
      description: 'Organizes files by creation or modification timeline into structured Year / Month / Quarter hierarchies.',
      example: 'Archives/2026/08_August/2026-08-14_Research_Report.pdf',
    },
    {
      id: 'TYPE_FORMAT',
      name: 'File Type & Extension',
      icon: FileType,
      color: 'var(--status-safe)',
      description: 'Sorts files deterministically into verified Magika MIME format categories (PDFs, Source Code, Spreadsheets, Media).',
      example: 'Media/Images/PNG/diagram_architecture.png',
    },
    {
      id: 'SEMANTIC_CLUSTER',
      name: 'EmbeddingGemma Semantic Cluster',
      icon: Network,
      color: 'var(--accent-blue)',
      description: 'Uses 300M vector embeddings and cosine similarity clustering to group topically related content across formats.',
      example: 'Clusters/Tax_Returns_&_Receipts/receipt_apple_2026.pdf',
    },
  ];

  return (
    <div className="view-container">
      <div style={{ marginBottom: 20 }}>
        <h2 className="heading-lg">Auto AI Topology Planner (Gemma Agent Core)</h2>
        <p className="subheading">
          Select an organizational topology. Local Gemma model evaluates file metadata and semantic vectors to propose a deterministic folder hierarchy.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16, marginBottom: 24 }}>
        {topologies.map((t) => {
          const Icon = t.icon;
          const isSelected = selectedTopology === t.id;

          return (
            <div
              key={t.id}
              className={`glass-panel`}
              style={{
                padding: 20,
                cursor: 'pointer',
                borderColor: isSelected ? t.color : 'var(--border-subtle)',
                boxShadow: isSelected ? `0 0 20px ${t.color}33` : 'var(--shadow-card)',
                transition: 'all var(--transition-normal)',
              }}
              onClick={() => setSelectedTopology(t.id)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ padding: 10, borderRadius: 'var(--radius-sm)', background: `${t.color}22` }}>
                    <Icon size={20} color={t.color} />
                  </div>
                  <h3 style={{ fontSize: 16, fontWeight: 600 }}>{t.name}</h3>
                </div>
                {isSelected && <CheckCircle2 size={20} color={t.color} />}
              </div>

              <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16, lineHeight: 1.5 }}>
                {t.description}
              </p>

              <div style={{ background: 'var(--bg-tertiary)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', fontSize: 12, fontFamily: 'var(--font-mono)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Target Pattern: </span>
                <span style={{ color: t.color }}>{t.example}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="glass-panel" style={{ padding: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>Ready to Generate Strategy Plan?</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
            Generates a dry-run operation plan with 0 direct filesystem mutations until you approve.
          </div>
        </div>

        <button className="btn-primary" onClick={() => onGeneratePlan(selectedTopology)}>
          <Sparkles size={16} />
          <span>Generate Dry-Run Plan with Gemma AI</span>
        </button>
      </div>
    </div>
  );
};
