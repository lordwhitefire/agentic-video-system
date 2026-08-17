import { useEffect, type ReactNode } from "react";
import { Icon } from "./Icon";

export function useEscape(active: boolean, onEscape: () => void) {
  useEffect(() => {
    if (!active) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onEscape();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [active, onEscape]);
}

export function Modal({
  open,
  title,
  subtitle,
  onClose,
  children,
  width = 720,
}: {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
  width?: number;
}) {
  useEscape(open, onClose);
  if (!open) return null;

  return (
    <div className="avis-overlay" onMouseDown={onClose}>
      <section
        className="avis-modal"
        style={{ width }}
        onMouseDown={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <header className="avis-modal-header">
          <div>
            <h2>{title}</h2>
            {subtitle && <p>{subtitle}</p>}
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <Icon type="x" />
          </button>
        </header>
        <div className="avis-modal-body">{children}</div>
      </section>
    </div>
  );
}