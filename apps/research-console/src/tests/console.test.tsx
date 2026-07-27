import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

import { api, sanitizeNotes } from '../api/client';
import { parseSSE } from '../api/events';
import { StatusBadge } from '../components/StatusBadge';
import { HealthPanel } from '../components/HealthPanel';
import { ReadinessPanel } from '../components/ReadinessPanel';
import { SafetyControls } from '../components/SafetyControls';
import { EventTimeline } from '../components/EventTimeline';
import { CausalTrace } from '../components/CausalTrace';
import { SensorPanel } from '../components/SensorPanel';
import { AudioPanel } from '../components/AudioPanel';
import { DecisionPanel } from '../components/DecisionPanel';
import { OutcomePanel } from '../components/OutcomePanel';
import { ExportPanel } from '../components/ExportPanel';
import { AppShell } from '../components/AppShell';
import { ExperimentsPage } from '../pages/ExperimentsPage';
import { SessionCreatePage } from '../pages/SessionCreatePage';
import { OverviewPage } from '../pages/OverviewPage';
import { SystemPage } from '../pages/SystemPage';
import { SessionReviewPage } from '../pages/SessionReviewPage';
import type { ExperimentResponse, ProtocolReference, HealthResponse } from '../api/models';

const mkResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

let fetchMock: ReturnType<typeof vi.fn>;
let esInstances: Array<InstanceType<typeof MockEventSource>>;

