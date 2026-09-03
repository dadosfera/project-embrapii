export type IconName =
  | "settings"
  | "database"
  | "library"
  | "model"
  | "context"
  | "seed"
  | "chevron-left"
  | "chevron-right"
  | "send"
  | "more"
  | "info"
  | "copy"
  | "code"
  | "close";

const paths: Record<IconName, JSX.Element> = {
  settings: <><path d="M4 7h7" /><path d="M15 7h5" /><circle cx="13" cy="7" r="2" /><path d="M4 17h4" /><path d="M12 17h8" /><circle cx="10" cy="17" r="2" /></>,
  database: <><ellipse cx="12" cy="5" rx="7" ry="3" /><path d="M5 5v6c0 1.7 3.1 3 7 3s7-1.3 7-3V5" /><path d="M5 11v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" /></>,
  library: <><path d="M5 4h14v5H5z" /><path d="M4 10h16v5H4z" /><path d="M6 16h12v4H6z" /></>,
  model: <><rect x="6" y="6" width="12" height="12" rx="2" /><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3" /><path d="M10 10h4v4h-4z" /></>,
  context: <><path d="M6 3h9l4 4v14H6z" /><path d="M15 3v5h4" /><path d="M9 12h7M9 16h7" /></>,
  seed: <><path d="M12 21V9" /><path d="M12 13c-4 0-7-2.4-7-6 4 0 7 2.4 7 6Z" /><path d="M12 17c4 0 7-2.4 7-6-4 0-7 2.4-7 6Z" /></>,
  "chevron-left": <path d="m15 18-6-6 6-6" />,
  "chevron-right": <path d="m9 18 6-6-6-6" />,
  send: <><path d="m12 19V5" /><path d="m6 11 6-6 6 6" /></>,
  more: <><circle cx="5" cy="12" r="1" /><circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" /></>,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6" /><path d="M12 7.5h.01" /></>,
  copy: <><rect x="8" y="8" width="11" height="12" rx="2" /><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h2" /></>,
  code: <><path d="m8 9-3 3 3 3" /><path d="m16 9 3 3-3 3" /><path d="m14 5-4 14" /></>,
  close: <><path d="m6 6 12 12" /><path d="m18 6-12 12" /></>
};

export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {paths[name]}
    </svg>
  );
}
