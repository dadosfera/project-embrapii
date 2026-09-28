import { useEffect, useState } from "react";

/**
 * true quando a viewport está abaixo do breakpoint (mobile). Usado pelos rankings horizontais
 * (Compras/Medicamentos): nomes de fornecedor/fabricante vêm em CAIXA ALTA da base, mais largos
 * por caractere do que texto normal, e o eixo Y do Recharts tem largura fixa — sem isso, o rótulo
 * trunca por um nº de caracteres calibrado para telas largas e o texto sobra pela esquerda, ficando
 * cortado pelo `overflow-hidden` do contêiner (achado de QA B5).
 */
export function useEhTelaEstreita(breakpoint = 640): boolean {
  const [estreita, setEstreita] = useState(
    () => typeof window !== "undefined" && window.innerWidth < breakpoint,
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mq = window.matchMedia(`(max-width: ${breakpoint - 1}px)`);
    const atualizar = () => setEstreita(mq.matches);
    atualizar();
    mq.addEventListener("change", atualizar);
    return () => mq.removeEventListener("change", atualizar);
  }, [breakpoint]);

  return estreita;
}
