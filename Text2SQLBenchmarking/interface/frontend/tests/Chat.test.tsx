import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ChatJob } from "../src/api/types";
import { ChatPlaceholder } from "../src/features/chat/ChatPlaceholder";

const configuration = { database: "db", library: "lib", model_id: "model", context: "ctx" };
const accepted: ChatJob = { job_id: "j", state: "accepted", configuration, sql: null, columns: null, rows: null, rowCount: null, displayedRowCount: null, truncated: null, generationTimeSeconds: null, executionTimeSeconds: null, error: null };
const succeeded: ChatJob = { ...accepted, state: "succeeded", sql: "SELECT 1", columns: ["x"], rows: [[1]], rowCount: 1, displayedRowCount: 1, truncated: false, generationTimeSeconds: 1, executionTimeSeconds: 2, error: null };

function renderChat(props: Partial<React.ComponentProps<typeof ChatPlaceholder>> = {}) {
  return render(<ChatPlaceholder configuration={configuration} onActivityChange={vi.fn()} onVisibleChange={vi.fn()} {...props} />);
}

function completedResponse(job: ChatJob = succeeded) {
  globalThis.fetch = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ job_id: "j", snapshot: accepted }) })
    .mockResolvedValue({ ok: true, json: () => Promise.resolve({ job }) });
}

afterEach(() => { vi.restoreAllMocks(); });

