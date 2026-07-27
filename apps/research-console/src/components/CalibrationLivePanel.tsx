import * as React from 'react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { StatusBadge } from './StatusBadge';
import type { CalibrationProfile } from '../api/models';

interface CalibrationLivePanelProps {
  participantId: string | null;
  profileId: string | null;
}

export const CalibrationLivePanel: React.FC<CalibrationLivePanelProps> = ({
  participantId,
  profileId,
}) => {
  const [profile, setProfile] = useState<CalibrationProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!participantId || !profileId) {
      setProfile(null);
      return;
    }
    setError(null);
    api
      .getCalibrationProfile(participantId, profileId)
      .then(setProfile)
      .catch(() => setError('Unable to load pinned calibration profile'));
  }, [participantId, profileId]);

  if (!participantId || !profileId) {
    return (
      <section className="card" aria-label="Calibration live display">
        <h3>Calibration</h3>
        <p>No profile pinned for this session.</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="card" aria-label="Calibration live display">
        <h3>Calibration</h3>
        <p className="warning">{error}</p>
      </section>
    );
  }

  if (!profile) {
    return (
      <section className="card" aria-label="Calibration live display">
        <h3>Calibration</h3>
        <p>Loading pinned profile…</p>
      </section>
    );
  }

  const compatible = profile.validity_status === 'valid' || profile.validity_status === 'degraded';
  const coverage = Object.keys(profile.feature_baselines);

  return (
    <section className="card" aria-label="Calibration live display">
      <h3>Calibration — Live Session</h3>
      <p>
        Pinned profile: {profile.profile_id} (version {profile.profile_version})
      </p>
      <p>
        Compatibility:{' '}
        <StatusBadge
          status={compatible ? 'healthy' : 'failed'}
          label={compatible ? 'compatible' : 'incompatible'}
        />
      </p>
      <p>Feature coverage: {coverage.length === 0 ? 'none' : coverage.join(', ')}</p>
      {profile.validity_status !== 'valid' && (
        <p className="warning" role="status">
          Calibration warning: profile is {profile.validity_status}
        </p>
      )}

      <h4>Raw vs calibrated features</h4>
      <table>
        <thead>
          <tr>
            <th>Feature</th>
            <th>Modality</th>
            <th>Raw (source)</th>
            <th>Calibrated</th>
            <th>Method</th>
            <th>Center</th>
            <th>Dispersion</th>
          </tr>
        </thead>
        <tbody>
          {coverage.map((name) => {
            const b = profile.feature_baselines[name];
            return (
              <tr key={name}>
                <td>{name}</td>
                <td>{b.modality}</td>
                <td>—</td>
                <td>—</td>
                <td>{b.transformation_recommendation}</td>
                <td>{b.central_tendency}</td>
                <td>{b.dispersion}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
};
