import { SHELL_ICONS, type ShellIconName } from "./icons-shell";
import { IconSvg } from "./IconSvg";

type Props = { name: ShellIconName; size?: number; label?: string; className?: string };

/** Mesmo <Icon>, restrito aos ícones do shell, para não puxar o registro completo para a entrada. */
export function ShellIcon({ name, ...props }: Props) {
  return <IconSvg svg={SHELL_ICONS[name]} {...props} />;
}
