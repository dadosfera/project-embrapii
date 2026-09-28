import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError, UiError } from "@/lib/http";
import { ChartFrame } from "./ChartFrame";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { KpiCard } from "./KpiCard";
import { PageHeader } from "./PageHeader";
import { moedaCompacta, numeroCompacto, numeroExato } from "./format";

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
  it("KpiCard com valor zero mostra '0', não 'sem dado', e é acessível por teclado", () => {
    render(<TooltipProvider><KpiCard label="Instituições" value={0} format={numeroCompacto} /></TooltipProvider>);
    const valor = screen.getByText("0").closest("p")!;
    expect(valor).toBeInTheDocument();
    expect(valor).toHaveAttribute("tabIndex", "0");
    expect(valor).not.toHaveAttribute("aria-label");
    expect(valor).toHaveTextContent(`Instituições: ${numeroExato(0)}`);
  });
  it("EmptyState mostra causa e ação", () => {
    render(<EmptyState title="Sem estoque" cause="Nenhuma instituição registrou." action={<button>Ver outro</button>} />);
    expect(screen.getByText("Nenhuma instituição registrou.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ver outro" })).toBeInTheDocument();
  });
  it("ErrorState chama onRetry e mostra a mensagem da ApiError", () => {
    const onRetry = vi.fn();
    render(<ErrorState error={new ApiError(503, "Banco indisponível")} onRetry={onRetry} />);
    expect(screen.getByText("Banco indisponível")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
  it("ErrorState mostra texto genérico para erro que não é ApiError", () => {
    render(<ErrorState error={new TypeError("Failed to fetch")} />);
    expect(screen.queryByText("Failed to fetch")).not.toBeInTheDocument();
    expect(screen.getByText("Não foi possível carregar os dados.")).toBeInTheDocument();
  });
  it("ErrorState mostra a mensagem de um UiError do próprio app", () => {
    render(<ErrorState error={new UiError("Não foi possível carregar o mapa (404).")} />);
    expect(screen.getByText("Não foi possível carregar o mapa (404).")).toBeInTheDocument();
  });
  it("ErrorState cai no texto genérico se a ApiError vier sem mensagem", () => {
    render(<ErrorState error={new ApiError(500, "")} />);
    expect(screen.getByText("Não foi possível carregar os dados.")).toBeInTheDocument();
  });
  it("ChartFrame tem título e fonte", () => {
    render(<ChartFrame title="Evolução" source="DATASUS"><div>g</div></ChartFrame>);
    expect(screen.getByRole("heading", { name: "Evolução" })).toBeInTheDocument();
    expect(screen.getByText(/DATASUS/)).toBeInTheDocument();
  });
});
