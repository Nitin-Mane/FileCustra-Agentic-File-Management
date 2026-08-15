import React, { useState } from 'react';
import { HelpCircle, Check, ArrowRight, RotateCcw, Filter, FolderPlus, Tag } from 'lucide-react';

interface GuidedQueryViewProps {
  onCompleteQuery: (answers: Record<string, string>) => void;
}

export const GuidedQueryView: React.FC<GuidedQueryViewProps> = ({ onCompleteQuery }) => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [answers, setAnswers] = useState<Record<string, string>>({
    primaryGoal: 'ORGANIZE_PROJECTS',
    depthPreference: 'MAX_3_LEVELS',
    namingConvention: 'SNAKE_CASE_LOWERCASE',
    duplicatePolicy: 'AUTO_INDEX_SUFFIX',
    protectedFolders: 'EXCLUDE_GIT_AND_NODE_MODULES',
  });

  const steps = [
    {
      num: 1,
      question: 'What is your primary goal for this file collection?',
      field: 'primaryGoal',
      options: [
        { label: 'Group files into project & client domain folders', value: 'ORGANIZE_PROJECTS' },
        { label: 'Sort documents by year, quarter, and month timeline', value: 'SORT_BY_DATE' },
        { label: 'Separate code repositories from assets & media', value: 'SEPARATE_CODE_MEDIA' },
        { label: 'Identify and isolate duplicate/near-duplicate files', value: 'ISOLATE_DUPLICATES' },
      ],
    },
    {
      num: 2,
      question: 'What is your preferred maximum folder tree depth?',
      field: 'depthPreference',
      options: [
        { label: 'Shallow (Maximum 2 folder levels deep)', value: 'SHALLOW_2_LEVELS' },
        { label: 'Balanced (Maximum 3 folder levels deep - Recommended)', value: 'MAX_3_LEVELS' },
        { label: 'Deep (Hierarchical taxonomies up to 5 levels deep)', value: 'DEEP_5_LEVELS' },
      ],
    },
    {
      num: 3,
      question: 'Which file & folder naming convention do you prefer?',
      field: 'namingConvention',
      options: [
        { label: 'snake_case (e.g. 2026_q3_financial_report.pdf)', value: 'SNAKE_CASE_LOWERCASE' },
        { label: 'Title Case with Spaces (e.g. 2026 Q3 Financial Report.pdf)', value: 'TITLE_CASE' },
        { label: 'kebab-case (e.g. 2026-q3-financial-report.pdf)', value: 'KEBAB_CASE' },
        { label: 'Preserve original file names intact', value: 'PRESERVE_ORIGINAL' },
      ],
    },
    {
      num: 4,
      question: 'How should path & file name collisions be handled?',
      field: 'duplicatePolicy',
      options: [
        { label: 'Auto-append numeric suffix (e.g. report_(1).pdf) - Safe', value: 'AUTO_INDEX_SUFFIX' },
        { label: 'Move duplicates to dedicated _Duplicates folder', value: 'MOVE_TO_DUPLICATE_DIR' },
        { label: 'Prompt user for manual confirmation before writing', value: 'PROMPT_USER' },
      ],
    },
    {
      num: 5,
      question: 'Are there system or code directories to protect & skip?',
      field: 'protectedFolders',
      options: [
        { label: 'Exclude .git, node_modules, build, .env, and system files', value: 'EXCLUDE_GIT_AND_NODE_MODULES' },
        { label: 'Exclude hidden files (starting with dot .)', value: 'EXCLUDE_DOTFILES' },
        { label: 'Include all non-executable files in analysis', value: 'INCLUDE_ALL' },
      ],
    },
  ];

  const handleSelectOption = (field: string, val: string) => {
    setAnswers({ ...answers, [field]: val });
  };

  const handleNext = () => {
    if (currentStep < 5) setCurrentStep(currentStep + 1);
    else onCompleteQuery(answers);
  };

  const currentConfig = steps[currentStep - 1];

  return (
    <div className="view-container">
      <div style={{ marginBottom: 20 }}>
        <h2 className="heading-lg">Guided Query Workflow (5-Question Intent Compiler)</h2>
        <p className="subheading">
          Answer 5 simple structured questions to tailor the organization rules to your exact personal preferences.
        </p>
      </div>

      {/* Progress Steps Header */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        {steps.map((s) => (
          <div
            key={s.num}
            style={{
              flex: 1,
              padding: '10px 14px',
              borderRadius: 'var(--radius-sm)',
              background: currentStep === s.num ? 'var(--accent-cyan-glow)' : 'var(--bg-tertiary)',
              border: `1px solid ${currentStep === s.num ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
              color: currentStep === s.num ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              fontSize: 12,
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>Question {s.num}</span>
            {currentStep > s.num && <Check size={14} color="var(--status-safe)" />}
          </div>
        ))}
      </div>

      {/* Main Question Card */}
      <div className="glass-panel" style={{ padding: 24, marginBottom: 24 }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 20, color: 'var(--text-primary)' }}>
          {currentConfig.num}. {currentConfig.question}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {currentConfig.options.map((opt) => {
            const isSelected = answers[currentConfig.field] === opt.value;
            return (
              <div
                key={opt.value}
                style={{
                  padding: 16,
                  borderRadius: 'var(--radius-sm)',
                  background: isSelected ? 'rgba(6, 182, 212, 0.1)' : 'var(--bg-tertiary)',
                  border: `1px solid ${isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all var(--transition-fast)',
                }}
                onClick={() => handleSelectOption(currentConfig.field, opt.value)}
              >
                <span style={{ fontSize: 14, fontWeight: isSelected ? 600 : 400, color: isSelected ? 'var(--accent-cyan)' : 'var(--text-primary)' }}>
                  {opt.label}
                </span>
                {isSelected && <Check size={18} color="var(--accent-cyan)" />}
              </div>
            );
          })}
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          className="btn-secondary"
          onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
          disabled={currentStep === 1}
        >
          <RotateCcw size={16} />
          <span>Previous Step</span>
        </button>

        <button className="btn-primary" onClick={handleNext}>
          <span>{currentStep === 5 ? 'Compile Rules & Generate Plan' : 'Next Question'}</span>
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
};
