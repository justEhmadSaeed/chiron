import type { AgentRun, AgentRunCreateRequest } from "@chiron/contracts";

import { getApiBaseUrl } from "@/lib/config";

export async function listAgentRuns(): Promise<AgentRun[]> {
  const response = await fetch(`${getApiBaseUrl()}/v1/agent-runs`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Failed to list agent runs");
  }

  return (await response.json()) as AgentRun[];
}

export async function createAgentRun(payload: AgentRunCreateRequest): Promise<AgentRun> {
  const response = await fetch(`${getApiBaseUrl()}/v1/agent-runs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error("Failed to create agent run");
  }

  return (await response.json()) as AgentRun;
}
