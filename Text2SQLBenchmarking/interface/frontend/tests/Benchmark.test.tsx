import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { BenchmarkJob, CatalogResponse, ExperimentStatus } from "../src/api/types";
import { BenchmarkPlaceholder } from "../src/features/benchmark/BenchmarkPlaceholder";

const configuration = { database: "sih_database", library: "raw_model", model_id: "model", context: "default" };
const metricMetadata = [
  { key: "execution_accuracy", code: "EX", label: "Acurácia de Execução (EX)", description: "Proporção de consultas cujo resultado executado é exatamente igual ao da Ground Truth.", format: "percentage" as const, order: 1, prominence: "primary" as const, initially_visible: true, parquet_column: null },
  { key: "soft_f1", code: "Soft_F1", label: "Soft F1", description: "F1 entre os conjuntos de linhas retornadas, ignorando ordem e multiplicidade.", format: "percentage" as const, order: 2, prominence: "secondary" as const, initially_visible: true, parquet_column: "soft_f1" },
  { key: "stats", code: "Stats", label: "Statistical Summarization", description: "Stats.", format: "percentage" as const, order: 3, prominence: "detail" as const, initially_visible: false, parquet_column: "stats" },
  { key: "similarity", code: "Similarity", label: "Similarity", description: "Similarity.", format: "percentage" as const, order: 4, prominence: "detail" as const, initially_visible: false, parquet_column: "similarity" },
  { key: "ves", code: "VES", label: "Valid Efficiency Score", description: "VES.", format: "percentage" as const, order: 5, prominence: "detail" as const, initially_visible: false, parquet_column: "ves" },
  { key: "exact_match", code: "EM", label: "Exact Match", description: "EM.", format: "percentage" as const, order: 6, prominence: "detail" as const, initially_visible: false, parquet_column: "exact_match" },
  { key: "component_match", code: "CM", label: "Component Match (CM)", description: "Média de similaridade entre colunas, tabelas, agregações e condições SQL.", format: "percentage" as const, order: 7, prominence: "secondary" as const, initially_visible: true, parquet_column: "component_match" },
  { key: "structural_correctness", code: "StCo", label: "Structural Correctness", description: "StCo.", format: "percentage" as const, order: 8, prominence: "detail" as const, initially_visible: false, parquet_column: "structural_correctness" },
  { key: "logical_form_accuracy", code: "LFA", label: "Logical Form Accuracy", description: "LFA.", format: "percentage" as const, order: 9, prominence: "detail" as const, initially_visible: false, parquet_column: "logical_form_accuracy" },
  { key: "leco", code: "LeCo", label: "Levenshtein Correctness", description: "LeCo.", format: "percentage" as const, order: 10, prominence: "detail" as const, initially_visible: false, parquet_column: "leco" },
  { key: "skeleton_correctness", code: "SkCo", label: "Skeleton Correctness", description: "SkCo.", format: "percentage" as const, order: 11, prominence: "detail" as const, initially_visible: false, parquet_column: "skeleton_correctness" },
  { key: "pcm_f1", code: "PCMF1", label: "Partial Component Match F1", description: "PCMF1.", format: "percentage" as const, order: 12, prominence: "detail" as const, initially_visible: false, parquet_column: "pcm_f1" },
  { key: "query_affinity_score", code: "QAS", label: "Query Affinity Score", description: "QAS.", format: "percentage" as const, order: 13, prominence: "detail" as const, initially_visible: false, parquet_column: "query_affinity_score" }
];
const catalog: CatalogResponse = {
  databases: [{ id: "sih_database", label: "SIH/DataSUS" }, { id: "datasus", label: "JABUTI-SQL" }],
  libraries: [{ id: "raw_model", label: "RawModel", contexts: ["default", "examples"], model_ids: ["model"], availability: { chat: { available: true, reason: null }, benchmark: { available: true, reason: null } }, order: 1 }],
  models: [{ id: "model", label: "Modelo sintético", family: "general", order: 1 }],
  contexts: [{ id: "default", label: "Configuração padrão" }, { id: "examples", label: "Somente exemplos" }],
  metrics: metricMetadata,
  initial_configuration: configuration
};
const missing = { relative_path: "artifact.parquet", exists: false, size: null, mtime_ns: null, sha256: null };
const existing = { relative_path: "artifact.parquet", exists: true, size: 10, mtime_ns: 20, sha256: "hash" };
const aggregate = {
  metrics: {
    execution_accuracy: { value: 0.215686, available: true, numerator: 11, denominator: 51 },
    soft_f1: { value: 0.625, available: true, denominator: 51 },
    stats: { value: 0.5, available: true, denominator: 51 },
    similarity: { value: 0.5, available: true, denominator: 51 },
    ves: { value: 0.5, available: true, denominator: 51 },
    exact_match: { value: 0.5, available: true, denominator: 51 },
    component_match: { value: 0.75, available: true, denominator: 49 },
    structural_correctness: { value: 0.5, available: true, denominator: 51 },
    logical_form_accuracy: { value: 0.5, available: true, denominator: 51 },
    leco: { value: 0.5, available: true, denominator: 51 },
    skeleton_correctness: { value: 0.5, available: true, denominator: 51 },
    pcm_f1: { value: 0.5, available: true, denominator: 51 },
    query_affinity_score: { value: 0.5, available: true, denominator: 51 }
  },
  counts: { total: 51, correct: 11, incorrect_without_error: 30, errors: 10, timeouts: 4 },
  times: { generation: 10, execution_ground_truth: 20, execution_generated: 30, execution_total: 50, recorded_total: 60 }
};

