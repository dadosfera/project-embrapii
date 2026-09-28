import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { AppShell } from "./AppShell";

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
});
