import type { ApiErrorEnvelope, BenchmarkAction, BenchmarkJob, CatalogResponse, ChatJob, ConfigurationSelection, ExperimentStatus, HealthResponse, SystemStatus } from "./types";

const DEFAULT_TIMEOUT_MS = 8_000;
const apiBase = (import.meta.env.VITE_API_BASE_URL || "/api/v1").replace(/\/$/, "");
export class PublicApiError extends Error { constructor(readonly code: string, message: string, readonly retryable = false) { super(message); } }
export class RequestCancelledError extends Error {}

async function requestJson<T>(path: string, options: { method?: string; body?: unknown; signal?: AbortSignal } = {}): Promise<T> {
  const controller = new AbortController(); let timedOut = false; let externallyAborted = false;
  const timer = window.setTimeout(() => { timedOut = true; controller.abort(); }, DEFAULT_TIMEOUT_MS);
  const abortExternal = () => { externallyAborted = true; controller.abort(); };
  if (options.signal?.aborted) abortExternal(); else options.signal?.addEventListener("abort", abortExternal, { once: true });
  try {
    const response = await fetch(`${apiBase}${path}`, { method: options.method || "GET", headers: { Accept: "application/json", ...(options.body === undefined ? {} : { "Content-Type": "application/json" }) }, body: options.body === undefined ? undefined : JSON.stringify(options.body), signal: controller.signal });
    let body: unknown; try { body = await response.json(); } catch { throw new PublicApiError("INVALID_RESPONSE", "A API retornou uma resposta inválida."); }
    if (!response.ok) { const envelope = body as Partial<ApiErrorEnvelope>; if (envelope.error?.code && envelope.error.message) throw new PublicApiError(envelope.error.code, envelope.error.message, Boolean(envelope.error.retryable)); throw new PublicApiError("API_ERROR", "A API retornou um erro seguro."); }
    return body as T;
  } catch (error) {
    if (error instanceof PublicApiError) throw error;
    if (timedOut) throw new PublicApiError("REQUEST_TIMEOUT", "A API demorou mais que o esperado para responder.", true);
    if (externallyAborted) throw new RequestCancelledError();
    throw new PublicApiError("NETWORK_ERROR", "Não foi possível conectar à API local.", true);
  } finally { window.clearTimeout(timer); options.signal?.removeEventListener("abort", abortExternal); }
}
export const apiClient = {
  getCatalog: (signal?: AbortSignal) => requestJson<CatalogResponse>("/capabilities", { signal }), getStatus: (signal?: AbortSignal) => requestJson<SystemStatus>("/system/status", { signal }), getHealth: (signal?: AbortSignal) => requestJson<HealthResponse>("/health", { signal }),
  createChat: (question: string, configuration: ConfigurationSelection, signal?: AbortSignal) => requestJson<{ job_id: string; snapshot: ChatJob }>("/chat/jobs", { method: "POST", body: { question, ...configuration }, signal }), getChat: (jobId: string, signal?: AbortSignal) => requestJson<{ job: ChatJob }>(`/chat/jobs/${encodeURIComponent(jobId)}`, { signal }),
  getBenchmarkStatus: (configuration: ConfigurationSelection, seed: number, signal?: AbortSignal) => {
    const query = new URLSearchParams({ ...configuration, seed: String(seed) });
    return requestJson<ExperimentStatus>(`/benchmark/experiments/status?${query.toString()}`, { signal });
  },
  getActiveBenchmark: (signal?: AbortSignal) => requestJson<{ job: BenchmarkJob | null }>("/benchmark/jobs/active", { signal }),
  getBenchmark: (jobId: string, signal?: AbortSignal) => requestJson<{ job: BenchmarkJob }>(`/benchmark/jobs/${encodeURIComponent(jobId)}`, { signal }),
  createBenchmark: (configuration: ConfigurationSelection, seed: number, action: BenchmarkAction, confirmationToken?: string, signal?: AbortSignal) => requestJson<{ job_id: string; snapshot: BenchmarkJob; poll: string }>("/benchmark/jobs", { method: "POST", body: { ...configuration, seed, action, ...(confirmationToken ? { confirmationToken } : {}) }, signal }),
  createReexecutionIntent: (configuration: ConfigurationSelection, seed: number, signal?: AbortSignal) => requestJson<{ confirmationToken: string; expiresInSeconds: number }>("/benchmark/reexecution-intents", { method: "POST", body: { ...configuration, seed }, signal })
};
