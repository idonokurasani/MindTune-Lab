import { useEffect, useRef, useState } from 'react';
import { initialSseState, parseSSE, type SseState } from '../api/events';
import type { EventSummary } from '../api/models';

const isEventSummary = (data: unknown): data is EventSummary =>
  typeof data === 'object' &&
  data !== null &&
  'event_id' in data &&
  typeof (data as EventSummary).event_id === 'string';

export const useSessionEvents = (sessionId: string | null, maxHistory = 1000) => {
  const [state, setState] = useState<SseState>(initialSseState);
  const seenRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!sessionId) {
      setState(initialSseState);
      return;
    }
    let closed = false;
    let es: EventSource | null = null;
    let reconnectTimer = 0;

    const connect = (lastId?: string) => {
      if (closed) return;
      setState((s) => ({ ...s, connecting: true }));
      const url =
        `/api/v1/sessions/${encodeURIComponent(sessionId)}/events/stream` +
        (lastId ? `?last_event_id=${encodeURIComponent(lastId)}` : '');
      es = new EventSource(url);
      es.onopen = () => {
        setState((s) => ({ ...s, connected: true, connecting: false, error: null, stale: false }));
      };
      es.onmessage = (event: MessageEvent) => {
        const parsed = parseSSE(`data: ${event.data}`);
        parsed.forEach((p) => {
          if (isEventSummary(p.data)) {
            const ev = p.data;
            setState((prev) => {
              if (seenRef.current.has(ev.event_id)) return prev;
              seenRef.current.add(ev.event_id);
              const events = [...prev.events, ev];
              if (events.length > maxHistory) events.splice(0, events.length - maxHistory);
              return { ...prev, events, lastId: ev.event_id, stale: false };
            });
          }
        });
      };
      es.onerror = () => {
        setState((s) => ({ ...s, connected: false, connecting: false, error: 'Connection lost', stale: true }));
        es?.close();
        reconnectTimer = window.setTimeout(() => connect(state.lastId ?? undefined), 3000);
      };
    };

    connect();
    return () => {
      closed = true;
      window.clearTimeout(reconnectTimer);
      es?.close();
    };
  }, [sessionId, maxHistory]);

  return state;
};
