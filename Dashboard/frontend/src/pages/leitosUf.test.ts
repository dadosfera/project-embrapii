import { describe, expect, it } from "vitest";

import type { LeitosPorUf } from "../lib/api";
import { barrasEmpilhadasUf } from "./leitosUf";

function item(overrides: Partial<LeitosPorUf>): LeitosPorUf {
  return {
    uf: "SP",
    leitos_gerais: 0,
    leitos_sus: 0,
    leitos_uti: 0,
    leitos_uti_sus: 0,
    instituicoes: 0,
    ...overrides,
  };
}

describe("barrasEmpilhadasUf", () => {
  it("ordena por total decrescente, e uf crescente no empate", () => {
    const porUf = [
      item({ uf: "RJ", leitos_gerais: 100, leitos_sus: 40 }),
      item({ uf: "SP", leitos_gerais: 300, leitos_sus: 100 }),
      item({ uf: "BA", leitos_gerais: 100, leitos_sus: 20 }),
    ];

    const barras = barrasEmpilhadasUf(porUf, "gerais");

    expect(barras.map((b) => b.uf)).toEqual(["SP", "BA", "RJ"]);
  });

  it("nao_sus nunca é negativo, mesmo se sus > total (dado inconsistente)", () => {
    const porUf = [item({ uf: "SP", leitos_gerais: 10, leitos_sus: 15 })];

    const barras = barrasEmpilhadasUf(porUf, "gerais");

    expect(barras[0].nao_sus).toBe(0);
  });

  it("filtra UFs que ehUf não reconhece (ex.: 'Não informado')", () => {
    const porUf = [
      item({ uf: "SP", leitos_gerais: 10, leitos_sus: 5 }),
      item({ uf: "Não informado", leitos_gerais: 999, leitos_sus: 1 }),
    ];

    const barras = barrasEmpilhadasUf(porUf, "gerais");

    expect(barras).toHaveLength(1);
    expect(barras[0].uf).toBe("SP");
  });

  it("a métrica 'uti' usa as colunas de UTI, não as gerais", () => {
    const porUf = [
      item({
        uf: "SP",
        leitos_gerais: 100,
        leitos_sus: 50,
        leitos_uti: 20,
        leitos_uti_sus: 8,
      }),
    ];

    const barras = barrasEmpilhadasUf(porUf, "uti");

    expect(barras[0]).toMatchObject({ sus: 8, nao_sus: 12, total: 20 });
  });

  it("calcula percentual_sus, e null quando o total é zero", () => {
    const porUf = [
      item({ uf: "SP", leitos_gerais: 200, leitos_sus: 50 }),
      item({ uf: "RJ", leitos_gerais: 0, leitos_sus: 0 }),
    ];

    const barras = barrasEmpilhadasUf(porUf, "gerais");

    expect(barras.find((b) => b.uf === "SP")?.percentual_sus).toBe(25);
    expect(barras.find((b) => b.uf === "RJ")?.percentual_sus).toBeNull();
  });
});
