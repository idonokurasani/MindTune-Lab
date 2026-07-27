import { useState, useCallback } from 'react';
import { api } from '../api/client';
import type { ControlCommand, SessionCreate, SessionResponse } from '../api/models';
import { ApiError } from '../api/errors';

export interface UseSessionState {
  session: SessionResponse | null;
  loading: boolean;
  error: string | null;
}

export const useSession = () => {
  const [state, setState] = useState<UseSessionState>({
    session: null,
    loading: false,
    error: null,
  });

  const createSession = useCallback(async (payload: SessionCreate) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const session = await api.createSession(payload);
      setState({ session, loading: false, error: null });
      return session;
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : String(e);
      setState({ session: null, loading: false, error: msg });
      throw e;
    }
  }, []);

  const loadSession = useCallback(async (id: string) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const session = await api.getSession(id);
      setState({ session, loading: false, error: null });
      return session;
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : String(e);
      setState({ session: null, loading: false, error: msg });
      throw e;
    }
  }, []);

  const sendControl = useCallback(
    async (sessionId: string, command: ControlCommand): Promise<SessionResponse> => {
      await api.controlSession(sessionId, command);
      return loadSession(sessionId);
    },
    [loadSession]
  );

  return { ...state, createSession, loadSession, sendControl };
};
