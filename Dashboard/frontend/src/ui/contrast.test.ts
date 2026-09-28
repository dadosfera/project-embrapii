import { describe, expect, it } from "vitest";
import { contraste } from "./contrast";

describe("contraste WCAG", () => {
  it("preto no branco é 21", () => expect(contraste("rgb(0,0,0)", "rgb(255,255,255)")).toBeCloseTo(21, 0));
  it("mesma cor é 1", () => expect(contraste("rgb(23,0,162)", "rgb(23,0,162)")).toBeCloseTo(1, 5));
  it("aceita hex", () => expect(contraste("#000000", "#ffffff")).toBeCloseTo(21, 0));
});
