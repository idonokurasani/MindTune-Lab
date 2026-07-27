import * as React from 'react';
import { useState } from 'react';
import type { ControlCommandName } from '../api/models';

const COMMAND_ORDER: ControlCommandName[] = ['prepare', 'start', 'pause', 'resume', 'freeze', 'unfreeze', 'force_baseline', 'release_baseline', 'stop', 'kill'];

interface SafetyControlsProps {
  disabled?: boolean;
  onCommand: (command: ControlCommandName) => void;
}

const labels: Record<ControlCommandName, string> = {
  prepare: 'Prepare',
  start: 'Start',
  pause: 'Pause',
  resume: 'Resume',
  freeze: 'Freeze',
  unfreeze: 'Unfreeze',
  force_baseline: 'Force Baseline',
  release_baseline: 'Release Baseline',
  stop: 'Stop',
  kill: 'Kill',
  step: 'Step',
};

export const SafetyControls: React.FC<SafetyControlsProps> = ({ disabled, onCommand }) => {
  const [confirming, setConfirming] = useState<ControlCommandName | null>(null);

  const handle = (command: ControlCommandName) => {
    if (command === 'kill') {
      if (confirming === 'kill') {
        onCommand(command);
        setConfirming(null);
      } else {
        setConfirming('kill');
      }
      return;
    }
    onCommand(command);
  };

  return (
    <section className="card" aria-label="Safety controls">
      <h2>Safety Controls</h2>
      <div className="grid">
        {COMMAND_ORDER.map((cmd) => (
          <button
            key={cmd}
            onClick={() => handle(cmd)}
            disabled={disabled}
            aria-describedby={cmd === 'kill' ? 'kill-warning' : undefined}
          >
            {cmd === 'kill' && confirming === 'kill' ? 'Confirm Kill' : labels[cmd]}
          </button>
        ))}
      </div>
      <p id="kill-warning" role="alert" aria-live="polite">
        {confirming === 'kill' ? 'Click again to confirm session kill.' : '\u00A0'}
      </p>
    </section>
  );
};
