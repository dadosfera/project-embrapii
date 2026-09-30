import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Compras } from "./Compras";

import {
  buscarComprasPorAno,
  buscarComprasPorModalidade,
  buscarComprasPorTipo,
  buscarComprasRecentes,
  buscarIntervaloCompras,
  buscarKpisCompras,
  buscarRankingFabricantes,
  buscarRankingFornecedores,
} from "../lib/api";

vi.mock("../lib/api");

const KPIS_PADRAO = {
  valor_total: 50_900_000_000,
  numero_compras: 12_000,
  quantidade_itens: 100_000,
  numero_fornecedores: 500,
  numero_fabricantes: 200,
  numero_mantenedoras: 50,
};

const POR_ANO_PADRAO = [
  { ano: 2020, valor_total: 5_000_000_000, numero_compras: 1_000, quantidade_itens: 10_000, maior_registro: 100_000_000, maior_registro_fornecedor: "Fornecedor A" },
  { ano: 2021, valor_total: 6_000_000_000, numero_compras: 1_200, quantidade_itens: 11_000, maior_registro: 120_000_000, maior_registro_fornecedor: "Fornecedor B" },
];

const POR_ANO_OUTLIER = [
  ...POR_ANO_PADRAO,
  {
    ano: 2025,
    valor_total: 23_200_000_000,
    numero_compras: 2_474,
    quantidade_itens: 20_000,
    maior_registro: 22_700_000_000,
    maior_registro_fornecedor: "MEDICAL MERCANTIL",
  },
];

function stubApi(porAno: typeof POR_ANO_PADRAO) {
  vi.mocked(buscarIntervaloCompras).mockResolvedValue({
    data_minima: "2020-01-01",
    data_maxima: "2025-12-31",
    ano_minimo: 2020,
    ano_maximo: 2025,
  });
  vi.mocked(buscarKpisCompras).mockResolvedValue(KPIS_PADRAO);
  vi.mocked(buscarComprasPorAno).mockResolvedValue(porAno);
  vi.mocked(buscarRankingFornecedores).mockResolvedValue([]);
  vi.mocked(buscarRankingFabricantes).mockResolvedValue([]);
  vi.mocked(buscarComprasPorModalidade).mockResolvedValue([]);
  vi.mocked(buscarComprasPorTipo).mockResolvedValue([]);
  vi.mocked(buscarComprasRecentes).mockResolvedValue([]);
}

function renderCompras() {
  return render(
    <MemoryRouter>
      <TooltipProvider>
        <Compras />
      </TooltipProvider>
    </MemoryRouter>,
  );
}

describe("Compras", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  });

  it("abre carregada em 2020-2025 sem nenhum clique", async () => {
    stubApi(POR_ANO_PADRAO);
    renderCompras();

    await waitFor(() => {
      expect(buscarKpisCompras).toHaveBeenCalledWith(
        expect.objectContaining({ data_inicio: "2020-01-01", data_fim: "2025-12-31" }),
      );
    });
  });

  it("tem o botão Aplicar", async () => {
    stubApi(POR_ANO_PADRAO);
    renderCompras();

    expect(await screen.findByRole("button", { name: "Aplicar" })).toBeInTheDocument();
  });

  it("mostra a nota do outlier quando um ano tem um único registro dominante", async () => {
    stubApi(POR_ANO_OUTLIER);
    renderCompras();

    await waitFor(() => expect(buscarComprasPorAno).toHaveBeenCalled());

    expect((await screen.findAllByText(/1 registro/)).length).toBeGreaterThan(0);
  });

  it("sem anos na base (/intervalo devolve null), mostra EmptyState em vez de skeleton eterno", async () => {
    vi.mocked(buscarIntervaloCompras).mockResolvedValue({
      data_minima: null,
      data_maxima: null,
      ano_minimo: null,
      ano_maximo: null,
    });

    renderCompras();

    expect(await screen.findByText("Sem compras na base")).toBeInTheDocument();
    expect(buscarKpisCompras).not.toHaveBeenCalled();
  });
});
