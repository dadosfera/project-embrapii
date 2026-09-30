import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { AppShell } from "./AppShell";

// Força o chunk do menu mobile a falhar, para exercitar o fallback MenuSimples (sem Dialog).
vi.mock("./MobileMenu", () => {
  throw new Error("Failed to fetch dynamically imported module: MobileMenu");
});

describe("AppShell", () => {
  it("mostra logo, selo do projeto e os 6 destinos", () => {
    render(<MemoryRouter><AppShell><p>conteúdo</p></AppShell></MemoryRouter>);
    expect(screen.getByAltText("Dadosfera")).toBeInTheDocument();
    expect(screen.getByText("Projeto EMBRAPII · DCC/UFMG")).toBeInTheDocument();
    for (const nome of ["Início", "Medicamentos", "Compras", "Leitos", "Mapa", "Fornecedores"]) {
      expect(screen.getAllByRole("link", { name: nome }).length).toBeGreaterThan(0);
    }
    expect(screen.getByText("conteúdo")).toBeInTheDocument();
  });

  it("o botão do menu fecha o fallback MenuSimples quando o chunk do menu falha", async () => {
    vi.spyOn(console, "warn").mockImplementation(() => {});
    render(<MemoryRouter><AppShell><p>conteúdo</p></AppShell></MemoryRouter>);
    const botao = screen.getByRole("button", { name: "Abrir menu" });

    fireEvent.click(botao);
    await waitFor(() => expect(screen.getByLabelText("Navegação principal (menu)")).toBeInTheDocument());

    fireEvent.click(botao);
    await waitFor(() =>
      expect(screen.queryByLabelText("Navegação principal (menu)")).not.toBeInTheDocument(),
    );

    vi.restoreAllMocks();
  });
});
