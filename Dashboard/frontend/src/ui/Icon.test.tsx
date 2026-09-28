import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Icon } from "./Icon";

describe("Icon", () => {
  it("renderiza svg decorativo por padrão", () => {
    const { container } = render(<Icon name="search" />);
    const el = container.firstElementChild!;
    expect(el.getAttribute("aria-hidden")).toBe("true");
    expect(container.innerHTML).toContain("<svg");
  });
  it("com label vira imagem acessível", () => {
    const { getByRole } = render(<Icon name="search" label="Buscar" />);
    expect(getByRole("img", { name: "Buscar" })).toBeInTheDocument();
  });
});
