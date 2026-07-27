import * as React from 'react';
import { createContext, useContext, useReducer, useCallback, createElement, type FC, type ReactNode } from 'react';
import type { ControlCommand, ControlResponse, ExperimentResponse, SessionResponse } from '../api/models';
import { api } from '../api/client';

export type Tab =
  | 'overview'
  | 'experiments'
  | 'session-create'
  | 'session-live'
  | 'session-review'
  | 'system'
  | 'hebrew'
  | 'curriculum'
  | 'learner-progression'
  | 'item-inspection';

export interface AppState {
  activeTab: Tab;
  sessions: SessionResponse[];
  experiments: ExperimentResponse[];
  selectedSessionId: string | null;
  selectedExperimentId: string | null;
  error: string | null;
}

type Action =
  | { type: 'SET_TAB'; tab: Tab }
  | { type: 'SET_SESSIONS'; sessions: SessionResponse[] }
  | { type: 'SET_EXPERIMENTS'; experiments: ExperimentResponse[] }
  | { type: 'SELECT_SESSION'; id: string | null }
  | { type: 'SELECT_EXPERIMENT'; id: string | null }
  | { type: 'SET_ERROR'; error: string | null }
  | { type: 'ADD_SESSION'; session: SessionResponse }
  | { type: 'UPDATE_SESSION'; session: SessionResponse }
  | { type: 'REMOVE_SESSION'; id: string }
  | { type: 'REMOVE_EXPERIMENT'; id: string };

const initialState: AppState = {
  activeTab: 'overview',
  sessions: [],
  experiments: [],
  selectedSessionId: null,
  selectedExperimentId: null,
  error: null,
};

const reducer = (state: AppState, action: Action): AppState => {
  switch (action.type) {
    case 'SET_TAB':
      return { ...state, activeTab: action.tab };
    case 'SET_SESSIONS':
      return { ...state, sessions: action.sessions };
    case 'SET_EXPERIMENTS':
      return { ...state, experiments: action.experiments };
    case 'SELECT_SESSION':
      return { ...state, selectedSessionId: action.id };
    case 'SELECT_EXPERIMENT':
      return { ...state, selectedExperimentId: action.id };
    case 'SET_ERROR':
      return { ...state, error: action.error };
    case 'ADD_SESSION':
      return { ...state, sessions: [...state.sessions, action.session] };
    case 'UPDATE_SESSION':
      return {
        ...state,
        sessions: state.sessions.map((s) => (s.id === action.session.id ? action.session : s)),
      };
    case 'REMOVE_SESSION':
      return {
        ...state,
        sessions: state.sessions.filter((s) => s.id !== action.id),
        selectedSessionId: state.selectedSessionId === action.id ? null : state.selectedSessionId,
      };
    case 'REMOVE_EXPERIMENT':
      return {
        ...state,
        experiments: state.experiments.filter((e) => e.id !== action.id),
        selectedExperimentId: state.selectedExperimentId === action.id ? null : state.selectedExperimentId,
      };
    default:
      return state;
  }
};

interface StoreContextValue {
  state: AppState;
  dispatch: React.Dispatch<Action>;
  refreshSessions: () => Promise<void>;
  refreshExperiments: () => Promise<void>;
  selectSession: (id: string) => void;
  sendControl: (sessionId: string, command: ControlCommand) => Promise<ControlResponse>;
}

const SessionStoreContext = createContext<StoreContextValue | null>(null);

export const SessionStoreProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  const refreshSessions = useCallback(async () => {
    const list = await api.listSessions();
    dispatch({ type: 'SET_SESSIONS', sessions: list.items });
  }, []);

  const refreshExperiments = useCallback(async () => {
    const list = await api.listExperiments();
    dispatch({ type: 'SET_EXPERIMENTS', experiments: list.items });
  }, []);

  const selectSession = useCallback((id: string) => {
    dispatch({ type: 'SELECT_SESSION', id });
  }, []);

  const sendControl = useCallback(async (sessionId: string, command: ControlCommand) => {
    const response = await api.controlSession(sessionId, command);
    const updated = await api.getSession(sessionId);
    dispatch({ type: 'UPDATE_SESSION', session: updated });
    return response;
  }, []);

  const value: StoreContextValue = {
    state,
    dispatch,
    refreshSessions,
    refreshExperiments,
    selectSession,
    sendControl,
  };

  return createElement(SessionStoreContext.Provider, { value }, children);
};

export const useSessionStore = () => {
  const ctx = useContext(SessionStoreContext);
  if (!ctx) throw new Error('useSessionStore must be used within SessionStoreProvider');
  return ctx;
};
