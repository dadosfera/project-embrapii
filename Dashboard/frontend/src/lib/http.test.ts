import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, request } from "./http";

function respostaJson(body: unknown, status: number) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function respostaTexto(texto: string, status: number, contentType = "text/plain") {
  return new Response(texto, { status, headers: { "content-type": contentType } });
}

describe("request: mensagem de erro (ErrorState mostra error.message)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("usa o detail da nossa API quando ele é uma mensagem de negócio", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaJson({ detail: "Medicamento não encontrado" }, 404)));
    await expect(request("/api/x")).rejects.toMatchObject(
      new ApiError(404, "Medicamento não encontrado"),
    );
  });

  it("junta os `msg` de uma lista de erro de validação (Pydantic)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        respostaJson({ detail: [{ msg: "campo obrigatório" }, { msg: "valor inválido" }] }, 422),
      ),
    );
    await expect(request("/api/x")).rejects.toMatchObject(
      new ApiError(422, "campo obrigatório; valor inválido"),
    );
  });

  it("um 404 JSON genérico (\"Not Found\", de um servidor que não é a nossa API) vira mensagem por status, não o texto cru", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaJson({ detail: "Not Found" }, 404)));
    await expect(request("/api/x")).rejects.toMatchObject(new ApiError(404, "Recurso não encontrado."));
  });

  it("um 500 sem corpo JSON vira \"O servidor não respondeu.\"", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaTexto("Internal Server Error", 500, "text/html")));
    await expect(request("/api/x")).rejects.toMatchObject(new ApiError(500, "O servidor não respondeu."));
  });

  it("outros status sem detail utilizável viram \"Erro {status} ao acessar a API.\"", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaTexto("Forbidden", 403, "text/plain")));
    await expect(request("/api/x")).rejects.toMatchObject(new ApiError(403, "Erro 403 ao acessar a API."));
  });

  it("502 com detail genérico (\"Bad Gateway\"-like) também usa a mensagem por status (5xx)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaJson({ detail: "Internal Server Error" }, 502)));
    await expect(request("/api/x")).rejects.toMatchObject(new ApiError(502, "O servidor não respondeu."));
  });
});
