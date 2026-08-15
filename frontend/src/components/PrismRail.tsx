import React from 'react';
import { StageType } from '../types';
import { CheckCircle2, Circle, ArrowRight } from 'lucide-react';

interface PrismRailProps {
  currentStage: StageType;
}

const STAGES: { id: StageType; label: string }[] = [
  { id: 'SCOPED', label: '1. Folder Scoped' },
  { id: 'ENUMERATING', label: '2. Enumerating Files' },
  { id: 'ANALYZING', label: '3. Magika & OCR Analysis' },
  { id: 'STRATEGY', label: '4. Strategy Topology' },
  { id: 'DRY_RUN', label: '5. Dry-Run Plan' },
  { id: 'EXECUTING', label: '6. Safe Execution' },
  { id: 'VERIFIED', label: '7. Verified & Journaled' },
];

export const PrismRail: React.FC<PrismRailProps> = ({ currentStage }) => {
  const currentIndex = STAGES.findIndex((s) => s.id === currentStage);

  return (
    <div className="prism-rail">
      {STAGES.map((stage, idx) => {
        const isCompleted = idx < currentIndex;
        const isActive = idx === currentIndex;

        return (
          <React.Fragment key={stage.id}>
            <div className={`stage-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
              {isCompleted ? (
                <CheckCircle2 size={14} color="var(--status-safe)" />
              ) : isActive ? (
                <div className="stage-dot" />
              ) : (
                <Circle size={12} color="var(--text-muted)" />
              )}
              <span>{stage.label}</span>
            </div>
            {idx < STAGES.length - 1 && (
              <ArrowRight size={12} color={isCompleted ? 'var(--status-safe)' : 'var(--border-subtle)'} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
