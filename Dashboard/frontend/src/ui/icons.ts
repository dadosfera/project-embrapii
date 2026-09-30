// Registro completo (shell + páginas). Importado por <Icon>, que só páginas e primitivas usam,
// então estes SVGs não entram no chunk de entrada. O shell usa <ShellIcon> (icons-shell.ts).
import { SHELL_ICONS } from "./icons-shell";
import search from "eva-icons/outline/svg/search-outline.svg?raw";
import close from "eva-icons/outline/svg/close-outline.svg?raw";
import alert from "eva-icons/outline/svg/alert-circle-outline.svg?raw";
import info from "eva-icons/outline/svg/info-outline.svg?raw";
import refresh from "eva-icons/outline/svg/refresh-outline.svg?raw";
import calendar from "eva-icons/outline/svg/calendar-outline.svg?raw";
import funnel from "eva-icons/outline/svg/funnel-outline.svg?raw";
import trending from "eva-icons/outline/svg/trending-up-outline.svg?raw";
import arrowDown from "eva-icons/outline/svg/arrow-downward-outline.svg?raw";
// Usados pelas primitivas shadcn (select, sheet, dialog, command).
import check from "eva-icons/outline/svg/checkmark-outline.svg?raw";
import chevronDown from "eva-icons/outline/svg/chevron-down-outline.svg?raw";
import chevronUp from "eva-icons/outline/svg/chevron-up-outline.svg?raw";

export const ICONS = {
  ...SHELL_ICONS,
  search, close, alert, info, refresh, calendar, funnel, trending, arrowDown, check, chevronDown, chevronUp,
} as const;

export type IconName = keyof typeof ICONS;
