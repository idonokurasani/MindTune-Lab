import { useState, useCallback } from 'react';
import { ApiError } from '../api/errors';

type ApiStatus = 'idle' | 'loading' | 'success' | 'error';

export interface UseApiResult<T> {
  data: T | null;
  error: ApiError | null;
  status: ApiStatus;
  execute: () => Promise<void>;
}

export const useApi = <T>(factory: () => Promise<T>): UseApiResult<T> => {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [status, setStatus] = useState<ApiStatus>('idle');

  const execute = useCallback(async () => {
    setStatus('loading');
    setError(null);
    try {
      const result = await factory();
      setData(result);
      setStatus('success');
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError('unknown', String(e), 0, ''));
      setStatus('error');
    }
  }, [factory]);

  return { data, error, status, execute };
};
