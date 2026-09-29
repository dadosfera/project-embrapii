import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { buscarIntervaloCompras } from "../lib/api";
import {
  buscarMapaFornecedoresPorUf,
  buscarRankingFornecedores,
} from "../lib/fornecedoresApi";
import { Fornecedores } from "./Fornecedores";

vi.mock("../lib/fornecedoresApi");
vi.mock("../lib/api");

const GEOJSON = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: { sigla: "MG", nome: "Minas Gerais" },
      geometry: { type: "Polygon", coordinates: [[[-46, -18], [-45, -18], [-45, -19], [-46, -19], [-46, -18]]] },
    },
    {
      type: "Feature",
      properties: { sigla: "SP", nome: "São Paulo" },
      geometry: { type: "Polygon", coordinates: [[[-48, -22], [-47, -22], [-47, -23], [-48, -23], [-48, -22]]] },
    },
  ],
};

const MAPA_PADRAO = [
  {
    uf: "MG",
    quantidade_nacional: 80,
    quantidade_estrangeiro: 20,
    quantidade_grupo_estrangeiro: 0,
    quantidade_desconhecida: 0,
    valor_nacional: 800,
    valor_estrangeiro: 200,
    valor_grupo_estrangeiro: 0,
    valor_desconhecido: 0,
    predominancia: "NACIONAL" as const,
  },
  {
    uf: "SP",
    quantidade_nacional: 50,
    quantidade_estrangeiro: 50,
    quantidade_grupo_estrangeiro: 0,
    quantidade_desconhecida: 0,
    valor_nacional: 500,
    valor_estrangeiro: 500,
    valor_grupo_estrangeiro: 0,
    valor_desconhecido: 0,
    predominancia: "EMPATE" as const,
  },
];

function stubApi() {
  vi.mocked(buscarIntervaloCompras).mockResolvedValue({
    data_minima: "2020-01-01",
    data_maxima: "2025-12-31",
    ano_minimo: 2020,
    ano_maximo: 2025,
  });
  vi.mocked(buscarMapaFornecedoresPorUf).mockResolvedValue(MAPA_PADRAO);
  vi.mocked(buscarRankingFornecedores).mockResolvedValue([]);
}

describe("Fornecedores", () => {
  beforeEach(() => {
    vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(GEOJSON),
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("abre em 2020-2025 e busca o ranking sem UF", async () => {
    stubApi();
    render(<Fornecedores />);

    await waitFor(() => {
      expect(buscarRankingFornecedores).toHaveBeenCalledWith(
        "2020-01-01",
        "2025-12-31",
        undefined,
        100,
      );
    });
  });

  it("clicar na UF do mapa filtra o ranking e mostra o rótulo; Limpar UF volta ao total", async () => {
    stubApi();
    render(<Fornecedores />);

    const mg = await screen.findByRole("button", { name: /Minas Gerais \(MG\)/ });
    fireEvent.click(mg);

    await waitFor(() => {
      expect(buscarRankingFornecedores).toHaveBeenCalledWith(
        "2020-01-01",
        "2025-12-31",
        "MG",
        100,
      );
    });

    expect(await screen.findByText(/Tabela filtrada por/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Limpar UF" }));

    await waitFor(() => {
      expect(buscarRankingFornecedores).toHaveBeenLastCalledWith(
        "2020-01-01",
        "2025-12-31",
        undefined,
        100,
      );
    });

    expect(
      screen.getByText("Tabela: todas as UFs. Clique numa UF do mapa para filtrar."),
    ).toBeInTheDocument();
  });

  it("não tem mais o select de UF da tabela", async () => {
    stubApi();
    render(<Fornecedores />);

    await screen.findByRole("button", { name: /Minas Gerais \(MG\)/ });
    expect(screen.queryByLabelText("UF (tabela)")).not.toBeInTheDocument();
  });

  it("o mapa mostra um único '%' (sem duplicar), na legenda e no rótulo da UF", async () => {
    stubApi();
    render(<Fornecedores />);

    // MG: 20/100 = 20,0% — o rótulo tem "20,0 %" (um símbolo), nunca "20,0% %".
    const mg = await screen.findByRole("button", { name: /Minas Gerais \(MG\)/ });
    expect(mg.getAttribute("aria-label")).toMatch(/20,0 %$/);
    expect(mg.getAttribute("aria-label")).not.toMatch(/%\s*%/);

    expect(screen.getByText("Legenda (%)")).toBeInTheDocument();
  });
});
