import * as React from 'react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import type { CalibrationProfile, CalibrationProfileList, CalibrationStatus } from '../api/models';

const CalibrationOverviewPage: React.FC = () => {
  const [participantId, setParticipantId] = useState('anon-1');
  const [status, setStatus] = useState<CalibrationStatus | null>(null);
  const [profiles, setProfiles] = useState<CalibrationProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [selectionReason, setSelectionReason] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, p] = await Promise.all([
        api.getCalibrationStatus(participantId),
        api.listCalibrationProfiles(participantId),
      ]);
      setStatus(s);
      setProfiles(p.items);
    } catch {
      setError('Failed to load calibration overview');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [participantId]);

  const handleSelect = async (profileId: string) => {
    try {
      const result = await api.selectCalibrationProfile(participantId, profileId);
      setSelectedProfileId(result.profile_id);
      setSelectionReason(result.reason);
      await load();
    } catch {
      setError('Failed to select profile');
    }
  };

  const recalibrationNeeded =
    status && (status.valid_profiles === 0 || profiles.length === 0);

  return (
    <section aria-label="Calibration overview">
      <h2>Calibration Overview</h2>

      <section className="card">
        <label>
          Participant pseudonym
          <input
            type="text"
            value={participantId}
            onChange={(e) => setParticipantId(e.target.value)}
            aria-label="Participant pseudonym"
          />
        </label>
        <button onClick={load} disabled={loading}>
          Refresh
        </button>
      </section>

      {error && <div className="error-banner" role="alert">{error}</div>}

      {status && (
        <section className="card" aria-label="Calibration status">
          <h3>Status</h3>
          <p>Participant: {status.participant_id}</p>
          <p>Total profiles: {status.total_profiles}</p>
          <p>Valid profiles: {status.valid_profiles}</p>
          <p>Latest profile: {status.latest_profile_id ?? '—'}</p>
          {recalibrationNeeded && (
            <p className="warning" role="status">
              Recalibration recommended: no valid profile is available.
            </p>
          )}
        </section>
      )}

      {selectedProfileId && (
        <section className="card" aria-label="Selection result">
          <p>
            Selected profile: {selectedProfileId} ({selectionReason ?? '—'})
          </p>
        </section>
      )}

      <section className="card" aria-label="Previous profiles">
        <h3>Previous Profiles</h3>
        {profiles.length === 0 ? (
          <p>No profiles found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Profile</th>
                <th>Version</th>
                <th>Sensor family</th>
                <th>Schema</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {profiles.map((p) => (
                <tr key={p.profile_id}>
                  <td>{p.profile_id}</td>
                  <td>{p.profile_version}</td>
                  <td>{p.sensor_family}</td>
                  <td>{p.feature_schema_version}</td>
                  <td>
                    <StatusBadge status={p.validity_status} label={p.validity_status} />
                  </td>
                  <td>
                    <button onClick={() => handleSelect(p.profile_id)}>
                      Select for future session
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </section>
  );
};

export default CalibrationOverviewPage;
