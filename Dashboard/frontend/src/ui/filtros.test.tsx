import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Alternador } from "./Alternador";
import { BotaoAplicar } from "./BotaoAplicar";
import { KpiCard } from "./KpiCard";
import { anosEntre } from "./periodo";
import { PeriodoAnos } from "./PeriodoAnos";
import { numeroCompacto, numeroExato } from "./format";

// Radix Select em jsdom precisa desses dois stubs (não implementados no jsdom): o Content usa
// ResizeObserver para medir o popper, e o Item usa hasPointerCapture ao lidar com seleção por
// ponteiro. scrollIntoView também não existe no jsdom e o Content chama ao abrir.
function comStubsDoRadixSelect(f: () => void) {
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Object.assign(HTMLElement.prototype, {
    hasPointerCapture: () => false,
    scrollIntoView: () => {},
  });
  try {
    f();
  } finally {
    vi.unstubAllGlobals();
  }
}

describe("PeriodoAnos", () => {
  it("renderiza 'De' e 'Até' com o ano atual", () => {
    render(
      <PeriodoAnos id="periodo" anos={anosEntre(2020, 2025)} de={2021} ate={2023} onChange={vi.fn()} />,
    );
    expect(screen.getByLabelText("De")).toHaveTextContent("2021");
    expect(screen.getByLabelText("Até")).toHaveTextContent("2023");
  });

  it("'Todos os anos' chama onChange(2020, 2025)", () => {
    const onChange = vi.fn();
    render(
      <PeriodoAnos id="periodo" anos={anosEntre(2020, 2025)} de={2021} ate={2023} onChange={onChange} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Todos os anos" }));
    expect(onChange).toHaveBeenCalledWith(2020, 2025);
  });

  it("'Até' só oferece anos a partir de 'De'", () => {
    comStubsDoRadixSelect(() => {
      render(
        <PeriodoAnos id="periodo" anos={anosEntre(2020, 2025)} de={2022} ate={2023} onChange={vi.fn()} />,
      );
      fireEvent.click(screen.getByLabelText("Até"));
      expect(screen.queryByRole("option", { name: "2021" })).not.toBeInTheDocument();
      expect(screen.getByRole("option", { name: "2022" })).toBeInTheDocument();
    });
  });
});

describe("BotaoAplicar", () => {
  it("tem nome 'Aplicar' sem carga", () => {
    render(<BotaoAplicar carregando={false} />);
    expect(screen.getByRole("button", { name: "Aplicar" })).toBeInTheDocument();
  });

  it("mantém o nome 'Aplicar' durante a carga e fica desabilitado/aria-busy", () => {
    render(<BotaoAplicar carregando />);
    const botao = screen.getByRole("button", { name: "Aplicar" });
    expect(botao).toBeDisabled();
    expect(botao).toHaveAttribute("aria-busy", "true");
  });

  it("mostra o aviso quando pendente", () => {
    render(<BotaoAplicar carregando={false} pendente />);
    expect(screen.getByRole("status")).toHaveTextContent("Há alterações não aplicadas.");
  });

  it("sem pendente, não mostra o aviso", () => {
    render(<BotaoAplicar carregando={false} />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});

describe("Alternador", () => {
  const opcoes = [
    { valor: "mensal" as const, rotulo: "Mensal" },
    { valor: "anual" as const, rotulo: "Anual" },
  ];

  it("a seta direita move o aria-checked para a próxima opção", () => {
    const Wrapper = () => {
      const [valor, setValor] = useState<"mensal" | "anual">("mensal");
      return <Alternador rotulo="Frequência" opcoes={opcoes} valor={valor} onChange={setValor} />;
    };
    render(<Wrapper />);
    const mensal = screen.getByRole("radio", { name: "Mensal" });
    fireEvent.keyDown(mensal, { key: "ArrowRight" });
    expect(screen.getByRole("radio", { name: "Anual" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "Mensal" })).toHaveAttribute("aria-checked", "false");
    // Roving tabindex (WAI-ARIA): o foco do DOM tem de seguir a opção recém-marcada.
    expect(document.activeElement).toBe(screen.getByRole("radio", { name: "Anual" }));
  });

  it("só a opção marcada tem tabindex 0 (roving)", () => {
    render(<Alternador rotulo="Frequência" opcoes={opcoes} valor="mensal" onChange={vi.fn()} />);
    expect(screen.getByRole("radio", { name: "Mensal" })).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("radio", { name: "Anual" })).toHaveAttribute("tabindex", "-1");
  });
});

describe("KpiCard destaque", () => {
  it("mantém o valor compacto com destaque ligado", () => {
    render(
      <TooltipProvider>
        <KpiCard label="Valor" value={50_923_000_000} format={numeroCompacto} destaque />
      </TooltipProvider>,
    );
    expect(screen.getAllByText("50,9 bi").length).toBeGreaterThan(0);
  });

  it("sem destaque, não altera o comportamento existente", () => {
    render(
      <TooltipProvider>
        <KpiCard label="Valor" value={10} format={numeroExato} />
      </TooltipProvider>,
    );
    expect(screen.getAllByText("10").length).toBeGreaterThan(0);
  });
});
