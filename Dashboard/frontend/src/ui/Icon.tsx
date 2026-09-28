import { ICONS, type IconName } from "./icons";
import { IconSvg } from "./IconSvg";

type Props = { name: IconName; size?: number; label?: string; className?: string };

/** Ícone Eva (outline) do registro completo. No shell (chunk de entrada) use <ShellIcon>. */
export function Icon({ name, ...props }: Props) {
  return <IconSvg svg={ICONS[name]} {...props} />;
}
