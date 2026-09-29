import { ehUf, UFS } from "../lib/ufs";
import type { EstoqueUf, LeitosPorUf } from "../lib/api";

/** UF ausente da resposta ou valor nulo/inválido: `null` (distinto de zero). */
export type LinhaEstoque = {
  uf: string;
  estoque_total: number | null;
  num_instituicoes: number | null;
};

export type LinhaLeitos = {
  uf: string;
  leitos_gerais: number | null;
  leitos_sus: number | null;
  leitos_uti: number | null;
  leitos_uti_sus: number | null;
  instituicoes: number | null;
  /** `leitos_sus / leitos_gerais * 100`; `null` quando `leitos_gerais` não é positivo. */
  percentual_sus: number | null;
};

function numeroOuNulo(valor: unknown): number | null {
  if (valor === null || valor === undefined) {
    return null;
  }

  const convertido = Number(valor);

  return Number.isFinite(convertido) ? convertido : null;
}

function calcularPercentualSus(
  gerais: number | null,
  sus: number | null,
): number | null {
  if (gerais === null || sus === null || gerais <= 0) {
    return null;
  }

  return (sus / gerais) * 100;
}

export function normalizarEstoque(dados: EstoqueUf[]): LinhaEstoque[] {
  const porUf = new Map<string, LinhaEstoque>();

  dados.forEach((item) => {
    if (!item.uf) {
      return;
    }

    const uf = item.uf.trim().toUpperCase();

    if (!ehUf(uf)) {
      return;
    }

    porUf.set(uf, {
      uf,
      estoque_total: numeroOuNulo(item.estoque_total),
      num_instituicoes: numeroOuNulo(item.num_instituicoes),
    });
  });

  return UFS.map(
    (uf) =>
      porUf.get(uf) ?? {
        uf,
        estoque_total: null,
        num_instituicoes: null,
      },
  );
}

export function normalizarLeitos(dados: LeitosPorUf[]): LinhaLeitos[] {
  const porUf = new Map<string, LinhaLeitos>();

  dados.forEach((item) => {
    if (!item.uf) {
      return;
    }

    const uf = item.uf.trim().toUpperCase();

    if (!ehUf(uf)) {
      return;
    }

    const leitosGerais = numeroOuNulo(item.leitos_gerais);
    const leitosSus = numeroOuNulo(item.leitos_sus);

    porUf.set(uf, {
      uf,
      leitos_gerais: leitosGerais,
      leitos_sus: leitosSus,
      leitos_uti: numeroOuNulo(item.leitos_uti),
      leitos_uti_sus: numeroOuNulo(item.leitos_uti_sus),
      instituicoes: numeroOuNulo(item.instituicoes),
      percentual_sus: calcularPercentualSus(leitosGerais, leitosSus),
    });
  });

  return UFS.map(
    (uf) =>
      porUf.get(uf) ?? {
        uf,
        leitos_gerais: null,
        leitos_sus: null,
        leitos_uti: null,
        leitos_uti_sus: null,
        instituicoes: null,
        percentual_sus: null,
      },
  );
}

/** Ordena por `chave` decrescente; linhas com `null` vão para o fim, nessa ordem. */
export function ordenarNulosPorUltimo<T>(
  linhas: T[],
  chave: (linha: T) => number | null,
): T[] {
  return [...linhas].sort((a, b) => {
    const valorA = chave(a);
    const valorB = chave(b);

    if (valorA === null && valorB === null) {
      return 0;
    }

    if (valorA === null) {
      return 1;
    }

    if (valorB === null) {
      return -1;
    }

    return valorB - valorA;
  });
}
