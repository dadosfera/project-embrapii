// Guardas de cor e de tokens do front. Falha (exit 1) se:
//  1. houver cor hex em src/**/*.ts(x) (testes fora) ou no index.css fora da camada
//     beast:tokens;
//  2. alguma variável CSS referenciada em src/**/*.ts(x) ou no index.css — `var(--x)` ou o
//     atalho do Tailwind 4 `bg-(--x)` — não estiver definida no index.css (`--x:`).
//     Ficam de fora as do Radix (`--radix-*`) e as internas do Tailwind/tw-animate (`--tw-*`);
//  3. houver `lucide-react` em src (ícones são só Eva, via src/ui/Icon);
//  4. houver `bg-muted` em src/components/ui (no nosso @theme, --color-muted é cor de texto;
//     nas primitivas shadcn use `bg-subtle`);
//  5. houver classe `dark:` em src/components/ui (não há tema escuro; no Tailwind 4 o `dark:`
//     segue o sistema operacional e ligaria sozinho).
//
// Limite conhecido: a guarda de cor só pega literais hex (#rgb, #rrggbb, ...). Não detecta
// cor "errada" por outro caminho — rgb()/hsl() literais, nomes de cor CSS (ex.: "tomato"),
// ou uma variável semântica definida mas usada no lugar errado (--danger onde deveria ser
// --danger-text, por exemplo). Essas exigem revisão manual ou um linter à parte.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const HEX = /#[0-9a-fA-F]{3,8}\b/g;
const REF_VAR = /var\(\s*(--[\w-]+)/g;
const REF_ATALHO = /[\w\]:]-\((?:\w+:)?(--[\w-]+)\)/g;
const IGNORADAS = /^--(radix|tw)-/;
const erros = [];

function walk(dir, out = []) {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) walk(p, out);
    else out.push(p);
  }
  return out;
}

const arquivos = walk("src");
const codigo = arquivos.filter((p) => /\.(ts|tsx)$/.test(p));

// 1. hex
for (const p of codigo) {
  if (/\.test\.tsx?$/.test(p)) continue;
  const m = readFileSync(p, "utf8").match(HEX);
  if (m) erros.push(`${p}: hex ${[...new Set(m)].join(", ")}`);
}

const css = readFileSync("src/index.css", "utf8");
const ini = css.indexOf("/* beast:tokens:start */");
const fim = css.indexOf("/* beast:tokens:end */");
if (ini < 0 || fim < 0) erros.push("src/index.css: marcadores beast:tokens ausentes");
else {
  const fora = (css.slice(0, ini) + css.slice(fim)).match(HEX);
  if (fora) erros.push(`src/index.css fora da camada de tokens: ${[...new Set(fora)].join(", ")}`);
}

// 2. variáveis referenciadas e não definidas
const definidas = new Set([...css.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]));
for (const p of [...codigo, "src/index.css"]) {
  const s = readFileSync(p, "utf8");
  const faltando = new Set();
  for (const re of [REF_VAR, REF_ATALHO]) {
    for (const m of s.matchAll(re)) {
      if (!definidas.has(m[1]) && !IGNORADAS.test(m[1])) faltando.add(m[1]);
    }
  }
  if (faltando.size) erros.push(`${p}: variável não definida no index.css: ${[...faltando].join(", ")}`);
}

// 3. lucide-react
for (const p of arquivos) {
  if (readFileSync(p, "utf8").includes("lucide-react")) erros.push(`${p}: lucide-react (use <Icon> de src/ui/Icon)`);
}

// 4 e 5. bg-muted e dark: nas primitivas
for (const p of arquivos.filter((p) => p.startsWith(join("src", "components", "ui")))) {
  const s = readFileSync(p, "utf8");
  if (/\bbg-muted\b/.test(s)) erros.push(`${p}: bg-muted (use bg-subtle)`);
  if (/(^|[\s"'`])dark:/m.test(s)) erros.push(`${p}: classe dark: (remova; não há tema escuro)`);
}

if (erros.length) { console.error(erros.join("\n")); process.exit(1); }
console.log("tokens OK");
