type Props = { svg: string; size?: number; label?: string; className?: string };

/** Renderiza um SVG Eva (outline). Decorativo por padrão; com `label` vira imagem acessível. */
export function IconSvg({ svg, size = 20, label, className }: Props) {
  const html = svg.replace("<svg", `<svg width="${size}" height="${size}" fill="currentColor" class="size-full"`);
  return (
    <span
      className={["inline-flex shrink-0", className].filter(Boolean).join(" ")}
      style={{ width: size, height: size }}
      {...(label ? { role: "img", "aria-label": label } : { "aria-hidden": true })}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
