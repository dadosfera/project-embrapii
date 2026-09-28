import type { RefObject } from "react";

import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { Navegacao } from "./Navegacao";

/**
 * Menu mobile (Radix Dialog). Carregado sob demanda pelo AppShell no primeiro toque no botão,
 * para o Dialog e suas dependências não entrarem no chunk de entrada.
 * Sem SheetTrigger, o foco volta ao botão do AppShell pelo `triggerRef`.
 */
export function MobileMenu({
  open,
  onOpenChange,
  triggerRef,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  triggerRef: RefObject<HTMLButtonElement | null>;
}) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        id="menu-mobile"
        side="right"
        className="w-72 bg-panel p-4"
        aria-describedby={undefined}
        onCloseAutoFocus={(e) => {
          e.preventDefault();
          triggerRef.current?.focus();
        }}
      >
        <SheetTitle className="px-1 text-sm font-semibold text-muted">Navegação</SheetTitle>
        <nav aria-label="Navegação principal (menu)" className="mt-4 flex flex-col gap-1">
          <Navegacao onNavigate={() => onOpenChange(false)} />
        </nav>
      </SheetContent>
    </Sheet>
  );
}
