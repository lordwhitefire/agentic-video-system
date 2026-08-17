import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Icon } from "./Icon";
import { Modal } from "./Modal";
import { Markdown } from "./Markdown";
import {
  agents,
  subAgents,
  type Agent,
  type Message,
} from "../data/mock";
import { formatBytes } from "./Resources";

export function AgentIcon({ type, color }: { type: string; color: string }) {
  return (
    <div className="agent-icon" style={{ background: color }}>
      <Icon type={type as never} size={22} stroke={1.7} />
    </div>
  );
}

export function Conversation({
  messages,
  agent,
  approval,
  onApprove,
  onReject,
  handoff,
  onAcceptHandoff,
  onRejectHandoff,
  canStop,
  onStop,
}: {
  messages: Message[];
  agent: Agent;
  approval?: { id: string; question: string } | null;
  onApprove?: () => void;
  onReject?: () => void;
  handoff?: { run_id: string; target: string; prompt: string } | null;
  onAcceptHandoff?: () => void;
  onRejectHandoff?: () => void;
  canStop?: boolean;
  onStop?: () => void;
}) {
  const headerColor = agent.headerColor ?? agent.color;
  const containerRef = useRef<HTMLDivElement>(null);
  const nearBottomRef = useRef(true);

  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    nearBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  };

  useEffect(() => {
    const el = containerRef.current;
    if (el && nearBottomRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, approval, handoff, canStop]);

  return (
    <div className="conversation" ref={containerRef} onScroll={handleScroll}>
      {messages.map((msg, index) =>
        msg.role === "user" ? (
          <div className="message-row user-row" key={msg.id}>
            <div className="message user-message">
              <span className="message-label">You</span>
              {msg.paragraphs.map((p) => (
                <p key={p}>{p}</p>
              ))}
              <span className="timestamp">{msg.time}</span>
              <span className="double-check">
                <Icon type="check" size={15} />
                <Icon type="check" size={15} />
              </span>
            </div>
          </div>
        ) : (
          <div
            className={`message-row agent-row ${index === 0 ? "first-message" : "third-message"}`}
            key={msg.id}
          >
            <AgentIcon type={agent.icon} color={headerColor} />
            <div
              className={`message agent-message ${msg.question ? "question-message" : ""}`}
            >
              {msg.paragraphs.map((p) => (
                <Markdown key={p} text={p} />
              ))}
              <span className="timestamp">{msg.time}</span>
            </div>
          </div>
        ),
      )}

      {canStop && (
        <div className="message-row agent-row working-row">
          <AgentIcon type={agent.icon} color={headerColor} />
          <div className="message working-message">
            <span className="stop-spinner" aria-hidden="true" />
            <span>Agent is working…</span>
            <button type="button" className="secondary-button" onClick={onStop}>
              Stop
            </button>
          </div>
        </div>
      )}

      {approval && (
        <div className="control-card approval-card">
          <div className="control-card-head">
            <Icon type="info" size={15} />
            <strong>Approval required</strong>
          </div>
          <p className="control-card-body">{approval.question}</p>
          <div className="control-card-actions">
            <button type="button" className="primary-button" onClick={onApprove}>
              Approve
            </button>
            <button type="button" className="secondary-button" onClick={onReject}>
              Reject
            </button>
          </div>
        </div>
      )}

      {handoff && (
        <div className="control-card handoff-card">
          <div className="control-card-head">
            <Icon type="arrow" size={15} />
            <strong>Handoff request — {handoff.target}</strong>
          </div>
          <p className="control-card-body">{handoff.prompt}</p>
          <div className="control-card-actions">
            <button type="button" className="primary-button" onClick={onAcceptHandoff}>
              Accept
            </button>
            <button type="button" className="secondary-button" onClick={onRejectHandoff}>
              Reject
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export function Composer({
  value,
  setValue,
  onSend,
  placeholder,
  onAttach,
  onResource,
  onMedia,
  onLink,
  onMention,
}: {
  value: string;
  setValue: (value: string) => void;
  onSend: () => void;
  placeholder: string;
  onAttach: () => void;
  onResource: () => void;
  onMedia: () => void;
  onLink: () => void;
  onMention: () => void;
}) {
  const canSend = value.trim().length > 0;

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSend) onSend();
    }
  };

  return (
    <div className="composer">
      <textarea
        className="composer-input"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={2}
      />
      <div className="composer-bottom">
        <div className="composer-tools">
          <button type="button" title="Attach file" aria-label="Attach file" onClick={onAttach}>
            <Icon type="paperclip" size={19} />
          </button>
          <button
            type="button"
            title="Add project resource"
            aria-label="Add project resource"
            onClick={onResource}
          >
            <Icon type="file" size={19} />
          </button>
          <button type="button" title="Add media" aria-label="Add media" onClick={onMedia}>
            <Icon type="image" size={19} />
          </button>
          <button type="button" title="Add URL" aria-label="Add URL" onClick={onLink}>
            <Icon type="link" size={19} />
          </button>
          <button type="button" title="Mention agent" aria-label="Mention agent" onClick={onMention}>
            <Icon type="at" size={19} />
          </button>
        </div>
        <button
          type="button"
          className="send-button"
          disabled={!canSend}
          onClick={onSend}
          aria-label="Send"
        >
          <Icon type="send" size={22} />
        </button>
      </div>
    </div>
  );
}

export function AttachmentModal({
  open,
  onClose,
  onConfirm,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: (file: File) => void;
}) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  if (!open) return null;

  return (
    <Modal
      open={open}
      onClose={() => {
        setSelectedFile(null);
        onClose();
      }}
      title="Attach File"
      subtitle="Select a file to attach to this message."
      width={620}
    >
      <label className="drop-zone">
        <input
          hidden
          type="file"
          onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
        />
        <div className="drop-zone-icon">
          <Icon type="paperclip" size={24} />
        </div>
        <strong>Choose a file</strong>
        <span>Click to browse your device.</span>
      </label>
      {selectedFile && (
        <div className="selected-file">
          <Icon type="file" />
          <div>
            <strong>{selectedFile.name}</strong>
            <span>{formatBytes(selectedFile.size)}</span>
          </div>
        </div>
      )}
      <div className="modal-actions">
        <button
          type="button"
          className="secondary-button"
          onClick={() => {
            setSelectedFile(null);
            onClose();
          }}
        >
          Cancel
        </button>
        <button
          type="button"
          className="primary-button"
          disabled={!selectedFile}
          onClick={() => {
            if (!selectedFile) return;
            onConfirm(selectedFile);
            setSelectedFile(null);
          }}
        >
          Attach
        </button>
      </div>
    </Modal>
  );
}

