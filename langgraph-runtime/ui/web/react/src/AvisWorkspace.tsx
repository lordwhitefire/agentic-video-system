import { useEffect, useState } from "react";
import "./avis-workspace.css";
import "./avis-interactions.css";
import { Icon } from "./components/Icon";
import { useEscape } from "./components/Modal";
import { Toast, type ToastData } from "./components/Toast";
import { CreateAgentModal, useCreateAgentFlow } from "./components/CreateAgent";
import { AgentDirectory } from "./components/Directory";
import {
  ProjectResources,
  AddResourceModal,
  ResourceDetailDrawer,
  ProjectResourcePicker,
} from "./components/Resources";
import {
  WorkspaceSelector,
  CreateWorkspaceModal,
  NotificationsPopover,
  ProfileMenu,
} from "./components/Workspace";
import { Conversation, Composer, AttachmentModal, MediaPicker, UrlModal, AgentMentionPicker, AgentIcon } from "./components/Chat";
import { AgentHeader } from "./components/AgentHeader";
import {
  RightRail,
  AgentInfoDrawer,
  AgentContextDrawer,
  AgentSettingsDrawer,
  MemoryEditorModal,
  PastDiscussionsModal,
  CapabilityDetailModal,
  ToolPreviewModal,
} from "./components/RightRail";
import {
  agents,
  agentById,
  capabilityOptions,
  resources as mockResources,
  subAgents as mockSubAgents,
  suggestions,
  toolOptions,
  workspaceContext,
  workspaces as mockWorkspaces,
  type Agent,
  type Message,
  type SubAgent,
  type Workspace,
} from "./data/mock";
import {
  answerApproval,
  compactSession,
  createAgent,
  createProject,
  eventsToMessages,
  fetchProjects,
  fetchRegistry,
  fetchSnapshot,
  mergeCapabilities,
  mergeSubAgents,
  mergeTools,
  proposeHandoff,
  resolveHandoff,
  sendMessage,
  setSessionMode,
  slugify,
  spawnSubagent,
  stopSession,
  toolIdsForLabels,
  uploadResource,
  type CapabilityRow,
  type LiveMemorySlot,
  type LiveProject,
  type LiveSnapshot,
  type ToolRow,
} from "./data/live";

function AvisLogo() {
  return (
    <div className="avis-logo">
      <svg viewBox="0 0 52 46" aria-hidden="true">
        <defs>
          <linearGradient id="avisLogoGradient" x1="4" y1="4" x2="45" y2="42">
            <stop offset="0%" stopColor="#a78bfa" />
            <stop offset="52%" stopColor="#7c3aed" />
            <stop offset="100%" stopColor="#c084fc" />
          </linearGradient>
        </defs>
        <path
          d="M7 37 20 8.5c1.1-2.4 4.3-2.7 5.8-.5l5.4 8.2-6.1 7.2-2.8-4.4-6.8 18H7Z"
          fill="url(#avisLogoGradient)"
        />
        <path
          d="m25.2 8.2 4.7-1.5c2.2-.7 4.4.2 5.6 2.1L47 27.2c1.8 2.8-.2 6.4-3.5 6.6l-6.1.4-12.2-26Z"
          fill="url(#avisLogoGradient)"
        />
      </svg>
      <div>
        <div className="avis-wordmark">AVIS</div>
        <div className="avis-subtitle">AI Video Intelligence System</div>
      </div>
    </div>
  );
}

function SidebarAgent({
  agent,
  active,
  onSelect,
}: {
  agent: Agent;
  active: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      className={`sidebar-agent ${active ? "selected" : ""}`}
      onClick={onSelect}
    >
      <AgentIcon type={agent.icon} color={agent.color} />
      <div className="agent-copy">
        <div className="agent-name">{agent.name}</div>
        <div className="online">
          <span />
          {agent.status}
        </div>
      </div>
    </button>
  );
}

type ModalName =
  | "create-workspace"
  | "attachment"
  | "resource-picker"
  | "media"
  | "url"
  | "mention"
  | "memory"
  | "past-discussions"
  | "capability"
  | "tool"
  | "resource-add"
  | "directory";

type DrawerName = "agent-info" | "agent-context" | "agent-settings" | "resource-detail";
type PopoverName = "workspace-menu" | "notifications" | "profile" | "more";

