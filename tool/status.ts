/**
 * Agenticine Status Tool — logs agent activity to the shared work log.
 *
 * Every agent uses this to log:
 * - task_assigned  — superior logs who they assigned a task to
 * - work_started   — worker logs they're starting
 * - work_complete  — worker logs they're done + what they did
 * - review_started — superior logs they're reviewing
 * - review_complete— superior logs their verdict
 * - blocked        — any agent logs they're stuck
 * - recruited      — HR logs a new agent was recruited
 *
 * The tool appends to <project>/.agenticine/memory/work-log.md (shared, append-only).
 * It also writes a snapshot to <project>/.agenticine/status/<agent>.json.
 *
 * The project path is resolved via resolveProjectPath():
 *   1. Explicit `path` argument from the agent
 *   2. ~/.config-agenticine/active-project.txt (the active project)
 *   3. process.cwd() (fallback)
 *
 * Agents CANNOT read or edit work-log.md through this tool — only append.
 *
 * Place in: tool/status.ts (auto-discovered by OpenCode)
 */

export default {
  description: "Log your activity to the shared work log. Every agent must call this when: receiving a task, starting work, completing work, starting a review, completing a review, getting blocked, or recruiting an agent. Appends to .agenticine/memory/work-log.md — cannot read or edit existing entries. The project path is auto-detected from active-project.txt (or pass 'path' to override).",
  args: {
    event: {
      type: "string",
      description: "Event type: task_assigned | work_started | work_complete | review_started | review_complete | blocked | recruited",
    },
    task_id: {
      type: "string",
      description: "Task identifier (e.g., task-2026-07-12-001). Use 'N/A' if not applicable.",
    },
    details: {
      type: "string",
      description: "What you did, how you did it, or what's happening. Be specific.",
    },
    reported_to: {
      type: "string",
      description: "Who you're reporting to (for work_complete, review_complete). Omit if not applicable.",
      optional: true,
    },
    files_changed: {
      type: "array",
      items: { type: "string" },
      description: "Files changed (for work_complete). Omit if not applicable.",
      optional: true,
    },
    notes: {
      type: "string",
      description: "Additional notes (e.g., review verdict, blocking reason). Omit if not applicable.",
      optional: true,
    },
    path: {
      type: "string",
      description: "Project folder path (auto-detected from active-project.txt if omitted).",
      optional: true,
    },
  },
  async execute(args, context) {
    const fs = await import("fs")
    const path = await import("path")
    const { resolveProjectPath } = await import("./lib/agents-json.js")

    const agentName = context.agent || "Unknown"
    const timestamp = new Date().toISOString()
    const projectPath = resolveProjectPath(args.path)

    const agenticineDir = path.join(projectPath, ".agenticine")
    const memoryDir = path.join(agenticineDir, "memory")
    const statusDir = path.join(agenticineDir, "status")
    const workLogPath = path.join(memoryDir, "work-log.md")

    // Ensure directories exist
    fs.mkdirSync(memoryDir, { recursive: true })
    fs.mkdirSync(statusDir, { recursive: true })

    // ─── Build the work log entry ───
    const eventLabel = args.event.replace(/_/g, " ").toUpperCase()
    let entry = `## [${timestamp}] ${agentName} — ${eventLabel}\n`
    entry += `- **Task ID:** ${args.task_id || "N/A"}\n`

    if (args.event === "task_assigned") {
      entry += `- **Details:** ${args.details}\n`
    } else if (args.event === "work_started") {
      entry += `- **Details:** ${args.details}\n`
    } else if (args.event === "work_complete") {
      entry += `- **What I did:** ${args.details}\n`
      if (args.files_changed && args.files_changed.length > 0) {
        entry += `- **Files changed:** ${args.files_changed.join(", ")}\n`
      }
      if (args.reported_to) {
        entry += `- **Reported to:** ${args.reported_to}\n`
      }
      entry += `- **Status:** Ready for review\n`
    } else if (args.event === "review_started") {
      entry += `- **Reviewing:** ${args.details}\n`
    } else if (args.event === "review_complete") {
      entry += `- **Verdict:** ${args.notes || "N/A"}\n`
      entry += `- **Notes:** ${args.details}\n`
      if (args.reported_to) {
        entry += `- **Forwarded to:** ${args.reported_to}\n`
      }
    } else if (args.event === "blocked") {
      entry += `- **Blocking issue:** ${args.details}\n`
      entry += `- **What I need:** ${args.notes || "See details"}\n`
    } else if (args.event === "recruited") {
      entry += `- **Details:** ${args.details}\n`
    } else {
      entry += `- **Details:** ${args.details}\n`
    }

    entry += `\n`

    // ─── Append to work-log.md (create if doesn't exist) ───
    if (!fs.existsSync(workLogPath)) {
      fs.writeFileSync(
        workLogPath,
        "# Agenticine Work Log\n\n> Auto-generated by the status tool. Every agent action is logged here in chronological order.\n\n",
        "utf-8"
      )
    }
    fs.appendFileSync(workLogPath, entry, "utf-8")

    // ─── Write per-agent status snapshot ───
    const agentStatusPath = path.join(statusDir, `${agentName}.json`)
    const statusSnapshot = {
      agent: agentName,
      event: args.event,
      task_id: args.task_id || null,
      timestamp: timestamp,
      details: args.details,
      reported_to: args.reported_to || null,
      notes: args.notes || null,
      project: projectPath,
    }
    fs.writeFileSync(agentStatusPath, JSON.stringify(statusSnapshot, null, 2), "utf-8")

    return `Logged: ${eventLabel} to work-log.md (project: ${projectPath})`
  },
}