function status(artifact_state: ExperimentStatus["artifact_state"], changes: Partial<ExperimentStatus> = {}): ExperimentStatus {
  return {
    configuration,
    seed: 42,
    artifact_state,
    generation: artifact_state === "not_started" ? missing : existing,
    execution: artifact_state === "complete" || artifact_state === "invalid_result" ? existing : missing,
    invalid_reason: artifact_state === "invalid_result" ? "Parquet inválido" : null,
    ...(artifact_state === "complete" ? aggregate : { metrics: null, counts: null, times: null }),
    ...changes
  };
}

function job(state: BenchmarkJob["state"], withResult = false, changes: Partial<BenchmarkJob> = {}): BenchmarkJob {
  return {
    job_id: "job-1",
    configuration,
    seed: 42,
    action: "run_missing_stages",
    state,
    stage: state,
    artifact_state: withResult ? "complete" : "not_started",
    created_at: "2026-08-08T12:00:00-03:00",
    updated_at: "2026-08-08T12:00:01-03:00",
    history_directory: null,
    error: null,
    ...(withResult ? aggregate : { metrics: null, counts: null, times: null }),
    ...changes
  };
}

function response(body: unknown, ok = true) {
  return Promise.resolve({ ok, json: () => Promise.resolve(body) });
}

function renderBenchmark(props: Partial<React.ComponentProps<typeof BenchmarkPlaceholder>> = {}) {
  return render(<BenchmarkPlaceholder configuration={configuration} catalog={catalog} onActivityChange={vi.fn()} onVisibleChange={vi.fn()} {...props} />);
}

