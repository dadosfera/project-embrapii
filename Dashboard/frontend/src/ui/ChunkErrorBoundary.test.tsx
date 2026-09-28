import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ChunkCarregado, ChunkErrorBoundary, FLAG_RECARGA, ehErroDeChunk } from "./ChunkErrorBoundary";

function Explode({ mensagem }: { mensagem: string }): never {
  throw new TypeError(mensagem);
}

const ERRO_CHUNK = "Failed to fetch dynamically imported module: http://x/assets/Compras-abc.js";

function montar(mensagem: string, recarregar: () => void, autoReload = true) {
  return render(
    <ChunkErrorBoundary
      autoReload={autoReload}
      recarregar={recarregar}
      fallback={(r) => (
        <div>
          <p>Não foi possível carregar a página</p>
          <button onClick={r}>Recarregar</button>
        </div>
      )}
    >
      <Explode mensagem={mensagem} />
    </ChunkErrorBoundary>,
  );
}

describe("ChunkErrorBoundary", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.spyOn(console, "error").mockImplementation(() => {});
    vi.spyOn(console, "warn").mockImplementation(() => {});
  });
  afterEach(() => vi.restoreAllMocks());

  it("reconhece erros de import dinâmico", () => {
    expect(ehErroDeChunk(new TypeError(ERRO_CHUNK))).toBe(true);
    expect(ehErroDeChunk(new TypeError("Importing a module script failed."))).toBe(true);
    expect(ehErroDeChunk(new Error("x is undefined"))).toBe(false);
  });

  it("na primeira falha de chunk recarrega uma vez e grava a flag", () => {
    const recarregar = vi.fn();
    montar(ERRO_CHUNK, recarregar);
    expect(recarregar).toHaveBeenCalledTimes(1);
    expect(sessionStorage.getItem(FLAG_RECARGA)).toBe("1");
    expect(screen.queryByText("Não foi possível carregar a página")).not.toBeInTheDocument();
  });

  it("com a flag já gravada não recarrega sozinho e mostra o fallback com Recarregar", () => {
    sessionStorage.setItem(FLAG_RECARGA, "1");
    const recarregar = vi.fn();
    montar(ERRO_CHUNK, recarregar);
    expect(recarregar).not.toHaveBeenCalled();
    expect(screen.getByText("Não foi possível carregar a página")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Recarregar" }));
    expect(recarregar).toHaveBeenCalledTimes(1);
  });

  it("erro que não é de chunk mostra o fallback sem recarregar", () => {
    const recarregar = vi.fn();
    montar("x is undefined", recarregar);
    expect(recarregar).not.toHaveBeenCalled();
    expect(screen.getByText("Não foi possível carregar a página")).toBeInTheDocument();
  });

  it("sem autoReload mostra o fallback direto", () => {
    const recarregar = vi.fn();
    montar(ERRO_CHUNK, recarregar, false);
    expect(recarregar).not.toHaveBeenCalled();
    expect(screen.getByText("Não foi possível carregar a página")).toBeInTheDocument();
  });

  it("ChunkCarregado limpa a flag", () => {
    sessionStorage.setItem(FLAG_RECARGA, "1");
    render(<ChunkCarregado />);
    expect(sessionStorage.getItem(FLAG_RECARGA)).toBeNull();
  });

  it("sai do erro quando a resetKey muda", () => {
    sessionStorage.setItem(FLAG_RECARGA, "1");
    const fb = () => <p>falhou</p>;
    const { rerender } = render(
      <ChunkErrorBoundary resetKey="/a" fallback={fb}>
        <Explode mensagem="x" />
      </ChunkErrorBoundary>,
    );
    expect(screen.getByText("falhou")).toBeInTheDocument();
    rerender(
      <ChunkErrorBoundary resetKey="/b" fallback={fb}>
        <p>ok</p>
      </ChunkErrorBoundary>,
    );
    expect(screen.getByText("ok")).toBeInTheDocument();
  });
});
