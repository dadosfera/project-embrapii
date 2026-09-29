import { ehUf } from "../lib/ufs";
import type { LeitosPorUf } from "../lib/api";

export type MetricaUf = "gerais" | "uti";

export type BarraUf = {
  uf: string;
  sus: number;
  nao_sus: number;
  total: number;
  percentual_sus: number | null;
};

/** Coerção numérica (a API pode mandar decimal como string). */
function numero(valor: unknown) {
  const convertido = Number(valor);
  return Number.isFinite(convertido) ? convertido : 0;
}

/**
 * Barras empilhadas SUS/não-SUS por UF, para a métrica escolhida ("gerais" ou "uti").
 * Descarta UFs que `ehUf` não reconhece (ex.: "Não informado", que senão viraria a 28ª barra).
 * Ordena por total decrescente, com `uf` crescente no empate.
 */
export function barrasEmpilhadasUf(porUf: LeitosPorUf[], metrica: MetricaUf): BarraUf[] {
  return porUf
    .filter((item) => ehUf(item.uf))
    .map((item) => {
      const total = numero(metrica === "gerais" ? item.leitos_gerais : item.leitos_uti);
      const sus = numero(metrica === "gerais" ? item.leitos_sus : item.leitos_uti_sus);
      const nao_sus = Math.max(0, total - sus);
      const percentual_sus = total > 0 ? (sus / total) * 100 : null;

      return { uf: item.uf, sus, nao_sus, total, percentual_sus };
    })
    .sort((a, b) => b.total - a.total || a.uf.localeCompare(b.uf));
}
