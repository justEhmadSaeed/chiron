/**
 * Optional origin of the Chiron FastAPI server (e.g. `http://127.0.0.1:8000`, no trailing slash).
 * When unset, requests stay same-origin so the Vite dev proxy can forward `/api` and `/ws`.
 */
function normalizeBackendOrigin(raw: string | undefined): string {
  const t = raw?.trim();
  if (!t) return "";
  return t.replace(/\/+$/, "");
}

export const backendOrigin = normalizeBackendOrigin(import.meta.env.VITE_BACKEND_URL);

export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  if (!backendOrigin) return p;
  return `${backendOrigin}${p}`;
}

export function agentEventsWebSocketUrl(): string {
  if (backendOrigin) {
    const url = new URL(
      backendOrigin.startsWith("http://") || backendOrigin.startsWith("https://")
        ? backendOrigin
        : `http://${backendOrigin}`
    );
    const wsProtocol = url.protocol === "https:" ? "wss:" : "ws:";
    return `${wsProtocol}//${url.host}/ws/agent-events`;
  }
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}/ws/agent-events`;
}
