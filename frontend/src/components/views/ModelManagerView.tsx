import React from 'react';
import { ModelEntry } from '../../types';
import { Cpu, Download, CheckCircle2, Zap, ShieldCheck, HardDrive } from 'lucide-react';

interface ModelManagerViewProps {
  models: ModelEntry[];
  onToggleModel: (id: string) => void;
}

export const ModelManagerView: React.FC<ModelManagerViewProps> = ({ models, onToggleModel }) => {
  return (
    <div className="view-container">
      <div style={{ marginBottom: 20 }}>
        <h2 className="heading-lg">Local AI Models & Hardware Runtime Manager</h2>
        <p className="subheading">
          Manage local quantized model weights. Supports Google Magika, EmbeddingGemma 300M, and Gemma 4 E2B IT quantized reasoning lanes.
        </p>
      </div>

      {/* Hardware Benchmark Banner */}
      <div className="glass-panel" style={{ padding: 16, marginBottom: 20, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Detected Graphics GPU</div>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--accent-cyan)', marginTop: 2 }}>NVIDIA / DirectML (4GB+ VRAM)</div>
        </div>

        <div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Primary Edge Runtime</div>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--accent-violet)', marginTop: 2 }}>LiteRT-LM / llama.cpp</div>
        </div>

        <div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>CPU Multi-Thread Fallback</div>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--status-safe)', marginTop: 2 }}>16 Cores Active</div>
        </div>

        <div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Offline Privacy Status</div>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--status-safe)', marginTop: 2 }}>100% Local Inference</div>
        </div>
      </div>

      {/* Model Catalog Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
        {models.map((model) => (
          <div key={model.id} className="glass-panel" style={{ padding: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
              <div>
                <span className="badge badge-cyan" style={{ marginBottom: 6, display: 'inline-block' }}>
                  {model.category}
                </span>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>{model.name}</h3>
              </div>

              {model.installed ? (
                <span className="badge badge-safe" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  <CheckCircle2 size={12} /> Installed
                </span>
              ) : (
                <button className="btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }}>
                  <Download size={14} /> Download
                </button>
              )}
            </div>

            <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-secondary)', marginBottom: 16 }}>
              <span>Quantization: <code style={{ color: 'var(--text-primary)' }}>{model.quantization}</code></span>
              <span>Size: <code style={{ color: 'var(--text-primary)' }}>{model.sizeGb} GB</code></span>
              <span>Benchmark: <code style={{ color: 'var(--accent-cyan)' }}>{model.benchmarkScore} t/s</code></span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: 12 }}>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {model.active ? 'Currently Selected Active Lane' : 'Available for Offline Selection'}
              </span>

              <button
                className={model.active ? 'btn-primary' : 'btn-secondary'}
                style={{ padding: '6px 14px', fontSize: 12 }}
                onClick={() => onToggleModel(model.id)}
                disabled={!model.installed}
              >
                {model.active ? 'Active Lane' : 'Select Lane'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
