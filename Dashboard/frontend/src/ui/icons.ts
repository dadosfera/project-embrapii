import home from "eva-icons/outline/svg/home-outline.svg?raw";
import droplet from "eva-icons/outline/svg/droplet-outline.svg?raw";
import cart from "eva-icons/outline/svg/shopping-cart-outline.svg?raw";
import activity from "eva-icons/outline/svg/activity-outline.svg?raw";
import map from "eva-icons/outline/svg/map-outline.svg?raw";
import briefcase from "eva-icons/outline/svg/briefcase-outline.svg?raw";
import search from "eva-icons/outline/svg/search-outline.svg?raw";
import menu from "eva-icons/outline/svg/menu-outline.svg?raw";
import close from "eva-icons/outline/svg/close-outline.svg?raw";
import alert from "eva-icons/outline/svg/alert-circle-outline.svg?raw";
import info from "eva-icons/outline/svg/info-outline.svg?raw";
import refresh from "eva-icons/outline/svg/refresh-outline.svg?raw";
import inbox from "eva-icons/outline/svg/inbox-outline.svg?raw";
import calendar from "eva-icons/outline/svg/calendar-outline.svg?raw";
import funnel from "eva-icons/outline/svg/funnel-outline.svg?raw";
import trending from "eva-icons/outline/svg/trending-up-outline.svg?raw";
import arrowDown from "eva-icons/outline/svg/arrow-downward-outline.svg?raw";
// Usados pelas primitivas shadcn (select, sheet, dialog, command).
import check from "eva-icons/outline/svg/checkmark-outline.svg?raw";
import chevronDown from "eva-icons/outline/svg/chevron-down-outline.svg?raw";
import chevronUp from "eva-icons/outline/svg/chevron-up-outline.svg?raw";

export const ICONS = {
  home, droplet, cart, activity, map, briefcase, search, menu, close,
  alert, info, refresh, inbox, calendar, funnel, trending, arrowDown,
  check, chevronDown, chevronUp,
} as const;

export type IconName = keyof typeof ICONS;
