import * as React from 'react';
import { useEffect, useState } from 'react';
import { AppShell } from './components/AppShell';
import { OverviewPage } from './pages/OverviewPage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { SessionCreatePage } from './pages/SessionCreatePage';
import { SessionLivePage } from './pages/SessionLivePage';
import { SessionReviewPage } from './pages/SessionReviewPage';
import CalibrationOverviewPage from './pages/CalibrationOverviewPage';
import CalibrationProfilePage from './pages/CalibrationProfilePage';
import CalibrationSessionPage from './pages/CalibrationSessionPage';
import HebrewSessionPage from './pages/HebrewSessionPage';
import CurriculumPage from './pages/CurriculumPage';
import LearnerProgressionPage from './pages/LearnerProgressionPage';
import ItemInspectionPage from './pages/ItemInspectionPage';
import { ScientificValidationPage } from './pages/ScientificValidationPage';
import { SystemPage } from './pages/SystemPage';
import { api } from './api/client';
import { toApiMode } from './api/models';
import type { ExperimentCreate, ExperimentResponse, HealthResponse, ProtocolReference, RuntimeMode, SensorResponse, SessionResponse } from './api/models';
import type { Tab } from './state/sessionStore';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [liveness, setLiveness] = useState<{ status: string } | null>(null);
  const [protocols, setProtocols] = useState<ProtocolReference[]>([]);
  const [experiments, setExperiments] = useState<ExperimentResponse[]>([]);
  const [sessions, setSessions] = useState<SessionResponse[]>([]);
  const [sensors, setSensors] = useState<SensorResponse[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  const refresh = async () => {
    try {
      const [h, live, p, exps, sess, sens] = await Promise.all([
        api.getHealth(),
        api.getLiveness(),
        api.getProtocols(),
        api.listExperiments(),
        api.listSessions(),
        api.listSensors(),
      ]);
      setHealth(h);
      setLiveness(live);
      setProtocols(p.items);
      setExperiments(exps.items);
      setSessions(sess.items);
      setSensors(sens.items);
    } catch {
      // Keep previous state; UI will show disconnected badges.
    }
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleCreateExperiment = async (data: ExperimentCreate) => {
    await api.createExperiment(data);
    const exps = await api.listExperiments();
    setExperiments(exps.items);
  };

  const handleDeleteExperiment = async (id: string) => {
    await api.deleteExperiment(id);
    setExperiments((prev) => prev.filter((e) => e.id !== id));
  };

  const handleCreateSession = async (payload: {
    experiment_id?: string;
    learner_id: string;
    mode: RuntimeMode;
    protocol_version_id?: string;
    sensor_source: string;
    stimulus_set: string;
    playback_backend: string;
    notes: string;
  }) => {
    const session = await api.createSession({
      experiment_id: payload.experiment_id,
      learner_id: payload.learner_id,
      mode: toApiMode(payload.mode),
      protocol_version_id: payload.protocol_version_id,
      parameters: {
        sensor_source: payload.sensor_source,
        stimulus_set: payload.stimulus_set,
        playback_backend: payload.playback_backend,
        notes: payload.notes,
      },
    });
    setSessions((prev) => [...prev, session]);
    setSelectedSessionId(session.id);
    return session;
  };

  const handleStart = async (sessionId: string) => {
    await api.controlSession(sessionId, { command: 'start' });
    setActiveTab('session-live');
  };

  const renderPage = () => {
    const activeSessionId =
      selectedSessionId ?? sessions.find((s) => s.status === 'running')?.id ?? sessions[0]?.id ?? null;
    switch (activeTab) {
      case 'overview':
        return <OverviewPage health={health} liveness={liveness} />;
      case 'experiments':
        return (
          <ExperimentsPage
            experiments={experiments}
            protocols={protocols}
            onCreate={handleCreateExperiment}
            onDelete={handleDeleteExperiment}
          />
        );
      case 'session-create':
        return (
          <SessionCreatePage
            experiments={experiments}
            protocols={protocols}
            onCreate={handleCreateSession}
            onStart={handleStart}
          />
        );
      case 'session-live':
        return <SessionLivePage sessionId={activeSessionId} />;
      case 'session-review':
        return <SessionReviewPage sessionId={activeSessionId} />;
      case 'calibration-overview':
        return <CalibrationOverviewPage />;
      case 'calibration-session':
        return <CalibrationSessionPage />;
      case 'calibration-profile-review':
        return <CalibrationProfilePage />;
      case 'hebrew':
        return <HebrewSessionPage />;
      case 'curriculum':
        return <CurriculumPage />;
      case 'learner-progression':
        return <LearnerProgressionPage />;
      case 'item-inspection':
        return <ItemInspectionPage />;
      case 'validation':
        return <ScientificValidationPage />;
      case 'system':
        return <SystemPage health={health} protocols={protocols} sensors={sensors} />;
      default:
        return <OverviewPage health={health} liveness={liveness} />;
    }
  };

  return (
    <AppShell activeTab={activeTab} setTab={setActiveTab}>
      {renderPage()}
    </AppShell>
  );
};

export default App;
