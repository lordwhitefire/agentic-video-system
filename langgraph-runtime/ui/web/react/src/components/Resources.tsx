import { useState, type ReactNode } from "react";
import { Icon } from "./Icon";
import { Modal } from "./Modal";
import { resourceCategories } from "../data/mock";

export function formatBytes(bytes: number) {
  if (!bytes) return "0 KB";
  const mb = bytes / 1024 / 1024;
  if (mb >= 1) return `${mb.toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export function ResourceSection({
  title,
  items,
  expanded,
  onToggle,
  onAdd,
  onSelect,
}: {
  title: string;
  items: string[];
  expanded: boolean;
  onToggle: () => void;
  onAdd: () => void;
  onSelect: (item: string) => void;
}) {
  return (
    <section className={`resource-section ${expanded ? "expanded" : ""}`}>
      <button type="button" className="resource-heading" onClick={onToggle}>
        <span className="resource-heading-left">
          <Icon type="file" size={15} />
          <span>{title}</span>
        </span>
        <Icon type={expanded ? "chevronDown" : "chevronRight"} size={14} />
      </button>
      {expanded && (
        <div className="resource-items">
          <button type="button" className="resource-add" onClick={onAdd}>
            <Icon type="plus" size={14} />
            <span>Add Resource</span>
          </button>
          <div className="resource-scroll">
            {items.map((item) => (
              <button
                type="button"
                className="resource-item"
                key={item}
                onClick={() => onSelect(item)}
              >
                <Icon type="file" size={13} />
                <span>{item}</span>
                <Icon type="chevronRight" size={12} />
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

export function ProjectResources({
  expandedMap,
  onToggle,
  onAddResource,
  onSelectResource,
  files,
}: {
  expandedMap: Record<string, boolean>;
  onToggle: (category: string) => void;
  onAddResource: (category: string) => void;
  onSelectResource: (category: string, item: string) => void;
  files: Record<string, string[]>;
}) {
  return (
    <div className="resource-list">
      {resourceCategories.map((category) => (
        <ResourceSection
          key={category}
          title={category}
          items={files[category] ?? []}
          expanded={!!expandedMap[category]}
          onToggle={() => onToggle(category)}
          onAdd={() => onAddResource(category)}
          onSelect={(item) => onSelectResource(category, item)}
        />
      ))}
    </div>
  );
}

export function AddResourceModal({
  open,
  category,
  onClose,
  onConfirm,
}: {
  open: boolean;
  category: string | null;
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
      title="Add Resource"
      subtitle={`Select a file to add to ${category ?? "this"} collection.`}
      width={620}
    >
      <div
        className="drop-zone"
        role="button"
        tabIndex={0}
        onClick={() => document.getElementById("resource-file-input")?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter") document.getElementById("resource-file-input")?.click();
        }}
      >
        <div className="drop-zone-icon">
          <Icon type="paperclip" size={22} />
        </div>
        <strong>Select a file</strong>
        <span>Choose a file from your device.</span>
        <input
          id="resource-file-input"
          type="file"
          hidden
          onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
        />
      </div>

      {selectedFile && (
        <div className="selected-file">
          <Icon type="file" />
          <div>
            <strong>{selectedFile.name}</strong>
            <span>{formatBytes(selectedFile.size)}</span>
          </div>
          <button
            type="button"
            className="icon-button small"
            onClick={() => setSelectedFile(null)}
            aria-label="Remove file"
          >
            <Icon type="x" size={15} />
          </button>
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
          Add Resource
        </button>
      </div>
    </Modal>
  );
}

export function ResourceDetailDrawer({
  open,
  category,
  item,
  agentName,
  workspaceName,
  onClose,
}: {
  open: boolean;
  category: string | null;
  item: string | null;
  agentName: string;
  workspaceName: string;
  onClose: () => void;
}) {
  if (!open || !item) return null;
  const ext = item.includes(".") ? item.split(".").pop()!.toUpperCase() : "Template";

  return (
    <div className="drawer-backdrop" onMouseDown={onClose}>
      <aside className="avis-drawer" onMouseDown={(e) => e.stopPropagation()}>
        <header className="drawer-header">
          <div>
            <div className="eyebrow">RESOURCE</div>
            <h2>{item}</h2>
            <p>{category}</p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <Icon type="x" />
          </button>
        </header>
        <div className="drawer-body">
          <DetailRow label="Type" value={ext} />
          <DetailRow label="Status" value="Available" accent="green" />
          <DetailRow label="Used by" value={agentName} />
          <DetailRow label="Workspace" value={workspaceName} />
          <div className="drawer-note">
            This is a front-end preview. No document content is loaded.
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

export function DetailRow({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: "green";
}) {
  return (
    <div className="detail-row">
      <span className="detail-label">{label}</span>
      <span className={`detail-value ${accent ? "accent" : ""}`}>{value}</span>
    </div>
  );
}

export function ProjectResourcePicker({
  open,
  onClose,
  onSelect,
  files,
}: {
  open: boolean;
  onClose: () => void;
  onSelect: (category: string, item: string) => void;
  files: Record<string, string[]>;
}) {
  const [category, setCategory] = useState("Knowledge Base");
  if (!open) return null;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Add Project Resource"
      subtitle="Select an existing project resource."
      width={780}
    >
      <div className="resource-picker-layout">
        <aside className="resource-picker-nav">
          {resourceCategories.map((name) => (
            <button
              type="button"
              className={category === name ? "picker-nav-row active" : "picker-nav-row"}
              key={name}
              onClick={() => setCategory(name)}
            >
              {name}
            </button>
          ))}
        </aside>
        <main className="resource-picker-results">
          {(files[category] ?? []).map((item) => (
            <button
              type="button"
              className="picker-resource-row"
              key={item}
              onClick={() => onSelect(category, item)}
            >
              <Icon type="file" size={15} />
              <span>{item}</span>
              <Icon type="chevronRight" size={13} />
            </button>
          ))}
        </main>
      </div>
    </Modal>
  );
}

export function ResourceDrawerWrapper({
  children,
}: {
  children: ReactNode;
}) {
  return <>{children}</>;
}