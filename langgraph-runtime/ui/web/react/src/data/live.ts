import { subAgents as mockSubAgents, type Message, type SubAgent } from "./mock";

export type LiveCapability = {
  name: string;
  created: boolean;
  description?: string;
  knowledge?: string;
  guidance?: string;
  skills?: string[];
  tools?: string[];
  resources?: string;
  created_at?: string;
};

export type LiveTool = { name: string; doc: string; permission?: string };

export type LiveAgentHeader = {
  id: string;
  name: string;
  description: string;
  department: string;
  tier: string;
  identity: string;
  capabilities: LiveCapability[];
  skills: string[];
  tools: LiveTool[];
  manages: string[];
  head: string | null;
};

export type LiveRegistryEntry = {
  id: string;
  name: string;
  description: string;
  department: string;
  tier: string;
  parent?: string;
};

export type CapabilityRow = {
  name: string;
  created: boolean;
  record?: LiveCapability;
};

export type ToolRow = { name: string; doc?: string };

export type LiveMemorySlot = { key: string; label: string; available: boolean };

export type LiveSession = {
  id: string;
  title: string;
  status: string;
  mode: string;
  last_activity_at: string;
  handoff_pending: boolean;
  run_id: string | null;
  project: string | null;
};

export type ConversationEvent = {
  type: string;
  timestamp: string;
  agent_id?: string;
  content?: string;
  tool?: { name?: string; args?: unknown };
  error?: boolean;
  text?: string;
};

export type LiveActiveSession = {
  id: string;
  title: string;
  status: string;
  mode: string;
  task: string;
  conversation: ConversationEvent[];
  pending_approval: { id: string; question: string } | null;
  pending_handoff: {
    run_id: string;
    target: string;
    prompt: string;
    decision: string | null;
  } | null;
  pending_compact: boolean;
  can_stop: boolean;
  memory: Record<string, string>;
  memory_slots: LiveMemorySlot[];
};

export type LiveSnapshot = {
  agent: LiveAgentHeader;
  sessions: LiveSession[];
  active_session_id: string | null;
  active_session: LiveActiveSession | null;
  model_configured: boolean;
};

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(path, init);
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function fetchRegistry(): Promise<LiveRegistryEntry[] | null> {
  const data = await fetchJson<{ agents: LiveRegistryEntry[] }>("/api/agents");
  return data?.agents ?? null;
}

export async function fetchAgentHeader(agentId: string): Promise<LiveAgentHeader | null> {
  const data = await fetchJson<{ agent: LiveAgentHeader }>(
    `/api/studio/agents/${encodeURIComponent(agentId)}`,
  );
  return data?.agent ?? null;
}

export async function fetchSnapshot(
  agentId: string,
  projectId?: string | null,
): Promise<LiveSnapshot | null> {
  const url = projectId
    ? `/api/studio/agents/${encodeURIComponent(agentId)}?project=${encodeURIComponent(projectId)}`
    : `/api/studio/agents/${encodeURIComponent(agentId)}`;
  return fetchJson<LiveSnapshot>(url);
}

// --- W6.5: conversation controls ---------------------------------------------

export type StudioActionResult = {
  ok: boolean;
  error?: string;
  [key: string]: unknown;
};