describe("Chat", () => {
  it("mostra o estado vazio dinâmico, resumo da configuração e envia uma pergunta uma única vez", async () => {
    completedResponse();
    const onOpenConfiguration = vi.fn();
    renderChat({ onOpenConfiguration });

    expect(screen.getByText("O que gostaria de saber sobre a base db?")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Pergunte sobre db")).toBeInTheDocument();
    expect(screen.queryByText("T2")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Abrir configuração: db, lib, model, ctx/ }));
    expect(onOpenConfiguration).toHaveBeenCalledTimes(1);

    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "qual?" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    expect(screen.getByRole("button", { name: "Enviar pergunta" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(2));
    expect(screen.getByText("qual?")).toBeInTheDocument();
  });

  it("usa o símbolo da Dadosfera somente nas respostas do assistente", async () => {
    completedResponse();
    const mounted = renderChat();
    expect(mounted.container.querySelector(".chat-empty-state .assistant-avatar")).toBeNull();

    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "qual?" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    expect(await screen.findByRole("cell", { name: "1" })).toBeInTheDocument();

    const avatar = mounted.container.querySelector<HTMLImageElement>(".assistant-avatar img");
    expect(avatar).not.toBeNull();
    expect(avatar?.src).toContain("dadosfera-symbol");
    expect(document.body.textContent).not.toContain("T2");
  });

  it("Enter envia e Shift+Enter preserva a composição sem enviar", async () => {
    completedResponse();
    renderChat();
    const editor = screen.getByLabelText("Pergunta independente");
    expect(screen.getByRole("button", { name: "Enviar pergunta" })).toBeDisabled();
    fireEvent.change(editor, { target: { value: "   " } });
    fireEvent.keyDown(editor, { key: "Enter", code: "Enter" });
    expect(globalThis.fetch).not.toHaveBeenCalled();
    fireEvent.change(editor, { target: { value: "linha 1" } });
    fireEvent.keyDown(editor, { key: "Enter", code: "Enter", shiftKey: true });
    expect(globalThis.fetch).not.toHaveBeenCalled();
    fireEvent.change(editor, { target: { value: "linha 1\nlinha 2" } });
    fireEvent.keyDown(editor, { key: "Enter", code: "Enter" });
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(2));
    expect(screen.getByText(/linha 1/)).toHaveTextContent("linha 1 linha 2");
  });

  it("traduz estados internos ativos para linguagem amigável", async () => {
    let resolvePoll: ((value: unknown) => void) | undefined;
    globalThis.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ job_id: "j", snapshot: { ...accepted, state: "generating" } }) })
      .mockImplementationOnce(() => new Promise((resolve) => { resolvePoll = resolve; }));
    const mounted = renderChat();
    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "q" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    await waitFor(() => expect(screen.getAllByRole("status").some((item) => item.textContent?.includes("Gerando SQL..."))).toBe(true));
    expect(document.body.textContent).not.toContain("generating");
    mounted.unmount();
    resolvePoll?.({ ok: true, json: () => Promise.resolve({ job: succeeded }) });
  });

  it("mantém Detalhes técnicos e SQL recolhidos e aninhados por padrão", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText }
    });
    completedResponse();
    renderChat();
    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "q" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    expect(await screen.findByRole("cell", { name: "1" })).toBeInTheDocument();

    const technicalSummary = screen.getByText("Detalhes técnicos");
    const technicalDetails = technicalSummary.closest("details");
    expect(technicalDetails).not.toHaveAttribute("open");
    expect(technicalDetails).toContainElement(screen.getByText("Mostrar SQL"));
    expect(technicalDetails).toContainElement(screen.getByRole("button", { name: "Copiar SQL" }));
    expect(within(technicalDetails as HTMLElement).getByText("db")).toBeInTheDocument();
    expect(within(technicalDetails as HTMLElement).getByText("lib")).toBeInTheDocument();
    expect(within(technicalDetails as HTMLElement).getByText("model")).toBeInTheDocument();
    expect(within(technicalDetails as HTMLElement).getByText("ctx")).toBeInTheDocument();
    expect(within(technicalDetails as HTMLElement).getByText("1 s")).toBeInTheDocument();
    expect(within(technicalDetails as HTMLElement).getByText("2 s")).toBeInTheDocument();

    fireEvent.click(technicalSummary);
    const sqlSummary = screen.getByText("Mostrar SQL");
    const sqlDetails = sqlSummary.closest("details");
    expect(sqlDetails).not.toHaveAttribute("open");
    fireEvent.click(sqlSummary);
    expect(sqlDetails).toHaveAttribute("open");
    expect(screen.getByRole("button", { name: "Copiar SQL" })).toBeInTheDocument();
    expect(within(sqlDetails as HTMLElement).getByText("SELECT 1")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Copiar SQL" }));
    expect(await screen.findByText("SQL copiada")).toBeInTheDocument();
    expect(writeText).toHaveBeenCalledWith("SELECT 1");
  });

  it("limpa a conversa somente pelo menu de ações", () => {
    renderChat();
    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "q" } });
    expect(screen.queryByRole("menuitem", { name: "Limpar conversa" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Mais ações da conversa" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Limpar conversa" }));
    expect(screen.getByLabelText("Pergunta independente")).toHaveValue("");
  });

  it("mantém tabela e aviso do limite de 200 linhas", async () => {
    completedResponse({ ...succeeded, truncated: true, rowCount: 240, displayedRowCount: 200 });
    const first = renderChat();
    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "q" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    expect(await screen.findByRole("table", { name: "Resultado da consulta" })).toBeInTheDocument();
    expect(screen.getByText("Resultado truncado em 200 linhas.")).toBeInTheDocument();
    first.unmount();

    completedResponse({ ...succeeded, rows: [], rowCount: 0, displayedRowCount: 0 });
    renderChat();
    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "sem linhas" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    expect(await screen.findByText("Resultado vazio.")).toBeInTheDocument();
    expect(screen.queryByRole("table", { name: "Resultado da consulta" })).not.toBeInTheDocument();
  });

  it("mantém perguntas sucessivas independentes e envia somente a pergunta atual", async () => {
    let submissions = 0;
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url.endsWith("/chat/jobs") && init?.method === "POST") {
        submissions += 1;
        const current = { ...accepted, job_id: `job-${submissions}` };
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ job_id: current.job_id, snapshot: current }) });
      }
      const jobId = url.split("/").pop() as string;
      const value = jobId === "job-1" ? 1 : 2;
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ job: { ...succeeded, job_id: jobId, rows: [[value]] } })
      });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    renderChat();

    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "primeira pergunta" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    expect(await screen.findByRole("cell", { name: "1" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "segunda pergunta" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    expect(await screen.findByRole("cell", { name: "2" })).toBeInTheDocument();
    expect(screen.getByText("primeira pergunta")).toBeInTheDocument();
    expect(screen.getByText("segunda pergunta")).toBeInTheDocument();

    const bodies = fetchMock.mock.calls
      .filter(([url, init]) => String(url).endsWith("/chat/jobs") && init?.method === "POST")
      .map(([, init]) => JSON.parse(String(init?.body)));
    expect(bodies).toEqual([
      { question: "primeira pergunta", ...configuration },
      { question: "segunda pergunta", ...configuration }
    ]);
    expect(bodies.every((body) => !("history" in body) && !("sql" in body))).toBe(true);
  });

  it.each([
    ["MODEL_LOAD_ERROR", "Não há espaço suficiente em disco para baixar ou carregar este modelo. Libere espaço no servidor e tente novamente."],
    ["MODEL_LOAD_ERROR", "Não há memória suficiente na GPU para carregar este modelo."],
    ["QUERY_TIMEOUT", "A consulta excedeu o tempo limite."],
    ["DATABASE_CONNECTION_ERROR", "Não foi possível conectar ao banco de dados."],
    ["INTERNAL_ERROR", "Ocorreu um erro interno. Nenhum detalhe interno foi exposto."]
  ])("apresenta erro terminal estruturado %s sem retomar polling", async (code, message) => {
    const failed = { ...accepted, state: "failed" as const, error: { code, message, retryable: code !== "INTERNAL_ERROR" }, internal_detail: "token=secret /srv/private", traceback: "secret trace" };
    completedResponse(failed);
    renderChat();
    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "q" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    expect(await screen.findByText(message)).toBeInTheDocument();
    expect(screen.getByText(code, { selector: "code" })).toBeInTheDocument();
    vi.useFakeTimers();
    await act(async () => {
      vi.advanceTimersByTime(650);
      await Promise.resolve();
    });
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    expect(document.body.textContent).not.toMatch(/internal_detail|traceback|token=secret|\/srv\/private/);
  });

  it("RESOURCE_BUSY preserva a pergunta e permite apenas nova submissão manual", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ error: { code: "RESOURCE_BUSY", message: "Outra operação pesada está em andamento.", retryable: true } })
    });
    renderChat();
    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "pergunta preservada" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    expect(await screen.findByText("RESOURCE_BUSY", { selector: "code" })).toBeInTheDocument();
    expect(screen.getByLabelText("Pergunta independente")).toHaveValue("pergunta preservada");
    fireEvent.click(screen.getByRole("button", { name: "Revisar e tentar manualmente" }));
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("retryable preenche novamente o editor, mas não reenvia automaticamente", async () => {
    completedResponse({ ...succeeded, state: "failed", error: { code: "X", message: "falhou", retryable: true } });
    renderChat();
    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "q" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    const retry = await screen.findByRole("button", { name: "Tentar novamente" });
    fireEvent.click(retry);
    expect(screen.getByLabelText("Pergunta independente")).toHaveValue("q");
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
  });

  it("retryable=false oferece edição, não retry nem nova chamada", async () => {
    completedResponse({ ...accepted, state: "failed", error: { code: "SQL_SYNTAX_ERROR", message: "A consulta gerada possui erro de sintaxe.", retryable: false } });
    renderChat();
    fireEvent.change(screen.getByLabelText("Pergunta independente"), { target: { value: "q" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pergunta" }));
    expect(await screen.findByText("SQL_SYNTAX_ERROR", { selector: "code" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Tentar novamente" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Editar pergunta" }));
    expect(screen.getByLabelText("Pergunta independente")).toHaveValue("q");
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
  });
});
