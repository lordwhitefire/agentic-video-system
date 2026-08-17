import { useMemo, useState } from "react";
import { Icon } from "./Icon";
import { agents, subAgents, type SubAgent } from "../data/mock";

export function AgentDirectory({
  open,
  onClose,
  onSelectAgent,
  onNewAgent,
  extraPrimaryAgents,
  extraSubAgents,
}: {
  open: boolean;
  onClose: () => void;
  onSelectAgent: (agentId: string) => void;
  onNewAgent: () => void;
  extraPrimaryAgents: { name: string; status: string }[];
  extraSubAgents: SubAgent[];
}) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");

  const primaryList = useMemo(() => {
    const all = [...agents.map((a) => ({ name: a.name, status: a.status })), ...extraPrimaryAgents];
    const q = query.toLowerCase();
    return all.filter(
      (a) =>
        a.name.toLowerCase().includes(q) &&
        (filter === "all" || (filter === "primary" && a.status !== "Available")),
    );
  }, [query, filter, extraPrimaryAgents]);

  const subList = useMemo(() => {
    const all = [...subAgents, ...extraSubAgents];
    const q = query.toLowerCase();
    return all.filter(
      (a) =>
        a.name.toLowerCase().includes(q) &&
        (filter === "all" || (filter === "sub" && a.status === "Available")),
    );
  }, [query, filter, extraSubAgents]);

  if (!open) return null;

  return (
    <div className="avis-overlay" onMouseDown={onClose}>
      <section
        className="directory-panel"
        onMouseDown={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="All Agents Directory"
      >
        <header className="directory-header">
          <div>
            <div className="eyebrow">AGENT NETWORK</div>
            <h2>All Agents Directory</h2>
            <p>Manage primary agents and specialized sub-agents.</p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <Icon type="x" />
          </button>
        </header>

        <div className="directory-toolbar">
          <div className="search-box">
            <Icon type="search" size={16} />
            <input
              placeholder="Search agents..."
              aria-label="Search agents"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <div className="filter-group">
            {(["all", "primary", "sub"] as const).map((f) => (
              <button
                type="button"
                key={f}
                className={filter === f ? "filter-chip active" : "filter-chip"}
                onClick={() => setFilter(f)}
              >
                {f === "all" ? "All" : f === "primary" ? "Primary" : "Sub"}
              </button>
            ))}
          </div>
          <button type="button" className="primary-button" onClick={onNewAgent}>
            <Icon type="plus" size={16} />
            New Agent
          </button>
        </div>

        <div className="directory-body">
          <section className="directory-section">
            <div className="directory-section-title">
              <span>PRIMARY AGENTS</span>
              <span>{primaryList.length}</span>
            </div>
            {primaryList.length === 0 && <div className="empty-state">No primary agents found.</div>}
            {primaryList.map((agent, index) => {
              const match = agents[index] ?? null;
              return (
                <button
                  type="button"
                  className="directory-row"
                  key={`${agent.name}-${index}`}
                  onClick={() => match && onSelectAgent(match.id)}
                >
                  <span className="directory-avatar" style={{ background: match?.color ?? "#3a4453" }}>
                    <Icon type={(match?.icon ?? "target") as never} size={15} stroke={1.6} />
                  </span>
                  <span className="directory-row-copy">
                    <strong>{agent.name}</strong>
                    <small>Primary Agent</small>
                  </span>
                  <span className="directory-row-status">{agent.status}</span>
                </button>
              );
            })}
          </section>

          <section className="directory-section">
            <div className="directory-section-title">
              <span>SUB-AGENTS</span>
              <span>{subList.length}</span>
            </div>
            {subList.length === 0 && <div className="empty-state">No sub-agents found.</div>}
            {subList.map((agent) => (
              <button
                type="button"
                className="directory-row"
                key={agent.id}
                onClick={() => {
                  const parent = agents.find((a) => a.id === agent.parent);
                  if (parent) onSelectAgent(parent.id);
                  onClose();
                }}
              >
                <span className="directory-avatar sub">
                  {agent.name.charAt(0)}
                </span>
                <span className="directory-row-copy">
                  <strong>{agent.name}</strong>
                  <small>Sub-agent · {agents.find((a) => a.id === agent.parent)?.name ?? "—"}</small>
                </span>
                <span className="directory-row-status">{agent.status}</span>
              </button>
            ))}
          </section>
        </div>
      </section>
    </div>
  );
}