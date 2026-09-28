import { describe, expect, it } from "vitest";
import { inicioHaMeses } from "./leitosDatas";

describe("inicioHaMeses", () => {
  it("volta 24 meses de calendário, mesmo dia", () => {
    expect(inicioHaMeses(new Date(2026, 8, 25), 24)).toBe("2024-09-25");
  });
  it("limita o dia ao último dia do mês de destino", () => {
    expect(inicioHaMeses(new Date(2026, 2, 31), 1)).toBe("2026-02-28");
  });
  it("atravessa a virada do ano e o fevereiro bissexto", () => {
    expect(inicioHaMeses(new Date(2025, 1, 28), 12)).toBe("2024-02-28");
    expect(inicioHaMeses(new Date(2024, 4, 31), 3)).toBe("2024-02-29");
    expect(inicioHaMeses(new Date(2026, 0, 15), 2)).toBe("2025-11-15");
  });
});
