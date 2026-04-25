import { Panel } from "@chiron/ui";

import { AgentActivityFeed } from "@/components/agent-activity-feed";

export default function HomePage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at top, rgba(0, 120, 255, 0.10), transparent 30%), #0b1020",
        color: "#f3f5f7",
        padding: "48px 24px"
      }}
    >
      <div style={{ margin: "0 auto", maxWidth: 960 }}>
        <div style={{ marginBottom: 24 }}>
          <p style={{ letterSpacing: "0.18em", textTransform: "uppercase", opacity: 0.7 }}>
            Chiron control plane
          </p>
          <h1 style={{ fontSize: "clamp(2.5rem, 5vw, 4.5rem)", margin: "12px 0" }}>
            Realtime visibility into multi-agent runs
          </h1>
          <p style={{ maxWidth: 640, lineHeight: 1.6, opacity: 0.82 }}>
            The frontend consumes typed REST endpoints for orchestration and a websocket stream for
            live agent events. This page is intentionally small; the architecture boundary is the
            main deliverable.
          </p>
        </div>
        <Panel title="Agent Event Stream">
          <AgentActivityFeed />
        </Panel>
      </div>
    </main>
  );
}
