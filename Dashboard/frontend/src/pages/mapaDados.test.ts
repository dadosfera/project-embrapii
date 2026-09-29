import { describe, expect, it } from "vitest";

import { UFS } from "../lib/ufs";
import type { EstoqueUf, LeitosPorUf } from "../lib/api";
import {
  normalizarEstoque,
  normalizarLeitos,
  ordenarNulosPorUltimo,
} from "./mapaDados";

function estoque(overrides: Partial<EstoqueUf>): EstoqueUf {
  return {
    uf: "SP",
    estoque_total: 0,
    num_instituicoes: 0,
    ...overrides,
  };
}

function leitos(overrides: Partial<LeitosPorUf>): LeitosPorUf {
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

describe("normalizarEstoque", () => {
  it("UF ausente vira null, e 0 continua 0", () => {
    const linhas = normalizarEstoque([estoque({ uf: "SP", estoque_total: 0 })]);

    const sp = linhas.find((l) => l.uf === "SP");
    const rj = linhas.find((l) => l.uf === "RJ");

    expect(sp?.estoque_total).toBe(0);
    expect(rj?.estoque_total).toBeNull();
    expect(rj?.num_instituicoes).toBeNull();
  });

  it("devolve as 27 UFs", () => {
    const linhas = normalizarEstoque([]);

    expect(linhas).toHaveLength(27);
    expect(linhas.map((l) => l.uf).sort()).toEqual([...UFS].sort());
  });

  it("ignora UF que ehUf não reconhece (ex.: 'Não informado')", () => {
    const linhas = normalizarEstoque([
      estoque({ uf: "Não informado", estoque_total: 999 }),
    ]);

    expect(linhas).toHaveLength(27);
    expect(linhas.every((l) => l.estoque_total === null)).toBe(true);
  });
});

describe("normalizarLeitos", () => {
  it("UF ausente vira null, e 0 continua 0", () => {
    const linhas = normalizarLeitos([leitos({ uf: "SP", leitos_gerais: 0 })]);

    const sp = linhas.find((l) => l.uf === "SP");
    const rj = linhas.find((l) => l.uf === "RJ");

    expect(sp?.leitos_gerais).toBe(0);
    expect(rj?.leitos_gerais).toBeNull();
    expect(rj?.percentual_sus).toBeNull();
  });

  it("percentual_sus fica null com gerais 0", () => {
    const linhas = normalizarLeitos([
      leitos({ uf: "SP", leitos_gerais: 0, leitos_sus: 0 }),
    ]);

    expect(linhas.find((l) => l.uf === "SP")?.percentual_sus).toBeNull();
  });

  it("percentual_sus é leitos_sus / leitos_gerais * 100", () => {
    const linhas = normalizarLeitos([
      leitos({ uf: "SP", leitos_gerais: 200, leitos_sus: 50 }),
    ]);

    expect(linhas.find((l) => l.uf === "SP")?.percentual_sus).toBe(25);
  });

  it("devolve as 27 UFs", () => {
    const linhas = normalizarLeitos([]);

    expect(linhas).toHaveLength(27);
    expect(linhas.map((l) => l.uf).sort()).toEqual([...UFS].sort());
  });

  it("ignora UF que ehUf não reconhece (ex.: 'Não informado')", () => {
    const linhas = normalizarLeitos([
      leitos({ uf: "Não informado", leitos_gerais: 999 }),
    ]);

    expect(linhas).toHaveLength(27);
    expect(linhas.every((l) => l.leitos_gerais === null)).toBe(true);
  });
});

describe("ordenarNulosPorUltimo", () => {
  it("põe os nulos no fim, e ordena o resto decrescente", () => {
    const linhas = [
      { chave: "a", valor: null },
      { chave: "b", valor: 10 },
      { chave: "c", valor: null },
      { chave: "d", valor: 30 },
      { chave: "e", valor: 20 },
    ];

    const ordenado = ordenarNulosPorUltimo(linhas, (l) => l.valor);

    expect(ordenado.map((l) => l.chave)).toEqual(["d", "e", "b", "a", "c"]);
  });
});
