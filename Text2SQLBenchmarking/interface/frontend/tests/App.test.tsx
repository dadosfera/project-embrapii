import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { SystemStatus } from "../src/api/types";
import App from "../src/App";
import { AppProvider } from "../src/state/AppContext";

const catalog = {
  databases: [{ id: "sih_database", label: "SIH/DataSUS" }, { id: "datasus", label: "JABUTI-SQL" }],
  libraries: [
    { id: "raw_model", label: "RawModel", contexts: ["default", "examples"], model_ids: ["general"], availability: { chat: { available: true, reason: null }, benchmark: { available: true, reason: null } }, order: 1 },
    { id: "vanna_ai", label: "VannaAI", contexts: ["none", "documentation"], model_ids: ["general"], availability: { chat: { available: true, reason: null }, benchmark: { available: true, reason: null } }, order: 2 },
    { id: "premsql_agent", label: "PremSQLAgent", contexts: ["default"], model_ids: ["general"], availability: { chat: { available: false, reason: { code: "PREMSQL_CHAT_UNAVAILABLE", message: "Use-o no modo Benchmark." } }, benchmark: { available: true, reason: null } }, order: 3 },
    { id: "xiyan_sql", label: "XiYanSQL", contexts: ["none", "examples"], model_ids: ["xiyan"], availability: { chat: { available: true, reason: null }, benchmark: { available: true, reason: null } }, order: 4 }
  ],
  models: [{ id: "general", label: "Modelo geral", family: "general", order: 1 }, { id: "xiyan", label: "Modelo XiYan", family: "xiyan", order: 2 }],
  contexts: [{ id: "default", label: "Configuração padrão" }, { id: "none", label: "Sem contexto" }, { id: "documentation", label: "Somente documentação" }, { id: "examples", label: "Somente exemplos" }],
  metrics: [
    { key: "execution_accuracy", code: "EX", label: "Acurácia de Execução (EX)", description: "EX.", format: "percentage", order: 1, prominence: "primary", initially_visible: true, parquet_column: null },
    { key: "soft_f1", code: "Soft_F1", label: "Soft F1", description: "Soft F1.", format: "percentage", order: 2, prominence: "secondary", initially_visible: true, parquet_column: "soft_f1" },
    { key: "component_match", code: "CM", label: "Component Match (CM)", description: "CM.", format: "percentage", order: 7, prominence: "secondary", initially_visible: true, parquet_column: "component_match" }
  ],
  initial_configuration: { database: "sih_database", library: "raw_model", model_id: "general", context: "default" }
};

const freeStatus: SystemStatus = { is_busy: false, active_operation: null, model_state: "EMPTY", runtime_loaded: false, runtime_configuration: null, benchmark_job: null };

function response(body: unknown, ok = true) {
  return Promise.resolve({ ok, json: () => Promise.resolve(body) });
}

function mockApi(status = freeStatus) {
  const fetchMock = vi.fn((url: string) => {
    if (url.includes("capabilities")) return response(catalog);
    if (url.includes("benchmark/experiments/status")) {
      const query = new URL(url, "http://localhost").searchParams;
      return response({
        configuration: {
          database: query.get("database"), library: query.get("library"), model_id: query.get("model_id"), context: query.get("context")
        },
        seed: Number(query.get("seed")), artifact_state: "not_started",
        generation: { relative_path: "generation.parquet", exists: false, size: null, mtime_ns: null, sha256: null },
        execution: { relative_path: "execution.parquet", exists: false, size: null, mtime_ns: null, sha256: null },
        invalid_reason: null, metrics: null, counts: null, times: null
      });
    }
    if (url.includes("benchmark/jobs/active")) return response({ job: status.benchmark_job });
    if (status.benchmark_job && url.includes(`benchmark/jobs/${status.benchmark_job.job_id}`)) return response({ job: status.benchmark_job });
    return response(status);
  });
  globalThis.fetch = fetchMock as unknown as typeof fetch;
  return fetchMock;
}

function renderApp() {
  return render(<AppProvider><App /></AppProvider>);
}

function pendingResponse(_url: string, init?: RequestInit): Promise<Response> {
  return new Promise((_, reject) => {
    init?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")), { once: true });
  });
}

afterEach(() => { vi.useRealTimers(); });

