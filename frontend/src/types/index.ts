export type StageType = 'SCOPED' | 'ENUMERATING' | 'ANALYZING' | 'STRATEGY' | 'DRY_RUN' | 'EXECUTING' | 'VERIFIED';

export interface FileItem {
  id: string;
  path: string;
  name: string;
  extension: string;
  sizeBytes: number;
  mimeType: string;
  magikaType: string;
  hashSha256?: string;
  isScannedPdf?: boolean;
  ocrExtracted?: boolean;
  riskCategory: 'SAFE' | 'UNKNOWN' | 'EXECUTABLE' | 'ARCHIVE';
  tags: string[];
}

export interface OperationPlanStep {
  id: string;
  sourcePath: string;
  targetPath: string;
  operationType: 'MOVE' | 'RENAME' | 'COPY' | 'CREATE_DIR';
  rationale: string;
  collisionStatus: 'NONE' | 'OVERWRITE_PREVENTED' | 'AUTO_INDEXED';
}

export interface OperationJournalEntry {
  id: string;
  timestamp: string;
  sessionId: string;
  operationCount: number;
  status: 'COMPLETED' | 'ROLLED_BACK';
  steps: OperationPlanStep[];
}

export interface ModelEntry {
  id: string;
  name: string;
  category: 'CLASSIFICATION' | 'EMBEDDING' | 'REASONING' | 'VISION';
  quantization: string;
  sizeGb: number;
  installed: boolean;
  active: boolean;
  benchmarkScore: number;
}

export interface DriveSnapshot {
  letter: string;
  name: string;
  usedGb: number;
  totalGb: number;
  freeGb: number;
  color: string;
  type: string;
  health: string;
}

export interface RuntimeSnapshot {
  sidecarStatus: 'READY' | 'BOOTING' | 'DEGRADED';
  privacyMode: 'OFFLINE_LOCKED' | 'ONLINE_ALLOWED';
  hardwareSummary: string;
  modelRuntime: string;
  indexedFiles: number;
  queuedTasks: number;
}

export interface HardwareMetric {
  id: string;
  label: string;
  value: string;
  detail: string;
  utilizationPct?: number;
  status: 'GOOD' | 'WARN' | 'ACTION';
}

export interface SecurityControl {
  id: string;
  label: string;
  state: string;
  detail: string;
  enabled: boolean;
}

export interface SettingsControl {
  id: string;
  label: string;
  value: string;
  detail: string;
}

export interface PhaseMilestone {
  id: string;
  title: string;
  description: string;
  status: 'DONE' | 'ACTIVE' | 'NEXT';
}

export interface SystemSnapshot {
  runtime: RuntimeSnapshot;
  drives: DriveSnapshot[];
  hardware: HardwareMetric[];
  security: SecurityControl[];
  settings: SettingsControl[];
  phaseOneMilestones: PhaseMilestone[];
}