function baseApi(experiment: ExperimentStatus, active: BenchmarkJob | null = null) {
  let statusCalls = 0;
  return vi.fn((url: string) => {
    if (url.includes("experiments/status")) {
      statusCalls += 1;
      return response(statusCalls > 1 && active ? status("complete") : experiment);
    }
    if (url.includes("jobs/active")) return response({ job: active });
    if (url.includes("jobs/job-1")) return response({ job: job("completed", true) });
    throw new Error(`URL inesperada: ${url}`);
  });
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe("Benchmark", () => {
  it("apresenta not_started e cria job com polling até o resultado", async () => {
    let statusCalls = 0;
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url.includes("experiments/status")) {
        statusCalls += 1;
        return response(status(statusCalls > 1 ? "complete" : "not_started"));
      }
      if (url.includes("jobs/active")) return response({ job: null });
      if (url.endsWith("/benchmark/jobs") && init?.method === "POST") return response({ job_id: "job-1", poll: "/api/v1/benchmark/jobs/job-1", snapshot: job("accepted") });
      if (url.includes("jobs/job-1")) return response({ job: job("completed", true) });
      throw new Error(`URL inesperada: ${url}`);
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    renderBenchmark();
    expect(await screen.findByText("Benchmark ainda não executado")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Executar benchmark" }));
    expect(await screen.findByText("21,57%", {}, { timeout: 2_000 })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Acurácia de Execução (EX)" })).toBeInTheDocument();
    expect(screen.getByText("11 de 51 consultas corretas")).toBeInTheDocument();
    const executionHeading = screen.getByRole("heading", { name: "Acurácia de Execução (EX)" });
    const counts = screen.getByLabelText("Contagens da Acurácia de Execução");
    for (const [label, value] of [["Total", "51"], ["Corretas", "11"], ["Incorretas sem erro", "30"], ["Erros", "10"], ["Timeouts", "4"]]) {
      const item = within(counts).getByText(label).closest("div");
      expect(item).not.toBeNull();
      expect(within(item as HTMLElement).getByText(value)).toBeInTheDocument();
    }
    const distributionHeading = screen.getByRole("heading", { name: "Distribuição dos resultados" });
    const legend = screen.getByRole("list", { name: "Legenda da distribuição" });
    expect(within(legend).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "Corretas11",
      "Incorretas sem erro30",
      "Erros10"
    ]);
    expect(screen.getByText("Geração").closest(".time-row")).toHaveTextContent("10 s");
    expect(screen.getByText("Execução da referência").closest(".time-row")).toHaveTextContent("20 s");
    expect(screen.getByText("Execução da consulta gerada").closest(".time-row")).toHaveTextContent("30 s");
    expect(screen.getByText("62,50%")).toBeInTheDocument();
    expect(screen.getByText("75,00%")).toBeInTheDocument();
    expect(screen.getByText("Cobertura: 49 de 51 consultas")).toBeInTheDocument();
    const softF1Heading = screen.getByRole("heading", { name: "Soft F1" });
    const componentMatchHeading = screen.getByRole("heading", { name: "Component Match (CM)" });
    expect(screen.queryByText("Soft F1 (Soft_F1)")).not.toBeInTheDocument();
    expect(executionHeading.compareDocumentPosition(counts) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(counts.compareDocumentPosition(distributionHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(distributionHeading.compareDocumentPosition(softF1Heading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(softF1Heading.compareDocumentPosition(componentMatchHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/Statistical Summarization|Valid Efficiency Score|Query Affinity Score/);
    expect(screen.getAllByText("Incorretas sem erro").length).toBeGreaterThan(0);
    expect(screen.getByText("Subconjunto de erros")).toBeInTheDocument();
    expect(screen.getAllByText(/Tempo registrado total/).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Sobre Acurácia de Execução (EX)" })).toBeInTheDocument();
    const glossary = screen.getByText("Entenda as métricas").closest("details");
    expect(glossary).not.toHaveAttribute("open");
    fireEvent.click(screen.getByText("Entenda as métricas"));
    expect(glossary).toHaveAttribute("open");
    expect(screen.getAllByText("A consulta foi executada, mas o resultado obtido foi diferente da referência.").length).toBeGreaterThan(0);
    expect(screen.getAllByText("F1 entre os conjuntos de linhas retornadas, ignorando ordem e multiplicidade.").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Média de similaridade entre colunas, tabelas, agregações e condições SQL.").length).toBeGreaterThan(0);
    const creation = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/benchmark/jobs") && init?.method === "POST");
    expect(JSON.parse(String(creation?.[1]?.body))).toMatchObject({ ...configuration, seed: 42, action: "run_missing_stages" });
  });

  it("mostra travessão para métrica indisponível sem recalcular no frontend", async () => {
    const unavailable = status("complete", {
      metrics: {
        ...aggregate.metrics,
        component_match: { value: null, available: false, denominator: 0 }
      }
    });
    globalThis.fetch = baseApi(unavailable) as unknown as typeof fetch;
    renderBenchmark();

    expect(await screen.findByText("21,57%")).toBeInTheDocument();
    const secondary = screen.getByLabelText("Métricas secundárias");
    expect(within(secondary).getByText("—")).toBeInTheDocument();
    expect(within(secondary).getByText("Cobertura: 0 de 51 consultas")).toBeInTheDocument();
  });

  it("explica generation_only e executa apenas etapas faltantes", async () => {
    globalThis.fetch = baseApi(status("generation_only")) as unknown as typeof fetch;
    renderBenchmark();
    expect(await screen.findByText("Geração disponível")).toBeInTheDocument();
    expect(screen.getByText(/Somente execução e métricas/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Executar etapas faltantes" })).toBeInTheDocument();
  });

  it("mostra resultado complete e bloqueia sobrescrita de invalid_result", async () => {
    globalThis.fetch = baseApi(status("complete")) as unknown as typeof fetch;
    const mounted = renderBenchmark();
    expect(await screen.findByText("21,57%")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reexecutar benchmark" })).toBeInTheDocument();
    mounted.unmount();

    globalThis.fetch = baseApi(status("invalid_result")) as unknown as typeof fetch;
    renderBenchmark();
    expect(await screen.findByText("Resultado inválido")).toBeInTheDocument();
    expect(screen.getByText("Nenhum arquivo será sobrescrito.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Executar|Reexecutar/ })).not.toBeInTheDocument();
  });

  it("remove o resultado anterior ao trocar default por examples e não o restaura se a consulta falhar", async () => {
    const changedConfiguration = { ...configuration, context: "examples" };
    const fetchMock = vi.fn((url: string) => {
      if (url.includes("experiments/status")) {
        const context = new URL(url, "http://localhost").searchParams.get("context");
        if (context === configuration.context) return response(status("complete"));
        return response({ error: { code: "INTERNAL_ERROR", message: "Falha sintética da nova seleção.", retryable: false } }, false);
      }
      if (url.includes("jobs/active")) return response({ job: null });
      throw new Error(`URL inesperada: ${url}`);
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    const onActivityChange = vi.fn();
    const onVisibleChange = vi.fn();
    const mounted = render(
      <BenchmarkPlaceholder
        configuration={configuration}
        catalog={catalog}
        onActivityChange={onActivityChange}
        onVisibleChange={onVisibleChange}
      />
    );

    expect(await screen.findByText("21,57%")).toBeInTheDocument();
    mounted.rerender(
      <BenchmarkPlaceholder
        configuration={changedConfiguration}
        catalog={catalog}
        onActivityChange={onActivityChange}
        onVisibleChange={onVisibleChange}
      />
    );

    expect(screen.queryByText("21,57%")).not.toBeInTheDocument();
    expect(await screen.findByText("Falha sintética da nova seleção.")).toBeInTheDocument();
    expect(screen.queryByText("21,57%")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reexecutar benchmark" })).not.toBeInTheDocument();
  });

  it("ignora ExperimentStatus cuja seed não corresponde à seed exibida", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url.includes("experiments/status")) {
        const requestedSeed = Number(new URL(url, "http://localhost").searchParams.get("seed"));
        return response(status("complete", { seed: requestedSeed === 42 ? requestedSeed : 42 }));
      }
      if (url.includes("jobs/active")) return response({ job: null });
      throw new Error(`URL inesperada: ${url}`);
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    const onActivityChange = vi.fn();
    const onVisibleChange = vi.fn();
    const mounted = render(
      <BenchmarkPlaceholder
        configuration={configuration}
        catalog={catalog}
        seed={42}
        onActivityChange={onActivityChange}
        onVisibleChange={onVisibleChange}
      />
    );

    expect(await screen.findByText("21,57%")).toBeInTheDocument();
    mounted.rerender(
      <BenchmarkPlaceholder
        configuration={configuration}
        catalog={catalog}
        seed={99}
        onActivityChange={onActivityChange}
        onVisibleChange={onVisibleChange}
      />
    );

    expect(screen.queryByText("21,57%")).not.toBeInTheDocument();
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).includes("seed=99"))).toBe(true));
    expect(screen.queryByText("21,57%")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reexecutar benchmark" })).not.toBeInTheDocument();
  });

  it("recupera job ativo e continua o polling", async () => {
    globalThis.fetch = baseApi(status("not_started"), job("executing")) as unknown as typeof fetch;
    renderBenchmark();
    expect(await screen.findByRole("heading", { name: "Operação em andamento" })).toBeInTheDocument();
    expect(await screen.findByText("Executando e comparando consultas...")).toBeInTheDocument();
    expect(screen.queryByText("O acompanhamento respeita os limites dos scripts científicos existentes.")).not.toBeInTheDocument();
    expect(await screen.findByText("21,57%", {}, { timeout: 2_000 })).toBeInTheDocument();
  });

  it("recupera configuração e seed 123 do mesmo job ativo e continua acompanhando", async () => {
    const recoveredConfiguration = { ...configuration, database: "datasus" };
    const recovered = job("executing", false, { configuration: recoveredConfiguration, seed: 123 });
    const onBenchmarkRecovered = vi.fn();
    const fetchMock = vi.fn((url: string) => {
      if (url.includes("experiments/status")) return response(status("generation_only", { configuration: recoveredConfiguration, seed: 123 }));
      if (url.includes("jobs/active")) return response({ job: recovered });
      if (url.includes("jobs/job-1")) return response({ job: recovered });
      throw new Error(`URL inesperada: ${url}`);
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    renderBenchmark({ activeBenchmarkJob: recovered, onBenchmarkRecovered });

    expect(await screen.findByRole("button", { name: /Abrir configuração:.*Seed 123/ })).toBeInTheDocument();
    expect(screen.getByText(/JABUTI-SQL/)).toBeInTheDocument();
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).includes("experiments/status") && String(url).includes("database=datasus") && String(url).includes("seed=123"))).toBe(true));
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).includes("jobs/job-1"))).toBe(true), { timeout: 2_000 });
  });

  it("remove resultado arquivado após reexecução failed e preserva a mensagem terminal", async () => {
    let statusCalls = 0;
    const failed = job("failed", false, {
      action: "reexecute",
      error: { code: "SQL_GENERATION_ERROR", message: "Falha sintética após o arquivamento.", retryable: false }
    });
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url.includes("experiments/status")) {
        statusCalls += 1;
        return response(status(statusCalls === 1 ? "complete" : "not_started"));
      }
      if (url.includes("jobs/active")) return response({ job: null });
      if (url.includes("reexecution-intents")) return response({ confirmationToken: "opaque", expiresInSeconds: 300 });
      if (url.endsWith("/benchmark/jobs") && init?.method === "POST") return response({ job_id: "job-1", poll: "/api/v1/benchmark/jobs/job-1", snapshot: job("accepted", false, { action: "reexecute" }) });
      if (url.includes("jobs/job-1")) return response({ job: failed });
      throw new Error(`URL inesperada: ${url}`);
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    renderBenchmark();

    fireEvent.click(await screen.findByRole("button", { name: "Reexecutar benchmark" }));
    fireEvent.click(screen.getByRole("button", { name: "Arquivar e reexecutar" }));
    expect(await screen.findByText("Falha sintética após o arquivamento.", {}, { timeout: 2_000 })).toBeInTheDocument();
    expect(await screen.findByText("Benchmark ainda não executado")).toBeInTheDocument();
    expect(screen.queryByText("21,57%")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reexecutar benchmark" })).not.toBeInTheDocument();
  });

  it("atualiza os artefatos após interrupted sem apagar o diagnóstico", async () => {
    let statusCalls = 0;
    const interrupted = job("interrupted", false, {
      error: { code: "INTERNAL_ERROR", message: "Execução interrompida de forma sintética.", retryable: false }
    });
    const fetchMock = vi.fn((url: string) => {
      if (url.includes("experiments/status")) {
        statusCalls += 1;
        return response(status(statusCalls === 1 ? "not_started" : "generation_only"));
      }
      if (url.includes("jobs/active")) return response({ job: statusCalls <= 1 ? job("executing") : null });
      if (url.includes("jobs/job-1")) return response({ job: interrupted });
      throw new Error(`URL inesperada: ${url}`);
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    renderBenchmark();

    expect(await screen.findByText("Execução interrompida de forma sintética.", {}, { timeout: 2_000 })).toBeInTheDocument();
    expect(await screen.findByText("Geração disponível")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Benchmark interrompido" })).toBeInTheDocument();
  });

  it("confirma reexecução, cria intent e usa o token uma única vez", async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url.includes("experiments/status")) return response(status("complete"));
      if (url.includes("jobs/active")) return response({ job: null });
      if (url.includes("reexecution-intents")) return response({ confirmationToken: "opaque", expiresInSeconds: 300 });
      if (url.endsWith("/benchmark/jobs") && init?.method === "POST") return response({ job_id: "job-1", poll: "/api/v1/benchmark/jobs/job-1", snapshot: job("accepted") });
      if (url.includes("jobs/job-1")) return response({ job: job("completed", true) });
      throw new Error(`URL inesperada: ${url}`);
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    renderBenchmark();
    fireEvent.click(await screen.findByRole("button", { name: "Reexecutar benchmark" }));
    expect(screen.getByRole("dialog", { name: "Reexecutar este Benchmark?" })).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("reexecution-intents"))).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Arquivar e reexecutar" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).includes("reexecution-intents"))).toBe(true));
    const creation = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/benchmark/jobs") && init?.method === "POST");
    expect(JSON.parse(String(creation?.[1]?.body))).toMatchObject({ action: "reexecute", confirmationToken: "opaque" });
    expect(document.body.textContent).not.toContain("opaque");
  });

  it("exige nova confirmação em REEXECUTION_STATE_CHANGED e mostra RESOURCE_BUSY", async () => {
    const stateChanged = vi.fn((url: string, init?: RequestInit) => {
      if (url.includes("experiments/status")) return response(status("complete"));
      if (url.includes("jobs/active")) return response({ job: null });
      if (url.includes("reexecution-intents")) return response({ confirmationToken: "old", expiresInSeconds: 300 });
      if (url.endsWith("/benchmark/jobs") && init?.method === "POST") return response({ error: { code: "REEXECUTION_STATE_CHANGED", message: "mudou", retryable: false } }, false);
      throw new Error(`URL inesperada: ${url}`);
    });
    globalThis.fetch = stateChanged as unknown as typeof fetch;
    const mounted = renderBenchmark();
    fireEvent.click(await screen.findByRole("button", { name: "Reexecutar benchmark" }));
    fireEvent.click(screen.getByRole("button", { name: "Arquivar e reexecutar" }));
    expect(await screen.findByText(/Revise o resultado e confirme novamente/)).toBeInTheDocument();
    expect(stateChanged.mock.calls.filter(([url]) => String(url).includes("reexecution-intents"))).toHaveLength(1);
    mounted.unmount();

    const busy = vi.fn((url: string, init?: RequestInit) => {
      if (url.includes("experiments/status")) return response(status("not_started"));
      if (url.includes("jobs/active")) return response({ job: null });
      if (url.endsWith("/benchmark/jobs") && init?.method === "POST") return response({ error: { code: "RESOURCE_BUSY", message: "Outra operação pesada está em andamento.", retryable: true } }, false);
      throw new Error(`URL inesperada: ${url}`);
    });
    globalThis.fetch = busy as unknown as typeof fetch;
    renderBenchmark();
    fireEvent.click(await screen.findByRole("button", { name: "Executar benchmark" }));
    expect(await screen.findByText("Outra operação pesada está em andamento.")).toBeInTheDocument();
  });

  it.each([
    ["MODEL_LOAD_ERROR", "Não há espaço suficiente em disco para baixar ou carregar este modelo. Libere espaço no servidor e tente novamente.", true],
    ["ARCHIVE_ERROR", "Não foi possível arquivar os artefatos existentes com segurança.", false],
    ["INTERNAL_ERROR", "Ocorreu um erro interno. Nenhum detalhe interno foi exposto.", false]
  ])("mantém erro terminal %s e respeita retryable", async (code, message, retryable) => {
    let statusCalls = 0;
    const terminal = job("failed", false, {
      error: { code, message, retryable },
      internal_detail: "token=secret /srv/private",
      traceback: "secret trace"
    } as Partial<BenchmarkJob>);
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url.includes("experiments/status")) { statusCalls += 1; return response(status("not_started")); }
      if (url.includes("jobs/active")) return response({ job: null });
      if (url.endsWith("/benchmark/jobs") && init?.method === "POST") return response({ job_id: "job-1", poll: "/api/v1/benchmark/jobs/job-1", snapshot: job("accepted") });
      if (url.includes("jobs/job-1")) return response({ job: terminal });
      throw new Error(`URL inesperada: ${url}`);
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    renderBenchmark();
    fireEvent.click(await screen.findByRole("button", { name: "Executar benchmark" }));
    expect(await screen.findByText(message, {}, { timeout: 2_000 })).toBeInTheDocument();
    expect(screen.getByText(code, { selector: "code" })).toBeInTheDocument();
    const manualRetry = screen.queryByRole("button", { name: "Consultar artefatos para nova tentativa" });
    expect(Boolean(manualRetry)).toBe(retryable);
    const callsAfterTerminal = fetchMock.mock.calls.length;
    vi.useFakeTimers();
    await act(async () => {
      vi.advanceTimersByTime(650);
      await Promise.resolve();
    });
    expect(fetchMock).toHaveBeenCalledTimes(callsAfterTerminal);
    expect(document.body.textContent).not.toMatch(/internal_detail|traceback|token=secret|\/srv\/private/);
  });

  it("retryable permite preparar uma nova tentativa, mas nunca a envia automaticamente", async () => {
    let creations = 0;
    const failed = job("failed", false, {
      error: { code: "MODEL_LOAD_ERROR", message: "Falha recuperável sintética.", retryable: true }
    });
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url.includes("experiments/status")) return response(status("not_started"));
      if (url.includes("jobs/active")) return response({ job: null });
      if (url.endsWith("/benchmark/jobs") && init?.method === "POST") {
        creations += 1;
        return response({ job_id: "job-1", poll: "/api/v1/benchmark/jobs/job-1", snapshot: job("accepted") });
      }
      if (url.includes("jobs/job-1")) return response({ job: failed });
      throw new Error(`URL inesperada: ${url}`);
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    renderBenchmark();
    fireEvent.click(await screen.findByRole("button", { name: "Executar benchmark" }));
    const retry = await screen.findByRole("button", { name: "Consultar artefatos para nova tentativa" });
    expect(creations).toBe(1);
    fireEvent.click(retry);
    await waitFor(() => expect(screen.getByRole("button", { name: "Executar benchmark" })).toBeInTheDocument());
    expect(creations).toBe(1);
  });
});
