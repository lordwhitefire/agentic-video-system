import { useState } from "react";
import { Icon } from "./Icon";
import { useEscape } from "./Modal";
import {
  capabilityOptions,
  memoryOptions,
  resourceCategories,
  subAgents,
  toolOptions,
} from "../data/mock";

export type NewAgent = {
  type: "primary" | "sub";
  name: string;
  description: string;
  role: string;
  capabilities: string[];
  tools: string[];
  projectResources: string[];
  memoryContext: string[];
  allowedSubAgents: string[];
  callableBy: string[];
  model: string;
  autonomy: string;
  approvalRequired: boolean;
};

export const emptyNewAgent: NewAgent = {
  type: "primary",
  name: "",
  description: "",
  role: "",
  capabilities: [],
  tools: [],
  projectResources: [],
  memoryContext: [],
  allowedSubAgents: [],
  callableBy: [],
  model: "Default",
  autonomy: "assisted",
  approvalRequired: true,
};

const tabs: [string, string][] = [
  ["type", "Agent Type"],
  ["about", "About"],
  ["capabilities", "Capabilities"],
  ["tools", "Tools & Resources"],
  ["resources", "Project Resources"],
  ["memory", "Memory & Context"],
  ["relationships", "Agent Relationships"],
  ["settings", "Settings"],
];

