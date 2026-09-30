// Fuso fixo com deslocamento negativo: o teste de hojeLocal() só pega a regressão para
// toISOString() (UTC) se a noite local já for o dia seguinte em UTC.
process.env.TZ = "America/Sao_Paulo";

import "@testing-library/jest-dom/vitest";

import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// Sem `test.globals` no vite.config.ts, a limpeza automática do RTL (que depende de um
// `afterEach` global) não se registra sozinha. Registra explicitamente para não vazar DOM
// entre testes de um mesmo arquivo.
afterEach(() => {
  cleanup();
});
