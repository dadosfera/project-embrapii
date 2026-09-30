import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SeletorUf } from "./SeletorUf";

describe("SeletorUf", () => {
  it('mostra "Todas" quando value é vazio', () => {
    render(<SeletorUf id="uf-teste" label="Estado" value="" onChange={vi.fn()} />);
    expect(screen.getByRole("combobox")).toHaveTextContent("Todas");
  });

  it("lista as 27 UFs mais Todas", () => {
    render(<SeletorUf id="uf-teste" label="Estado" value="" onChange={vi.fn()} />);
    fireEvent.click(screen.getByRole("combobox"));
    expect(screen.getAllByRole("option")).toHaveLength(28);
  });

  it("escolher uma UF chama onChange com a sigla", () => {
    const onChange = vi.fn();
    render(<SeletorUf id="uf-teste" label="Estado" value="" onChange={onChange} />);
    fireEvent.click(screen.getByRole("combobox"));
    fireEvent.click(screen.getByRole("option", { name: "MG" }));
    expect(onChange).toHaveBeenCalledWith("MG");
  });

  it('escolher "Todas" chama onChange com string vazia', () => {
    const onChange = vi.fn();
    render(<SeletorUf id="uf-teste" label="Estado" value="MG" onChange={onChange} />);
    fireEvent.click(screen.getByRole("combobox"));
    fireEvent.click(screen.getByRole("option", { name: "Todas" }));
    expect(onChange).toHaveBeenCalledWith("");
  });

  it("disabled desabilita o combobox", () => {
    render(<SeletorUf id="uf-teste" label="Estado" value="" onChange={vi.fn()} disabled />);
    expect(screen.getByRole("combobox")).toBeDisabled();
  });
});
