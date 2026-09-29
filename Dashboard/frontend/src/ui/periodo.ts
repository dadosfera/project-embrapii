/** Funções puras de período por ano, compartilhadas pelos filtros de evolução das páginas. */

/** Lista de anos de `min` a `max`, inclusive, em ordem crescente. */
export function anosEntre(min: number, max: number): number[] {
  const anos: number[] = [];
  for (let ano = min; ano <= max; ano++) anos.push(ano);
  return anos;
}

/** Datas de início/fim do período, cobrindo o ano inteiro em cada ponta. */
export function datasDoPeriodo(de: number, ate: number): { data_inicio: string; data_fim: string } {
  return { data_inicio: `${de}-01-01`, data_fim: `${ate}-12-31` };
}

/** Rótulo curto do período: um ano isolado, ou o intervalo com meia-risca. */
export function rotuloPeriodo(de: number, ate: number): string {
  return de === ate ? `${de}` : `${de}–${ate}`;
}

/** Ano de uma data "AAAA-MM-DD" (ou com hora), sem passar por Date para não deslocar o fuso. */
export function anoDeIso(iso: string | null): number | null {
  if (!iso) return null;
  const ano = Number(iso.slice(0, 4));
  return Number.isNaN(ano) ? null : ano;
}
