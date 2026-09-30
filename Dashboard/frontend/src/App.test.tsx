import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

// Substitui as páginas de verdade (recharts, tabelas, chamadas à API...) por marcadores simples,
// para isolar só o que este arquivo testa: a barra de progresso de navegação (App.tsx/AppShell.tsx).
// "/compras" sempre rejeita (chunk quebrado), as demais resolvem na hora (chunk já pré-carregado).
//
// O caso "clica numa rota B ainda pendente, aperta Voltar para A (já montada)" (follow-up do QA
// à correção de B4: RotaRevelada, em App.tsx, agora depende de `location` em vez de `key`) não
// tem um teste de unidade aqui: reproduzir um <Suspense>/`React.lazy` genuinamente pendente e
// depois destravado por uma segunda navegação, em jsdom + testing-library, não chega a comitar a
// segunda transição enquanto a primeira segue suspensa (parece uma limitação do agendador do
// React nesse ambiente, não do código) — o cenário está coberto de verdade em
// e2e/navegacao-lenta.spec.ts ("Voltar para uma rota já montada com a rota clicada ainda
// pendente", tag @slow), que roda num Chromium de verdade com o chunk seguro por `page.route`.
vi.mock("./rotas", () => {
  const paginaOk = (nome: string, texto: string) => () =>
    Promise.resolve({ [nome]: () => <main id="conteudo" tabIndex={-1}>{texto}</main> }) as Promise<
      Record<string, () => React.ReactElement>
    >;

  return {
    carregadoresDeRota: {
      "/": paginaOk("Home", "Home (mock)"),
      "/medicamentos": paginaOk("Medicamentos", "Medicamentos (mock)"),
      // Mensagem genérica (NÃO bate no padrão de erro de chunk do ChunkErrorBoundary): senão o
      // `autoReload` do App entraria em ação (recarregaria a página) em vez de mostrar o fallback.
      "/compras": () => Promise.reject(new Error("Compras: erro de propósito para o teste")),
      "/leitos": paginaOk("Leitos", "Leitos (mock)"),
      "/mapa": paginaOk("Mapa", "Mapa (mock)"),
      "/fornecedores": paginaOk("Fornecedores", "Fornecedores (mock)"),
    },
    preCarregarTodasAsRotas: () => {},
    preCarregarRota: () => {},
  };
});

const barraDeProgresso = () => screen.queryByRole("status", { name: "Carregando página" });

describe("App: barra de navegação pendente (achado B4, com follow-up do QA)", () => {
  it("limpa a barra quando a navegação termina em erro (fallback do ChunkErrorBoundary)", async () => {
    vi.spyOn(console, "warn").mockImplementation(() => {});
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );
    await screen.findByText("Home (mock)");

    fireEvent.click(screen.getByRole("link", { name: "Compras" }));

    await waitFor(() => expect(screen.getByText("Não foi possível carregar a página")).toBeInTheDocument());
    // O fallback (FalhaAoCarregar) chama `aoMontar` (o resolver) no próprio mount: a barra não
    // deveria ficar acesa por cima da mensagem de erro até o timeout de segurança de 15s.
    expect(barraDeProgresso()).not.toBeInTheDocument();

    vi.restoreAllMocks();
  });
});
