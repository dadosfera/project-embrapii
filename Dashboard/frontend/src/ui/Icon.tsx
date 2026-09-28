import { ICONS, type IconName } from "./icons";

type Props = { name: IconName; size?: number; label?: string; className?: string };

/** Ícone Eva (outline). Decorativo por padrão; com `label` vira imagem acessível. */
export function Icon({ name, size = 20, label, className }: Props) {
  const svg = ICONS[name].replace("<svg", `<svg width="${size}" height="${size}" fill="currentColor" class="size-full"`);
  return (
    <span
      className={["inline-flex shrink-0", className].filter(Boolean).join(" ")}
      style={{ width: size, height: size }}
      {...(label ? { role: "img", "aria-label": label } : { "aria-hidden": true })}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
