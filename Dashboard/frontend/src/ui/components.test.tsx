import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError } from "@/lib/http";
import { ChartFrame } from "./ChartFrame";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { KpiCard } from "./KpiCard";
import { PageHeader } from "./PageHeader";
import { moedaCompacta } from "./format";

describe("componentes de página", () => {
  it("PageHeader tem h1 e descrição", () => {
    render(<PageHeader icon="cart" title="Compras" description="Compras públicas" />);
    expect(screen.getByRole("heading", { level: 1, name: "Compras" })).toBeInTheDocument();
    expect(screen.getByText("Compras públicas")).toBeInTheDocument();
  });
  it("KpiCard mostra compacto e 'sem dado' para nulo", () => {
    const { rerender } = render(<TooltipProvider><KpiCard label="Valor" value={50_923_000_000} format={moedaCompacta} /></TooltipProvider>);
    expect(screen.getByText(/R\$\s50,9\sbi/)).toBeInTheDocument();
    rerender(<TooltipProvider><KpiCard label="Valor" value={null} format={moedaCompacta} /></TooltipProvider>);
    expect(screen.getByText("sem dado")).toBeInTheDocument();
  });
  it("KpiCard em loading não mostra valor", () => {
    render(<TooltipProvider><KpiCard label="Valor" value={10} format={moedaCompacta} loading /></TooltipProvider>);
    expect(screen.queryByText(/R\$/)).not.toBeInTheDocument();
  });
  it("EmptyState mostra causa e ação", () => {
    render(<EmptyState title="Sem estoque" cause="Nenhuma instituição registrou." action={<button>Ver outro</button>} />);
    expect(screen.getByText("Nenhuma instituição registrou.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ver outro" })).toBeInTheDocument();
  });
  it("ErrorState chama onRetry", () => {
    const onRetry = vi.fn();
    render(<ErrorState error={new ApiError(503, "Banco indisponível")} onRetry={onRetry} />);
    expect(screen.getByText("Banco indisponível")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
  it("ChartFrame tem título e fonte", () => {
    render(<ChartFrame title="Evolução" source="DATASUS"><div>g</div></ChartFrame>);
    expect(screen.getByRole("heading", { name: "Evolução" })).toBeInTheDocument();
    expect(screen.getByText(/DATASUS/)).toBeInTheDocument();
  });
});
