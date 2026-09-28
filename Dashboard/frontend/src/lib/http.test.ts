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

  it("um 500 sem corpo JSON vira \"O servidor encontrou um erro.\"", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaTexto("Internal Server Error", 500, "text/html")));
    await expect(request("/api/x")).rejects.toMatchObject(new ApiError(500, "O servidor encontrou um erro."));
  });

  it("outros status sem detail utilizável viram \"Erro {status} ao acessar a API.\"", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaTexto("Bad Request", 400, "text/plain")));
    await expect(request("/api/x")).rejects.toMatchObject(new ApiError(400, "Erro 400 ao acessar a API."));
  });

  it("401 e 403 (mesmo com detail genérico) viram aviso de sessão expirada", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaJson({ detail: "Unauthorized" }, 401)));
    await expect(request("/api/x")).rejects.toMatchObject(
      new ApiError(401, "Sua sessão pode ter expirado. Recarregue a página."),
    );

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaTexto("Forbidden", 403, "text/plain")));
    await expect(request("/api/x")).rejects.toMatchObject(
      new ApiError(403, "Sua sessão pode ter expirado. Recarregue a página."),
    );
  });

  it("502/503/504 com detail genérico (gateway/serviço indisponível) usam a mensagem por status (5xx)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaJson({ detail: "Internal Server Error" }, 502)));
    await expect(request("/api/x")).rejects.toMatchObject(new ApiError(502, "O servidor não respondeu."));

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaJson({ detail: "Service Unavailable" }, 503)));
    await expect(request("/api/x")).rejects.toMatchObject(new ApiError(503, "O servidor não respondeu."));

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaJson({ detail: "Gateway Timeout" }, 504)));
    await expect(request("/api/x")).rejects.toMatchObject(new ApiError(504, "O servidor não respondeu."));
  });

  it("429 e 422 com detail genérico também não vazam o texto cru do framework", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaJson({ detail: "Too Many Requests" }, 429)));
    await expect(request("/api/x")).rejects.toMatchObject(new ApiError(429, "Erro 429 ao acessar a API."));

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respostaJson({ detail: "Unprocessable Entity" }, 422)));
    await expect(request("/api/x")).rejects.toMatchObject(new ApiError(422, "Erro 422 ao acessar a API."));
  });
});
