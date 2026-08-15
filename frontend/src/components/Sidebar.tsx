import React from 'react';
import {
  FolderSearch,
  Activity,
  Cpu,
  Settings,
  Terminal,
  Layers,
  Bot,
  FileCheck,
  Undo2,
  SlidersHorizontal,
} from 'lucide-react';

export type NavTab =
  | 'home'
  | 'discovery'
  | 'constellation'
  | 'mode-selection'
  | 'auto-ai'
  | 'terminal'
  | 'guided-query'
  | 'operation-plan'
  | 'journal-undo'
  | 'models'
  | 'settings';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab }) => {
  const items = [
    { id: 'discovery' as NavTab, label: '1. Folder Selection', icon: FolderSearch },
    { id: 'constellation' as NavTab, label: '2. File Formatting Matrix', icon: Layers },
    { id: 'mode-selection' as NavTab, label: '3. Select Execution Engine', icon: SlidersHorizontal },
    { id: 'operation-plan' as NavTab, label: '4. Gemma Technical Plan', icon: FileCheck },
    { id: 'journal-undo' as NavTab, label: '5. Safe Execution & Rollback', icon: Undo2 },
    { id: 'terminal' as NavTab, label: 'Terminal Console', icon: Terminal },
    { id: 'models' as NavTab, label: 'Local Models Library', icon: Cpu },
    { id: 'settings' as NavTab, label: 'Security & Preferences', icon: Settings },
  ];

  return (
    <aside className="app-sidebar">
      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', padding: '4px 8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Guided Sequential Steps
      </div>
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = activeTab === item.id;
        return (
          <div
            key={item.id}
            className={`nav-item ${isActive ? 'active' : ''}`}
            onClick={() => onSelectTab(item.id)}
          >
            <Icon size={17} color={isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)'} />
            <span>{item.label}</span>
          </div>
        );
      })}
    </aside>
  );
};
