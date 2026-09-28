// Ícones do chunk de entrada: AppShell, Navegacao e EmptyState (fallback de erro de rota).
// Só entra aqui o que o shell usa; o resto fica em icons.ts, que só as páginas e primitivas importam.
import home from "eva-icons/outline/svg/home-outline.svg?raw";
import droplet from "eva-icons/outline/svg/droplet-outline.svg?raw";
import cart from "eva-icons/outline/svg/shopping-cart-outline.svg?raw";
import activity from "eva-icons/outline/svg/activity-outline.svg?raw";
import map from "eva-icons/outline/svg/map-outline.svg?raw";
import briefcase from "eva-icons/outline/svg/briefcase-outline.svg?raw";
import menu from "eva-icons/outline/svg/menu-outline.svg?raw";
import inbox from "eva-icons/outline/svg/inbox-outline.svg?raw";

export const SHELL_ICONS = { home, droplet, cart, activity, map, briefcase, menu, inbox } as const;

export type ShellIconName = keyof typeof SHELL_ICONS;
