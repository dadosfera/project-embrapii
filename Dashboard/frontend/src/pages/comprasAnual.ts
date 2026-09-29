/** Funções puras da evolução anual de compras: outlier de "um registro só" por ano. */

import type { CompraPorAno } from "../lib/api";
import { moedaCompacta } from "@/ui/format";

/** Limite estrito: um único registro acima disso do valor do ano marca o ano como outlier. */
export const LIMITE_OUTLIER = 0.2;

export type AnoCompras = {
  ano: number;
  valor_total: number;
  numero_compras: number;
  maior_registro: number | null;
  maior_registro_fornecedor: string | null;
  participacao_maior: number | null;
  outlier: boolean;
};

/** Coerção numérica (a API pode mandar decimal como string) — segue numero() de Compras.tsx. */
function numero(valor: unknown): number {
  const convertido = Number(valor);
  return Number.isFinite(convertido) ? convertido : 0;
}

function numeroOuNulo(valor: unknown): number | null {
  if (valor === null || valor === undefined || valor === "") return null;
  const convertido = Number(valor);
  return Number.isFinite(convertido) ? convertido : null;
}

/**
 * Anota cada ano com a participação do maior registro no valor total e se isso caracteriza
 * um outlier. Um ano com um único registro nunca é marcado: a participação seria sempre 100%
 * e a nota não diria nada (não haveria "outro" registro para comparar).
 */
export function anotarOutliers(linhas: CompraPorAno[], limite = LIMITE_OUTLIER): AnoCompras[] {
  return linhas.map((linha) => {
    const valorTotal = numero(linha.valor_total);
    const numeroCompras = numero(linha.numero_compras);
    const maiorRegistro = numeroOuNulo(linha.maior_registro);
    const participacaoMaior =
      maiorRegistro !== null && valorTotal > 0 ? maiorRegistro / valorTotal : null;

    const outlier =
      numeroCompras > 1
      && valorTotal > 0
      && participacaoMaior !== null
      && participacaoMaior > limite;

    return {
      ano: numero(linha.ano),
      valor_total: valorTotal,
      numero_compras: numeroCompras,
      maior_registro: maiorRegistro,
      maior_registro_fornecedor: linha.maior_registro_fornecedor ?? null,
      participacao_maior: participacaoMaior,
      outlier,
    };
  });
}

/** Nota de um ano marcado: "2025: 1 registro (MEDICAL MERCANTIL …) = R$ 22,7 bi, 97,9% do valor do ano." */
export function notaOutlier(a: AnoCompras): string {
  const participacao = (a.participacao_maior ?? 0) * 100;
  const percentual = participacao.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
  const fornecedor = a.maior_registro_fornecedor ?? "Não informado";
  return `${a.ano}: 1 registro (${fornecedor}) = ${moedaCompacta(a.maior_registro)}, ${percentual}% do valor do ano.`;
}
