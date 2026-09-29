import { describe, expect, it } from "vitest";
import { escalaQuantis, rotuloFaixa } from "./escalaMapa";
import { numeroExato } from "./format";

describe("escalaQuantis", () => {
  it("27 valores positivos distintos dão 5 faixas e todo valor cai numa delas", () => {
    const valores = Array.from({ length: 27 }, (_, i) => i + 1);
    const escala = escalaQuantis(valores);
    expect(escala.faixas).toHaveLength(5);
    for (const v of valores) {
      const c = escala.classeDe(v);
      expect(c.tipo).toBe("faixa");
    }
  });

  it("[0, null, 10, 10, 10] dá zero, sem-registro e uma faixa só", () => {
    const escala = escalaQuantis([0, null, 10, 10, 10]);
    expect(escala.classeDe(0)).toEqual({ tipo: "zero" });
    expect(escala.classeDe(null)).toEqual({ tipo: "sem-registro" });
    expect(escala.classeDe(undefined)).toEqual({ tipo: "sem-registro" });
    expect(escala.faixas).toHaveLength(1);
    const c = escala.classeDe(10);
    expect(c).toEqual({ tipo: "faixa", indice: 0, min: 10, max: 10 });
  });

  it("valores empatados na borda ficam na mesma classe", () => {
    // Muitos valores repetidos no limiar de corte: garantimos que os limiares
    // duplicados são removidos e o valor de corte não separa iguais.
    const valores = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2];
    const escala = escalaQuantis(valores);
    const classes = valores.filter((v) => v === 1).map((v) => escala.classeDe(v));
    const indices = new Set(classes.map((c) => (c.tipo === "faixa" ? c.indice : -1)));
    expect(indices.size).toBe(1);
  });

  it("dois valores positivos distintos dão 2 faixas", () => {
    const escala = escalaQuantis([5, 100]);
    expect(escala.faixas).toHaveLength(2);
    expect(escala.classeDe(5)).toEqual({ tipo: "faixa", indice: 0, min: 5, max: 5 });
    expect(escala.classeDe(100)).toEqual({ tipo: "faixa", indice: 1, min: 100, max: 100 });
  });

  it('rotuloFaixa({min: 1, max: 500}, numeroExato) === "1–500"', () => {
    expect(rotuloFaixa({ min: 1, max: 500 }, numeroExato)).toBe("1–500");
  });

  it('rotuloFaixa com min === max mostra só um número', () => {
    expect(rotuloFaixa({ min: 500, max: 500 }, numeroExato)).toBe("500");
  });
});
