import { describe, expect, it } from "vitest";
import { contraste } from "./contrast";
import { CATEGORICA_VARS, SEQUENCIAL_VARS } from "./chartTheme";

// valores das variáveis Beast (espelho de src/index.css camada 1.1), só para o teste
const BEAST: Record<string, string> = {
  "--beast-primary-500": "rgb(23,0,162)", "--beast-info-700": "rgb(41,134,168)",
  "--beast-success-600": "rgb(65,150,67)", "--beast-warning-700": "rgb(179,106,0)",
  "--beast-primary-300": "rgb(116,102,199)", "--beast-danger-600": "rgb(220,38,38)",
};
const BRANCO = "rgb(255,255,255)";

describe("paleta categórica", () => {
  it("tem 6 cores", () => expect(CATEGORICA_VARS).toHaveLength(6));
  it("cada cor tem contraste >= 3 contra o fundo (marcas gráficas, WCAG 1.4.11)", () => {
    for (const v of CATEGORICA_VARS) expect(contraste(BEAST[v], BRANCO), v).toBeGreaterThanOrEqual(3);
  });
  it("sequencial tem 5 classes", () => expect(SEQUENCIAL_VARS).toHaveLength(5));
});