async function postStudio<T extends StudioActionResult>(
  agentId: string,
  path: string,
  body: Record<string, unknown>,
): Promise<T> {
  const data = await fetchJson<T>(
    `/api/studio/agents/${encodeURIComponent(agentId)}${path}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
  return (data ?? { ok: false, error: "no response" }) as T;
}

export function sendMessage(
  agentId: string,
  message: string,
  sessionId?: string | null,
  projectId?: string | null,
): Promise<StudioActionResult> {
  return postStudio(agentId, "/messages", {
    message,
    session_id: sessionId ?? undefined,
    project: projectId ?? undefined,
  });
}

export function setSessionMode(
  agentId: string,
  mode: "plan" | "build",
  sessionId?: string | null,
): Promise<StudioActionResult & { mode?: string }> {
  return postStudio(agentId, "/mode", {
    mode,
    session_id: sessionId ?? undefined,
  });
}

export function answerApproval(
  agentId: string,
  sessionId: string,
  answer: "approve" | "reject",
): Promise<StudioActionResult> {
  return postStudio(agentId, "/approval", { session_id: sessionId, answer });
}

export function resolveHandoff(
  agentId: string,
  sessionId: string,
  decision: "accept" | "reject",
): Promise<StudioActionResult> {
  return postStudio(agentId, "/handoff", { session_id: sessionId, decision });
}

export function proposeHandoff(
  agentId: string,
  sessionId: string | null,
  target: string,
  prompt: string,
): Promise<StudioActionResult> {
  return postStudio(agentId, "/handoff/propose", {
    session_id: sessionId ?? undefined,
    target,
    prompt,
  });
}

export function spawnSubagent(
  agentId: string,
  sessionId: string | null,
  subagentId: string,
  task: string,
): Promise<StudioActionResult> {
  return postStudio(agentId, "/subagent/spawn", {
    session_id: sessionId ?? undefined,
    subagent_id: subagentId,
    task,
  });
}

export function stopSession(
  agentId: string,
  sessionId: string,
): Promise<StudioActionResult> {
  return postStudio(agentId, "/stop", { session_id: sessionId });
}

export function compactSession(
  agentId: string,
  sessionId: string,
  answer: "yes" | "no",
): Promise<StudioActionResult> {
  return postStudio(agentId, "/compact", { session_id: sessionId, answer });
}

// --- W7: notifications -----------------------------------------------------

export type LiveNotification = {
  id: string;
  title: string;
  time: string;
  read: boolean;
  kind: string;
};

export async function fetchNotifications(
  limit: number = 20,
): Promise<LiveNotification[] | null> {
  const data = await fetchJson<{ notifications: LiveNotification[] }>(
    `/api/notifications?limit=${limit}`,
  );
  return data?.notifications ?? null;
}

// --- W2: agent creation -----------------------------------------------------

export type CreateAgentPayload = {
  name: string;
  slug: string;
  type: "primary" | "sub";
  parent?: string;
  description?: string;
  identity?: string;
  department?: string;
  capabilities: string[];
  skills: string[];
  tools: string[];
  tool_labels: string[];
  manages?: string[];
};

export type CreateAgentResult = {
  ok: boolean;
  error?: string;
  agent?: LiveRegistryEntry;
};

/** The wizard's mock tool labels map to real registry tool ids (W2). */
const TOOL_LABEL_TO_IDS: Record<string, string[]> = {
  "Research Tools": ["websearch", "webfetch", "retrieve_knowledge"],
  "Trend Explorer": ["websearch", "retrieve_knowledge"],
  "Competitor Analyzer": ["websearch", "webfetch"],
  "Reference Finder": ["websearch", "webfetch", "retrieve_knowledge"],
};

export function toolIdsForLabels(labels: string[]): string[] {
  const ids: string[] = [];
  for (const label of labels) {
    for (const id of TOOL_LABEL_TO_IDS[label] ?? []) {
      if (!ids.includes(id)) ids.push(id);
    }
  }
  return ids;
}

export function slugify(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export async function createAgent(
  payload: CreateAgentPayload,
): Promise<CreateAgentResult> {
  const data = await fetchJson<CreateAgentResult>("/api/studio/agents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return data ?? { ok: false, error: "no response" };
}

// --- W3/W4: projects & resources ------------------------------------------

export type LiveResource = {
  name: string;
  size: number;
  date: string;
  type: string;
};

export type LiveProject = {
  id: string;
  name: string;
  created_at: string;
  resources: Record<string, LiveResource[]>;
};

export type ProjectResult = {
  ok: boolean;
  error?: string;
  project?: LiveProject;
};

export async function fetchProjects(): Promise<LiveProject[] | null> {
  const data = await fetchJson<{ projects: LiveProject[] }>("/api/projects");
  return data?.projects ?? null;
}

export async function createProject(name: string): Promise<ProjectResult> {
  const data = await fetchJson<ProjectResult>("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return data ?? { ok: false, error: "no response" };
}

export async function uploadResource(
  projectId: string,
  category: string,
  file: File,
): Promise<ProjectResult> {
  const form = new FormData();
  form.append("category", category);
  form.append("file", file);
  const data = await fetchJson<ProjectResult>(
    `/api/projects/${encodeURIComponent(projectId)}/resources`,
    { method: "POST", body: form },
  );
  return data ?? { ok: false, error: "no response" };
}

export function resourceFiles(
  project: LiveProject | undefined,
  category: string,
): string[] {
  return (project?.resources?.[category] ?? []).map((r) => r.name);
}

function fmtTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function eventsToMessages(events: ConversationEvent[]): Message[] {
  return events.map((ev, index) => {
    const id = `ev-${index}`;
    const time = fmtTime(ev.timestamp);
    switch (ev.type) {
      case "user_message":
        return { id, role: "user", paragraphs: [ev.content ?? ""], time };
      case "assistant_message":
      case "reasoning_summary":
        return { id, role: "agent", paragraphs: [ev.content ?? ""], time };
      case "tool_call": {
        const name = ev.tool?.name ?? "tool";
        const arg = formatToolArg(ev.tool?.args);
        return { id, role: "agent", paragraphs: [`\u2192 ${name}${arg ? `: ${arg}` : ""}`], time };
      }
      case "tool_result": {
        const name = ev.tool?.name ?? "tool";
        const outcome = ev.text ?? (ev.error ? "failed" : "done");
        return { id, role: "agent", paragraphs: [`\u2192 ${name}: ${outcome}`], time };
      }
      case "approval_request":
        return {
          id,
          role: "agent",
          question: true,
          paragraphs: [ev.content ?? "Approval requested."],
          time,
        };
      case "compact_request":
        return {
          id,
          role: "agent",
          question: true,
          paragraphs: [ev.content ?? "This conversation is getting long — compact it?"],
          time,
        };
      default:
        return { id, role: "agent", paragraphs: [ev.content ?? ""], time };
    }
  });
}

function formatToolArg(args: unknown): string {
  if (!args || typeof args !== "object") return "";
  const a = args as Record<string, unknown>;
  // priority keys that make a good one-line summary
  const priority = ["file", "filename", "key", "url", "query", "run_id", "target", "class"];
  for (const k of priority) {
    const v = a[k];
    if (typeof v === "string" && v.length > 0) return v;
    if (typeof v === "number") return String(v);
  }
  // fallback: first non-empty string value
  for (const v of Object.values(a)) {
    if (typeof v === "string" && v.length > 0) return v;
  }
  return "";
}

export function dayOf(iso: string | null): string {
  if (!iso) return "Earlier";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "Earlier";
  const now = new Date();
  const startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const start = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const days = Math.round((startToday - start) / 86400000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days <= 7) return "Last Week";
  return "Earlier";
}

export function mergeCapabilities(
  mockNames: string[],
  live: LiveCapability[] | null,
): CapabilityRow[] {
  const rows: CapabilityRow[] = mockNames.map((name) => ({ name, created: false }));
  if (!live) return rows;
  for (const cap of live) {
    const existing = rows.find((r) => r.name === cap.name);
    if (existing) {
      if (cap.created) {
        existing.created = true;
        existing.record = cap;
      }
    } else {
      rows.push({ name: cap.name, created: cap.created, record: cap.created ? cap : undefined });
    }
  }
  return rows;
}

export function mergeTools(mockNames: string[], live: LiveTool[] | null): ToolRow[] {
  const rows: ToolRow[] = mockNames.map((name) => ({ name }));
  if (!live) return rows;
  for (const tool of live) {
    const existing = rows.find((r) => r.name === tool.name);
    if (existing) existing.doc = tool.doc;
    else rows.push({ name: tool.name, doc: tool.doc });
  }
  return rows;
}

export function mergeSubAgents(live: LiveRegistryEntry[] | null): SubAgent[] {
  if (!live) return mockSubAgents;
  const subs = live
    .filter((e) => e.tier === "subagent")
    .map((e) => ({
      id: e.id,
      name: e.name,
      parent: e.parent ?? "video-strategy",
      status: "Available",
    }));
  return subs.length > 0 ? subs : mockSubAgents;
}