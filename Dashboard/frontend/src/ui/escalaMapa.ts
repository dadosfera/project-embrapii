/** Escala coroplética por quantis, sem d3-scale (só o necessário para os mapas). */

export type ClasseMapa =
  | { tipo: "sem-registro" }
  | { tipo: "zero" }
  | { tipo: "faixa"; indice: number; min: number; max: number };

export type EscalaMapa = {
  classeDe(v: number | null | undefined): ClasseMapa;
  faixas: { indice: number; min: number; max: number }[];
  /** true se `valores` tinha algum `null`/`undefined`. */
  temSemRegistro: boolean;
  /** true se `valores` tinha algum `0`. */
  temZero: boolean;
};

/**
 * Quantis calculados só sobre os valores > 0. `null`/`undefined` vira "sem-registro",
 * `0` vira "zero". O limiar da classe `i` (1..k-1) é `ordenados[floor(i*n/k)]`; limiares
 * repetidos são removidos (valores iguais nunca ficam em classes diferentes), então com
 * menos de `k` valores distintos o número de classes cai junto. O índice da classe é a
 * quantidade de limiares ≤ v.
 */
export function escalaQuantis(valores: (number | null | undefined)[], k = 5): EscalaMapa {
  const temSemRegistro = valores.some((v) => v == null || Number.isNaN(v));
  const temZero = valores.some((v) => v === 0);
  const positivos = valores.filter((v): v is number => v != null && !Number.isNaN(v) && v > 0);
  const ordenados = [...positivos].sort((a, b) => a - b);
  const n = ordenados.length;

  const limiares: number[] = [];
  for (let i = 1; i < k; i++) {
    const limiar = ordenados[Math.floor((i * n) / k)];
    if (limiar !== undefined && !limiares.includes(limiar)) limiares.push(limiar);
  }
  limiares.sort((a, b) => a - b);

  function indiceDe(v: number): number {
    let idx = 0;
    for (const l of limiares) if (v >= l) idx++;
    return idx;
  }

  const membros = new Map<number, { min: number; max: number }>();
  for (const v of ordenados) {
    const idx = indiceDe(v);
    const atual = membros.get(idx);
    if (!atual) membros.set(idx, { min: v, max: v });
    else {
      if (v < atual.min) atual.min = v;
      if (v > atual.max) atual.max = v;
    }
  }

  // Os índices "crus" (contagem de limiares ≤ v) podem ter buracos — ex.: [5, 100] só
  // popula os índices 1 e 2. Renumeramos para 0..m-1 em ordem crescente, para que
  // `faixas[i].indice === i` sempre valha e `cores[classeDe(v).indice]` combine com
  // `cores[i]` da legenda (mesma indexação nos dois lugares).
  const brutosOrdenados = [...membros.keys()].sort((a, b) => a - b);
  const renumeracao = new Map<number, number>(brutosOrdenados.map((bruto, i) => [bruto, i]));

  const faixas = brutosOrdenados.map((bruto) => {
    const { min, max } = membros.get(bruto)!;
    return { indice: renumeracao.get(bruto)!, min, max };
  });
  const faixaPorIndiceNovo = new Map(faixas.map((f) => [f.indice, f]));

  function classeDe(v: number | null | undefined): ClasseMapa {
    if (v == null || Number.isNaN(v)) return { tipo: "sem-registro" };
    if (v === 0) return { tipo: "zero" };
    if (v < 0) return { tipo: "sem-registro" };
    const bruto = indiceDe(v);
    const idx = renumeracao.get(bruto);
    const f = idx === undefined ? undefined : faixaPorIndiceNovo.get(idx);
    if (!f || idx === undefined) return { tipo: "sem-registro" };
    return { tipo: "faixa", indice: idx, min: f.min, max: f.max };
  }

  return { classeDe, faixas, temSemRegistro, temZero };
}

/** "1–500", ou "500" se min === max. */
export function rotuloFaixa(f: { min: number; max: number }, formatar: (v: number) => string): string {
  return f.min === f.max ? formatar(f.min) : `${formatar(f.min)}–${formatar(f.max)}`;
}
