import { describe, expect, it } from "vitest";
import { anotarOutliers, completarAnos, notaOutlier, LIMITE_OUTLIER } from "./comprasAnual";
import type { CompraPorAno } from "../lib/api";

function linha(sobrescreve: Partial<CompraPorAno> = {}): CompraPorAno {
  return {
    ano: 2024,
    valor_total: 1_000_000,
    numero_compras: 10,
    quantidade_itens: 100,
    maior_registro: 100_000,
    maior_registro_fornecedor: "Fornecedor X",
    ...sobrescreve,
  };
}

describe("anotarOutliers", () => {
  it("marca 2025 com um registro de 97,9% do valor do ano", () => {
    const [ano] = anotarOutliers([
      linha({
        ano: 2025,
        valor_total: 23_200_000_000,
        numero_compras: 2_474,
        maior_registro: 22_700_000_000,
        maior_registro_fornecedor: "MEDICAL MERCANTIL",
      }),
    ]);

    expect(ano.outlier).toBe(true);
    expect(notaOutlier(ano)).toMatch(
      /2025: 1 registro \(MEDICAL MERCANTIL\) = R\$\s22,7\sbi, 97,\d% do valor do ano\./,
    );
  });

  it("não marca quando a participação é exatamente o limite (20%)", () => {
    const [ano] = anotarOutliers([
      linha({
        valor_total: 1_000_000,
        numero_compras: 5,
        maior_registro: 200_000,
      }),
    ]);

    expect(ano.outlier).toBe(false);
    expect(ano.participacao_maior).toBeCloseTo(LIMITE_OUTLIER);
  });

  it("não marca quando valor_total é 0", () => {
    const [ano] = anotarOutliers([
      linha({
        valor_total: 0,
        numero_compras: 5,
        maior_registro: 0,
      }),
    ]);

    expect(ano.outlier).toBe(false);
  });

  it("não marca quando numero_compras é 1", () => {
    const [ano] = anotarOutliers([
      linha({
        valor_total: 1_000_000,
        numero_compras: 1,
        maior_registro: 1_000_000,
      }),
    ]);

    expect(ano.outlier).toBe(false);
  });

  it("acentua 'Nao informado' vindo sem acento do backend, igual ao caso null", () => {
    const [comAcento, semAcento, ausente] = anotarOutliers([
      linha({ ano: 2020, maior_registro_fornecedor: "Não informado" }),
      linha({ ano: 2021, maior_registro_fornecedor: "Nao informado" }),
      linha({ ano: 2022, maior_registro_fornecedor: null }),
    ]);

    expect(notaOutlier(comAcento)).toMatch(/\(Não informado\)/);
    expect(notaOutlier(semAcento)).toMatch(/\(Não informado\)/);
    expect(notaOutlier(ausente)).toMatch(/\(Não informado\)/);
  });
});

describe("completarAnos", () => {
  it("preenche com linhas zeradas os anos sem compras entre de..ate", () => {
    const completo = completarAnos(
      [linha({ ano: 2020 }), linha({ ano: 2023 })],
      2020,
      2023,
    );

    expect(completo.map((a) => a.ano)).toEqual([2020, 2021, 2022, 2023]);
    expect(completo[1]).toMatchObject({
      ano: 2021,
      valor_total: 0,
      numero_compras: 0,
      quantidade_itens: 0,
      maior_registro: null,
      maior_registro_fornecedor: null,
    });
    // Anos com dado real não são mexidos.
    expect(completo[0]).toMatchObject({ ano: 2020, valor_total: 1_000_000 });
  });

  it("com todos os anos presentes, devolve as mesmas linhas", () => {
    const linhas = [linha({ ano: 2020 }), linha({ ano: 2021 })];
    expect(completarAnos(linhas, 2020, 2021)).toEqual(linhas);
  });
});
