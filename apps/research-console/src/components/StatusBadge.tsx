import * as React from 'react';
import type { HealthStatus } from '../api/models';

interface StatusBadgeProps {
  status: HealthStatus | string;
  label: string;
  message?: string;
}

export const statusText = (status: string): string => {
  switch (status) {
    case 'healthy':
      return 'healthy';
    case 'degraded':
      return 'degraded';
    case 'stale':
      return 'stale';
    case 'disconnected':
      return 'disconnected';
    case 'failed':
      return 'failed';
    case 'stopped':
      return 'stopped';
    default:
      return 'unknown';
  }
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label, message }) => {
  const text = statusText(status);
  return (
    <span className={`badge badge--${text}`} role="status" aria-label={`${label}: ${text}`}>
      {label}: {text}
      {message ? <span className="sr-only">; {message}</span> : null}
    </span>
  );
};
