import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChoroplethLegend } from "./ChoroplethLegend";
import { escalaQuantis } from "./escalaMapa";
import { numeroExato } from "./format";

describe("ChoroplethLegend", () => {
  it("mostra sem registro, 0 e as 5 faixas com a unidade na legenda", () => {
    const valores = [null, 0, ...Array.from({ length: 27 }, (_, i) => i + 1)];
    const escala = escalaQuantis(valores);
    const cores = ["#111", "#222", "#333", "#444", "#555"]; // cores resolvidas (não vêm de hex no componente)

    render(
      <ChoroplethLegend
        escala={escala}
        cores={cores}
        unidade="leitos"
        formatar={numeroExato}
        mostrarSemRegistro
        mostrarZero
      />,
    );

    expect(screen.getByText("Legenda (leitos)")).toBeInTheDocument();
    expect(screen.getByText("sem registro")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
    expect(escala.faixas).toHaveLength(5);
    for (const f of escala.faixas) {
      const rotulo = f.min === f.max ? numeroExato(f.min) : `${numeroExato(f.min)}–${numeroExato(f.max)}`;
      expect(screen.getByText(rotulo)).toBeInTheDocument();
    }
  });

  it("sem mostrarSemRegistro/mostrarZero, esconde o que não existir nos dados por padrão", () => {
    const escala = escalaQuantis([5, 100]);
    render(<ChoroplethLegend escala={escala} cores={["#111", "#222"]} unidade="itens" formatar={numeroExato} />);
    expect(screen.queryByText("sem registro")).not.toBeInTheDocument();
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("com props omitidas, segue os dados: null e 0 na entrada mostram as duas linhas", () => {
    const escala = escalaQuantis([null, 0, 5, 100]);
    render(<ChoroplethLegend escala={escala} cores={["#111", "#222"]} unidade="itens" formatar={numeroExato} />);
    expect(screen.getByText("sem registro")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("false explícito esconde mesmo quando os dados têm null e 0", () => {
    const escala = escalaQuantis([null, 0, 5, 100]);
    render(
      <ChoroplethLegend
        escala={escala}
        cores={["#111", "#222"]}
        unidade="itens"
        formatar={numeroExato}
        mostrarSemRegistro={false}
        mostrarZero={false}
      />,
    );
    expect(screen.queryByText("sem registro")).not.toBeInTheDocument();
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });
});
