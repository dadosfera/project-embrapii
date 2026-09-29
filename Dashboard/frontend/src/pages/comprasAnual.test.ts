import { describe, expect, it } from "vitest";
import { anotarOutliers, notaOutlier, LIMITE_OUTLIER } from "./comprasAnual";
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
});