describe("shell da interface", () => {
  it("abre em Chat, mostra loading e usa a configuração retornada pela API", async () => {
    const fetchMock = mockApi();
    renderApp();
    expect(screen.getByText("Carregando catálogo e estado operacional...")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Chat SQL" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Chat SQL" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("button", { name: "Benchmark" })).not.toHaveAttribute("aria-current");
    expect((screen.getByLabelText("Biblioteca") as HTMLSelectElement).value).toBe("raw_model");
    expect(screen.getAllByText("RawModel").length).toBeGreaterThan(0);
    expect(screen.getByText("O que gostaria de saber sobre a base SIH/DataSUS?")).toBeInTheDocument();
    expect(screen.queryByText("API pronta para configuração.")).not.toBeInTheDocument();
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      "/api/v1/capabilities",
      "/api/v1/system/status"
    ]);
    expect(document.body.textContent?.toLowerCase()).not.toContain("token");
    expect(document.body.textContent?.toLowerCase()).not.toContain("local_models");
  });

  it("remove PremSQLAgent do Chat, preserva as bibliotecas válidas e restaura PremSQL no Benchmark", async () => {
    mockApi();
    renderApp();
    await screen.findByRole("heading", { name: "Chat SQL" });
    const chatLibrary = screen.getByLabelText("Biblioteca") as HTMLSelectElement;
    expect(Array.from(chatLibrary.options).map((option) => option.text)).toEqual(["RawModel", "VannaAI", "XiYanSQL"]);
    expect(screen.queryByRole("option", { name: "PremSQLAgent" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Benchmark" }));
    expect(screen.getByRole("option", { name: "PremSQLAgent" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Biblioteca"), { target: { value: "premsql_agent" } });
    expect((screen.getByLabelText("Biblioteca") as HTMLSelectElement).value).toBe("premsql_agent");
    expect((screen.getByRole("option", { name: "PremSQLAgent" }) as HTMLOptionElement).disabled).toBe(false);
    await waitFor(() => expect(screen.queryByText("Consultando artefatos e job ativo...")).not.toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Chat SQL" }));
    expect((screen.getByLabelText("Biblioteca") as HTMLSelectElement).value).toBe("raw_model");
    expect(screen.queryByRole("option", { name: "PremSQLAgent" })).not.toBeInTheDocument();
    expect(Array.from((screen.getByLabelText("Biblioteca") as HTMLSelectElement).options).map((option) => option.text)).toEqual(["RawModel", "VannaAI", "XiYanSQL"]);

    fireEvent.click(screen.getByRole("button", { name: "Benchmark" }));
    expect((screen.getByLabelText("Biblioteca") as HTMLSelectElement).value).toBe("premsql_agent");
    expect(screen.getByRole("option", { name: "PremSQLAgent" })).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByText("Consultando artefatos e job ativo...")).not.toBeInTheDocument());
  });

  it("filtra e corrige modelo e contexto ao alterar biblioteca", async () => {
    mockApi();
    renderApp();
    await screen.findByRole("heading", { name: "Chat SQL" });
    fireEvent.change(screen.getByLabelText("Biblioteca"), { target: { value: "xiyan_sql" } });
    expect((screen.getByLabelText("Modelo") as HTMLSelectElement).value).toBe("xiyan");
    expect((screen.getByLabelText("Contexto") as HTMLSelectElement).value).toBe("none");
    expect(screen.getByRole("option", { name: "Modelo XiYan" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Modelo geral" })).not.toBeInTheDocument();
  });

  it("oferece Examples para RawModel nos dois modos sem criar outra biblioteca", async () => {
    mockApi();
    renderApp();
    await screen.findByRole("heading", { name: "Chat SQL" });

    const chatContext = screen.getByLabelText("Contexto") as HTMLSelectElement;
    expect(Array.from(chatContext.options).map((option) => option.text)).toEqual([
      "Configuração padrão",
      "Somente exemplos"
    ]);
    fireEvent.change(chatContext, { target: { value: "examples" } });
    expect(chatContext.value).toBe("examples");
    expect(screen.getByRole("button", { name: /Abrir configuração:.*Somente exemplos/ })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: /RawModelExamples/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Benchmark" }));
    expect((screen.getByLabelText("Contexto") as HTMLSelectElement).value).toBe("examples");
    expect(screen.getByLabelText("Seed")).toHaveValue(42);
    expect(screen.getByRole("button", { name: /Abrir configuração:.*Somente exemplos.*Seed 42/ })).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByText("Consultando artefatos e job ativo...")).not.toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Chat SQL" }));
    expect((screen.getByLabelText("Contexto") as HTMLSelectElement).value).toBe("examples");
    expect(screen.queryByLabelText("Seed")).not.toBeInTheDocument();
  });

  it("mostra e atualiza a seed somente no Benchmark", async () => {
    const fetchMock = mockApi();
    renderApp();
    await screen.findByRole("heading", { name: "Chat SQL" });
    expect(screen.queryByLabelText("Seed")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Benchmark" }));
    expect(screen.getByLabelText("Seed")).toHaveValue(42);
    fireEvent.change(screen.getByLabelText("Seed"), { target: { value: "99" } });
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).includes("benchmark/experiments/status") && String(url).includes("seed=99"))).toBe(true));
    fireEvent.click(screen.getByRole("button", { name: "Recolher configuração" }));
    expect(screen.getByText("Seed", { selector: '[role="tooltip"]' })).toBeInTheDocument();
    const seedRailButton = screen.getByRole("button", { name: "Seed" });
    expect(seedRailButton).toHaveAttribute("aria-describedby", "rail-tooltip-seed");
    fireEvent.click(seedRailButton);
    expect(screen.getByLabelText("Seed")).toHaveValue(99);

    fireEvent.click(screen.getByRole("button", { name: "Chat SQL" }));
    expect(screen.queryByLabelText("Seed")).not.toBeInTheDocument();
  });

  it("bloqueia controles quando o status informa operação ativa", async () => {
    mockApi({ ...freeStatus, is_busy: true, active_operation: "BENCHMARK" });
    renderApp();
    await screen.findByText("Benchmark em execução...");
    expect(screen.getByRole("button", { name: "Benchmark" })).toBeDisabled();
    expect(screen.getByLabelText("Biblioteca")).toBeDisabled();
  });

  it("reabre no Benchmark e restaura configuração e seed do job ativo", async () => {
    const benchmarkJob = {
      job_id: "active-benchmark", configuration: { database: "datasus", library: "raw_model", model_id: "general", context: "default" }, seed: 123,
      action: "run_missing_stages" as const, state: "executing" as const, stage: "executing" as const, artifact_state: "generation_only" as const,
      created_at: "2026-08-08T12:00:00-03:00", updated_at: "2026-08-08T12:01:00-03:00", history_directory: null,
      metrics: null, counts: null, times: null, error: null
    };
    const fetchMock = mockApi({ ...freeStatus, is_busy: true, active_operation: "BENCHMARK", benchmark_job: benchmarkJob });
    renderApp();
    expect(await screen.findByRole("heading", { name: "Benchmark" })).toBeInTheDocument();
    expect((screen.getByLabelText("Base de dados") as HTMLSelectElement).value).toBe("datasus");
    expect(screen.getByLabelText("Seed")).toHaveValue(123);
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).includes("benchmark/experiments/status") && String(url).includes("database=datasus") && String(url).includes("seed=123"))).toBe(true));
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).includes("benchmark/jobs/active-benchmark"))).toBe(true), { timeout: 2_000 });
  });

  it("descobre depois do carregamento um Benchmark externo e troca configuração e seed juntas", async () => {
    vi.useFakeTimers();
    const benchmarkJob = {
      job_id: "external-benchmark", configuration: { database: "datasus", library: "raw_model", model_id: "general", context: "default" }, seed: 123,
      action: "run_missing_stages" as const, state: "executing" as const, stage: "executing" as const, artifact_state: "generation_only" as const,
      created_at: "2026-08-08T12:00:00-03:00", updated_at: "2026-08-08T12:01:00-03:00", history_directory: null,
      metrics: null, counts: null, times: null, error: null
    };
    const activeStatus = { ...freeStatus, is_busy: true, active_operation: "BENCHMARK", benchmark_job: benchmarkJob };
    let systemStatusCalls = 0;
    const fetchMock = vi.fn((url: string) => {
      if (url.includes("capabilities")) return response(catalog);
      if (url.includes("system/status")) {
        systemStatusCalls += 1;
        return response(systemStatusCalls === 1 ? freeStatus : activeStatus);
      }
      if (url.includes("benchmark/experiments/status")) {
        const query = new URL(url, "http://localhost").searchParams;
        return response({ configuration: benchmarkJob.configuration, seed: Number(query.get("seed")), artifact_state: "generation_only", generation: { relative_path: "generation.parquet", exists: true, size: 1, mtime_ns: 1, sha256: "hash" }, execution: { relative_path: "execution.parquet", exists: false, size: null, mtime_ns: null, sha256: null }, invalid_reason: null, metrics: null, counts: null, times: null });
      }
      if (url.includes("benchmark/jobs/active")) return response({ job: benchmarkJob });
      if (url.includes("benchmark/jobs/external-benchmark")) return response({ job: benchmarkJob });
      throw new Error(`URL inesperada: ${url}`);
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    renderApp();
    expect(await screen.findByRole("heading", { name: "Chat SQL" })).toBeInTheDocument();

    await act(async () => {
      vi.advanceTimersByTime(500);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(await screen.findByRole("heading", { name: "Benchmark" })).toBeInTheDocument();
    expect((screen.getByLabelText("Base de dados") as HTMLSelectElement).value).toBe("datasus");
    expect(screen.getByLabelText("Seed")).toHaveValue(123);
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("benchmark/experiments/status") && String(url).includes("database=datasus") && String(url).includes("seed=123"))).toBe(true);
  });

  it("oferece retry seguro e recolhe a sidebar", async () => {
    const fetchMock = vi.fn()
      .mockRejectedValueOnce(new Error("network"))
      .mockImplementation((url: string) => response(url.includes("capabilities") ? catalog : freeStatus));
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    renderApp();
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(await screen.findByRole("heading", { name: "Chat SQL" })).toBeInTheDocument();
    const toggle = screen.getByRole("button", { name: "Recolher configuração" });
    fireEvent.click(toggle);
    expect(screen.getByRole("button", { name: "Configuração geral" })).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByRole("button", { name: "Base de dados" })).toBeInTheDocument();
    expect(screen.queryByLabelText("Seed")).not.toBeInTheDocument();
    for (const tooltip of ["Configuração", "Base de dados", "Biblioteca", "Modelo", "Contexto"]) {
      expect(screen.getByText(tooltip, { selector: '[role="tooltip"]' })).toBeInTheDocument();
    }

    fireEvent.click(screen.getByRole("button", { name: /Abrir configuração: SIH\/DataSUS/ }));
    expect(screen.getByRole("button", { name: "Recolher configuração" })).toHaveAttribute("aria-expanded", "true");
    fireEvent.click(screen.getByRole("button", { name: "Recolher configuração" }));

    for (const label of ["Configuração geral", "Base de dados", "Biblioteca", "Modelo", "Contexto"]) {
      fireEvent.click(screen.getByRole("button", { name: label }));
      expect(screen.getByRole("button", { name: "Recolher configuração" })).toHaveAttribute("aria-expanded", "true");
      fireEvent.click(screen.getByRole("button", { name: "Recolher configuração" }));
    }
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
  });

  it("mostra timeout seguro, sai do loading e o retry refaz as duas leituras", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn()
      .mockImplementationOnce(pendingResponse)
      .mockImplementationOnce(pendingResponse)
      .mockImplementation((url: string) => response(url.includes("capabilities") ? catalog : freeStatus));
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    renderApp();
    await act(async () => {
      vi.advanceTimersByTime(8_000);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(screen.getByRole("alert")).toHaveTextContent("A API demorou mais que o esperado para responder.");
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    await act(async () => { await Promise.resolve(); });
    expect(screen.getByRole("heading", { name: "Chat SQL" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(4);
  });

  it("ignora cancelamento no desmontar e apresenta envelopes e JSON inválido com segurança", async () => {
    const signals: AbortSignal[] = [];
    globalThis.fetch = vi.fn((_url: string, init?: RequestInit) => {
      if (init?.signal) signals.push(init.signal);
      return pendingResponse(_url, init);
    }) as unknown as typeof fetch;
    const mounted = renderApp();
    mounted.unmount();
    expect(signals).toHaveLength(2);
    expect(signals.every((signal) => signal.aborted)).toBe(true);

    globalThis.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: false, json: () => Promise.resolve({ error: { code: "RESOURCE_BUSY", message: "Outra operação pesada está em andamento.", retryable: true } }) })
      .mockImplementationOnce(pendingResponse) as unknown as typeof fetch;
    renderApp();
    expect(await screen.findByRole("alert")).toHaveTextContent("Outra operação pesada está em andamento.");
    expect(screen.queryByText(/internal_detail|traceback/i)).not.toBeInTheDocument();

    globalThis.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: () => Promise.reject(new Error("bad json")) })
      .mockImplementationOnce(pendingResponse) as unknown as typeof fetch;
    renderApp();
    expect(await screen.findByText("A API retornou uma resposta inválida.")).toBeInTheDocument();
  });
});