function StepHeading({ title, description }: { title: string; description: string }) {
  return (
    <div className="step-heading">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}

function MultiSelectStep({
  title,
  description,
  options,
  selected,
  onChange,
}: {
  title: string;
  description: string;
  options: string[];
  selected: string[];
  onChange: (values: string[]) => void;
}) {
  const toggle = (option: string) =>
    onChange(
      selected.includes(option)
        ? selected.filter((item) => item !== option)
        : [...selected, option],
    );

  return (
    <div className="step-content">
      <StepHeading title={title} description={description} />
      <div className="selection-list">
        {options.map((option) => {
          const checked = selected.includes(option);
          return (
            <button
              type="button"
              key={option}
              className={`selection-row ${checked ? "selected" : ""}`}
              onClick={() => toggle(option)}
            >
              <span className={`selection-check ${checked ? "checked" : ""}`}>
                {checked && <Icon type="check" size={14} />}
              </span>
              <span>{option}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function AgentRelationshipsStep({
  agent,
  setAgent,
}: {
  agent: NewAgent;
  setAgent: (updater: (a: NewAgent) => NewAgent) => void;
}) {
  return (
    <div className="step-content">
      <StepHeading
        title="Agent Relationships"
        description="Define which sub-agents this agent may call, and who may call this agent."
      />
      <div className="relationship-groups">
        <div className="relationship-group">
          <div className="relationship-group-title">Allowed Sub-agents</div>
          {agent.type === "primary" ? (
            <div className="selection-list">
              {subAgents.map((sub) => {
                const checked = agent.allowedSubAgents.includes(sub.id);
                return (
                  <button
                    type="button"
                    key={sub.id}
                    className={`selection-row ${checked ? "selected" : ""}`}
                    onClick={() =>
                      setAgent((a) => ({
                        ...a,
                        allowedSubAgents: checked
                          ? a.allowedSubAgents.filter((id) => id !== sub.id)
                          : [...a.allowedSubAgents, sub.id],
                      }))
                    }
                  >
                    <span className={`selection-check ${checked ? "checked" : ""}`}>
                      {checked && <Icon type="check" size={14} />}
                    </span>
                    <span>{sub.name}</span>
                  </button>
                );
              })}
            </div>
          ) : (
            <p className="relationship-note">
              Sub-agents cannot call other agents. Choose who can call this agent below.
            </p>
          )}
        </div>

        <div className="relationship-group">
          <div className="relationship-group-title">Callable By (Primary Agents)</div>
          <div className="selection-list">
            {["Video Strategy Agent", "Creative Director Agent", "Scene Planning Agent"].map(
              (name) => {
                const checked = agent.callableBy.includes(name);
                return (
                  <button
                    type="button"
                    key={name}
                    className={`selection-row ${checked ? "selected" : ""}`}
                    onClick={() =>
                      setAgent((a) => ({
                        ...a,
                        callableBy: checked
                          ? a.callableBy.filter((item) => item !== name)
                          : [...a.callableBy, name],
                      }))
                    }
                  >
                    <span className={`selection-check ${checked ? "checked" : ""}`}>
                      {checked && <Icon type="check" size={14} />}
                    </span>
                    <span>{name}</span>
                  </button>
                );
              },
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function AgentSettingsStep({
  agent,
  setAgent,
}: {
  agent: NewAgent;
  setAgent: (updater: (a: NewAgent) => NewAgent) => void;
}) {
  return (
    <div className="step-content">
      <StepHeading
        title="Settings"
        description="Model, autonomy level, and approval behavior for the new agent."
      />
      <div className="field-row">
        <label className="field">
          <span>Model</span>
          <select
            value={agent.model}
            onChange={(e) => setAgent((a) => ({ ...a, model: e.target.value }))}
          >
            <option>Default</option>
            <option>Fast</option>
            <option>Precise</option>
          </select>
        </label>
        <label className="field">
          <span>Autonomy</span>
          <select
            value={agent.autonomy}
            onChange={(e) => setAgent((a) => ({ ...a, autonomy: e.target.value }))}
          >
            <option value="assisted">Assisted</option>
            <option value="autonomous">Autonomous</option>
          </select>
        </label>
      </div>
      <button
        type="button"
        className={`toggle-row ${agent.approvalRequired ? "on" : ""}`}
        onClick={() => setAgent((a) => ({ ...a, approvalRequired: !a.approvalRequired }))}
      >
        <span>
          <strong>Require human approval</strong>
          <small>Consequential actions are blocked until the human approves.</small>
        </span>
        <span className="toggle">
          <span className="toggle-knob" />
        </span>
      </button>
    </div>
  );
}

export function CreateAgentModal({
  open,
  onClose,
  activeTab,
  setActiveTab,
  agent,
  setAgent,
  onCreate,
}: {
  open: boolean;
  onClose: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  agent: NewAgent;
  setAgent: (updater: (a: NewAgent) => NewAgent) => void;
  onCreate: () => void;
}) {
  useEscape(open, onClose);
  if (!open) return null;

  return (
    <div className="avis-overlay" onMouseDown={onClose}>
      <section
        className="agent-create-modal"
        onMouseDown={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Create New Agent"
      >
        <header className="avis-modal-header">
          <div>
            <div className="eyebrow">AGENT NETWORK</div>
            <h2>Create New Agent</h2>
            <p>Configure the agent&apos;s identity, access, context and behavior.</p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <Icon type="x" />
          </button>
        </header>

        <div className="agent-create-layout">
          <nav className="agent-create-tabs">
            {tabs.map(([id, label]) => (
              <button
                type="button"
                key={id}
                className={activeTab === id ? "create-tab active" : "create-tab"}
                onClick={() => setActiveTab(id)}
              >
                <span>{label}</span>
                <Icon type="chevronRight" size={14} />
              </button>
            ))}
          </nav>

          <main className="agent-create-content">
            {activeTab === "type" && (
              <div className="step-content">
                <StepHeading
                  title="Agent Type"
                  description="Choose whether this agent is autonomous or callable by another agent."
                />
                <div className="type-grid">
                  <button
                    type="button"
                    className={`type-card ${agent.type === "primary" ? "selected" : ""}`}
                    onClick={() => setAgent((a) => ({ ...a, type: "primary" }))}
                  >
                    <div className="type-icon">A</div>
                    <strong>Primary Agent</strong>
                    <span>Autonomous agent responsible for a major area of work.</span>
                  </button>
                  <button
                    type="button"
                    className={`type-card ${agent.type === "sub" ? "selected" : ""}`}
                    onClick={() => setAgent((a) => ({ ...a, type: "sub" }))}
                  >
                    <div className="type-icon">S</div>
                    <strong>Sub-agent</strong>
                    <span>Specialized helper that can be called by primary agents.</span>
                  </button>
                </div>
              </div>
            )}

            {activeTab === "about" && (
              <div className="step-content">
                <StepHeading
                  title="About This Agent"
                  description="Define the identity and responsibility displayed in the workspace."
                />
                <label className="field">
                  <span>Agent Name</span>
                  <input
                    value={agent.name}
                    onChange={(e) => setAgent((a) => ({ ...a, name: e.target.value }))}
                    placeholder="e.g. Audience Analyzer"
                  />
                </label>
                <label className="field">
                  <span>Short Description</span>
                  <input
                    value={agent.description}
                    onChange={(e) => setAgent((a) => ({ ...a, description: e.target.value }))}
                    placeholder="What is this agent for?"
                  />
                </label>
                <label className="field">
                  <span>Agent Role / Specialization</span>
                  <textarea
                    rows={7}
                    value={agent.role}
                    onChange={(e) => setAgent((a) => ({ ...a, role: e.target.value }))}
                    placeholder="I specialize in..."
                  />
                </label>
              </div>
            )}

            {activeTab === "capabilities" && (
              <MultiSelectStep
                title="Capabilities"
                description="Choose what this agent is designed to do."
                options={capabilityOptions}
                selected={agent.capabilities}
                onChange={(values) => setAgent((a) => ({ ...a, capabilities: values }))}
              />
            )}

            {activeTab === "tools" && (
              <MultiSelectStep
                title="Tools & Resources"
                description="Choose the tools this agent can access."
                options={toolOptions}
                selected={agent.tools}
                onChange={(values) => setAgent((a) => ({ ...a, tools: values }))}
              />
            )}

            {activeTab === "resources" && (
              <MultiSelectStep
                title="Project Resources"
                description="Choose the project resource categories available to the agent."
                options={resourceCategories}
                selected={agent.projectResources}
                onChange={(values) => setAgent((a) => ({ ...a, projectResources: values }))}
              />
            )}

            {activeTab === "memory" && (
              <MultiSelectStep
                title="Memory & Context"
                description="Choose workspace context this agent can access."
                options={memoryOptions}
                selected={agent.memoryContext}
                onChange={(values) => setAgent((a) => ({ ...a, memoryContext: values }))}
              />
            )}

            {activeTab === "relationships" && (
              <AgentRelationshipsStep agent={agent} setAgent={setAgent} />
            )}

            {activeTab === "settings" && <AgentSettingsStep agent={agent} setAgent={setAgent} />}
          </main>
        </div>

        <footer className="agent-create-footer">
          <button type="button" className="secondary-button" onClick={onClose}>
            Cancel
          </button>
          <button type="button" className="primary-button" onClick={onCreate}>
            Create Agent
          </button>
        </footer>
      </section>
    </div>
  );
}

export function useCreateAgentFlow() {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState("type");
  const [agent, setAgent] = useState<NewAgent>(emptyNewAgent);

  const openModal = () => {
    setAgent(emptyNewAgent);
    setTab("type");
    setOpen(true);
  };

  return { open, setOpen, openModal, tab, setTab, agent, setAgent };
}