import { useState } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { buscarFornecedoresAutocomplete, type FornecedorAutocomplete } from "../lib/api";
import { FornecedorPicker } from "./FornecedorPicker";

/** Wrapper controlado: repassa a seleção de volta ao `value`, como as páginas reais fazem. */
function PickerControlado({
  onSelect,
}: {
  onSelect?: (f: FornecedorAutocomplete | null) => void;
}) {
  const [valor, setValor] = useState<FornecedorAutocomplete | null>(null);
  return (
    <FornecedorPicker
      id="fornecedor-teste"
      label="Fornecedor"
      value={valor}
      onSelect={(f) => {
        setValor(f);
        onSelect?.(f);
      }}
    />
  );
}

vi.mock("../lib/api");

const DIMEVA: FornecedorAutocomplete = {
  fornecedor_id: 1,
  nome: "DIMEVA DISTRIBUIDORA DE MEDICAMENTOS LTDA",
  cnpj: "12345678000199",
  valor_total: 1_200_000,
  numero_compras: 42,
};

const UNICA: FornecedorAutocomplete = {
  fornecedor_id: 2,
  nome: "UNICA COMERCIO HOSPITALAR",
  cnpj: null,
  valor_total: 50_000,
  numero_compras: 3,
};

function renderPicker(value: FornecedorAutocomplete | null = null) {
  const onSelect = vi.fn();
  render(
    <FornecedorPicker id="fornecedor-teste" label="Fornecedor" value={value} onSelect={onSelect} />,
  );
  return onSelect;
}

describe("FornecedorPicker", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("não busca com menos de 2 caracteres", async () => {
    renderPicker();
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "d" } });
    vi.advanceTimersByTime(300);
    expect(buscarFornecedoresAutocomplete).not.toHaveBeenCalled();
  });

  it("busca após 250ms de debounce e mostra CNPJ formatado + valor compacto", async () => {
    vi.mocked(buscarFornecedoresAutocomplete).mockResolvedValue([DIMEVA]);
    renderPicker();

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "dimeva" } });
    expect(buscarFornecedoresAutocomplete).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(250);

    await waitFor(() => expect(buscarFornecedoresAutocomplete).toHaveBeenCalledWith("dimeva"));
    expect(await screen.findByText("12.345.678/0001-99")).toBeInTheDocument();
    expect(screen.getByText(/mil|mi/)).toBeInTheDocument();
  });

  it("selecionar uma opção chama onSelect e fecha a lista", async () => {
    vi.mocked(buscarFornecedoresAutocomplete).mockResolvedValue([DIMEVA]);
    const onSelectSpy = vi.fn();
    render(<PickerControlado onSelect={onSelectSpy} />);

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "dimeva" } });
    await vi.advanceTimersByTimeAsync(250);

    const opcao = await screen.findByText(DIMEVA.nome);
    fireEvent.click(opcao);

    expect(onSelectSpy).toHaveBeenCalledWith(DIMEVA);
    expect(screen.getByRole("combobox")).toHaveValue(DIMEVA.nome);
  });

  it("Escape fecha a lista e restaura o texto do valor selecionado", async () => {
    vi.mocked(buscarFornecedoresAutocomplete).mockResolvedValue([UNICA]);
    renderPicker(DIMEVA);

    const campo = screen.getByRole("combobox");
    fireEvent.change(campo, { target: { value: "unica" } });
    await vi.advanceTimersByTimeAsync(250);
    await screen.findByText(UNICA.nome);

    fireEvent.keyDown(campo, { key: "Escape" });
    expect(campo).toHaveValue(DIMEVA.nome);
  });

  it("botão Limpar chama onSelect(null) e esvazia o texto", () => {
    const onSelectSpy = vi.fn();
    render(
      <FornecedorPicker id="fornecedor-teste" label="Fornecedor" value={DIMEVA} onSelect={onSelectSpy} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Limpar fornecedor" }));
    expect(onSelectSpy).toHaveBeenCalledWith(null);
    expect(screen.getByRole("combobox")).toHaveValue("");
  });

  it("CNPJ sem 14 dígitos não quebra: mostra o valor original", async () => {
    vi.mocked(buscarFornecedoresAutocomplete).mockResolvedValue([{ ...DIMEVA, cnpj: "123" }]);
    renderPicker();

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "dimeva" } });
    await vi.advanceTimersByTimeAsync(250);

    expect(await screen.findByText("123")).toBeInTheDocument();
  });

  it("fornecedor sem CNPJ mostra traço", async () => {
    vi.mocked(buscarFornecedoresAutocomplete).mockResolvedValue([UNICA]);
    renderPicker();

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "unica" } });
    await vi.advanceTimersByTimeAsync(250);

    expect(await screen.findByText("sem dado")).toBeInTheDocument();
  });

  it("clique fora fecha a lista", async () => {
    vi.mocked(buscarFornecedoresAutocomplete).mockResolvedValue([DIMEVA]);
    render(
      <div>
        <FornecedorPicker id="fornecedor-teste" label="Fornecedor" value={null} onSelect={vi.fn()} />
        <button type="button">fora</button>
      </div>,
    );

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "dimeva" } });
    await vi.advanceTimersByTimeAsync(250);
    await screen.findByText(DIMEVA.nome);

    fireEvent.mouseDown(screen.getByRole("button", { name: "fora" }));
    expect(screen.queryByText(DIMEVA.nome)).not.toBeInTheDocument();
  });
});
