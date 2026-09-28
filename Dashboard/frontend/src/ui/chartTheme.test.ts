/// <reference types="node" />
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { contraste } from "./contrast";
import { CATEGORICA_VARS, SEQUENCIAL_VARS, dotPara, linha } from "./chartTheme";

// Lê os valores reais das variáveis Beast de src/index.css (camada beast:tokens), em vez de
// manter uma cópia hardcoded que pode ficar desatualizada em relação ao CSS de verdade.
// process.cwd() é a raiz do frontend (onde o vitest roda), não este arquivo: import.meta.url
// aqui não é um file:// estável sob o transform do Vite/Vitest.
const css = readFileSync(resolve(process.cwd(), "src/index.css"), "utf8");
const ini = css.indexOf("/* beast:tokens:start */");
const fim = css.indexOf("/* beast:tokens:end */");
if (ini < 0 || fim < 0) throw new Error("marcadores beast:tokens ausentes em src/index.css");
const camadaTokens = css.slice(ini, fim);

const BEAST: Record<string, string> = {};
for (const m of camadaTokens.matchAll(/(--beast-[a-z]+-\d+):\s*(#[0-9a-fA-F]{3,8})/g)) {
  BEAST[m[1]] = m[2];
}

function valorBeast(nomeVar: string): string {
  const valor = BEAST[nomeVar];
  if (!valor) throw new Error(`${nomeVar} não encontrada em src/index.css`);
  return valor;
}

const BRANCO = "#ffffff";
const FUNDO = valorBeast("--beast-basic-200"); // --bg

describe("paleta categórica", () => {
  it("tem 6 cores", () => expect(CATEGORICA_VARS).toHaveLength(6));
  it("cada cor tem contraste >= 3 contra o branco (marcas gráficas, WCAG 1.4.11)", () => {
    for (const v of CATEGORICA_VARS) expect(contraste(valorBeast(v), BRANCO), v).toBeGreaterThanOrEqual(3);
  });
  it("cada cor tem contraste >= 3 contra --bg (fundo real dos gráficos)", () => {
    for (const v of CATEGORICA_VARS) expect(contraste(valorBeast(v), FUNDO), v).toBeGreaterThanOrEqual(3);
  });
  it("sequencial tem 5 classes", () => expect(SEQUENCIAL_VARS).toHaveLength(5));
});

describe("dotPara", () => {
  it("marca cada ponto em séries de até 12 pontos", () => {
    expect(dotPara(1)).toEqual(linha.dot);
    expect(dotPara(12)).toEqual(linha.dot);
  });
  it("tira os marcadores acima de 12 pontos (o activeDot do hover continua em linha)", () => {
    expect(dotPara(13)).toBe(false);
    expect(dotPara(24)).toBe(false);
    expect(linha.activeDot).toEqual({ r: 5 });
  });
});
