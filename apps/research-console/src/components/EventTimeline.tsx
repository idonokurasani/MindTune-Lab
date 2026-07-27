import * as React from 'react';
import type { EventSummary } from '../api/models';

interface EventTimelineProps {
  events: EventSummary[];
}

export const EventTimeline: React.FC<EventTimelineProps> = ({ events }) => {
  return (
    <section className="card" aria-label="Event timeline">
      <h2>Event Timeline</h2>
      <ol className="list" aria-label="Events in sequence" reversed>
        {events.slice().reverse().map((e) => (
          <li key={e.event_id}>
            <time dateTime={new Date(e.timestamp * 1000).toISOString()}>
              {new Date(e.timestamp * 1000).toLocaleTimeString()}
            </time>{' '}
            — <strong>{e.event_type}</strong> ({e.component}, seq {e.session_sequence_number})
          </li>
        ))}
      </ol>
    </section>
  );
};
