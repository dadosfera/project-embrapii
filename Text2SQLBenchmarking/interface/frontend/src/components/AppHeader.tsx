import dadosferaSymbol from "../assets/dadosfera-symbol.png";
import type { Mode, SystemStatus } from "../api/types";
import { ModeSwitcher } from "./ModeSwitcher";
import { OperationStatus } from "./OperationStatus";

interface Props {
  mode: Mode;
  disabled: boolean;
  status: SystemStatus | null;
  chatActive: boolean;
  benchmarkActive: boolean;
  onModeChange: (mode: Mode) => void;
}

export function AppHeader({ mode, disabled, status, chatActive, benchmarkActive, onModeChange }: Props) {
  return (
    <header className="app-header">
      <div className="brand" aria-label="Dadosfera Text2SQL">
        <img src={dadosferaSymbol} alt="" className="brand-symbol" />
        <span>Text2SQL</span>
      </div>
      <ModeSwitcher mode={mode} disabled={disabled} onChange={onModeChange} />
      <OperationStatus status={status} chatActive={chatActive} benchmarkActive={benchmarkActive} />
    </header>
  );
}
