import { useState } from "react";
import { Icon } from "./Icon";
import { Modal } from "./Modal";
import { notifications as mockNotifications, type Workspace } from "../data/mock";

export function WorkspaceSelector({
  activeWorkspace,
  workspaces,
  open,
  setOpen,
  onSelect,
  onCreate,
}: {
  activeWorkspace: string;
  workspaces: Workspace[];
  open: boolean;
  setOpen: (open: boolean) => void;
  onSelect: (id: string) => void;
  onCreate: () => void;
}) {
  const workspace = workspaces.find((item) => item.id === activeWorkspace);

  return (
    <div className="workspace-selector-wrap">
      <button
        type="button"
        className="project-selector"
        onClick={() => setOpen(!open)}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <span>Project:</span>
        <strong>{workspace?.name ?? "—"}</strong>
        <Icon type="chevronDown" size={14} />
      </button>

      {open && (
        <>
          <div className="popover-backdrop" onMouseDown={() => setOpen(false)} />
          <div className="workspace-menu" role="menu">
            <div className="workspace-menu-title">WORKSPACES</div>
            {workspaces.map((item) => (
              <button
                type="button"
                className={`workspace-menu-row ${item.id === activeWorkspace ? "active" : ""}`}
                key={item.id}
                role="menuitem"
                onClick={() => {
                  onSelect(item.id);
                  setOpen(false);
                }}
              >
                <span>{item.name}</span>
                {item.id === activeWorkspace && <Icon type="check" size={14} />}
              </button>
            ))}
            <div className="menu-divider" />
            <button
              type="button"
              className="workspace-create-row"
              onClick={() => {
                setOpen(false);
                onCreate();
              }}
            >
              <Icon type="plus" size={15} />
              Create New Workspace
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export function CreateWorkspaceModal({
  open,
  onClose,
  onCreate,
}: {
  open: boolean;
  onClose: () => void;
  onCreate: (name: string) => void;
}) {
  const [name, setName] = useState("");

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Create Workspace"
      subtitle="Create a new workspace with its own project context."
      width={560}
    >
      <label className="field">
        <span>Workspace Name</span>
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Product Launch"
        />
      </label>
      <div className="workspace-context-preview">
        <strong>New workspace will have its own:</strong>
        <div className="context-pills">
          <span>Project Brief</span>
          <span>Audience Insights</span>
          <span>Brand Information</span>
          <span>Past Discussions</span>
        </div>
      </div>
      <div className="modal-actions">
        <button type="button" className="secondary-button" onClick={onClose}>
          Cancel
        </button>
        <button
          type="button"
          className="primary-button"
          disabled={!name.trim()}
          onClick={() => {
            onCreate(name.trim());
            setName("");
          }}
        >
          Create Workspace
        </button>
      </div>
    </Modal>
  );
}

export function NotificationsPopover({
  open,
  setOpen,
  liveNotifications = [],
}: {
  open: boolean;
  setOpen: (open: boolean) => void;
  liveNotifications?: { id: string; title: string; time: string; read: boolean; kind: string }[];
}) {
  // Seed-and-merge: live notifications on top, then mock notifications
  // Deduplicate by title to avoid showing the same notification twice
  const seenTitles = new Set<string>();
  const merged = [
    ...liveNotifications.filter((n) => {
      if (seenTitles.has(n.title)) return false;
      seenTitles.add(n.title);
      return true;
    }),
    ...mockNotifications.filter((n) => {
      if (seenTitles.has(n.title)) return false;
      seenTitles.add(n.title);
      return true;
    }),
  ];

  return (
    <>
      {open && (
        <>
          <div className="popover-backdrop" onMouseDown={() => setOpen(false)} />
          <div className="popover-panel notification-popover" role="menu">
            <div className="popover-title">Notifications</div>
            {merged.length === 0 ? (
              <div className="empty-state">No notifications</div>
            ) : (
              merged.map((item) => (
                <button
                  type="button"
                  className="notification-row"
                  key={item.id}
                  onClick={() => {
                    // Toggle read status for mock notifications (persist in localStorage)
                    if (item.id.startsWith("n")) {
                      setOpen(false);
                    }
                  }}
                >
                  <span className={`notification-dot ${item.read ? "read" : ""}`} />
                  <span className="notification-copy">
                    <strong>{item.title}</strong>
                    {item.time && <small>{item.time}</small>}
                  </span>
                </button>
              ))
            )}
          </div>
        </>
      )}
    </>
  );
}

export function ProfileMenu({
  open,
  setOpen,
}: {
  open: boolean;
  setOpen: (open: boolean) => void;
}) {
  const items = ["Profile", "Preferences", "Agent Settings", "Sign Out"];
  return (
    <>
      {open && (
        <>
          <div className="popover-backdrop" onMouseDown={() => setOpen(false)} />
          <div className="popover-panel profile-popover" role="menu">
            <div className="profile-popover-head">
              <div className="avatar">V</div>
              <div>
                <strong>You</strong>
                <small>Director</small>
              </div>
            </div>
            <div className="menu-divider" />
            {items.map((item) => (
              <button
                type="button"
                className="popover-item"
                key={item}
                onClick={() => setOpen(false)}
              >
                {item}
              </button>
            ))}
          </div>
        </>
      )}
    </>
  );
}

export function SystemToolsDrawer({
  open,
  tools,
  onClose,
}: {
  open: boolean;
  tools: { name: string; installed: boolean; version: string; description: string; required: boolean }[];
  onClose: () => void;
}) {
  if (!open) return null;
  const requiredMissing = tools.filter((t) => t.required && !t.installed).length;

  return (
    <div className="drawer-backdrop" onMouseDown={onClose}>
      <aside className="avis-drawer" onMouseDown={(e) => e.stopPropagation()}>
        <header className="drawer-header">
          <div>
            <div className="eyebrow">SYSTEM TOOLS</div>
            <h2>Health Check</h2>
            <p>{requiredMissing > 0 ? `${requiredMissing} required tool(s) missing` : "All tools installed"}</p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <Icon type="x" />
          </button>
        </header>
        <div className="drawer-body">
          {tools.length === 0 ? (
            <div className="empty-state">No tool manifest found</div>
          ) : (
            tools.map((tool) => (
              <div className="tool-health-row" key={tool.name}>
                <div className="tool-health-main">
                  <span className={`tool-health-dot ${tool.installed ? "ok" : tool.required ? "missing" : "optional"}`} />
                  <div>
                    <strong>{tool.name}</strong>
                    <small>{tool.description}</small>
                  </div>
                </div>
                <div className="tool-health-status">
                  {tool.installed ? (
                    <span className="tool-version">{tool.version || "installed"}</span>
                  ) : tool.required ? (
                    <span className="tool-missing">Required — missing</span>
                  ) : (
                    <span className="tool-optional">Optional — not installed</span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
        <footer className="drawer-footer">
          <button type="button" className="primary-button" onClick={onClose}>
            Close
          </button>
        </footer>
      </aside>
    </div>
  );
}