export default function AvisWorkspace() {
  const [activeAgentId, setActiveAgentId] = useState("video-strategy");
  const [activeWorkspaceId, setActiveWorkspaceId] = useState("cinematic-brand-film");
  const [mode, setMode] = useState<"plan" | "build">("plan");

  const [createdAgents, setCreatedAgents] = useState<Agent[]>([]);
  const [createdSubAgents, setCreatedSubAgents] = useState<SubAgent[]>([]);
  const [allWorkspaces, setAllWorkspaces] = useState<Workspace[]>(mockWorkspaces);
  const [liveProjects, setLiveProjects] = useState<LiveProject[]>([]);
  const [resourceState, setResourceState] = useState<Record<string, string[]>>(mockResources);
  const [liveSubAgents, setLiveSubAgents] = useState<SubAgent[]>([]);
  const [snapshotCache, setSnapshotCache] = useState<Record<string, LiveSnapshot>>({});
  const [localSends, setLocalSends] = useState<Message[]>([]);

  const allAgents = [...agents, ...createdAgents];
  const allSubAgents = [...mockSubAgents, ...createdSubAgents];
  const agent = allAgents.find((a) => a.id === activeAgentId) ?? allAgents[0];
  const realProject = liveProjects.find((p) => p.id === activeWorkspaceId) ?? null;
  const workspace =
    allWorkspaces.find((w) => w.id === activeWorkspaceId) ?? allWorkspaces[0];
  const ctx = workspaceContext[workspace.id] ?? workspaceContext["cinematic-brand-film"];

  const snapshot = snapshotCache[agent.id] ?? null;
  const liveHeader = snapshot?.agent ?? null;
  const liveSession = snapshot?.active_session ?? null;
  const liveSessions = snapshot?.sessions ?? null;

  useEffect(() => {
    let cancelled = false;
    fetchRegistry().then((registry) => {
      if (!cancelled && registry) setLiveSubAgents(mergeSubAgents(registry));
    });
    fetchProjects().then((projects) => {
      if (!cancelled && projects && projects.length > 0) {
        setLiveProjects(projects);
        setResourceState((current) => {
          const merged = { ...current };
          for (const p of projects) {
            for (const [category, files] of Object.entries(p.resources)) {
              const seen = new Set(merged[category] ?? []);
              for (const f of files) {
                if (!seen.has(f.name)) {
                  merged[category] = [...(merged[category] ?? []), f.name];
                  seen.add(f.name);
                }
              }
            }
          }
          return merged;
        });
      }
    });
    const projectId = realProject?.id ?? null;
    fetchSnapshot(activeAgentId, projectId).then((snap) => {
      if (!cancelled && snap) {
        setSnapshotCache((current) => ({ ...current, [snap.agent.id]: snap }));
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const [messages, setMessages] = useState<Message[]>([]);
  const [composerValue, setComposerValue] = useState("");

  const [expandedResources, setExpandedResources] = useState<Record<string, boolean>>({});
  const [modal, setModal] = useState<ModalName | null>(null);
  const [drawer, setDrawer] = useState<DrawerName | null>(null);
  const [popover, setPopover] = useState<PopoverName | null>(null);
  const [railOpen, setRailOpen] = useState(false);

  const [resourceDetail, setResourceDetail] = useState<{ category: string; item: string } | null>(null);
  const [addResourceCategory, setAddResourceCategory] = useState<string | null>(null);
  const [memoryItem, setMemoryItem] = useState<string | null>(null);
  const [memoryValue, setMemoryValue] = useState("");
  const [capabilityName, setCapabilityName] = useState<string | null>(null);
  const [toolName, setToolName] = useState<string | null>(null);
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const capabilityRows: CapabilityRow[] = mergeCapabilities(
    agent.capabilities,
    liveHeader?.capabilities ?? null,
  );
  const toolRows: ToolRow[] = mergeTools(agent.tools, liveHeader?.tools ?? null);
  const liveAbout = liveHeader?.identity ?? null;
  const capabilityRecord = capabilityRows.find((c) => c.name === capabilityName)?.record ?? null;
  const toolDoc = toolRows.find((t) => t.name === toolName)?.doc ?? null;

  const liveTimeline =
    liveSession && liveSession.conversation.length > 0
      ? eventsToMessages(liveSession.conversation)
      : null;
  const liveMemorySlots: LiveMemorySlot[] | null = snapshot
    ? liveSession?.memory_slots ?? [
        { key: "brief", label: "Project Brief", available: false },
        { key: "audience", label: "Audience Insights", available: false },
        { key: "brand", label: "Brand Information", available: false },
      ]
    : null;
  const extraSends = liveTimeline
    ? localSends.filter(
        (m) =>
          !liveTimeline.some(
            (lm) =>
              lm.role === "user" && lm.paragraphs.join("\n") === m.paragraphs.join("\n"),
          ),
      )
    : [];
  const displayMessages = liveTimeline ? [...liveTimeline, ...extraSends] : messages;

  const createFlow = useCreateAgentFlow();

  const pushToast = (title: string, message: string) => {
    const id = Date.now();
    setToasts((current) => [...current, { id, title, message }]);
    setTimeout(() => setToasts((current) => current.filter((t) => t.id !== id)), 3500);
  };

  useEscape(
    popover !== null || modal !== null || drawer !== null || railOpen,
    () => {
      if (popover) setPopover(null);
      else if (modal) setModal(null);
      else if (drawer) setDrawer(null);
      else if (railOpen) setRailOpen(false);
    },
  );

  const selectAgent = (agentId: string) => {
    setActiveAgentId(agentId);
    setMessages([]);
    setComposerValue("");
    setPopover(null);
    setLocalSends([]);
    // Fetch snapshot with current project so we land on the project's latest session
    const projectId = realProject?.id ?? null;
    fetchSnapshot(agentId, projectId).then((snap) => {
      if (snap) {
        setSnapshotCache((current) => ({ ...current, [snap.agent.id]: snap }));
      }
    });
  };

  const refreshSnapshot = (agentId: string, projectId?: string | null) => {
    fetchSnapshot(agentId, projectId).then((snap) => {
      if (snap) {
        setSnapshotCache((current) => ({ ...current, [snap.agent.id]: snap }));
      }
    });
  };

  const activateSession = (sessionId: string) => {
    const projectId = realProject?.id ?? null;
    void fetch(
      `/api/studio/agents/${encodeURIComponent(agent.id)}/sessions/${encodeURIComponent(sessionId)}/activate`,
      { method: "POST" },
    )
      .then(() => refreshSnapshot(agent.id, projectId))
      .catch(() => pushToast("Session switch failed", "Could not reach the backend."));
  };

  const deleteSession = (sessionId: string) => {
    const projectId = realProject?.id ?? null;
    void fetch(
      `/api/studio/agents/${encodeURIComponent(agent.id)}/sessions/${encodeURIComponent(sessionId)}`,
      { method: "DELETE" },
    )
      .then((r) => r.json())
      .then((body) => {
        if (body?.ok) {
          refreshSnapshot(agent.id, projectId);
          pushToast("Session deleted", "Conversation removed.");
        } else {
          pushToast("Session not deleted", body?.error ?? "Unknown error.");
        }
      })
      .catch(() => pushToast("Session not deleted", "Could not reach the backend."));
  };

  const newSession = () => {
    const projectId = realProject?.id ?? null;
    void fetch(`/api/studio/agents/${encodeURIComponent(agent.id)}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task: "New discussion", mode: "plan", project: projectId }),
    })
      .then((r) => r.json())
      .then((body) => {
        if (body?.ok) {
          refreshSnapshot(agent.id, projectId);
          pushToast("Session started", `${body.title ?? "New discussion"} is now active.`);
        } else {
          pushToast("Session not started", body?.error ?? "Unknown error.");
        }
      })
      .catch(() => pushToast("Session not started", "Could not reach the backend."));
  };

  const selectWorkspace = (workspaceId: string) => {
    setActiveWorkspaceId(workspaceId);
    setMessages([]);
    // When switching projects, fetch snapshot with the new project to land on its latest session
    const project = liveProjects.find((p) => p.id === workspaceId);
    const projectId = project?.id ?? null;
    refreshSnapshot(agent.id, projectId);
  };

  const handleSend = () => {
    const text = composerValue.trim();
    if (!text) return;

    // Parse @mentions: @agent-name (kebab-case IDs from the registry)
    const mentionRegex = /@([a-z0-9-]+)/g;
    const mentions: string[] = [];
    let match;
    while ((match = mentionRegex.exec(text)) !== null) {
      mentions.push(match[1]);
    }

    const primaryAgentIds = agents.map((a) => a.id);
    const subAgentIds = mockSubAgents.map((s) => s.id);
    const allAgentIds = [...primaryAgentIds, ...subAgentIds];

    // Check if any mention is a known agent
    const validMentions = mentions.filter((m) => allAgentIds.includes(m));
    const firstValidMention = validMentions[0];

    const sessionId = liveSession?.id ?? null;
    const projectId = realProject?.id ?? null;

    // If the message has a valid @mention as the first thing (or only mention), handle it
    if (firstValidMention && text.trim().startsWith(`@${firstValidMention}`)) {
      const restOfMessage = text.slice(text.indexOf(firstValidMention) + firstValidMention.length + 1).trim();
      const prompt = restOfMessage || text; // use full text if no extra content

      if (primaryAgentIds.includes(firstValidMention)) {
        // @primary-agent → handoff proposal
        proposeHandoff(agent.id, sessionId, firstValidMention, prompt)
          .then((result) => {
            if (!result.ok) {
              pushToast("Handoff not proposed", result.error ?? "Could not reach the backend.");
              setComposerValue(text);
              return;
            }
            setComposerValue("");
            refreshSnapshot(agent.id, projectId);
          })
          .catch(() => {
            pushToast("Handoff not proposed", "Could not reach the backend.");
            setComposerValue(text);
          });
        return;
      }

      if (subAgentIds.includes(firstValidMention)) {
        // @sub-agent → spawn subagent in current session
        if (!liveSession) {
          pushToast("No active session", "Start a session first to spawn a sub-agent.");
          setComposerValue(text);
          return;
        }
        spawnSubagent(agent.id, sessionId, firstValidMention, prompt)
          .then((result) => {
            if (!result.ok) {
              pushToast("Sub-agent not spawned", result.error ?? "Could not reach the backend.");
              setComposerValue(text);
              return;
            }
            setComposerValue("");
            if (liveTimeline) {
              setLocalSends((current) => [...current, msg]);
            } else {
              setMessages((current) => [...current, msg]);
            }
            refreshSnapshot(agent.id, projectId);
          })
          .catch(() => {
            pushToast("Sub-agent not spawned", "Could not reach the backend.");
            setComposerValue(text);
          });
        return;
      }
    }

    // Normal message (no valid @mention at start)
    const msg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      paragraphs: [text],
      time: "Now",
    };
    sendMessage(agent.id, text, sessionId, projectId)
      .then((result) => {
        if (!result.ok) {
          pushToast("Message not sent", result.error ?? "Could not reach the backend.");
          setComposerValue(text);
          return;
        }
        setComposerValue("");
        if (liveTimeline) {
          setLocalSends((current) => [...current, msg]);
        } else {
          setMessages((current) => [...current, msg]);
        }
        refreshSnapshot(agent.id, projectId);
      })
      .catch(() => {
        pushToast("Message not sent", "Could not reach the backend.");
        setComposerValue(text);
      });
  };

  const switchMode = (next: "plan" | "build") => {
    if (next === mode) return;
    if (!liveSession) {
      setMode(next);
      return;
    }
    setSessionMode(agent.id, next, liveSession.id)
      .then((result) => {
        if (result.ok) {
          setMode((result.mode === "build" ? "build" : "plan") as "plan" | "build");
          refreshSnapshot(agent.id);
        } else {
          pushToast("Mode not switched", result.error ?? "Could not reach the backend.");
        }
      })
      .catch(() => pushToast("Mode not switched", "Could not reach the backend."));
  };

  const handleApproval = (answer: "approve" | "reject") => {
    if (!liveSession) return;
    answerApproval(agent.id, liveSession.id, answer)
      .then((result) => {
        if (!result.ok) pushToast("Approval not recorded", result.error ?? "Unknown error.");
        refreshSnapshot(agent.id);
      })
      .catch(() => pushToast("Approval not recorded", "Could not reach the backend."));
  };

  const handleHandoff = (decision: "accept" | "reject") => {
    if (!liveSession) return;
    resolveHandoff(agent.id, liveSession.id, decision)
      .then((result) => {
        if (!result.ok) pushToast("Handoff not resolved", result.error ?? "Unknown error.");
        refreshSnapshot(agent.id);
      })
      .catch(() => pushToast("Handoff not resolved", "Could not reach the backend."));
  };

  const handleStop = () => {
    if (!liveSession) return;
    stopSession(agent.id, liveSession.id)
      .then((result) => {
        if (!result.ok) pushToast("Stop not sent", result.error ?? "Unknown error.");
        refreshSnapshot(agent.id);
      })
      .catch(() => pushToast("Stop not sent", "Could not reach the backend."));
  };

  useEffect(() => {
    if (!liveSession) return;
    if (!["working", "waiting", "stopping"].includes(liveSession.status)) return;
    const projectId = realProject?.id ?? null;
    const timer = window.setInterval(() => {
      refreshSnapshot(agent.id, projectId);
    }, 1500);
    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agent.id, liveSession?.status, realProject?.id]);

  const openMemoryEditor = (item: string) => {
    if (item === "Past Discussions") {
      setModal("past-discussions");
      return;
    }
    setMemoryItem(item);
    const key =
      item === "Project Brief" ? "brief" : item === "Audience Insights" ? "audience" : "brand";
    const real = liveSession?.memory?.[key] ?? "";
    setMemoryValue(real || ctx[key as "brief" | "audience" | "brand"]);
    setModal("memory");
  };

  const saveMemory = () => {
    setModal(null);
    if (liveSession && memoryItem) {
      const key =
        memoryItem === "Project Brief"
          ? "brief"
          : memoryItem === "Audience Insights"
            ? "audience"
            : "brand";
      void fetch(
        `/api/studio/agents/${encodeURIComponent(agent.id)}/sessions/${encodeURIComponent(liveSession.id)}/memory`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ memory: { [key]: memoryValue } }),
        },
      )
        .then((r) => r.json())
        .then((body) => {
          if (body?.ok) {
            refreshSnapshot(agent.id);
            pushToast("Context updated", `${memoryItem} saved to the session memory.`);
          } else {
            pushToast("Context not saved", body?.error ?? "Unknown error.");
          }
        })
        .catch(() => pushToast("Context not saved", "Could not reach the backend."));
    } else {
      pushToast("Context updated", `${memoryItem} saved locally.`);
    }
  };

  const handleCreateAgent = async () => {
    const form = createFlow.agent;
    if (!form.name.trim()) {
      pushToast("Agent not created", "An agent name is required.");
      return;
    }
    const agentId = slugify(form.name);
    const parentName = form.callableBy[0] ?? null;
    const parentId =
      agentById(parentName ?? "")?.id ??
      agents.find((a) => a.name === parentName)?.id ??
      "video-strategy";
    const result = await createAgent({
      name: form.name.trim(),
      slug: agentId,
      type: form.type,
      parent: form.type === "sub" ? parentId : undefined,
      description: form.description.trim(),
      identity: form.role.trim() || `I'm the ${form.name.trim()}.`,
      department: "Custom",
      capabilities: form.capabilities,
      skills: form.capabilities,
      tools: toolIdsForLabels(form.tools),
      tool_labels: form.tools,
      manages: form.type === "primary" ? form.allowedSubAgents : undefined,
    });
    if (!result.ok) {
      pushToast("Agent not created", result.error ?? "the server could not create it.");
      return;
    }
    const created = result.agent;
    if (form.type === "primary") {
      const entry: Agent = {
        id: created?.id ?? agentId,
        name: created?.name ?? form.name.trim(),
        color: "#7134d7",
        icon: "target",
        role: form.description.trim() || "Custom primary agent",
        about: form.role.trim() || "I specialize in the area assigned to me.",
        greeting: form.role.trim() || "I help you with the area assigned to me.",
        status: "Online",
        capabilities:
          form.capabilities.length > 0 ? form.capabilities : capabilityOptions.slice(0, 3),
        tools: form.tools.length > 0 ? form.tools : toolOptions.slice(0, 2),
      };
      setCreatedAgents((current) => [...current, entry]);
      pushToast("Agent created", `${entry.name} added to the agent network.`);
    } else {
      const entry: SubAgent = {
        id: created?.id ?? agentId,
        name: created?.name ?? form.name.trim(),
        parent: created?.parent ?? parentId,
        status: "Available",
      };
      setCreatedSubAgents((current) => [...current, entry]);
      pushToast("Agent created", `${entry.name} added to the directory as a sub-agent.`);
    }
    fetchRegistry().then((registry) => {
      if (registry) setLiveSubAgents(mergeSubAgents(registry));
    });
    createFlow.setOpen(false);
  };

  const handleCreateWorkspace = async (name: string) => {
    const result = await createProject(name);
    if (result.ok && result.project) {
      setLiveProjects((current) => [...current, result.project!]);
      setActiveWorkspaceId(result.project!.id);
      setModal(null);
      pushToast("Project created", `${result.project!.name} is now the active project.`);
      // Refresh snapshot with the new project to land on its session
      refreshSnapshot(agent.id, result.project!.id);
      return;
    }
    const id = `ws-${Date.now()}`;
    setAllWorkspaces((current) => [...current, { id, name }]);
    setActiveWorkspaceId(id);
    setModal(null);
    pushToast("Workspace created", `${name} is now the active workspace.`);
  };

  const confirmAddResource = async (file: File) => {
    if (!addResourceCategory) return;
    const category = addResourceCategory;
    let uploaded = false;
    if (realProject) {
      const result = await uploadResource(realProject.id, category, file);
      uploaded = result.ok;
      if (!uploaded && result.error) {
        pushToast("Upload failed", result.error);
      }
    }
    if (!uploaded) {
      pushToast("Resource added", `${file.name} added to ${category} locally.`);
    } else {
      pushToast("Resource added", `${file.name} uploaded to ${realProject!.name}.`);
    }
    setResourceState((current) => {
      const seen = new Set(current[category] ?? []);
      if (seen.has(file.name)) return current;
      return { ...current, [category]: [...(current[category] ?? []), file.name] };
    });
    setModal(null);
    setAddResourceCategory(null);
  };

  const confirmAttach = (file: File) => {
    setModal(null);
    if (!realProject) {
      pushToast("No active project", "Select a project first to attach files.");
      return;
    }
    // Upload to project's Media Library
    uploadResource(realProject.id, "Media Library", file)
      .then((result) => {
        if (result.ok) {
          pushToast("File uploaded", `${file.name} added to ${realProject.name}'s Media Library.`);
          // Update local resource state
          setResourceState((current) => {
            const seen = new Set(current["Media Library"] ?? []);
            if (seen.has(file.name)) return current;
            return { ...current, "Media Library": [...(current["Media Library"] ?? []), file.name] };
          });
        } else {
          pushToast("Upload failed", result.error ?? "Could not upload file.");
        }
      })
      .catch(() => pushToast("Upload failed", "Could not reach the backend."));
  };

  const selectResourceFromPicker = (_category: string, item: string) => {
    setModal(null);
    pushToast("Resource selected", item);
  };

  const selectMedia = (item: string) => {
    setModal(null);
    pushToast("Media selected", item);
  };

  const addUrl = (url: string) => {
    setModal(null);
    // Call webfetch (read-only, allowed in both modes)
    if (!liveSession) {
      pushToast("No active session", "Start a session first to fetch URLs.");
      return;
    }
    const sessionId = liveSession.id;
    // Use the webfetch tool via a message that triggers it
    // For now, send a message that will cause the agent to call webfetch
    const msg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      paragraphs: [`Fetch URL: ${url}`],
      time: "Now",
    };
    const projectId = realProject?.id ?? null;
    sendMessage(agent.id, `Fetch URL: ${url}`, sessionId, projectId)
      .then((result) => {
        if (!result.ok) {
          pushToast("Fetch not sent", result.error ?? "Could not reach the backend.");
          return;
        }
        if (liveTimeline) {
          setLocalSends((current) => [...current, msg]);
        } else {
          setMessages((current) => [...current, msg]);
        }
        refreshSnapshot(agent.id, projectId);
      })
      .catch(() => pushToast("Fetch not sent", "Could not reach the backend."));
  };

  const mentionAgent = (name: string) => {
    setComposerValue((current) => `${current}@${name} `);
    setModal(null);
  };

  const openResourceDetail = (category: string, item: string) => {
    setResourceDetail({ category, item });
    setDrawer("resource-detail");
  };

  return (
    <main className="avis-app">
      <aside className="left-sidebar">
        <div className="brand-area">
          <AvisLogo />
        </div>

        <div className="agent-section">
          <div className="section-heading">
            <span>AGENT NETWORK</span>
            <button
              type="button"
              className="plus-button"
              aria-label="Add agent"
              onClick={createFlow.openModal}
            >
              +
            </button>
          </div>

          <div className="agent-list">
            {allAgents.map((a) => (
              <SidebarAgent
                key={a.id}
                agent={a}
                active={a.id === activeAgentId}
                onSelect={() => selectAgent(a.id)}
              />
            ))}
          </div>

          <button
            type="button"
            className="directory-button"
            onClick={() => setModal("directory")}
          >
            <span className="directory-left">
              <Icon type="target" size={14} />
              All Agents Directory
            </span>
            <Icon type="arrow" size={14} />
          </button>
        </div>

        <div className="resources-section">
          <div className="resources-title">PROJECT RESOURCES</div>
          <ProjectResources
            expandedMap={expandedResources}
            onToggle={(category) =>
              setExpandedResources((current) => ({ ...current, [category]: !current[category] }))
            }
            onAddResource={(category) => {
              setAddResourceCategory(category);
              setModal("resource-add");
            }}
            onSelectResource={openResourceDetail}
            files={resourceState}
          />
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="workspace-title">Workspace</div>

          <WorkspaceSelector
            activeWorkspace={activeWorkspaceId}
            workspaces={liveProjects}
            open={popover === "workspace-menu"}
            setOpen={(open) => setPopover(open ? "workspace-menu" : null)}
            onSelect={selectWorkspace}
            onCreate={() => setModal("create-workspace")}
          />

          <div className="topbar-right">
            <div className="mode-switch">
              <button
                type="button"
                className={`mode ${mode === "plan" ? "active" : ""}`}
                onClick={() => switchMode("plan")}
              >
                Plan Mode
              </button>
              <button
                type="button"
                className={`mode ${mode === "build" ? "active" : ""}`}
                onClick={() => switchMode("build")}
              >
                Build Mode
              </button>
            </div>

            <button
              type="button"
              className="icon-button"
              aria-label="Agent details"
              title="Agent details"
              onClick={() => setRailOpen((open) => !open)}
            >
              <Icon type="panel" size={21} />
            </button>

            <button
              type="button"
              className="icon-button bell-button"
              aria-label="Notifications"
              onClick={() => setPopover(popover === "notifications" ? null : "notifications")}
            >
              <Icon type="bell" size={21} />
            </button>

            <div className="profile">
              <button
                type="button"
                className="profile-button"
                onClick={() => setPopover(popover === "profile" ? null : "profile")}
              >
                <div className="avatar">V</div>
                <div className="profile-copy">
                  <div>You</div>
                  <small>Director</small>
                </div>
                <Icon type="chevron" size={16} />
              </button>
            </div>
          </div>
        </header>

        <div className="workspace-body">
          <section className="chat-panel">
            <AgentHeader
              agent={agent}
              onInfo={() => setDrawer("agent-info")}
              onContext={() => setDrawer("agent-context")}
              onSettings={() => setDrawer("agent-settings")}
              moreOpen={popover === "more"}
              setMoreOpen={(open) => setPopover(open ? "more" : null)}
            />

            <Conversation
              messages={displayMessages}
              agent={agent}
              approval={liveSession?.pending_approval ?? null}
              onApprove={() => handleApproval("approve")}
              onReject={() => handleApproval("reject")}
              handoff={liveSession?.pending_handoff ?? null}
              onAcceptHandoff={() => handleHandoff("accept")}
              onRejectHandoff={() => handleHandoff("reject")}
              canStop={liveSession?.can_stop ?? false}
              onStop={handleStop}
              pendingCompact={liveSession?.pending_compact ?? false}
              onCompact={(answer) => {
                if (!liveSession) return;
                compactSession(agent.id, liveSession.id, answer)
                  .then((result) => {
                    if (!result.ok) pushToast("Compact failed", result.error ?? "Unknown error.");
                    refreshSnapshot(agent.id, realProject?.id ?? null);
                  })
                  .catch(() => pushToast("Compact failed", "Could not reach the backend."));
              }}
            />

            <div className="suggestions">
              {suggestions.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  onClick={() => openMemoryEditor(item.memory)}
                >
                  <Icon type="check" size={16} />
                  {item.label}
                </button>
              ))}
            </div>

            <Composer
              value={composerValue}
              setValue={setComposerValue}
              onSend={handleSend}
              placeholder={`Message ${agent.name}...`}
              onAttach={() => setModal("attachment")}
              onResource={() => setModal("resource-picker")}
              onMedia={() => setModal("media")}
              onLink={() => setModal("url")}
              onMention={() => setModal("mention")}
            />

            <footer className="mode-footer">
              You&apos;re in {mode === "plan" ? "Plan" : "Build"} Mode.
              {mode === "plan"
                ? " Discuss, refine, and plan without executing."
                : " Execution is permitted. Agents explain consequential actions before doing them."}
              <span>Switch to {mode === "plan" ? "Build" : "Plan"} Mode →</span>
            </footer>
          </section>
        </div>
      </section>

      {railOpen && (
        <>
          <div className="rail-backdrop" onMouseDown={() => setRailOpen(false)} />
          <RightRail
            agent={agent}
            liveCapabilities={capabilityRows}
            liveTools={toolRows}
            liveAbout={liveAbout}
            liveSubAgents={liveSubAgents.length > 0 ? [...liveSubAgents, ...createdSubAgents] : allSubAgents}
            liveMemorySlots={liveMemorySlots}
            onAboutClick={() => setDrawer("agent-info")}
            onCapabilityClick={(name) => {
              setCapabilityName(name);
              setModal("capability");
            }}
            onMemoryClick={openMemoryEditor}
            onToolClick={(name) => {
              setToolName(name);
              setModal("tool");
            }}
          />
        </>
      )}

      <CreateAgentModal
        open={createFlow.open}
        onClose={() => createFlow.setOpen(false)}
        activeTab={createFlow.tab}
        setActiveTab={createFlow.setTab}
        agent={createFlow.agent}
        setAgent={createFlow.setAgent}
        onCreate={handleCreateAgent}
      />

      <AgentDirectory
        open={modal === "directory"}
        onClose={() => setModal(null)}
        onSelectAgent={selectAgent}
        onNewAgent={() => {
          setModal(null);
          createFlow.openModal();
        }}
        extraPrimaryAgents={createdAgents.map((a) => ({ name: a.name, status: a.status }))}
        extraSubAgents={createdSubAgents}
      />

      <AddResourceModal
        open={modal === "resource-add"}
        category={addResourceCategory}
        onClose={() => {
          setModal(null);
          setAddResourceCategory(null);
        }}
        onConfirm={confirmAddResource}
      />

      <ResourceDetailDrawer
        open={drawer === "resource-detail"}
        category={resourceDetail?.category ?? null}
        item={resourceDetail?.item ?? null}
        agentName={agent.name}
        workspaceName={workspace.name}
        onClose={() => setDrawer(null)}
      />

      <CreateWorkspaceModal
        open={modal === "create-workspace"}
        onClose={() => setModal(null)}
        onCreate={handleCreateWorkspace}
      />

      <AttachmentModal
        open={modal === "attachment"}
        onClose={() => setModal(null)}
        onConfirm={confirmAttach}
      />

      <ProjectResourcePicker
        open={modal === "resource-picker"}
        onClose={() => setModal(null)}
        onSelect={selectResourceFromPicker}
        files={resourceState}
      />

      <MediaPicker
        open={modal === "media"}
        onClose={() => setModal(null)}
        onSelect={selectMedia}
        media={resourceState["Media Library"]}
      />

      <UrlModal open={modal === "url"} onClose={() => setModal(null)} onAdd={addUrl} />

      <AgentMentionPicker
        open={modal === "mention"}
        onClose={() => setModal(null)}
        onSelect={mentionAgent}
      />

      <MemoryEditorModal
        open={modal === "memory"}
        item={memoryItem ?? ""}
        value={memoryValue}
        setValue={setMemoryValue}
        onClose={() => setModal(null)}
        onSave={saveMemory}
      />

      <PastDiscussionsModal
        open={modal === "past-discussions"}
        sessions={liveSessions}
        onClose={() => setModal(null)}
        onActivate={activateSession}
        onDelete={deleteSession}
        onNewSession={newSession}
        onCompact={(sessionId) => {
          compactSession(agent.id, sessionId, "yes")
            .then((result) => {
              if (!result.ok) pushToast("Compact failed", result.error ?? "Unknown error.");
              refreshSnapshot(agent.id, realProject?.id ?? null);
            })
            .catch(() => pushToast("Compact failed", "Could not reach the backend."));
        }}
      />

      <CapabilityDetailModal
        open={modal === "capability"}
        name={capabilityName ?? ""}
        record={capabilityRecord ?? undefined}
        onClose={() => setModal(null)}
      />

      <ToolPreviewModal
        open={modal === "tool"}
        name={toolName ?? ""}
        doc={toolDoc ?? undefined}
        onClose={() => setModal(null)}
      />

      <AgentInfoDrawer
        open={drawer === "agent-info"}
        agent={agent}
        workspaceCount={allWorkspaces.length}
        onClose={() => setDrawer(null)}
      />

      <AgentContextDrawer
        open={drawer === "agent-context"}
        agent={agent}
        workspace={workspace}
        onClose={() => setDrawer(null)}
      />

      <AgentSettingsDrawer open={drawer === "agent-settings"} onClose={() => setDrawer(null)} />

      <NotificationsPopover
        open={popover === "notifications"}
        setOpen={(open) => setPopover(open ? "notifications" : null)}
      />

      <ProfileMenu
        open={popover === "profile"}
        setOpen={(open) => setPopover(open ? "profile" : null)}
      />

      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          toast={toast}
          onClose={() => setToasts((current) => current.filter((t) => t.id !== toast.id))}
        />
      ))}
    </main>
  );
}