export function MediaPicker({
  open,
  onClose,
  onSelect,
  media,
}: {
  open: boolean;
  onClose: () => void;
  onSelect: (item: string) => void;
  media: string[];
}) {
  if (!open) return null;
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Select Media"
      subtitle="Choose visual media from the project library."
      width={820}
    >
      <div className="media-grid">
        {media.map((item) => (
          <button
            type="button"
            className="media-card"
            key={item}
            onClick={() => onSelect(item)}
          >
            <div className="media-placeholder">
              <Icon type="image" size={28} />
            </div>
            <span>{item}</span>
          </button>
        ))}
      </div>
    </Modal>
  );
}

export function UrlModal({
  open,
  onClose,
  onAdd,
}: {
  open: boolean;
  onClose: () => void;
  onAdd: (url: string) => void;
}) {
  const [url, setUrl] = useState("");
  if (!open) return null;
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Add URL Reference"
      subtitle="Add a URL to the current conversation context."
      width={620}
    >
      <label className="field">
        <span>URL</span>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
        />
      </label>
      <div className="modal-actions">
        <button type="button" className="secondary-button" onClick={onClose}>
          Cancel
        </button>
        <button
          type="button"
          className="primary-button"
          disabled={!url.trim()}
          onClick={() => {
            onAdd(url.trim());
            setUrl("");
          }}
        >
          Add Reference
        </button>
      </div>
    </Modal>
  );
}

export function AgentMentionPicker({
  open,
  onClose,
  onSelect,
}: {
  open: boolean;
  onClose: () => void;
  onSelect: (agent: string) => void;
}) {
  const [query, setQuery] = useState("");
  if (!open) return null;

  const all = [
    ...agents.map((a) => ({ id: a.id, name: a.name, parent: null as string | null })),
    ...subAgents.map((s) => ({ id: s.id, name: s.name, parent: s.parent })),
  ].filter((a) => a.name.toLowerCase().includes(query.toLowerCase()));

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Mention Agent"
      subtitle="Select an agent to mention in the conversation."
      width={650}
    >
      <div className="mention-search">
        <Icon type="search" size={16} />
        <input
          placeholder="Search agents..."
          aria-label="Search agents"
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      <div className="mention-list">
        {all.length === 0 && <div className="empty-state">No agents match your search.</div>}
        {all.map((agent) => {
          const match = agents.find((a) => a.id === agent.id);
          return (
            <button
              type="button"
              className="mention-row"
              key={agent.id}
              onClick={() => onSelect(agent.name)}
            >
              <span className="mention-avatar" style={{ background: match?.color ?? "#3a4453" }}>
                {agent.name.charAt(0)}
              </span>
              <div>
                <strong>{agent.name}</strong>
                <span>
                  {agent.parent
                    ? `Sub-agent · ${agents.find((a) => a.id === agent.parent)?.name}`
                    : "Primary Agent"}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </Modal>
  );
}