import { describe, expect, it } from "vitest";
import { data, hojeLocal, moedaCompacta, moedaExata, numeroCompacto, numeroExato, numeroUmaCasa, quantidade, SEM_DADO } from "./format";

const n = (s: string) => s.replace(/ /g, " ");

describe("format", () => {
  it("moeda compacta em pt-BR", () => {
    expect(n(moedaCompacta(50_923_000_000))).toBe("R$ 50,9 bi");
    expect(n(moedaCompacta(1_250_000))).toBe("R$ 1,3 mi");
    expect(n(moedaCompacta(980))).toBe("R$ 980");
  });
  it("número compacto", () => {
    expect(n(numeroCompacto(1_590_225))).toBe("1,6 mi");
    expect(n(numeroCompacto(1_500))).toBe("1,5 mil");
    expect(numeroCompacto(950)).toBe("950");
  });
  it("valores exatos", () => {
    expect(n(moedaExata(1234.5))).toBe("R$ 1.234,50");
    expect(numeroExato(1_590_225)).toBe("1.590.225");
  });
  it("quantidade: sempre inteiro pt-BR, mesmo com resíduo de ponto flutuante", () => {
    expect(n(quantidade(668_027.14))).toBe("668.027");
    expect(n(quantidade(53_852_468.1))).toBe("53.852.468");
    expect(n(quantidade(234_110))).toBe("234.110");
    expect(quantidade(0)).toBe("0");
    expect(quantidade(null)).toBe(SEM_DADO);
    expect(quantidade(undefined)).toBe(SEM_DADO);
  });
  it("número puro com uma casa decimal, sem símbolo — quem chama compõe o '%'", () => {
    expect(n(numeroUmaCasa(5.7))).toBe("5,7");
    expect(n(numeroUmaCasa(20))).toBe("20,0");
    expect(n(numeroUmaCasa(0))).toBe("0,0");
    expect(numeroUmaCasa(null)).toBe(SEM_DADO);
    expect(numeroUmaCasa(undefined)).toBe(SEM_DADO);
  });
  it("nulo vira 'sem dado', zero continua zero", () => {
    expect(moedaCompacta(null)).toBe(SEM_DADO);
    expect(numeroExato(undefined)).toBe(SEM_DADO);
    expect(numeroCompacto(0)).toBe("0");
  });
  it("data sem deslocar fuso", () => {
    expect(data("2021-01-01")).toBe("01/01/2021");
    expect(data("2021-01-01T00:00:00+00:00")).toBe("01/01/2021");
    expect(data(null)).toBe(SEM_DADO);
  });
  it("hoje pela data local, não pela UTC", () => {
    // 23h30 em Brasília já é dia 26 em UTC; toISOString() devolveria "2026-09-26".
    expect(hojeLocal(new Date(2026, 8, 25, 23, 30))).toBe("2026-09-25");
    expect(hojeLocal(new Date(2026, 0, 5, 0, 5))).toBe("2026-01-05");
  });
});
