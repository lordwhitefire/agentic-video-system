import { useState } from "react";
import { Icon } from "./Icon";
import { Modal } from "./Modal";
import {
  capabilityDetails,
  memoryOptions,
  workspaceContext,
  type Agent,
  type Workspace,
} from "../data/mock";
import {
  dayOf,
  type CapabilityRow,
  type LiveCapability,
  type LiveMemorySlot,
  type LiveSession,
  type ToolRow,
} from "../data/live";
import { DetailRow } from "./Resources";

export function AgentInfoDrawer({
  open,
  agent,
  workspaceCount,
  onClose,
}: {
  open: boolean;
  agent: Agent;
  workspaceCount: number;
  onClose: () => void;
}) {
  if (!open) return null;
  const headerColor = agent.headerColor ?? agent.color;

  return (
    <div className="drawer-backdrop" onMouseDown={onClose}>
      <aside className="avis-drawer" onMouseDown={(e) => e.stopPropagation()}>
        <header className="drawer-header">
          <div>
            <div className="eyebrow">ABOUT THIS AGENT</div>
            <h2>{agent.name}</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <Icon type="x" />
          </button>
        </header>
        <div className="drawer-body">
          <div className="drawer-agent-hero">
            <div className="agent-icon" style={{ background: headerColor }}>
              <Icon type={agent.icon as never} size={26} stroke={1.6} />
            </div>
            <div>
              <strong>{agent.name}</strong>
              <span>{agent.role}</span>
            </div>
          </div>
          <DetailRow label="Role" value={agent.role} />
          <DetailRow label="Status" value={agent.status} accent="green" />
          <DetailRow label="Workspace Access" value={`${workspaceCount} workspaces`} />
          <div className="drawer-note">{agent.about}</div>
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

export function AgentContextDrawer({
  open,
  agent,
  workspace,
  onClose,
}: {
  open: boolean;
  agent: Agent;
  workspace: Workspace;
  onClose: () => void;
}) {
  if (!open) return null;
  const ctx = workspaceContext[workspace.id] ?? workspaceContext["cinematic-brand-film"];

  return (
    <div className="drawer-backdrop" onMouseDown={onClose}>
      <aside className="avis-drawer" onMouseDown={(e) => e.stopPropagation()}>
        <header className="drawer-header">
          <div>
            <div className="eyebrow">WORKSPACE CONTEXT</div>
            <h2>{workspace.name}</h2>
            <p>Context available to {agent.name}.</p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <Icon type="x" />
          </button>
        </header>
        <div className="drawer-body">
          {(
            [
              ["Project Brief", ctx.brief],
              ["Audience Insights", ctx.audience],
              ["Brand Information", ctx.brand],
            ] as [string, string][]
          ).map(([label, value]) => (
            <div className="context-block" key={label}>
              <div className="context-block-title">{label}</div>
              <p>{value}</p>
            </div>
          ))}
          <div className="context-block">
            <div className="context-block-title">Past Discussions</div>
            {ctx.discussions.map((d: { title: string; day: string }) => (
              <div className="discussion-line" key={d.title}>
                <Icon type="clock" size={13} />
                <span>{d.title}</span>
                <small>{d.day}</small>
              </div>
            ))}
          </div>
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

export function AgentSettingsDrawer({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [model, setModel] = useState("Default");
  const [autonomy, setAutonomy] = useState("assisted");
  const [approval, setApproval] = useState(true);
  if (!open) return null;

  return (
    <div className="drawer-backdrop" onMouseDown={onClose}>
      <aside className="avis-drawer" onMouseDown={(e) => e.stopPropagation()}>
        <header className="drawer-header">
          <div>
            <div className="eyebrow">AGENT SETTINGS</div>
            <h2>Settings</h2>
            <p>Runtime preferences for the active agent.</p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <Icon type="x" />
          </button>
        </header>
        <div className="drawer-body">
          <label className="field">
            <span>Model</span>
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              <option>Default</option>
              <option>Fast</option>
              <option>Precise</option>
            </select>
          </label>
          <label className="field">
            <span>Autonomy</span>
            <select value={autonomy} onChange={(e) => setAutonomy(e.target.value)}>
              <option value="assisted">Assisted</option>
              <option value="autonomous">Autonomous</option>
            </select>
          </label>
          <button
            type="button"
            className={`toggle-row ${approval ? "on" : ""}`}
            onClick={() => setApproval(!approval)}
          >
            <span>
              <strong>Require human approval</strong>
              <small>Consequential actions are blocked until the human approves.</small>
            </span>
            <span className="toggle">
              <span className="toggle-knob" />
            </span>
          </button>
          <div className="drawer-note">Front-end only — no settings are persisted.</div>
        </div>
        <footer className="drawer-footer">
          <button type="button" className="secondary-button" onClick={onClose}>
            Cancel
          </button>
          <button type="button" className="primary-button" onClick={onClose}>
            Save Changes
          </button>
        </footer>
      </aside>
    </div>
  );
}

export function MemoryEditorModal({
  open,
  item,
  value,
  setValue,
  onClose,
  onSave,
}: {
  open: boolean;
  item: string;
  value: string;
  setValue: (value: string) => void;
  onClose: () => void;
  onSave: () => void;
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={item || "Memory & Context"}
      subtitle="Edit the workspace-specific context available to the active agent."
      width={760}
    >
      <textarea
        className="large-editor"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={`Enter ${item.toLowerCase()}...`}
      />
      <div className="modal-actions">
        <button type="button" className="secondary-button" onClick={onClose}>
          Cancel
        </button>
        <button type="button" className="primary-button" onClick={onSave}>
          Save Changes
        </button>
      </div>
    </Modal>
  );
}

export function PastDiscussionsModal({
  open,
  sessions,
  onClose,
  onActivate,
  onDelete,
  onNewSession,
  onCompact,
}: {
  open: boolean;
  sessions: LiveSession[] | null;
  onClose: () => void;
  onActivate?: (sessionId: string) => void;
  onDelete?: (sessionId: string) => void;
  onNewSession?: () => void;
  onCompact?: (sessionId: string) => void;
}) {
  const [query, setQuery] = useState("");
  if (!open) return null;
  const realSessions = (sessions ?? []).map((s) => ({
    id: s.id,
    title: s.title,
    day: dayOf(s.last_activity_at),
  }));
  const days = ["Today", "Yesterday", "Last Week", "Earlier"];
  const groups = days
    .map((day) => ({
      day,
      items: realSessions.filter(
        (d) => d.day === day && d.title.toLowerCase().includes(query.toLowerCase()),
      ),
    }))
    .filter((group) => group.items.length > 0);

  return (
    <Modal open={open} onClose={onClose} title="Past Discussions" width={620}>
      <div className="modal-actions modal-actions-top">
        <div className="mention-search">
          <Icon type="search" size={16} />
          <input
            placeholder="Search conversations..."
            aria-label="Search conversations"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        {onNewSession && (
          <button type="button" className="primary-button" onClick={onNewSession}>
            <Icon type="plus" size={16} />
            New Session
          </button>
        )}
      </div>
      {groups.length === 0 ? (
        <div className="empty-state">No history yet.</div>
      ) : (
        groups.map((group) => (
          <div className="discussion-group" key={group.day}>
            <div className="discussion-group-title">{group.day}</div>
            {group.items.map((d) => (
              <div className="discussion-row real" key={d.id}>
                <button
                  type="button"
                  className="discussion-row-main"
                  onClick={() => {
                    onClose();
                    onActivate?.(d.id);
                  }}
                >
                  <Icon type="chat" size={14} />
                  <span>{d.title}</span>
                </button>
                <div className="discussion-actions">
                  {onCompact && (
                    <button
                      type="button"
                      className="discussion-compact"
                      aria-label="Compact session"
                      title="Compact this conversation"
                      onClick={(e) => {
                        e.stopPropagation();
                        onCompact?.(d.id);
                      }}
                    >
                      <Icon type="compress" size={12} />
                    </button>
                  )}
                  {onDelete && (
                    <button
                      type="button"
                      className="discussion-delete"
                      aria-label="Delete session"
                      title="Delete session"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete?.(d.id);
                      }}
                    >
                      <Icon type="x" size={12} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))
      )}
    </Modal>
  );
}

export function CapabilityDetailModal({
  open,
  name,
  record,
  onClose,
}: {
  open: boolean;
  name: string;
  record?: LiveCapability;
  onClose: () => void;
}) {
  const [enabled, setEnabled] = useState(true);
  if (!open) return null;
  const fallback = capabilityDetails[name] ?? {
    description: "Capability of the active agent. Details are configured per agent.",
    tools: ["Research Tools", "Reference Finder"],
  };
  const recordDetail = record ?? null;
  const description = recordDetail?.description ?? fallback.description;
  const detailTools = recordDetail?.tools ?? fallback.tools;

  return (
    <Modal open={open} onClose={onClose} title="Capability" width={620}>
      <div className="detail-block">
        <div className="detail-block-title">CAPABILITY</div>
        <h3>{name}</h3>
      </div>
      <div className="detail-block">
        <div className="detail-block-title">Description</div>
        <p>{description}</p>
      </div>
      {recordDetail?.knowledge && (
        <div className="detail-block">
          <div className="detail-block-title">Know-How</div>
          <p>{recordDetail.knowledge}</p>
        </div>
      )}
      {recordDetail?.guidance && (
        <div className="detail-block">
          <div className="detail-block-title">Guidance</div>
          <p>{recordDetail.guidance}</p>
        </div>
      )}
      <button
        type="button"
        className={`toggle-row ${enabled ? "on" : ""}`}
        onClick={() => setEnabled(!enabled)}
      >
        <span>
          <strong>Enabled</strong>
        </span>
        <span className="toggle">
          <span className="toggle-knob" />
        </span>
      </button>
      <div className="detail-block">
        <div className="detail-block-title">Available Tools</div>
        <div className="detail-tools">
          {detailTools.map((tool) => (
            <span key={tool} className="context-pill">
              {tool}
            </span>
          ))}
        </div>
      </div>
      <div className="modal-actions">
        <button type="button" className="primary-button" onClick={onClose}>
          Close
        </button>
      </div>
    </Modal>
  );
}

export function ToolPreviewModal({
  open,
  name,
  doc,
  onClose,
}: {
  open: boolean;
  name: string;
  doc?: string;
  onClose: () => void;
}) {
  if (!open) return null;
  return (
    <Modal open={open} onClose={onClose} title="Tool Preview" width={560}>
      <div className="detail-block">
        <div className="detail-block-title">TOOL</div>
        <h3>{name}</h3>
        <p>This tool is available to the active agent.</p>
      </div>
      {doc && (
        <div className="detail-block">
          <div className="detail-block-title">What it does</div>
          <p>{doc}</p>
        </div>
      )}
      <div className="tool-status-box">
        <span className="tool-status-dot" />
        {doc ? "Backend connection: Connected" : "Backend connection: Not connected"}
      </div>
      <div className="modal-actions">
        <button type="button" className="primary-button" onClick={onClose}>
          Close
        </button>
      </div>
    </Modal>
  );
}

export function RightRail({
  agent,
  liveCapabilities,
  liveTools,
  liveAbout,
  liveSubAgents,
  liveMemorySlots,
  onAboutClick,
  onCapabilityClick,
  onMemoryClick,
  onToolClick,
}: {
  agent: Agent;
  liveCapabilities: CapabilityRow[];
  liveTools: ToolRow[];
  liveAbout: string | null;
  liveSubAgents: { id: string; name: string; parent: string; status: string }[];
  liveMemorySlots: LiveMemorySlot[] | null;
  onAboutClick: () => void;
  onCapabilityClick: (name: string) => void;
  onMemoryClick: (item: string) => void;
  onToolClick: (name: string) => void;
}) {
  return (
    <aside className="right-panel">
      <div className="right-card about-card">
        <h2>ABOUT THIS AGENT</h2>
        <button type="button" className="about-card-button" onClick={onAboutClick}>
          <p>You are interacting with the</p>
          <strong>{agent.name}.</strong>
          <p>{liveAbout ?? agent.about}</p>
          <p>I don&apos;t execute unless you ask me to in Build Mode.</p>
        </button>
      </div>

      <div className="right-card">
        <h2>CAPABILITIES</h2>
        <div className="capability-list">
          {liveCapabilities.map((item) => (
            <button
              type="button"
              className="capability-row"
              key={item.name}
              onClick={() => onCapabilityClick(item.name)}
            >
              <span className="purple-mini-icon">
                <Icon type="check" size={13} />
              </span>
              <span>{item.name}</span>
              <Icon type="chevronRight" size={13} className="row-chevron" />
            </button>
          ))}
        </div>
      </div>

      <div className="right-card memory-card">
        <h2>MEMORY &amp; CONTEXT</h2>
        {liveMemorySlots ? (
          <>
            {liveMemorySlots.map((slot) => (
              <button
                type="button"
                className="memory-row"
                key={slot.key}
                onClick={() => onMemoryClick(slot.label)}
              >
                <Icon type={slot.available ? "file" : "x"} size={16} />
                <span>{slot.label}</span>
                {slot.available ? (
                  <span className="green-check">✓</span>
                ) : (
                  <span className="memory-x">
                    <Icon type="x" size={11} />
                  </span>
                )}
              </button>
            ))}
            <button
              type="button"
              className="memory-row"
              onClick={() => onMemoryClick("Past Discussions")}
            >
              <Icon type="clock" size={16} />
              <span>Past Discussions</span>
              <Icon type="chevronRight" size={13} className="row-chevron" />
            </button>
          </>
        ) : (
          memoryOptions.map((item) => (
            <button
              type="button"
              className="memory-row"
              key={item}
              onClick={() => onMemoryClick(item)}
            >
              <Icon type={item === "Past Discussions" ? "clock" : "file"} size={16} />
              <span>{item}</span>
              {item === "Past Discussions" ? (
                <Icon type="chevronRight" size={13} className="row-chevron" />
              ) : (
                <span className="green-check">✓</span>
              )}
            </button>
          ))
        )}
      </div>

      <div className="right-card tools-card">
        <h2>TOOLS &amp; RESOURCES</h2>
        {liveTools.map((tool) => (
          <button
            type="button"
            className="tool-row"
            key={tool.name}
            onClick={() => onToolClick(tool.name)}
          >
            <span className="tool-left">
              <Icon type="panel" size={16} />
              {tool.name}
            </span>
            <span className="tool-external">
              <Icon type="external" size={13} />
            </span>
          </button>
        ))}
      </div>

      <div className="right-card right-card-subagents">
        <h2>SUB-AGENTS</h2>
        {(() => {
          const subs = liveSubAgents.filter((s) => s.parent === agent.id);
          if (subs.length === 0) return <p className="subagent-note">No sub-agents assigned.</p>;
          return subs.map((s) => (
            <div className="memory-row" key={s.id}>
              <Icon type="target" size={14} />
              <span>{s.name}</span>
              <span className="subagent-status">Available</span>
            </div>
          ));
        })()}
      </div>
    </aside>
  );
}