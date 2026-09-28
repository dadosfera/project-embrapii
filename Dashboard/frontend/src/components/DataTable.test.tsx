import { render, screen } from "@testing-library/react";
import type { ColumnDef } from "@tanstack/react-table";
import { describe, expect, it } from "vitest";
import { DataTable } from "./DataTable";

type Linha = { nome: string; valor: number };
const cols: ColumnDef<Linha, unknown>[] = [
  { accessorKey: "nome", header: "Nome" },
  { accessorKey: "valor", header: "Valor", meta: { align: "right" } },
  { accessorKey: "obs", header: "Obs", meta: { priority: "low" } },
];

describe("DataTable", () => {
  it("alinha numérico à direita com tabular-nums", () => {
    render(<DataTable data={[{ nome: "A", valor: 10 }]} columns={cols} />);
    const cel = screen.getByText("10").closest("td")!;
    expect(cel.className).toMatch(/text-right/);
    expect(cel.className).toMatch(/tabular-nums/);
  });
  it("coluna de baixa prioridade é escondida abaixo de lg", () => {
    render(<DataTable data={[{ nome: "A", valor: 10 }]} columns={cols} />);
    expect(screen.getByRole("columnheader", { name: "Obs" }).className).toMatch(/hidden lg:table-cell/);
  });
  it("vazio usa EmptyState com a mensagem", () => {
    render(<DataTable data={[]} columns={cols} emptyMessage="Nada no período." />);
    expect(screen.getByText("Nada no período.")).toBeInTheDocument();
  });
});
