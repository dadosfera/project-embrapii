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

describe("ShellIcon", () => {
  it("renderiza igual ao Icon e o registro completo contém os ícones do shell", async () => {
    const { ShellIcon } = await import("./ShellIcon");
    const { SHELL_ICONS } = await import("./icons-shell");
    const { ICONS } = await import("./icons");
    const a = render(<ShellIcon name="menu" />).container.innerHTML;
    const b = render(<Icon name="menu" />).container.innerHTML;
    expect(a).toBe(b);
    for (const [nome, svg] of Object.entries(SHELL_ICONS)) expect(ICONS[nome as keyof typeof ICONS]).toBe(svg);
  });
});
