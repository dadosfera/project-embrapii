// Falha se o chunk JS de entrada (referenciado no index.html) passar do limite.
import { readFileSync, statSync } from "node:fs";

const LIMITE = 250 * 1024;
const html = readFileSync("dist/index.html", "utf8");
const src = /<script[^>]+type="module"[^>]+src="\.?\/?([^"]+\.js)"/.exec(html)?.[1];
if (!src) { console.error("entrada JS não encontrada no dist/index.html"); process.exit(1); }
const tam = statSync(`dist/${src}`).size;
console.log(`${src}: ${(tam / 1024).toFixed(1)} kB (limite ${LIMITE / 1024} kB)`);
if (tam > LIMITE) process.exit(1);
