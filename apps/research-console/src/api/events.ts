import type { EventSummary } from './models';

export interface ParsedEvent {
  id: string;
  event: string;
  data: unknown;
}

export const parseSSE = (chunk: string): ParsedEvent[] => {
  const events: ParsedEvent[] = [];
  const blocks = chunk.split('\n\n');
  for (const block of blocks) {
    if (!block.trim()) continue;
    const lines = block.split('\n');
    let id = '';
    let event = 'message';
    const dataLines: string[] = [];
    for (const line of lines) {
      if (line.startsWith('id:')) {
        id = line.slice(3).trim();
      } else if (line.startsWith('event:')) {
        event = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trim());
      } else if (line.startsWith(':heartbeat')) {
        // heartbeat comment
      }
    }
    if (dataLines.length > 0) {
      try {
        const parsed = JSON.parse(dataLines.join('\n')) as unknown;
        events.push({ id, event, data: parsed });
      } catch {
        // Ignore malformed data
      }
    }
  }
  return events;
};

export interface SseState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  lastId: string | null;
  events: EventSummary[];
  stale: boolean;
}

export const initialSseState: SseState = {
  connected: false,
  connecting: false,
  error: null,
  lastId: null,
  events: [],
  stale: false,
};
