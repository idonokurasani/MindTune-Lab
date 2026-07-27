import * as React from 'react';
import type { Tab } from '../state/sessionStore';

const TABS: { id: Tab; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'experiments', label: 'Experiments' },
  { id: 'session-create', label: 'Create Session' },
  { id: 'session-live', label: 'Live Session' },
  { id: 'session-review', label: 'Review' },
  { id: 'hebrew', label: 'Hebrew' },
  { id: 'system', label: 'System' },
];

interface AppShellProps {
  activeTab: Tab;
  setTab: (tab: Tab) => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ activeTab, setTab, children }) => {
  return (
    <div className="app-shell">
      <header>
        <h1>MindTune Research Console</h1>
        <nav aria-label="Primary navigation">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              aria-pressed={activeTab === t.id}
              aria-current={activeTab === t.id ? 'page' : undefined}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main id="main-content">{children}</main>
      <footer className="card" role="contentinfo">
        <p>CLM-05B Research Console — loopback API only — no credentials persisted.</p>
      </footer>
    </div>
  );
};
