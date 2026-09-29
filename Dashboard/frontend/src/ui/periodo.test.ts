import { describe, expect, it } from "vitest";
import { anosEntre, datasDoPeriodo, rotuloPeriodo } from "./periodo";

describe("anosEntre", () => {
  it("lista os anos do intervalo, inclusive as pontas", () => {
    expect(anosEntre(2020, 2025)).toEqual([2020, 2021, 2022, 2023, 2024, 2025]);
  });
  it("com min === max devolve um único ano", () => {
    expect(anosEntre(2021, 2021)).toEqual([2021]);
  });
});

describe("datasDoPeriodo", () => {
  it("devolve o primeiro e o último dia dos anos de ponta", () => {
    expect(datasDoPeriodo(2020, 2025)).toEqual({ data_inicio: "2020-01-01", data_fim: "2025-12-31" });
  });
  it("com um único ano, cobre o ano inteiro", () => {
    expect(datasDoPeriodo(2021, 2021)).toEqual({ data_inicio: "2021-01-01", data_fim: "2021-12-31" });
  });
});

describe("rotuloPeriodo", () => {
  it("um único ano não usa meia-risca", () => {
    expect(rotuloPeriodo(2021, 2021)).toBe("2021");
  });
  it("intervalo usa meia-risca", () => {
    expect(rotuloPeriodo(2020, 2025)).toBe("2020–2025");
  });
});
