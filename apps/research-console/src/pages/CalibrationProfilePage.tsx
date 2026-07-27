import * as React from 'react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import type { CalibrationFeatureBaseline, CalibrationProfile, CalibrationSelectionResponse } from '../api/models';

const CalibrationProfilePage: React.FC = () => {
  const [participantId, setParticipantId] = useState('anon-1');
  const [profileId, setProfileId] = useState('');
  const [profile, setProfile] = useState<CalibrationProfile | null>(null);
  const [invalidateReason, setInvalidateReason] = useState('');
  const [selection, setSelection] = useState<CalibrationSelectionResponse | null>(null);
  const [createdSessionId, setCreatedSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!profileId.trim()) return;
    setError(null);
    try {
      const p = await api.getCalibrationProfile(participantId, profileId);
      setProfile(p);
    } catch {
      setError('Failed to load calibration profile');
    }
  };

  useEffect(() => {
    load();
  }, [participantId, profileId]);

  const handleValidate = async () => {
    if (!profileId.trim()) return;
    try {
      const p = await api.validateCalibrationProfile(participantId, profileId);
      setProfile(p);
    } catch {
      setError('Failed to validate profile');
    }
  };

  const handleInvalidate = async () => {
    if (!profileId.trim()) return;
    if (!invalidateReason.trim()) {
      setError('Invalidation requires a reason');
      return;
    }
    try {
      const p = await api.invalidateCalibrationProfile(participantId, profileId, {
        reason: invalidateReason,
      });
      setProfile(p);
      setInvalidateReason('');
    } catch {
      setError('Failed to invalidate profile');
    }
  };

  const handleSelect = async () => {
    if (!profileId.trim()) return;
    try {
      const result = await api.selectCalibrationProfile(participantId, profileId);
      setSelection(result);
    } catch {
      setError('Failed to select profile');
    }
  };

  const startRecalibration = async () => {
    try {
      const session = await api.createCalibration({
        participant_id: participantId,
        sensor_family: 'fc11',
        sensor_config_fingerprint: 'fc11.default',
        parser_version: 'fc11.parser.v1',
        feature_schema_version: 'clm07.schema.v1',
      });
      setCreatedSessionId(session.session_id);
    } catch {
      setError('Failed to start recalibration session');
    }
  };

  const driftRecommendation = (p: CalibrationProfile): string | null => {
    if (p.validity_status === 'expired') return 'Profile expired — recalibration recommended';
    if (p.validity_status === 'incompatible') return 'Profile incompatible with current sensor/schema';
    if (p.validity_status === 'superseded') return 'Profile superseded — use newer version';
    if (p.validity_status !== 'valid' && p.validity_status !== 'degraded') return 'Profile not valid — review and recalibrate if needed';
    return null;
  };

  return (
    <section aria-label="Calibration profile review">
      <h2>Profile Review</h2>

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
        <label>
          Profile ID
          <input
            type="text"
            value={profileId}
            onChange={(e) => setProfileId(e.target.value)}
            aria-label="Profile ID"
          />
        </label>
        <button onClick={load}>Load</button>
      </section>

      {error && <div className="error-banner" role="alert">{error}</div>}

      {profile && (
        <>
          <section className="card" aria-label="Profile provenance">
            <h3>Provenance</h3>
            <p>Profile: {profile.profile_id}</p>
            <p>Version: {profile.profile_version}</p>
            <p>Participant: {profile.participant_id}</p>
            <p>Sensor family: {profile.sensor_family}</p>
            <p>Sensor fingerprint: {profile.sensor_config_fingerprint}</p>
            <p>Feature schema: {profile.feature_schema_version}</p>
            <p>Status: <StatusBadge status={profile.validity_status} label={profile.validity_status} /></p>
            <p>Accepted observations: {profile.accepted_observation_count}</p>
            <p>Rejected observations: {profile.rejected_observation_count}</p>
            {driftRecommendation(profile) && (
              <p className="warning" role="status">{driftRecommendation(profile)}</p>
            )}
          </section>

          <section className="card" aria-label="Feature baselines">
            <h3>Feature Baselines</h3>
            {Object.keys(profile.feature_baselines).length === 0 ? (
              <p>No feature baselines.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Feature</th>
                    <th>Modality</th>
                    <th>Unit</th>
                    <th>Accepted</th>
                    <th>Rejected</th>
                    <th>Center</th>
                    <th>Dispersion</th>
                    <th>Method</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(profile.feature_baselines).map(([name, b]) => (
                    <BaselineRow key={name} name={name} baseline={b} />
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <section className="card" aria-label="Typed actions">
            <h3>Actions</h3>
            <button onClick={handleValidate}>Validate profile</button>
            <button onClick={handleSelect}>Select for future session</button>
            <button onClick={startRecalibration}>Start recalibration session</button>
            <label>
              Invalidation reason
              <input
                type="text"
                value={invalidateReason}
                onChange={(e) => setInvalidateReason(e.target.value)}
                aria-label="Invalidation reason"
              />
            </label>
            <button onClick={handleInvalidate}>Invalidate profile</button>
          </section>

          {selection && (
            <section className="card" aria-label="Selection result">
              <p>
                Selected: {selection.profile_id} ({selection.reason})
              </p>
            </section>
          )}

          {createdSessionId && (
            <section className="card" aria-label="Recalibration session">
              <p>New recalibration session: {createdSessionId}</p>
            </section>
          )}
        </>
      )}
    </section>
  );
};

const BaselineRow: React.FC<{ name: string; baseline: CalibrationFeatureBaseline }> = ({
  name,
  baseline,
}) => {
  return (
    <tr>
      <td>{name}</td>
      <td>{baseline.modality}</td>
      <td>{baseline.unit}</td>
      <td>{baseline.accepted_count}</td>
      <td>{baseline.rejected_count}</td>
      <td>{baseline.central_tendency}</td>
      <td>{baseline.dispersion}</td>
      <td>{baseline.transformation_recommendation}</td>
    </tr>
  );
};

export default CalibrationProfilePage;
