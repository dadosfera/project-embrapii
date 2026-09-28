export const SEM_DADO = "sem dado";

type Num = number | null | undefined;

const compacto = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
const moedaCompactaFmt = new Intl.NumberFormat("pt-BR", {
  style: "currency", currency: "BRL", notation: "compact", maximumFractionDigits: 1,
});
const moedaExataFmt = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const inteiro = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });

function vazio(v: Num): v is null | undefined {
  return v === null || v === undefined || Number.isNaN(v);
}

export function moedaCompacta(v: Num): string {
  return vazio(v) ? SEM_DADO : moedaCompactaFmt.format(v);
}
export function numeroCompacto(v: Num): string {
  return vazio(v) ? SEM_DADO : compacto.format(v);
}
export function moedaExata(v: Num): string {
  return vazio(v) ? SEM_DADO : moedaExataFmt.format(v);
}
export function numeroExato(v: Num): string {
  return vazio(v) ? SEM_DADO : inteiro.format(v);
}
/** "AAAA-MM-DD" (com ou sem hora) → "DD/MM/AAAA", sem passar por Date para não deslocar o fuso. */
export function data(v: string | null | undefined): string {
  if (!v) return SEM_DADO;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(v);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : v;
}
