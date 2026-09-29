import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Leitos } from "./Leitos";

import {
  buscarEvolucaoLeitos,
  buscarOpcoesLeitos,
  buscarPainelLeitos,
} from "../lib/api";

vi.mock("../lib/api");

const KPIS_PADRAO = {
  leitos_gerais: 500_000,
  leitos_sus: 300_000,
  leitos_uti: 40_000,
  leitos_uti_sus: 25_000,
  instituicoes_com_registro: 6_000,
  competencia_minima: "2024-01-01",
  competencia_maxima: "2026-01-01",
};

const POR_UF_PADRAO = [
  { uf: "SP", leitos_gerais: 1_000, leitos_sus: 600, leitos_uti: 100, leitos_uti_sus: 50, instituicoes: 100 },
  { uf: "RJ", leitos_gerais: 500, leitos_sus: 200, leitos_uti: 300, leitos_uti_sus: 250, instituicoes: 50 },
];

function painelPadrao() {
  return {
    kpis: KPIS_PADRAO,
    por_uf: POR_UF_PADRAO,
    tipos_uti: [],
    evolucao: [{ competencia: "2025-01-01", leitos_gerais: 100, leitos_sus: 50, leitos_uti: 10, leitos_uti_sus: 5, instituicoes: 20 }],
    instituicoes: [],
  };
}

function stubApi() {
  vi.mocked(buscarOpcoesLeitos).mockResolvedValue({
    data_minima: "2010-01-01",
    data_maxima: "2026-01-01",
    ufs: ["SP", "RJ"],
  });
  vi.mocked(buscarPainelLeitos).mockResolvedValue(painelPadrao());
  vi.mocked(buscarEvolucaoLeitos).mockResolvedValue([
    { competencia: "2025-06-01", leitos_gerais: 200, leitos_sus: 100, leitos_uti: 20, leitos_uti_sus: 10, instituicoes: 30 },
  ]);
}

function renderLeitos() {
  return render(
    <MemoryRouter>
      <TooltipProvider>
        <Leitos />
      </TooltipProvider>
    </MemoryRouter>,
  );
}

describe("Leitos", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  });

  it("abre carregada sem nenhum clique, com a competência mais recente e todas as UFs", async () => {
    stubApi();
    renderLeitos();

    await waitFor(() => {
      expect(buscarPainelLeitos).toHaveBeenCalledWith(
        { modo: "ultima_competencia", uf: "" },
        "2024-01-01",
        "2026-01-01",
      );
    });
  });

  it("mostra 'Leitos gerais' e 'Participação do SUS' na primeira linha de KPIs", async () => {
    stubApi();
    renderLeitos();

    expect((await screen.findAllByText("Leitos gerais")).length).toBeGreaterThan(0);
    expect(await screen.findByText("Participação do SUS")).toBeInTheDocument();
  });

  it("não sobra o texto 'Aplicar filtros'", async () => {
    stubApi();
    renderLeitos();

    await waitFor(() => expect(buscarPainelLeitos).toHaveBeenCalled());

    expect(screen.queryByText("Aplicar filtros")).not.toBeInTheDocument();
  });

  it("aplicar o período da evolução chama buscarEvolucaoLeitos e não recarrega o painel inteiro", async () => {
    stubApi();
    renderLeitos();

    await screen.findByRole("tab", { name: "Evolução histórica" });
    expect(buscarPainelLeitos).toHaveBeenCalledTimes(1);

    fireEvent.mouseDown(screen.getByRole("tab", { name: "Evolução histórica" }));

    const inicio = await screen.findByLabelText("Início da evolução");
    fireEvent.change(inicio, { target: { value: "2025-01-01" } });

    fireEvent.click(screen.getByRole("button", { name: "Aplicar período da evolução" }));

    await waitFor(() => {
      expect(buscarEvolucaoLeitos).toHaveBeenCalledWith("", "2025-01-01", "2026-01-01");
    });

    expect(buscarPainelLeitos).toHaveBeenCalledTimes(1);
  });

  it("o Alternador 'UTI' troca as barras da aba Distribuição por UF", async () => {
    stubApi();
    renderLeitos();

    await waitFor(() => expect(buscarPainelLeitos).toHaveBeenCalled());

    const grupo = await screen.findByRole("radiogroup", { name: "Tipo de leito" });
    expect(within(grupo).getByRole("radio", { name: "Gerais" })).toHaveAttribute("aria-checked", "true");

    fireEvent.click(within(grupo).getByRole("radio", { name: "UTI" }));

    expect(within(grupo).getByRole("radio", { name: "UTI" })).toHaveAttribute("aria-checked", "true");
  });
});
