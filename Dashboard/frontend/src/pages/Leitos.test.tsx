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

// Radix Select em jsdom precisa desses stubs (não implementados no jsdom): o Content usa
// ResizeObserver para medir o popper, e o Item usa hasPointerCapture ao lidar com seleção por
// ponteiro.
function comStubsDoRadixSelect() {
  Object.assign(HTMLElement.prototype, {
    hasPointerCapture: () => false,
    scrollIntoView: () => {},
  });
}

/** Promise controlável de fora, para simular uma resposta de evolução que demora a resolver. */
function deferido<T>() {
  let resolve!: (v: T) => void;
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
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

  it("quando a carga automática inicial falha, 'Tentar de novo' chama buscarPainelLeitos de novo", async () => {
    vi.mocked(buscarOpcoesLeitos).mockResolvedValue({
      data_minima: "2010-01-01",
      data_maxima: "2026-01-01",
      ufs: ["SP", "RJ"],
    });
    vi.mocked(buscarPainelLeitos).mockRejectedValueOnce(new Error("falhou"));
    renderLeitos();

    const retry = await screen.findByRole("button", { name: "Tentar de novo" });
    expect(buscarPainelLeitos).toHaveBeenCalledTimes(1);

    vi.mocked(buscarPainelLeitos).mockResolvedValue(painelPadrao());
    fireEvent.click(retry);

    // Sem filtrosConfirmados (a carga inicial nunca chegou a aplicar), aplicarFiltros cai
    // para as datas da evolução (dataInicioEvolucao/dataFimEvolucao), que a carga de opções
    // já preencheu com o intervalo padrão.
    await waitFor(() => {
      expect(buscarPainelLeitos).toHaveBeenCalledTimes(2);
    });
    expect(buscarPainelLeitos).toHaveBeenLastCalledWith(
      { modo: "ultima_competencia", uf: "" },
      "2024-01-01",
      "2026-01-01",
    );
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

  it("falha na evolução isolada mostra um ErrorState próprio na aba, sem acionar o da página inteira", async () => {
    stubApi();
    renderLeitos();

    await screen.findByRole("tab", { name: "Evolução histórica" });
    fireEvent.mouseDown(screen.getByRole("tab", { name: "Evolução histórica" }));

    vi.mocked(buscarEvolucaoLeitos).mockRejectedValueOnce(new Error("evolução falhou"));

    const inicio = await screen.findByLabelText("Início da evolução");
    fireEvent.change(inicio, { target: { value: "2025-01-01" } });
    fireEvent.click(screen.getByRole("button", { name: "Aplicar período da evolução" }));

    await waitFor(() => expect(buscarEvolucaoLeitos).toHaveBeenCalledTimes(1));

    // ErrorState próprio dentro da aba: a página continua mostrando o painel (KPIs) normal.
    expect(await screen.findByText("Não foi possível carregar")).toBeInTheDocument();
    expect((await screen.findAllByText("Leitos gerais")).length).toBeGreaterThan(0);

    vi.mocked(buscarEvolucaoLeitos).mockResolvedValue([
      { competencia: "2025-06-01", leitos_gerais: 200, leitos_sus: 100, leitos_uti: 20, leitos_uti_sus: 10, instituicoes: 30 },
    ]);
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));

    await waitFor(() => expect(buscarEvolucaoLeitos).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("Não foi possível carregar")).not.toBeInTheDocument();
  });

  it("uma evolução isolada em voo não sobrescreve o painel mais novo (outra UF)", async () => {
    vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
    comStubsDoRadixSelect();

    vi.mocked(buscarOpcoesLeitos).mockResolvedValue({
      data_minima: "2010-01-01",
      data_maxima: "2026-01-01",
      ufs: ["SP", "RJ"],
    });

    // O painel para "" (Todas) e o painel para "RJ" trazem evoluções bem distintas, para
    // conseguirmos identificar qual delas sobrou na tela no final do teste.
    vi.mocked(buscarPainelLeitos).mockImplementation(async (filtros) => {
      if (filtros.uf === "RJ") {
        return {
          ...painelPadrao(),
          evolucao: [
            { competencia: "2021-06-01", leitos_gerais: 777_777, leitos_sus: 1, leitos_uti: 1, leitos_uti_sus: 1, instituicoes: 1 },
          ],
        };
      }
      return painelPadrao();
    });

    const evolucaoAntiga = deferido<Awaited<ReturnType<typeof buscarEvolucaoLeitos>>>();
    vi.mocked(buscarEvolucaoLeitos).mockReturnValue(evolucaoAntiga.promise);

    renderLeitos();

    // 1) Carga inicial (uf ""), depois abre a aba Evolução e dispara um pedido de evolução
    // que fica pendente (a resposta só chega mais tarde, por mockReturnValue acima).
    await screen.findByRole("tab", { name: "Evolução histórica" });
    fireEvent.mouseDown(screen.getByRole("tab", { name: "Evolução histórica" }));

    const inicio = await screen.findByLabelText("Início da evolução");
    fireEvent.change(inicio, { target: { value: "2025-01-01" } });
    fireEvent.click(screen.getByRole("button", { name: "Aplicar período da evolução" }));

    await waitFor(() => expect(buscarEvolucaoLeitos).toHaveBeenCalledWith("", "2025-01-01", "2026-01-01"));

    // 2) Enquanto isso ainda está em voo, troca a UF para RJ e aplica os filtros gerais: um
    // painel novo (com evolução própria, marcador 777.777) é carregado por cima.
    fireEvent.click(screen.getByLabelText("Unidade Federativa"));
    fireEvent.click(await screen.findByRole("option", { name: "RJ" }));
    fireEvent.click(screen.getByRole("button", { name: "Aplicar" }));

    await waitFor(() => expect(buscarPainelLeitos).toHaveBeenCalledWith({ modo: "ultima_competencia", uf: "RJ" }, "2024-01-01", "2026-01-01"));

    // carregarPainel volta a aba para "uf"; volta para "Evolução histórica" para conferir
    // o dado exibido na tabela de evolução.
    fireEvent.mouseDown(await screen.findByRole("tab", { name: "Evolução histórica" }));
    expect(await screen.findByText("777.777")).toBeInTheDocument();

    // 3) Só agora a resposta velha da evolução (uf "") chega. Ela não pode sobrescrever a
    // evolução do painel de RJ que já está na tela.
    evolucaoAntiga.resolve([
      { competencia: "1999-12-01", leitos_gerais: 424_242, leitos_sus: 1, leitos_uti: 1, leitos_uti_sus: 1, instituicoes: 1 },
    ]);

    // Dá tempo para a promise resolvida se propagar (se ela for aplicada, o marcador aparece).
    await new Promise((r) => setTimeout(r, 20));

    expect(screen.queryByText("424.242")).not.toBeInTheDocument();
    expect(screen.getByText("777.777")).toBeInTheDocument();
  });
});
