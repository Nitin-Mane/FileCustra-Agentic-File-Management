import React, { useState, useEffect } from 'react';
import { SplashView } from './components/views/SplashView';
import { WelcomeView } from './components/views/WelcomeView';
import { DriveDashboardView } from './components/views/DriveDashboardView';
import { OnboardingSetupView } from './components/views/OnboardingSetupView';
import { SecuritySettingsView } from './components/views/SecuritySettingsView';
import { FileOrganizationFlowView } from './components/views/FileOrganizationFlowView';

import { Header } from './components/Header';
import { Sidebar, NavTab } from './components/Sidebar';
import { PrismRail } from './components/PrismRail';
import { Footer } from './components/Footer';

import { HomeView } from './components/views/HomeView';
import { DiscoveryView } from './components/views/DiscoveryView';
import { ConstellationView } from './components/views/ConstellationView';
import { ModeSelectionView } from './components/views/ModeSelectionView';
import { AutoAiView } from './components/views/AutoAiView';
import { GuidedQueryView } from './components/views/GuidedQueryView';
import { OperationPlanView } from './components/views/OperationPlanView';
import { JournalUndoView } from './components/views/JournalUndoView';
import { ModelManagerView } from './components/views/ModelManagerView';
import { SettingsView } from './components/views/SettingsView';
import { TerminalView } from './components/views/TerminalView';

import { StageType, FileItem, OperationPlanStep, OperationJournalEntry, ModelEntry, SystemSnapshot } from './types';
import { loadSystemSnapshot } from './services/systemSnapshot';

type AppFlowState = 'SPLASH' | 'WELCOME' | 'DASHBOARD' | 'ONBOARDING' | 'SECURITY_SETTINGS' | 'MAIN_APP';

