const RGB_RE = /rgba?\(\s*(\d+)\s*[,\s]\s*(\d+)\s*[,\s]\s*(\d+)/i;
const HEX_RE = /^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/;

function rgb(cor: string): [number, number, number] {
  const m = RGB_RE.exec(cor);
  if (m) return [Number(m[1]), Number(m[2]), Number(m[3])];
  const trimmed = cor.trim();
  if (!HEX_RE.test(trimmed)) {
    throw new Error(`contraste(): cor não reconhecida (esperado rgb()/rgba() ou hex): "${cor}"`);
  }
  const h = trimmed.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  return [0, 2, 4].map((i) => parseInt(full.slice(i, i + 2), 16)) as [number, number, number];
}
function luminancia(cor: string): number {
  const [r, g, b] = rgb(cor).map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
/** Razão de contraste WCAG 2.x entre duas cores (rgb()/rgba(), com vírgula ou espaço, ou hex). */
export function contraste(a: string, b: string): number {
  const [l1, l2] = [luminancia(a), luminancia(b)].sort((x, y) => y - x);
  return (l1 + 0.05) / (l2 + 0.05);
}
