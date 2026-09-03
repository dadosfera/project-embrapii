export type ThemePreference = "system" | "light" | "dark";

const STORAGE_KEY = "pairs.theme";

function isThemePreference(value: string | null): value is ThemePreference {
  return value === "system" || value === "light" || value === "dark";
}

export function getThemePreference(): ThemePreference {
  const saved = localStorage.getItem(STORAGE_KEY);
  return isThemePreference(saved) ? saved : "system";
}

export function applyTheme(theme: ThemePreference) {
  const root = document.documentElement;

  if (theme === "system") {
    root.removeAttribute("data-theme");
  } else {
    root.dataset.theme = theme;
  }
}

export function setThemePreference(theme: ThemePreference) {
  localStorage.setItem(STORAGE_KEY, theme);
  applyTheme(theme);
}

export function initTheme() {
  applyTheme(getThemePreference());
}
