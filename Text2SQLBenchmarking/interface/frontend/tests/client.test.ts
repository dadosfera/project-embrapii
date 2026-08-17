import { afterEach, describe, expect, it, vi } from "vitest";
import { apiClient, PublicApiError, RequestCancelledError } from "../src/api/client";

function pendingFetch(_url: string, init?: RequestInit): Promise<Response> {
  return new Promise((_, reject) => {
    init?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")), { once: true });
  });
}

afterEach(() => { vi.useRealTimers(); });

describe("cliente HTTP", () => {
  it("transforma apenas o abort do timer em erro público de timeout", async () => {
    vi.useFakeTimers();
    globalThis.fetch = vi.fn(pendingFetch) as unknown as typeof fetch;
    const request = apiClient.getCatalog();
    vi.advanceTimersByTime(8_000);
    await expect(request).rejects.toMatchObject({
      code: "REQUEST_TIMEOUT",
      message: "A API demorou mais que o esperado para responder.",
      retryable: true
    });
  });

  it("mantém cancelamento externo separado do timeout", async () => {
    globalThis.fetch = vi.fn(pendingFetch) as unknown as typeof fetch;
    const controller = new AbortController();
    const request = apiClient.getStatus(controller.signal);
    controller.abort();
    await expect(request).rejects.toBeInstanceOf(RequestCancelledError);
  });

  it("codifica status e confirmação do Benchmark sem expor paths", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
    const configuration = { database: "db", library: "lib", model_id: "org/model", context: "ctx" };
    await apiClient.getBenchmarkStatus(configuration, 42);
    await apiClient.createBenchmark(configuration, 42, "reexecute", "opaque");
    const calls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls[0][0]).toContain("model_id=org%2Fmodel");
    expect(JSON.parse(calls[1][1].body)).toEqual({ ...configuration, seed: 42, action: "reexecute", confirmationToken: "opaque" });
  });
});
