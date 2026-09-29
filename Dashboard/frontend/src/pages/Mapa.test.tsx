import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";

import { buscarLeitosPorUf, type LeitosPorUf } from "../lib/api";
import { Mapa } from "./Mapa";

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

// MG: 20 de 100 leitos gerais são SUS -> 20,0% de participação do SUS.
const LEITOS_PADRAO: LeitosPorUf[] = [
  { uf: "MG", leitos_gerais: 100, leitos_sus: 20, leitos_uti: 10, leitos_uti_sus: 5, instituicoes: 3 },
  { uf: "SP", leitos_gerais: 200, leitos_sus: 100, leitos_uti: 20, leitos_uti_sus: 10, instituicoes: 6 },
];

function renderMapa() {
  return render(
    <MemoryRouter>
      <TooltipProvider>
        <Mapa />
      </TooltipProvider>
    </MemoryRouter>,
  );
}

describe("Mapa: aba Leitos, métrica Participação do SUS", () => {
  beforeEach(() => {
    // Sem isto, a contagem de chamadas de buscarLeitosPorUf vaza entre testes (vi.mock não
    // reseta sozinho), o que quebra qualquer teste que confira toHaveBeenCalledTimes.
    vi.clearAllMocks();
    vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(GEOJSON),
    }));
    vi.mocked(buscarLeitosPorUf).mockResolvedValue(LEITOS_PADRAO);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("mostra um único '%' no rótulo da UF e na legenda (sem duplicar o símbolo)", async () => {
    renderMapa();

    fireEvent.mouseDown(screen.getByRole("tab", { name: "Leitos por estado" }));

    await waitFor(() => expect(buscarLeitosPorUf).toHaveBeenCalled());

    const mg = await screen.findByRole("button", { name: /Minas Gerais \(MG\)/ });
    expect(mg.getAttribute("aria-label")).toMatch(/20,0 %$/);
    expect(mg.getAttribute("aria-label")).not.toMatch(/%\s*%/);

    expect(screen.getByText("Legenda (%)")).toBeInTheDocument();
  });

  it("o botão Aplicar de Leitos não começa 'pendente' antes da primeira aplicação", async () => {
    renderMapa();

    fireEvent.mouseDown(screen.getByRole("tab", { name: "Leitos por estado" }));

    // Antes de qualquer clique em Aplicar, modoLeitosAplicado é null: não deve marcar pendente
    // (senão o botão mostraria "Há alterações não aplicadas." assim que a aba abre).
    await screen.findByRole("button", { name: "Aplicar" });
    expect(screen.queryByText("Há alterações não aplicadas.")).not.toBeInTheDocument();

    await waitFor(() => expect(buscarLeitosPorUf).toHaveBeenCalled());
    expect(screen.queryByText("Há alterações não aplicadas.")).not.toBeInTheDocument();
  });

  it("uma falha seguida de 'Tentar de novo' dispara só mais um pedido, e o painel reflete a resposta dele", async () => {
    // Cobre o contador `pedidoLeitos` (o mesmo padrão de `pedidoEstoque`): a falha limpa
    // falhaLeitos/mostra Skeleton, e a resposta que acaba na tela é a do pedido disparado pelo
    // retry — nunca uma resposta de um pedido anterior que viesse a resolver fora de ordem.
    vi.mocked(buscarLeitosPorUf)
      .mockRejectedValueOnce(new Error("falhou"))
      .mockResolvedValueOnce([
        { uf: "MG", leitos_gerais: 999_999, leitos_sus: 1, leitos_uti: 1, leitos_uti_sus: 1, instituicoes: 1 },
      ]);

    renderMapa();
    fireEvent.mouseDown(screen.getByRole("tab", { name: "Leitos por estado" }));

    const retry = await screen.findByRole("button", { name: "Tentar de novo" });
    expect(buscarLeitosPorUf).toHaveBeenCalledTimes(1);

    fireEvent.click(retry);

    await waitFor(() => expect(buscarLeitosPorUf).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("999.999")).toBeInTheDocument();
  });
});
