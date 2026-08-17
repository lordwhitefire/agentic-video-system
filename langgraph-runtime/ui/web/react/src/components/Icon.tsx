export type IconName =
  | "target"
  | "bulb"
  | "script"
  | "image"
  | "calendar"
  | "folder"
  | "chat"
  | "upload"
  | "info"
  | "panel"
  | "settings"
  | "more"
  | "bell"
  | "chevron"
  | "chevronDown"
  | "chevronRight"
  | "arrow"
  | "check"
  | "clock"
  | "file"
  | "search"
  | "link"
  | "at"
  | "paperclip"
  | "send"
  | "external"
  | "plus"
  | "x";

export function Icon({
  type,
  size = 18,
  stroke = 1.8,
  className,
}: {
  type: IconName;
  size?: number;
  stroke?: number;
  className?: string;
}) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: stroke,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true as const,
    className,
  };

  switch (type) {
    case "target":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8.5" />
          <circle cx="12" cy="12" r="5" />
          <circle cx="12" cy="12" r="1.5" />
          <path d="M12 3.5V1.8M20.5 12H22.2M12 20.5v1.7M3.5 12H1.8" />
          <path d="m16.8 7.2 2.8-2.8" />
        </svg>
      );
    case "bulb":
      return (
        <svg {...common}>
          <path d="M9 18h6" />
          <path d="M10 21h4" />
          <path d="M8.4 14.5A6 6 0 1 1 15.7 14c-.9.7-1.4 1.8-1.5 3H9.8c-.1-1-.5-1.8-1.4-2.5Z" />
          <path d="M12 3v2" />
        </svg>
      );
    case "script":
      return (
        <svg {...common}>
          <rect x="5" y="3.5" width="14" height="17" rx="2" />
          <path d="M8.5 8h7M8.5 12h7M8.5 16h4" />
        </svg>
      );
    case "image":
      return (
        <svg {...common}>
          <rect x="3" y="4" width="18" height="16" rx="2" />
          <circle cx="8.5" cy="9" r="1.5" />
          <path d="m5 17 4.5-4.5 3.2 3 2.3-2.3L20 17" />
        </svg>
      );
    case "calendar":
      return (
        <svg {...common}>
          <rect x="3" y="4.5" width="18" height="16" rx="2" />
          <path d="M7 2.5v4M17 2.5v4M3 9h18" />
          <path d="M8 13h2M14 13h2M8 17h2M14 17h2" />
        </svg>
      );
    case "folder":
      return (
        <svg {...common}>
          <path d="M3 6.5A2.5 2.5 0 0 1 5.5 4H10l2 2h6.5A2.5 2.5 0 0 1 21 8.5v9A2.5 2.5 0 0 1 18.5 20h-13A2.5 2.5 0 0 1 3 17.5Z" />
        </svg>
      );
    case "chat":
      return (
        <svg {...common}>
          <path d="M5 4h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-7l-5 3v-3H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z" />
          <path d="M7.5 9h9M7.5 12.5h6" />
        </svg>
      );
    case "upload":
      return (
        <svg {...common}>
          <path d="M12 15V4" />
          <path d="m8 8 4-4 4 4" />
          <path d="M5 14v5h14v-5" />
        </svg>
      );
    case "info":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 10.5v6" />
          <circle cx="12" cy="7.2" r=".7" fill="currentColor" stroke="none" />
        </svg>
      );
    case "panel":
      return (
        <svg {...common}>
          <rect x="4" y="4" width="16" height="16" rx="2" />
          <path d="M8 8h8M8 12h8M8 16h5" />
        </svg>
      );
    case "settings":
      return (
        <svg {...common}>
          <path d="M12 3.5a2 2 0 0 1 2 2v.3a6.8 6.8 0 0 1 1.8 1l.3-.2a2 2 0 1 1 2 3.5l-.3.2c.1.4.2.9.2 1.7s-.1 1.3-.2 1.7l.3.2a2 2 0 1 1-2 3.5l-.3-.2a6.8 6.8 0 0 1-1.8 1v.3a2 2 0 1 1-4 0v-.3a6.8 6.8 0 0 1-1.8-1l-.3.2a2 2 0 1 1-2-3.5l.3-.2A6.8 6.8 0 0 1 4 12.2a6.8 6.8 0 0 1 .2-1.7l-.3-.2a2 2 0 1 1 2-3.5l.3.2a6.8 6.8 0 0 1 1.8-1v-.3a2 2 0 0 1 4 0Z" />
          <circle cx="12" cy="12" r="2.7" />
        </svg>
      );
    case "more":
      return (
        <svg {...common}>
          <circle cx="6" cy="12" r="1" fill="currentColor" />
          <circle cx="12" cy="12" r="1" fill="currentColor" />
          <circle cx="18" cy="12" r="1" fill="currentColor" />
        </svg>
      );
    case "bell":
      return (
        <svg {...common}>
          <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 8.5h18C21 16 18 16 18 9Z" />
          <path d="M10 21h4" />
        </svg>
      );
    case "chevron":
      return (
        <svg {...common}>
          <path d="m7 9 5 5 5-5" />
        </svg>
      );
    case "chevronDown":
      return (
        <svg {...common}>
          <path d="m6 9 6 6 6-6" />
        </svg>
      );
    case "chevronRight":
      return (
        <svg {...common}>
          <path d="m9 6 6 6-6 6" />
        </svg>
      );
    case "arrow":
      return (
        <svg {...common}>
          <path d="M5 12h14M13 6l6 6-6 6" />
        </svg>
      );
    case "check":
      return (
        <svg {...common}>
          <path d="m5 12 4 4L19 6" />
        </svg>
      );
    case "clock":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 2" />
        </svg>
      );
    case "file":
      return (
        <svg {...common}>
          <path d="M6 3h8l4 4v14H6z" />
          <path d="M14 3v5h4M9 12h6M9 16h6" />
        </svg>
      );
    case "search":
      return (
        <svg {...common}>
          <circle cx="10.5" cy="10.5" r="6.5" />
          <path d="m16 16 4.5 4.5" />
        </svg>
      );
    case "link":
      return (
        <svg {...common}>
          <path d="M10 13.5 14.5 9" />
          <path d="M8 17H6.5a4 4 0 0 1 0-8H10M14 7h3.5a4 4 0 0 1 0 8H14" />
        </svg>
      );
    case "at":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="3.2" />
          <path d="M15.2 12v1.2c0 1.5 1 2.3 2.1 2.3 2.1 0 3.7-1.7 3.7-4.3 0-5-3.8-8.7-8.8-8.7A9.5 9.5 0 0 0 2.7 12c0 5.2 4.2 9.3 9.5 9.3 2.4 0 4.6-.8 6.2-2" />
        </svg>
      );
    case "paperclip":
      return (
        <svg {...common}>
          <path d="m9 12.5 6.5-6.5a3 3 0 0 1 4.2 4.2l-8.4 8.4a5 5 0 0 1-7.1-7.1L12 3.7" />
        </svg>
      );
    case "send":
      return (
        <svg {...common} strokeWidth={2}>
          <path d="m4 4 16 8-16 8 3-8-3-8Z" />
          <path d="M7 12h13" />
        </svg>
      );
    case "external":
      return (
        <svg {...common}>
          <path d="M14 4h6v6M20 4l-9 9" />
          <path d="M18 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5" />
        </svg>
      );
    case "plus":
      return (
        <svg {...common}>
          <path d="M12 5v14M5 12h14" />
        </svg>
      );
    case "x":
      return (
        <svg {...common}>
          <path d="m6 6 12 12M18 6 6 18" />
        </svg>
      );
    default:
      return <span />;
  }
}