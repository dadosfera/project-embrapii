import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAutocomplete } from "./useAutocomplete";

function setup(buscar = vi.fn(async (termo: string) => [termo])) {
  const hook = renderHook(
    (props: { valorTexto: string }) =>
      useAutocomplete<string[]>({
        valorTexto: props.valorTexto,
        buscar,
        vazio: [],
        mensagemErro: "falhou",
      }),
    { initialProps: { valorTexto: "" } },
  );
  return { hook, buscar };
}

describe("useAutocomplete", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("não busca abaixo do mínimo de caracteres", async () => {
    const { hook, buscar } = setup();
    act(() => hook.result.current.aoDigitar("a"));
    await vi.advanceTimersByTimeAsync(300);
    expect(buscar).not.toHaveBeenCalled();
    expect(hook.result.current.itens).toEqual([]);
  });

  it("busca após o debounce quando editando e acima do mínimo", async () => {
    const { hook, buscar } = setup();
    act(() => hook.result.current.aoDigitar("ab"));
    expect(buscar).not.toHaveBeenCalled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(250);
    });

    expect(buscar).toHaveBeenCalledWith("ab");
    await waitFor(() => expect(hook.result.current.itens).toEqual(["ab"]));
  });

  it("descarta resposta desatualizada (stale request)", async () => {
    let resolvePrimeira: (v: string[]) => void = () => {};
    const buscar = vi
      .fn()
      .mockImplementationOnce(() => new Promise<string[]>((r) => (resolvePrimeira = r)))
      .mockImplementationOnce(async () => ["segunda"]);
    const { hook } = setup(buscar);

    act(() => hook.result.current.aoDigitar("primeira"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(250);
    });

    act(() => hook.result.current.aoDigitar("segunda"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(250);
    });

    await waitFor(() => expect(hook.result.current.itens).toEqual(["segunda"]));

    // A primeira promise (desatualizada) resolve depois — não deve sobrescrever o resultado atual.
    await act(async () => {
      resolvePrimeira(["primeira"]);
      await Promise.resolve();
    });
    expect(hook.result.current.itens).toEqual(["segunda"]);
  });

  it("aoEscapar fecha e restaura o texto do valor selecionado", async () => {
    const buscar = vi.fn(async () => []);
    const hook = renderHook(() =>
      useAutocomplete<string[]>({ valorTexto: "Selecionado", buscar, vazio: [], mensagemErro: "x" }),
    );

    act(() => hook.result.current.aoDigitar("outra coisa"));
    expect(hook.result.current.texto).toBe("outra coisa");
    expect(hook.result.current.editando).toBe(true);

    act(() => hook.result.current.aoEscapar());
    expect(hook.result.current.editando).toBe(false);
    expect(hook.result.current.aberto).toBe(false);
    expect(hook.result.current.texto).toBe("Selecionado");
  });

  it("erro (rejeição sem Error) usa a mensagemErro informada", async () => {
    const buscar = vi.fn().mockRejectedValue("boom");
    const { hook } = setup(buscar);

    act(() => hook.result.current.aoDigitar("ab"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(250);
    });

    await waitFor(() => expect(hook.result.current.erro).toBe("falhou"));
  });
});
