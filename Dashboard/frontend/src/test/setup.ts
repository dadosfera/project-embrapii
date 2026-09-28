import "@testing-library/jest-dom/vitest";

import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// Sem `test.globals` no vite.config.ts, a limpeza automática do RTL (que depende de um
// `afterEach` global) não se registra sozinha. Registra explicitamente para não vazar DOM
// entre testes de um mesmo arquivo.
afterEach(() => {
  cleanup();
});
