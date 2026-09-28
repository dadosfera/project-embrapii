// Falha se o chunk JS de entrada (referenciado no index.html) passar do limite.
import { readFileSync, statSync } from "node:fs";

const LIMITE_BYTES = 250 * 1024;
const html = readFileSync("dist/index.html", "utf8");
const src = /<script[^>]+type="module"[^>]+src="\.?\/?([^"]+\.js)"/.exec(html)?.[1];
if (!src) { console.error("entrada JS não encontrada no dist/index.html"); process.exit(1); }
const tam = statSync(`dist/${src}`).size;
const fmt = (b) => `${(b / 1024).toFixed(1)} KiB (${(b / 1000).toFixed(1)} kB)`;
console.log(`${src}: ${fmt(tam)}; limite ${fmt(LIMITE_BYTES)}`);
if (tam > LIMITE_BYTES) process.exit(1);
