import type { components } from "./generated/api";

export type AgentRunStatus = components["schemas"]["AgentRunStatus"];

type GeneratedAgentRun = components["schemas"]["AgentRun"];

export interface AgentRun extends Omit<GeneratedAgentRun, "created_at" | "run_id"> {
  created_at: string;
  run_id: string;
}

export interface AgentRunCreateRequest {
  agent_name: string;
  input?: Record<string, unknown>;
}

export interface AgentEvent {
  event_id: string;
  run_id: string;
  event_type: string;
  created_at: string;
  payload: Record<string, unknown>;
}

export type QCResult = components["schemas"]["QCResult"];
export type Reference = components["schemas"]["Reference"];
export type ExperimentPlanData = components["schemas"]["ExperimentPlanData"];
export type ExperimentResponse = components["schemas"]["ExperimentResponse"];
