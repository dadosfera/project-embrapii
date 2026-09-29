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

  it("índice da classe é a quantidade de limiares ≤ v (limiares [6,11,17,22]) e faixas guardam os membros reais", () => {
    const valores = Array.from({ length: 27 }, (_, i) => i + 1);
    const escala = escalaQuantis(valores);
    expect(escala.classeDe(5)).toMatchObject({ tipo: "faixa", indice: 0 });
    expect(escala.classeDe(6)).toMatchObject({ tipo: "faixa", indice: 1 });
    expect(escala.classeDe(27)).toMatchObject({ tipo: "faixa", indice: 4 });
    expect(escala.faixas).toEqual([
      { indice: 0, min: 1, max: 5 },
      { indice: 1, min: 6, max: 10 },
      { indice: 2, min: 11, max: 16 },
      { indice: 3, min: 17, max: 21 },
      { indice: 4, min: 22, max: 27 },
    ]);
  });

  it("[0, null, 10, 10, 10] dá zero, sem-registro e uma faixa só", () => {
    const escala = escalaQuantis([0, null, 10, 10, 10]);
    expect(escala.classeDe(0)).toEqual({ tipo: "zero" });
    expect(escala.classeDe(null)).toEqual({ tipo: "sem-registro" });
    expect(escala.classeDe(undefined)).toEqual({ tipo: "sem-registro" });
    expect(escala.temZero).toBe(true);
    expect(escala.temSemRegistro).toBe(true);
    expect(escala.faixas).toHaveLength(1);
    const c = escala.classeDe(10);
    expect(c.tipo).toBe("faixa");
    if (c.tipo === "faixa") {
      expect(c.min).toBe(10);
      expect(c.max).toBe(10);
    }
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
    const c5 = escala.classeDe(5);
    const c100 = escala.classeDe(100);
    expect(c5.tipo).toBe("faixa");
    expect(c100.tipo).toBe("faixa");
    if (c5.tipo === "faixa" && c100.tipo === "faixa") {
      expect(c5.min).toBe(5);
      expect(c5.max).toBe(5);
      expect(c100.min).toBe(100);
      expect(c100.max).toBe(100);
      expect(c5.indice).not.toBe(c100.indice);
    }
    expect(escala.temSemRegistro).toBe(false);
    expect(escala.temZero).toBe(false);
  });

  it('rotuloFaixa({min: 1, max: 500}, numeroExato) === "1–500"', () => {
    expect(rotuloFaixa({ min: 1, max: 500 }, numeroExato)).toBe("1–500");
  });

  it('rotuloFaixa com min === max mostra só um número', () => {
    expect(rotuloFaixa({ min: 500, max: 500 }, numeroExato)).toBe("500");
  });
});