export const App: React.FC = () => {
  const [flowState, setFlowState] = useState<AppFlowState>('SPLASH');
  const [hasCompletedSetup, setHasCompletedSetup] = useState<boolean>(() => {
    return localStorage.getItem('filecustra_setup_completed') === 'true';
  });

  const [systemSnapshot, setSystemSnapshot] = useState<SystemSnapshot | undefined>(undefined);

  useEffect(() => {
    loadSystemSnapshot().then((snapshot) => setSystemSnapshot(snapshot));
  }, []);

  const [activeTab, setActiveTab] = useState<NavTab>('discovery');
  const [currentStage, setCurrentStage] = useState<StageType>('SCOPED');
  const [scopedFolder, setScopedFolder] = useState<string>('D:\\fullstack_ai_project\\Sample_Corpus');
  const [privacyLock, setPrivacyLock] = useState<boolean>(true);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [selectedEngineMode, setSelectedEngineMode] = useState<'AUTONOMOUS' | 'GUIDED_INTERACTIVE'>('AUTONOMOUS');

  const [files, setFiles] = useState<FileItem[]>([
    {
      id: 'f1',
      name: '2026_Q3_Financial_Audit.pdf',
      path: 'Unorganized/Docs/2026_Q3_Financial_Audit.pdf',
      extension: 'pdf',
      sizeBytes: 1542000,
      mimeType: 'application/pdf',
      magikaType: 'PDF Document',
      ocrExtracted: true,
      riskCategory: 'SAFE',
      tags: ['finance', 'audit', '2026', 'tax'],
    },
    {
      id: 'f2',
      name: 'architecture_diagram.png',
      path: 'Unorganized/Images/architecture_diagram.png',
      extension: 'png',
      sizeBytes: 890000,
      mimeType: 'image/png',
      magikaType: 'PNG Image',
      ocrExtracted: false,
      riskCategory: 'SAFE',
      tags: ['diagram', 'tauri', 'rust'],
    },
    {
      id: 'f3',
      name: 'sidecar_ipc_handler.py',
      path: 'Unorganized/Code/sidecar_ipc_handler.py',
      extension: 'py',
      sizeBytes: 14500,
      mimeType: 'text/x-python',
      magikaType: 'Python Source Code',
      ocrExtracted: false,
      riskCategory: 'SAFE',
      tags: ['python', 'sidecar', 'json-rpc'],
    },
    {
      id: 'f4',
      name: 'employee_payroll_2026.xlsx',
      path: 'Unorganized/Sheets/employee_payroll_2026.xlsx',
      extension: 'xlsx',
      sizeBytes: 340000,
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      magikaType: 'Excel Spreadsheet',
      ocrExtracted: false,
      riskCategory: 'SAFE',
      tags: ['payroll', 'hr', '2026'],
    },
    {
      id: 'f5',
      name: 'scan_receipt_apple_store.pdf',
      path: 'Unorganized/Scans/scan_receipt_apple_store.pdf',
      extension: 'pdf',
      sizeBytes: 2100000,
      mimeType: 'application/pdf',
      magikaType: 'Scanned PDF Document',
      ocrExtracted: true,
      riskCategory: 'SAFE',
      tags: ['receipt', 'apple', 'hardware', 'ocr'],
    },
  ]);

  const [operationSteps, setOperationSteps] = useState<OperationPlanStep[]>([
    {
      id: 'op1',
      sourcePath: 'Unorganized/Docs/2026_Q3_Financial_Audit.pdf',
      targetPath: 'Finance/Audits/2026/2026_Q3_Financial_Audit.pdf',
      operationType: 'MOVE',
      rationale: 'Gemma CoT Rationale: Grouped by semantic domain (Finance) and chronological year (2026)',
      collisionStatus: 'NONE',
    },
    {
      id: 'op2',
      sourcePath: 'Unorganized/Images/architecture_diagram.png',
      targetPath: 'Assets/Diagrams/architecture_diagram.png',
      operationType: 'MOVE',
      rationale: 'Gemma CoT Rationale: Categorized by Magika format (PNG) and tag (diagram)',
      collisionStatus: 'NONE',
    },
    {
      id: 'op3',
      sourcePath: 'Unorganized/Code/sidecar_ipc_handler.py',
      targetPath: 'Engineering/Sidecar/sidecar_ipc_handler.py',
      operationType: 'MOVE',
      rationale: 'Gemma CoT Rationale: Isolated into engineering module folder structure',
      collisionStatus: 'NONE',
    },
    {
      id: 'op4',
      sourcePath: 'Unorganized/Sheets/employee_payroll_2026.xlsx',
      targetPath: 'HR/Payroll/employee_payroll_2026.xlsx',
      operationType: 'MOVE',
      rationale: 'Gemma CoT Rationale: Grouped into HR domain hierarchy',
      collisionStatus: 'NONE',
    },
  ]);

  const [journalEntries, setJournalEntries] = useState<OperationJournalEntry[]>([
    {
      id: 'j-20260814-01',
      timestamp: '2026-08-14 22:15:00',
      sessionId: 'sess-8812',
      operationCount: 4,
      status: 'COMPLETED',
      steps: operationSteps,
    },
  ]);

  const [models, setModels] = useState<ModelEntry[]>([
    {
      id: 'm1',
      name: 'Google Magika File Type Classifier',
      category: 'CLASSIFICATION',
      quantization: 'INT8',
      sizeGb: 0.05,
      installed: true,
      active: true,
      benchmarkScore: 1200,
    },
    {
      id: 'm2',
      name: 'EmbeddingGemma 300M Vector Model',
      category: 'EMBEDDING',
      quantization: 'Q8_0',
      sizeGb: 0.32,
      installed: true,
      active: true,
      benchmarkScore: 450,
    },
    {
      id: 'm3',
      name: 'Gemma 4 E2B IT Quantized Reasoning Agent',
      category: 'REASONING',
      quantization: 'Q4_K_M',
      sizeGb: 1.85,
      installed: true,
      active: true,
      benchmarkScore: 48,
    },
  ]);

  const handleLaunchFileManagement = () => {
    setFlowState('MAIN_APP');
    setActiveTab('discovery');
    setCurrentStage('SCOPED');
  };

  const handleFinishSetup = () => {
    localStorage.setItem('filecustra_setup_completed', 'true');
    setHasCompletedSetup(true);
    setFlowState('MAIN_APP');
    setActiveTab('discovery');
    setCurrentStage('SCOPED');
  };

  const handleStartAnalysis = () => {
    setIsAnalyzing(true);
    setCurrentStage('ANALYZING');
    setTimeout(() => {
      setIsAnalyzing(false);
      setCurrentStage('ANALYZING');
    }, 1200);
  };

  const handleEngineModeSelected = (mode: 'AUTONOMOUS' | 'GUIDED_INTERACTIVE') => {
    setSelectedEngineMode(mode);
    if (mode === 'AUTONOMOUS') {
      setCurrentStage('STRATEGY');
      setActiveTab('auto-ai');
    } else {
      setCurrentStage('STRATEGY');
      setActiveTab('guided-query');
    }
  };

  const handleGeneratePlan = (topology: string) => {
    setCurrentStage('DRY_RUN');
    setActiveTab('operation-plan');
  };

  const handleExecutePlan = () => {
    setIsExecuting(true);
    setCurrentStage('EXECUTING');
    setTimeout(() => {
      setIsExecuting(false);
      setCurrentStage('VERIFIED');
      setActiveTab('journal-undo');
    }, 1500);
  };

  const handleRollback = (entryId: string) => {
    setJournalEntries(
      journalEntries.map((j) => (j.id === entryId ? { ...j, status: 'ROLLED_BACK' } : j))
    );
  };

  const handleToggleModel = (id: string) => {
    setModels(models.map((m) => (m.id === id ? { ...m, active: !m.active } : m)));
  };

  // Flow State Renders
  if (flowState === 'SPLASH') {
    return <SplashView onComplete={() => setFlowState('WELCOME')} />;
  }

  if (flowState === 'WELCOME') {
    return <WelcomeView onContinue={() => setFlowState('DASHBOARD')} />;
  }

  if (flowState === 'DASHBOARD') {
    return (
      <DriveDashboardView
        onOpenWorkspace={handleLaunchFileManagement}
        onOpenSecuritySettings={() => setFlowState('SECURITY_SETTINGS')}
        systemSnapshot={systemSnapshot}
      />
    );
  }

  if (flowState === 'SECURITY_SETTINGS') {
    return (
      <SecuritySettingsView
        onBackToDashboard={() => setFlowState('DASHBOARD')}
        privacyLock={privacyLock}
        onTogglePrivacyLock={() => setPrivacyLock(!privacyLock)}
      />
    );
  }

  if (flowState === 'ONBOARDING') {
    return <OnboardingSetupView onCompleteSetup={handleFinishSetup} />;
  }

  // MAIN_APP State: full-screen guided process. The old module pages remain in
  // source, but the user-facing journey is intentionally sequenced here.
  return (
    <FileOrganizationFlowView
      scopedFolder={scopedFolder}
      files={files}
      operationSteps={operationSteps}
      journalEntries={journalEntries}
      isExecuting={isExecuting}
      onSelectFolder={setScopedFolder}
      onExecutePlan={handleExecutePlan}
      onRollback={handleRollback}
      onBackToDashboard={() => setFlowState('DASHBOARD')}
    />
  );
};
