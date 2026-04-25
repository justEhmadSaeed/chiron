"use client";

import { useEffect, useState } from "react";

import type { AgentEvent } from "@chiron/contracts";

import { getWebSocketUrl } from "@/lib/config";

export function AgentActivityFeed() {
  const [events, setEvents] = useState<AgentEvent[]>([]);

  useEffect(() => {
    const socket = new WebSocket(getWebSocketUrl());

    socket.onmessage = (message) => {
      const event = JSON.parse(message.data) as AgentEvent;
      setEvents((current) => [event, ...current].slice(0, 20));
    };

    return () => {
      socket.close();
    };
  }, []);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      {events.length === 0 ? (
        <div style={{ opacity: 0.65 }}>Waiting for agent activity...</div>
      ) : (
        events.map((event) => (
          <article
            key={event.event_id}
            style={{
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 16,
              padding: 16,
              background: "rgba(255,255,255,0.03)"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
              <strong>{event.event_type}</strong>
              <span style={{ opacity: 0.6 }}>{event.run_id}</span>
            </div>
            <pre style={{ whiteSpace: "pre-wrap", margin: "8px 0 0", opacity: 0.8 }}>
              {JSON.stringify(event.payload, null, 2)}
            </pre>
          </article>
        ))
      )}
    </div>
  );
}
