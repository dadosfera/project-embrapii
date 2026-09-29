import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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
    {
      type: "Feature",
      properties: { sigla: "AC", nome: "Acre" },
      geometry: { type: "Polygon", coordinates: [[[-70, -9], [-69, -9], [-69, -10], [-70, -10], [-70, -9]]] },
    },
  ],
};

// `geojsonCache`/`geojsonPromise` são módulo-privados: cada teste importa o componente de
// novo, depois de `vi.resetModules()`, para começar sem cache do teste anterior.
async function importarComponente() {
  vi.resetModules();
  const modulo = await import("./MapaBrasil");
  return modulo.MapaBrasilUf;
}

describe("MapaBrasilUf", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(GEOJSON),
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("colore por quantis, hachura sem registro e distingue 0 de faixa", async () => {
    const MapaBrasilUf = await importarComponente();

    render(<MapaBrasilUf dados={[{ uf: "MG", valor: 10 }, { uf: "SP", valor: 0 }]} unidade="unidades" />);

    const mg = await screen.findByRole("button", { name: /MG.*10 unidades/ });
    const ac = screen.getByRole("button", { name: /sem registro/ });
    const sp = screen.getByRole("button", { name: /SP.*unidades/ });

    expect(ac.getAttribute("aria-label")).toMatch(/sem registro/);
    expect(ac.getAttribute("fill")).toMatch(/^url\(#/);
    expect(sp.getAttribute("fill")).not.toBe(mg.getAttribute("fill"));
  });

  it("Enter fixa a UF (aria-pressed e painel) e Escape limpa", async () => {
    const MapaBrasilUf = await importarComponente();

    render(<MapaBrasilUf dados={[{ uf: "MG", valor: 10 }, { uf: "SP", valor: 0 }]} unidade="unidades" />);

    const mg = await screen.findByRole("button", { name: /MG.*10 unidades/ });

    fireEvent.keyDown(mg, { key: "Enter" });
    expect(mg).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Minas Gerais")).toBeInTheDocument();

    fireEvent.keyDown(mg, { key: "Escape" });
    expect(mg).toHaveAttribute("aria-pressed", "false");
  });

  it("sem seleção, o painel lista as 5 maiores", async () => {
    const MapaBrasilUf = await importarComponente();

    render(<MapaBrasilUf dados={[{ uf: "MG", valor: 10 }, { uf: "SP", valor: 0 }]} unidade="unidades" />);

    await screen.findByRole("button", { name: /MG.*10 unidades/ });
    expect(screen.getByText("5 maiores")).toBeInTheDocument();
  });

  it("5 maiores só lista UF com valor positivo (exclui 0 e sem registro)", async () => {
    const MapaBrasilUf = await importarComponente();

    render(<MapaBrasilUf dados={[{ uf: "MG", valor: 10 }, { uf: "SP", valor: 0 }]} unidade="unidades" />);

    await screen.findByRole("button", { name: /MG.*10 unidades/ });
    const painel = screen.getByRole("complementary");
    expect(within(painel).getByText("Minas Gerais")).toBeInTheDocument();
    expect(within(painel).queryByText("São Paulo")).not.toBeInTheDocument();
    expect(within(painel).queryByText("Acre")).not.toBeInTheDocument();
  });

  it("sem nenhuma UF com valor positivo, mostra aviso em vez da lista", async () => {
    const MapaBrasilUf = await importarComponente();

    render(<MapaBrasilUf dados={[{ uf: "MG", valor: 0 }, { uf: "SP", valor: 0 }]} unidade="unidades" />);

    await screen.findByRole("button", { name: /MG.*unidades/ });
    const painel = screen.getByRole("complementary");
    expect(within(painel).getByText("Nenhuma UF com valor")).toBeInTheDocument();
    expect(within(painel).queryByRole("list")).not.toBeInTheDocument();
  });

  it("Escape no botão 'Limpar seleção' (fora do path) também limpa a UF fixada", async () => {
    const MapaBrasilUf = await importarComponente();

    render(<MapaBrasilUf dados={[{ uf: "MG", valor: 10 }, { uf: "SP", valor: 0 }]} unidade="unidades" />);

    const mg = await screen.findByRole("button", { name: /MG.*10 unidades/ });
    fireEvent.click(mg);
    expect(mg).toHaveAttribute("aria-pressed", "true");

    const limpar = screen.getByRole("button", { name: "Limpar seleção" });
    fireEvent.keyDown(limpar, { key: "Escape" });
    expect(mg).toHaveAttribute("aria-pressed", "false");
  });

  it("no modo controlado, clicar chama onFixarUf com a sigla", async () => {
    const MapaBrasilUf = await importarComponente();
    const onFixarUf = vi.fn();

    render(
      <MapaBrasilUf
        dados={[{ uf: "MG", valor: 10 }, { uf: "SP", valor: 0 }]}
        unidade="unidades"
        ufFixada={null}
        onFixarUf={onFixarUf}
      />,
    );

    const mg = await screen.findByRole("button", { name: /MG.*10 unidades/ });
    fireEvent.click(mg);

    expect(onFixarUf).toHaveBeenCalledWith("MG");
    // Modo controlado: sem o prop `ufFixada` atualizado de fora, o botão não deve fixar sozinho.
    expect(mg).toHaveAttribute("aria-pressed", "false");
  });
});
