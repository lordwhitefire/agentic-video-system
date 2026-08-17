import { Icon } from "./Icon";
import { AgentIcon } from "./Chat";
import type { Agent } from "../data/mock";

const actionItems = [
  "Edit Agent",
  "Duplicate Agent",
  "View Configuration",
  "Manage Sub-agents",
  "Archive Agent",
];

export function AgentHeader({
  agent,
  onInfo,
  onContext,
  onSettings,
  moreOpen,
  setMoreOpen,
}: {
  agent: Agent;
  onInfo: () => void;
  onContext: () => void;
  onSettings: () => void;
  moreOpen: boolean;
  setMoreOpen: (open: boolean) => void;
}) {
  const headerColor = agent.headerColor ?? agent.color;

  return (
    <header className="agent-header">
      <div className="agent-header-left">
        <AgentIcon type={agent.icon} color={headerColor} />
        <div>
          <div className="agent-title-line">
            <h1>{agent.name}</h1>
            <span className="status-pill">
              <span />
              {agent.status}
            </span>
          </div>
          <p>{agent.role}</p>
        </div>
      </div>

      <div className="agent-actions">
        <button
          type="button"
          className="header-icon"
          title="Agent information"
          aria-label="Agent information"
          onClick={onInfo}
        >
          <Icon type="info" size={20} />
        </button>
        <button
          type="button"
          className="header-icon"
          title="Agent workspace context"
          aria-label="Agent workspace context"
          onClick={onContext}
        >
          <Icon type="panel" size={20} />
        </button>
        <button
          type="button"
          className="header-icon"
          title="Agent settings"
          aria-label="Agent settings"
          onClick={onSettings}
        >
          <Icon type="settings" size={20} />
        </button>
        <div className="more-wrap">
          <button
            type="button"
            className="header-icon"
            title="More actions"
            aria-label="More actions"
            aria-haspopup="menu"
            aria-expanded={moreOpen}
            onClick={() => setMoreOpen(!moreOpen)}
          >
            <Icon type="more" size={20} />
          </button>
          {moreOpen && (
            <>
              <div className="popover-backdrop" onMouseDown={() => setMoreOpen(false)} />
              <div className="popover-panel agent-actions-menu" role="menu">
                <div className="popover-title">Agent Actions</div>
                <div className="menu-divider" />
                {actionItems.slice(0, 4).map((item) => (
                  <button
                    type="button"
                    className="popover-item"
                    key={item}
                    onClick={() => setMoreOpen(false)}
                  >
                    {item}
                  </button>
                ))}
                <div className="menu-divider" />
                <button
                  type="button"
                  className="popover-item danger"
                  onClick={() => setMoreOpen(false)}
                >
                  {actionItems[4]}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}