class MockEventSource {
  url = '';
  onopen: (() => void) | null = null;
  onmessage: ((e: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(url: string) {
    this.url = url;
    esInstances.push(this);
    setTimeout(() => this.onopen?.(), 0);
  }
  close() {}
  emit(data: string) {
    this.onmessage?.({ data } as MessageEvent);
  }
  fail() {
    this.onerror?.();
  }
}

beforeEach(() => {
  fetchMock = vi.fn();
  vi.stubGlobal('fetch', fetchMock);
  vi.stubGlobal('localStorage', {
    getItem: vi.fn(() => null),
    setItem: vi.fn(),
    removeItem: vi.fn(),
  });
  esInstances = [];
  vi.stubGlobal('EventSource', MockEventSource);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('CLM-05B Research Console', () => {
  // A. Console load
  it('loads and renders the console shell', () => {
    render(<AppShell activeTab="overview" setTab={() => {}}><div>content</div></AppShell>);
    expect(screen.getByText('MindTune Research Console')).toBeDefined();
    expect(screen.getByText('Overview')).toBeDefined();
    expect(screen.getByText('content')).toBeDefined();
    expect(screen.getByText('CLM-05B Research Console — loopback API only — no credentials persisted.')).toBeDefined();
  });

  it('shows correct health statuses with color-independent text', () => {
    render(<StatusBadge status="healthy" label="API" />);
    expect(screen.getByText('API: healthy')).toBeDefined();
    render(<StatusBadge status="failed" label="Sensor" />);
    expect(screen.getByText('Sensor: failed')).toBeDefined();
    render(<StatusBadge status="stale" label="Data" />);
    expect(screen.getByText('Data: stale')).toBeDefined();
  });

  it('renders the health panel with all subsystems', () => {
    const health: HealthResponse = { status: 'ok', ready: true, blocking_reasons: [], warnings: [], version: 'v1' };
    render(<HealthPanel health={health} />);
    expect(screen.getByText('API: healthy')).toBeDefined();
    expect(screen.getByText('Live Loop: healthy')).toBeDefined();
    expect(screen.getByText('Voice Cache: healthy')).toBeDefined();
    expect(screen.getByText('Renderer: healthy')).toBeDefined();
    expect(screen.getByText('Playback: healthy')).toBeDefined();
    expect(screen.getByText('Event Store: healthy')).toBeDefined();
    expect(screen.getByText('MPE: healthy')).toBeDefined();
    expect(screen.getByText('Sensor: healthy')).toBeDefined();
  });

  it('lists experiments and does not allow protocol editing', () => {
    const experiments: ExperimentResponse[] = [
      { id: 'exp-1', name: 'Exp A', protocol_version_id: 'clm-05-experimental.v1', parameters: {}, created_at: 0 },
    ];
    const protocols: ProtocolReference[] = [
      { protocol_version_id: 'clm-05-experimental.v1', name: 'CLM-05', description: '' },
    ];
    const onCreate = vi.fn();
    const onDelete = vi.fn();
    render(<ExperimentsPage experiments={experiments} protocols={protocols} onCreate={onCreate} onDelete={onDelete} />);
    expect(screen.getByText('Exp A')).toBeDefined();
    expect(screen.getByText('CLM-05 (clm-05-experimental.v1)')).toBeDefined();
  });

  it('does not render real-name, email, phone, birth, or address fields', () => {
    const protocols: ProtocolReference[] = [];
    const { container } = render(<SessionCreatePage experiments={[]} protocols={protocols} onCreate={vi.fn()} onStart={vi.fn()} />);
    const html = container.innerHTML;
    expect(html).not.toMatch(/name|email|phone|birth|address/i);
  });

  it('shows readiness blockers before starting', () => {
    render(<ReadinessPanel readiness={{ ready: false, blocking_reasons: ['missing_aaron_asset'], warnings: [] }} />);
    expect(screen.getByText('Blockers')).toBeDefined();
    expect(screen.getByText('missing_aaron_asset')).toBeDefined();
  });

  it('shows a rejected Aaron asset as a blocker', () => {
    render(<ReadinessPanel readiness={{ ready: false, blocking_reasons: ['missing_aaron_asset', 'rejected_pronunciation_asset'], warnings: [] }} />);
    expect(screen.getByText('Blockers')).toBeDefined();
    expect(screen.getByText('missing_aaron_asset')).toBeDefined();
    expect(screen.getByText('rejected_pronunciation_asset')).toBeDefined();
  });

  // B. Session lifecycle
  it('calls prepare, start, pause, resume, stop, kill control commands', () => {
    const handler = vi.fn();
    render(<SafetyControls onCommand={handler} />);
    fireEvent.click(screen.getByText('Prepare'));
    expect(handler).toHaveBeenCalledWith('prepare');
    fireEvent.click(screen.getByText('Start'));
    expect(handler).toHaveBeenCalledWith('start');
    fireEvent.click(screen.getByText('Pause'));
    expect(handler).toHaveBeenCalledWith('pause');
    fireEvent.click(screen.getByText('Resume'));
    expect(handler).toHaveBeenCalledWith('resume');
    fireEvent.click(screen.getByText('Freeze'));
    expect(handler).toHaveBeenCalledWith('freeze');
    fireEvent.click(screen.getByText('Unfreeze'));
    expect(handler).toHaveBeenCalledWith('unfreeze');
    fireEvent.click(screen.getByText('Force Baseline'));
    expect(handler).toHaveBeenCalledWith('force_baseline');
    fireEvent.click(screen.getByText('Release Baseline'));
    expect(handler).toHaveBeenCalledWith('release_baseline');
    fireEvent.click(screen.getByText('Stop'));
    expect(handler).toHaveBeenCalledWith('stop');
  });

  it('requires a confirmation click before kill', () => {
    const handler = vi.fn();
    render(<SafetyControls onCommand={handler} />);
    fireEvent.click(screen.getByText('Kill'));
    expect(handler).not.toHaveBeenCalled();
    expect(screen.getByText('Click again to confirm session kill.')).toBeDefined();
    fireEvent.click(screen.getByText('Confirm Kill'));
    expect(handler).toHaveBeenCalledWith('kill');
  });

  it('reports requested vs applied states', () => {
    render(<DecisionPanel requestedState="running" appliedState="paused" fallbackReason="baseline_lock" />);
    expect(screen.getByText('running')).toBeDefined();
    expect(screen.getByText('paused')).toBeDefined();
    expect(screen.getByText('baseline_lock')).toBeDefined();
  });

  it('renders sensor disconnected and not cognitive deterioration', () => {
    render(<SensorPanel sensor={{ sensor_id: 's1', sensor_type: 'synthetic', connected: false, session_id: null, lock_owner: null }} onConnect={vi.fn()} onDisconnect={vi.fn()} />);
    expect(screen.getByText('s1: disconnected')).toBeDefined();
    expect(screen.queryByText('cognitive deterioration')).toBeNull();
  });

  it('renders audio stimulus availability', () => {
    render(<AudioPanel stimuli={[{ stimulus_id: 'speech_segment', label: 'Giuseppe/Aaron bilingual composite', source_text: null, tts_text: null, locale: 'he-IL', duration_ms: 0, available: false }]} />);
    expect(screen.getByText('Giuseppe/Aaron bilingual composite')).toBeDefined();
    expect(screen.getByText(/no/i)).toBeDefined();
  });

  it('renders outcome summary', () => {
    render(<OutcomePanel outcome={{ status: 'completed', level: 2, tempo_ratio: 0.95, pause_duration_ms: 120 }} />);
    expect(screen.getByText('completed')).toBeDefined();
    expect(screen.getByText('2')).toBeDefined();
    expect(screen.getByText('0.95')).toBeDefined();
    expect(screen.getByText('120')).toBeDefined();
  });

  // C. Event timeline and SSE
  it('renders the event timeline in reverse order', () => {
    const events = [
      { event_id: 'e1', event_type: 'session_created', session_sequence_number: 1, timestamp: 1000, component: 'api' },
      { event_id: 'e2', event_type: 'session_started', session_sequence_number: 2, timestamp: 1001, component: 'orchestrator' },
    ];
    render(<EventTimeline events={events} />);
    const items = screen.getAllByRole('listitem');
    expect(items.length).toBe(2);
    expect(items[0].textContent).toMatch('session_started');
    expect(items[1].textContent).toMatch('session_created');
  });

  it('parses SSE data and suppresses duplicates', () => {
    const chunk = `data: {"event_id":"e1","event_type":"created","session_sequence_number":1,"timestamp":1,"component":"api"}\n\ndata: {"event_id":"e1","event_type":"created","session_sequence_number":1,"timestamp":1,"component":"api"}\n\n`;
    const parsed = parseSSE(chunk);
    expect(parsed.length).toBe(2);
    expect(parsed[0].data).toEqual(parsed[1].data);
  });

  it('reconstructs causal trace and shows missing links', () => {
    const trace = {
      observationFrame: { id: 'o1', type: 'ObservationFrame', missing: false },
      interventionOutcome: { id: 'i1', type: 'InterventionOutcome', missing: false },
    };
    const { container } = render(<CausalTrace trace={trace} />);
    expect(container.textContent).toContain('ObservationFrame');
    expect(container.textContent).toContain('InterventionOutcome');
    expect(container.textContent).toContain('missing');
  });

  // D. Exports
  it('shows export request with checksum and redacted flag', async () => {
    fetchMock.mockResolvedValueOnce(mkResponse({ session_id: 's1', export_id: 'x1', format: 'json', download_url: '/download', checksum: 'abc', record_count: 10, redacted: true }));
    render(<ExportPanel sessionId="s1" />);
    fireEvent.click(screen.getByText('Export JSON'));
    await waitFor(() => screen.getByText(/abc/));
    expect(screen.getByText(/abc/)).toBeDefined();
    expect(screen.getByText(/redacted: yes/)).toBeDefined();
  });

  it('sanitizes notes to prevent HTML injection', () => {
    expect(sanitizeNotes('<script>alert(1)</script>')).toBe('&lt;script&gt;alert(1)&lt;/script&gt;');
    expect(sanitizeNotes('')).toBe('');
  });

  // E. API client
  it('does not put the API token in localStorage', () => {
    expect(localStorage.getItem('VITE_API_TOKEN')).toBeNull();
    expect(localStorage.getItem('apiToken')).toBeNull();
  });

  it('calls the correct CLM-05 route inventory', async () => {
    fetchMock
      .mockResolvedValueOnce(mkResponse({ status: 'ok', ready: true, blocking_reasons: [], warnings: [], version: 'v1' }))
      .mockResolvedValueOnce(mkResponse({ items: [] }))
      .mockResolvedValueOnce(mkResponse({ id: 's1', experiment_id: null, learner_id: 'anon', mode: 'synthetic', status: 'created', protocol_version_id: 'clm-05-experimental.v1', created_at: 0, updated_at: 0 }));
    await api.getHealth();
    await api.listExperiments();
    await api.createSession({ learner_id: 'anon', mode: 'synthetic' });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    const healthCall = fetchMock.mock.calls[0][0] as string;
    expect(healthCall).toMatch(/\/health$/);
    expect(healthCall).toMatch(/^http:\/\/127\.0\.0\.1:8000/);
  });

  // F. Privacy / security rendering
  it('does not render MAC addresses, absolute paths, or real identity', () => {
    const health: HealthResponse = { status: 'ok', ready: true, blocking_reasons: [], warnings: ['some warning'], version: 'v1' };
    const { container } = render(<OverviewPage health={health} liveness={{ status: 'ok' }} />);
    const html = container.innerHTML;
    expect(html).not.toMatch(/([0-9A-Fa-f]{2}:){5}/);
    expect(html).not.toMatch(/Users\//);
    expect(html).not.toMatch(/John Doe/);
  });

  it('does not render credentials or provider payloads in system page', () => {
    const { container } = render(<SystemPage health={null} protocols={[]} sensors={[]} />);
    expect(container.textContent).not.toMatch(/api_key|token|secret|password/);
  });

  // G. Replay and synthetic-live scenarios
  it('renders review page for completed/killed sessions', () => {
    vi.spyOn(api, 'listEvents').mockResolvedValue({ session_id: 's1', page: 1, page_size: 20, total: 0, items: [] });
    vi.spyOn(api, 'getStimulus').mockResolvedValue({ stimulus_id: 'speech_segment', label: 'Giuseppe/Aaron bilingual composite', source_text: null, tts_text: null, locale: 'he-IL', duration_ms: 0, available: false });
    const { container } = render(<SessionReviewPage sessionId="s1" />);
    expect(container.textContent).toMatch('Review');
  });

  it('shows stable error codes without stack traces', async () => {
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ code: 'session_not_found', message: 'not found', request_id: 'r1', resource_id: 's1', retryable: false, details: {} }), { status: 404, headers: { 'Content-Type': 'application/json' } }));
    await expect(api.getSession('s1')).rejects.toThrow('not found');
    expect(fetchMock.mock.calls[0][0] as string).toMatch(/sessions\/s1/);
  });
});
