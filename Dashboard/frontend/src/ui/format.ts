export const SEM_DADO = "sem dado";

type Num = number | null | undefined;

const compacto = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
const moedaCompactaFmt = new Intl.NumberFormat("pt-BR", {
  style: "currency", currency: "BRL", notation: "compact", maximumFractionDigits: 1,
});
const moedaExataFmt = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const inteiro = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });
// Quantidades (itens fornecidos, unidades em estoque, etc.): a soma agregada que a API devolve
// pode legitimamente vir fracionária (é soma de quantidades de várias compras, não uma contagem
// de linhas) — não é só resíduo de ponto flutuante. Ainda assim, para a tabela ficar legível e
// não variar o nº de casas por linha ("668.027,14", "53.852.468,1", "234.110" na mesma coluna),
// mostramos sempre arredondado para inteiro; quem precisar da fração exata vai à API, não à tela.
const quantidadeFmt = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const umaCasaFmt = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

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
/** Quantidade (itens, unidades): sempre inteiro pt-BR, para não variar o nº de casas por linha/coluna. */
export function quantidade(v: Num): string {
  return vazio(v) ? SEM_DADO : quantidadeFmt.format(v);
}
/**
 * Número puro com uma casa decimal pt-BR ("12,3"), sem unidade/símbolo — quem quiser "%" ou outro
 * sufixo compõe por cima. Usado pelo `formatar` do mapa (que já monta "12,3 %" com `unidade`) e
 * pelos formatadores de percentual das páginas, para não duplicar a config do `Intl.NumberFormat`.
 */
export function numeroUmaCasa(v: Num): string {
  return vazio(v) ? SEM_DADO : umaCasaFmt.format(v);
}
/** "AAAA-MM-DD" (com ou sem hora) → "DD/MM/AAAA", sem passar por Date para não deslocar o fuso. */
export function data(v: string | null | undefined): string {
  if (!v) return SEM_DADO;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(v);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : v;
}
/** Data local de `d` em "AAAA-MM-DD" (toISOString() usa UTC e adianta o dia à noite no Brasil). */
export function hojeLocal(d: Date = new Date()): string {
  const mes = String(d.getMonth() + 1).padStart(2, "0");
  const dia = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mes}-${dia}`;
}
