// Falha se houver cor hex fora da camada de tokens Beast do index.css.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const HEX = /#[0-9a-fA-F]{3,8}\b/g;
const erros = [];

function walk(dir) {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) walk(p);
    else if (/\.(ts|tsx)$/.test(f) && !/\.test\.tsx?$/.test(f)) {
      const m = readFileSync(p, "utf8").match(HEX);
      if (m) erros.push(`${p}: ${[...new Set(m)].join(", ")}`);
    }
  }
}
walk("src");

const css = readFileSync("src/index.css", "utf8");
const ini = css.indexOf("/* beast:tokens:start */");
const fim = css.indexOf("/* beast:tokens:end */");
if (ini < 0 || fim < 0) erros.push("src/index.css: marcadores beast:tokens ausentes");
else {
  const fora = (css.slice(0, ini) + css.slice(fim)).match(HEX);
  if (fora) erros.push(`src/index.css fora da camada de tokens: ${[...new Set(fora)].join(", ")}`);
}

if (erros.length) { console.error(erros.join("\n")); process.exit(1); }
console.log("tokens OK");
