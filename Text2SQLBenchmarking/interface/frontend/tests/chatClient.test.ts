import { describe, expect, it, vi } from "vitest";
import { apiClient, PublicApiError } from "../src/api/client";

describe("cliente de Chat", () => {
  it("envia somente pergunta e configuração", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({ job_id: "1" }) });
    await apiClient.createChat("pergunta", { database: "db", library: "lib", model_id: "model", context: "ctx" });
    expect(JSON.parse((globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body)).toEqual({ question: "pergunta", database: "db", library: "lib", model_id: "model", context: "ctx" });
  });
  it("rejeita JSON inválido no POST", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.reject(new Error("bad")) });
    await expect(apiClient.createChat("q", { database: "db", library: "lib", model_id: "m", context: "c" })).rejects.toBeInstanceOf(PublicApiError);
  });
});
