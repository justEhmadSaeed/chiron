const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const wsUrl = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws/agent-events";

export function getApiBaseUrl() {
  return apiBaseUrl;
}

export function getWebSocketUrl() {
  return wsUrl;
}
