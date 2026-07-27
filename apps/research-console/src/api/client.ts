import { ApiError, NetworkError, parseError } from './errors';
import type {
  ControlCommand,
  ControlResponse,
  ErrorResponse,
  EventList,
  ExperimentCreate,
  ExperimentList,
  ExperimentResponse,
  ExportResponse,
  HealthResponse,
  ProtocolList,
  ReadinessResponse,
  SensorList,
  SensorRegister,
  SensorResponse,
  SessionCreate,
  SessionList,
  SessionResponse,
  StimulusList,
  StimulusResponse,
} from './models';

const getApiBase = () =>
  import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000/api/v1';

const getApiToken = () => import.meta.env.VITE_API_TOKEN;

const headers = (): Record<string, string> => {
  const h: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
  const token = getApiToken();
  if (token) {
    h.Authorization = `Bearer ${token}`;
  }
  return h;
};

const request = async <T>(
  method: string,
  path: string,
  body?: unknown
): Promise<T> => {
  const url = `${getApiBase()}${path}`;
  const init: RequestInit = {
    method,
    headers: headers(),
    credentials: 'same-origin',
  };
  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch {
    throw new NetworkError(`Unable to reach ${url}`);
  }
  if (!response.ok) {
    throw await parseError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  try {
    return (await response.json()) as T;
  } catch {
    return (await response.text()) as unknown as T;
  }
};

export const api = {
  getHealth: () => request<HealthResponse>('GET', '/health'),
  getLiveness: () => request<{ status: string }>('GET', '/health/live'),
  getProtocols: () => request<ProtocolList>('GET', '/protocols'),

  createExperiment: (data: ExperimentCreate) =>
    request<ExperimentResponse>('POST', '/experiments', data),
  listExperiments: () => request<ExperimentList>('GET', '/experiments'),
  getExperiment: (id: string) => request<ExperimentResponse>('GET', `/experiments/${encodeURIComponent(id)}`),
  deleteExperiment: (id: string) =>
    request<{ deleted: boolean; id: string }>('DELETE', `/experiments/${encodeURIComponent(id)}`),

  createSession: (data: SessionCreate) =>
    request<SessionResponse>('POST', '/sessions', data),
  listSessions: () => request<SessionList>('GET', '/sessions'),
  getSession: (id: string) => request<SessionResponse>('GET', `/sessions/${encodeURIComponent(id)}`),
  deleteSession: (id: string) =>
    request<{ deleted: boolean; id: string }>('DELETE', `/sessions/${encodeURIComponent(id)}`),
  getReadiness: (id: string) =>
    request<ReadinessResponse>('GET', `/sessions/${encodeURIComponent(id)}/readiness`),
  controlSession: (id: string, data: ControlCommand) =>
    request<ControlResponse>('POST', `/sessions/${encodeURIComponent(id)}/control`, data),

  registerSensor: (data: SensorRegister) =>
    request<SensorResponse>('POST', '/sensors', data),
  listSensors: () => request<SensorList>('GET', '/sensors'),
  getSensor: (id: string) => request<SensorResponse>('GET', `/sensors/${encodeURIComponent(id)}`),
  connectSensor: (id: string, sessionId?: string) =>
    request<SensorResponse>('POST', `/sensors/${encodeURIComponent(id)}/connect`, { session_id: sessionId ?? null }),
  disconnectSensor: (id: string, sessionId?: string) =>
    request<SensorResponse>('POST', `/sensors/${encodeURIComponent(id)}/disconnect`, { session_id: sessionId ?? null }),

  listStimuli: (sessionId?: string) =>
    request<StimulusList>('GET', `/stimuli${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''}`),
  getStimulus: (id: string, sessionId?: string) =>
    request<StimulusResponse>(
      'GET',
      `/stimuli/${encodeURIComponent(id)}${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''}`
    ),

  listEvents: (sessionId: string, page = 1, pageSize = 20) =>
    request<EventList>(
      'GET',
      `/sessions/${encodeURIComponent(sessionId)}/events?page=${page}&page_size=${pageSize}`
    ),

  requestExport: (sessionId: string, format: string) =>
    request<ExportResponse>('POST', `/sessions/${encodeURIComponent(sessionId)}/exports`, { format }),
  exportEvents: (sessionId: string, format: 'json' | 'jsonl') =>
    request<string>('GET', `/sessions/${encodeURIComponent(sessionId)}/export/events?format=${format}`),
  exportSummary: (sessionId: string, format: 'json' | 'jsonl') =>
    request<string>('GET', `/sessions/${encodeURIComponent(sessionId)}/export/summary?format=${format}`),
  exportManifest: (sessionId: string, format: 'json' | 'jsonl') =>
    request<string>('GET', `/sessions/${encodeURIComponent(sessionId)}/export/manifest?format=${format}`),

  hebrewReadiness: () => request<import('./models').HebrewReadiness>('GET', '/hebrew/readiness'),
  listHebrewItems: () => request<{ items: import('./models').HebrewItem[] }>('GET', '/hebrew/items'),
  getHebrewItem: (id: string) =>
    request<import('./models').HebrewItem>('GET', `/hebrew/items/${encodeURIComponent(id)}`),
  createHebrewSession: () =>
    request<{ session_id: string; status: string }>('POST', '/hebrew/sessions', {
      learner_id: 'anonymous',
      parameters: {},
    }),
  getHebrewSessionState: (sessionId: string) =>
    request<Record<string, unknown>>('GET', `/sessions/${encodeURIComponent(sessionId)}/hebrew/state`),
  getHebrewCurrentTrial: (sessionId: string) =>
    request<import('./models').HebrewTrial>('GET', `/sessions/${encodeURIComponent(sessionId)}/trials/current`),
  submitHebrewResponse: (sessionId: string, trialId: string, data: import('./models').HebrewResponseSubmit) =>
    request<import('./models').HebrewResponseResult>(
      'POST',
      `/sessions/${encodeURIComponent(sessionId)}/trials/${encodeURIComponent(trialId)}/response`,
      data,
    ),
  getHebrewLearningSummary: (sessionId: string) =>
    request<Record<string, unknown>>('GET', `/sessions/${encodeURIComponent(sessionId)}/learning-summary`),

  // CLM-06B curriculum endpoints
  listHebrewCurricula: () => request<{ curricula: import('./models').HebrewCurriculumSummary[] }>('GET', '/hebrew/curricula'),
  getHebrewCurriculum: (id: string) =>
    request<import('./models').HebrewCurriculum>('GET', `/hebrew/curricula/${encodeURIComponent(id)}`),
  getHebrewCurriculumVersions: (id: string) =>
    request<Array<Record<string, unknown>>>('GET', `/hebrew/curricula/${encodeURIComponent(id)}/versions`),
  getHebrewCurriculumReadiness: (id: string) =>
    request<import('./models').HebrewCurriculumReadiness>('GET', `/hebrew/curricula/${encodeURIComponent(id)}/readiness`),
  listHebrewUnits: () => request<{ units: import('./models').HebrewCurriculumUnit[] }>('GET', '/hebrew/units'),
  getHebrewUnit: (id: string) =>
    request<import('./models').HebrewCurriculumUnit>('GET', `/hebrew/units/${encodeURIComponent(id)}`),
  listHebrewSkills: () => request<{ skills: import('./models').HebrewCurriculumSkill[] }>('GET', '/hebrew/skills'),
  getHebrewLearnerState: (sessionId: string) =>
    request<import('./models').HebrewLearnerState>('GET', `/hebrew/learner-state/${encodeURIComponent(sessionId)}`),
  getHebrewProgression: (sessionId: string) =>
    request<import('./models').HebrewProgressionResponse>('GET', `/hebrew/progression/${encodeURIComponent(sessionId)}`),
  postHebrewNextProgression: (sessionId: string, data?: Record<string, unknown>) =>
    request<import('./models').HebrewProgressionResponse>(
      'POST',
      `/hebrew/progression/${encodeURIComponent(sessionId)}/next`,
      data,
    ),
};

export const isApiError = (error: unknown): error is ApiError =>
  error instanceof ApiError;

export const isErrorResponse = (data: unknown): data is ErrorResponse =>
  typeof data === 'object' &&
  data !== null &&
  'code' in data &&
  typeof (data as ErrorResponse).code === 'string';

export const sanitizeNotes = (input: string): string =>
  input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
