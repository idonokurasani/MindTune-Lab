import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { ReadinessResponse } from '../api/models';

export const useReadiness = (sessionId: string | null, pollMs = 2000) => {
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) {
      setReadiness(null);
      return;
    }
    let active = true;
    const fetchReadiness = async () => {
      setLoading(true);
      try {
        const r = await api.getReadiness(sessionId);
        if (active) {
          setReadiness(r);
          setError(null);
        }
      } catch (e) {
        if (active) {
          setError(e instanceof Error ? e.message : String(e));
        }
      } finally {
        if (active) setLoading(false);
      }
    };
    fetchReadiness();
    const interval = setInterval(fetchReadiness, pollMs);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [sessionId, pollMs]);

  return { readiness, loading, error };
};
