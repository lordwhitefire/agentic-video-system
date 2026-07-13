/**
 * Agenticine Create Agent — HR (Recruiter) uses this to create new agent files.
 *
 * Reads repo agent MD files from .agenticine/repo-agents/, concatenates them
 * with a custom identity prompt + YAML frontmatter, and writes the result
 * to the GLOBAL agent folder (~/.config-agenticine/opencode/agent/<name>.md).
 * Also updates .agenticine/agents.json so the broadcast/status tools can
 * enforce chain-of-command for the new agent.
 *
 * ALL agents (pre-built or recruited) are permanent and global — available
 * in every project, forever.
 *
 * Place in: tool/create_agent.ts (auto-discovered by OpenCode)
 */

export default {
  description: "Create a new agent file from repo templates. HR (Recruiter) uses this to recruit agents. The agent file is written to the GLOBAL agent folder (~/.config-agenticine/opencode/agent/) so it's available in every project. The registry is updated so broadcast/status tools can enforce chain-of-command. The agent is immediately spawnable via the task tool.",
  args: {
    name: {
      type: "string",
      description: "Agent name (lowercase, hyphenated, e.g., 'athena' or 'recruited-01')",
    },
    identity: {
      type: "string",
      description: "Custom identity prompt — who this agent is, who they report to, what their job is",
    },
    repo_files: {
      type: "array",
      items: { type: "string" },
      description: "Paths to repo agent MD files in .agenticine/repo-agents/ to concatenate (e.g., ['ankitmundada/categories/01-core-development/frontend-developer.md'])",
    },
    permissions: {
      type: "object",
      description: "Permissions object: { read, edit, bash, task, websearch, glob, grep, list, todowrite, question, skill } — each 'allow' or 'deny'",
    },
    department: {
      type: "string",
      description: "Department: strategy, audio, production, quality, personnel",
    },
    role_tier: {
      type: "string",
      description: "Role tier: 'head' or 'worker'",
    },
    title: {
      type: "string",
      description: "Human-readable title (e.g., 'Graphics Creator', 'Head of Strategy')",
    },
    reports_to: {
      type: "string",
      description: "Name of the agent this one reports to (e.g., 'strategist', 'editor', 'reviewer'). Required for chain-of-command enforcement.",
    },
  },
  async execute(args, context) {
    const fs = await import("fs")
    const path = await import("path")
    const { homedir } = await import("os")

    const callerAgent = context.agent || "Unknown"
    if (callerAgent.toLowerCase() !== "recruiter") {
      return `BLOCKED: Only Recruiter (HR) can create agents. ${callerAgent} is not authorized.`
    }

    if (!args.name || !args.identity || !args.reports_to) {
      return `BLOCKED: name, identity, and reports_to are all required.`
    }

    const agentName = args.name.toLowerCase()
    // Global agent folder — same place our 301 pre-built agents live.
    // ALL agents (pre-built or recruited) are permanent and global,
    // available in every project, forever.
    const agentsDir = path.join(homedir(), ".config-agenticine", "opencode", "agent")
    fs.mkdirSync(agentsDir, { recursive: true })
    const agentFile = path.join(agentsDir, `${agentName}.md`)

    if (fs.existsSync(agentFile)) {
      return `BLOCKED: Agent ${agentName} already exists at ${agentFile}. Pick a different name.`
    }

    // 1. Read repo agent MD files
    const repoDir = path.join(process.cwd(), ".agenticine", "repo-agents")
    let repoContent = ""
    for (const repoFile of args.repo_files || []) {
      const fullPath = path.join(repoDir, repoFile)
      try {
        repoContent += `\n\n# Battle-Tested Expertise (from ${repoFile})\n\n`
        repoContent += fs.readFileSync(fullPath, "utf-8")
      } catch {
        return `Repo file not found: ${repoFile} (looked at ${fullPath})`
      }
    }

    // 2. Build YAML frontmatter
    //    ISOLATION: Agenticine agents ALWAYS deny built-in edit/bash/task.
    //    - edit/bash → use safe_edit/safe_bash (6 Laws enforced)
    //    - task → use native task with glob permissions (allowlist-enforced)
    //    OpenCode built-in agents keep their own permissions — unaffected.
    const perms = args.permissions || { read: "allow", edit: "deny", bash: "deny", task: "deny" }
    const canDelegate = perms.task === "allow"
    const taskPerm = canDelegate
      ? 'task:\n    "*": deny\n    "recruited-*": allow'
      : 'task: deny'

    const frontmatter = [
      "---",
      `description: "Agenticine recruited agent — ${agentName} (${args.title || args.department || 'unassigned'}). ${args.identity.slice(0, 80)}..."`,
      "mode: subagent",
      canDelegate ? 'temperature: 0.2' : 'temperature: 0.1',
      "steps: 35",
      "permission:",
      `  read: ${perms.read || "allow"}`,
      `  edit: deny`,
      `  bash: deny`,
      `  safe_edit: ${perms.edit || "deny"}`,
      `  safe_bash: ${perms.bash || "deny"}`,
      `  ${taskPerm}`,
      "  broadcast: allow",
      "  recall: allow",
      `  websearch: ${perms.websearch || "deny"}`,
      `  glob: ${perms.glob || "allow"}`,
      `  grep: ${perms.grep || "allow"}`,
      `  list: ${perms.list || "allow"}`,
      `  todowrite: ${perms.todowrite || "deny"}`,
      `  question: ${perms.question || "allow"}`,
      `  skill: ${perms.skill || "allow"}`,
      "---",
    ].join("\n")

    // 3. Assemble the agent file (comprehensive format)
    const agentContent = `${frontmatter}

# ${agentName} — ${args.title || "Recruited Agent"}

${args.identity}

## When Invoked

Follow this startup procedure on every wake-up:

1. **Read your task prompt** — the spawning agent's prompt tells you what to do
2. **\`recall(agent_name="${args.reports_to}", show_output=true)\`** — see what your superior decided and why
3. **Read \`.agenticine/plan.md\`** — check overall project state (what's done, what's remaining)
4. **Check your inbox** — \`broadcast\` messages from your superior or peers
5. **Start working** — execute your task within your 35 tool calls

### Who to Check (Tiered Recall)
- **ALWAYS:** \`recall(agent_name="${args.reports_to}")\` — your direct superior's work
- **ONLY IF your task depends on them:** \`recall(agent_name="<peer>")\` — peers whose output you need
- **NEVER:** \`recall()\` with no args — checking everyone wastes all 35 calls

## Workflow Position
- **After:** ${args.reports_to} — receives tasks from them
- **Before:** ${canDelegate ? "Your subordinates (if any)" : "(no downstream agents — you execute, not delegate)"}
- **Complements:** Other agents in the ${args.department || "unassigned"} department
- **Coordinates:** ${canDelegate ? "Your team members" : "N/A — you are a worker, not a coordinator"}

## Department
${args.department || "unassigned"}

## Reports To
${args.reports_to}

## The 35-Call Rule
You have 35 tool calls. If you can't finish in 35:
- Summarize what's left in your final \`broadcast\` message
- Your superior (${args.reports_to}) will read the summary via \`recall\`
- Another agent will be recruited to continue

## Communication
- **Report status:** \`broadcast(message="Status: working on X")\` (no send_to = status update to all)
- **Ask your superior a question:** \`broadcast(send_to="${args.reports_to}", message="Question: ...")\`
- **Report completion:** \`broadcast(send_to="${args.reports_to}", message="Done: <summary of what I did>")\` + \`status({ status: "done", message: "..." })\`
- **Report blocker:** \`broadcast(send_to="${args.reports_to}", message="Blocked: <reason>")\` + \`status({ status: "blocked", message: "..." })\`

## Laws You Must Follow
- Law 1: 35-call limit (enforced by \`steps: 35\`)
- Law 2: No file over 300 lines (enforced by \`safe_edit\`)
- Law 3: Real-time docs (\`safe_edit\` logs every change to \`edit-log.md\`)
- Law 4: Chain of command (\`broadcast\` + \`task\` glob permissions enforce)
- Law 5: No inference (\`safe_edit\` Flagger scans — if unsure, ask via \`question\`)
- Law 6: Documentation (\`safe_edit\` + \`safe_bash\` auto-log to memory)

## Boundaries
- **Out of scope:** Anything outside your role as ${args.title || "a recruited agent"}
- **Hand off to:** ${args.reports_to} (for tasks outside your scope)
- **Never:** Affect OpenCode built-in agents, spawn agents not in your \`task\` allowlist, make decisions for the CEO (Law 5)

${repoContent}
`

    fs.writeFileSync(agentFile, agentContent, "utf-8")

    // 4. Update .agenticine/agents.json for chain-of-command enforcement
    const registryPath = path.join(process.cwd(), ".agenticine", "agents.json")
    let registry = {}
    try {
      registry = JSON.parse(fs.readFileSync(registryPath, "utf-8"))
    } catch {
      registry = {}
    }

    // Add the new agent
    registry[agentName] = {
      name: agentName,
      title: args.title || args.department || "Recruited Agent",
      department: args.department || "unassigned",
      roleTier: args.role_tier || "worker",
      reportsTo: args.reports_to,
      subordinates: [],
      createdAt: new Date().toISOString(),
    }

    // Add this agent to the superior's subordinates list
    const superiorKey = args.reports_to.toLowerCase()
    if (registry[superiorKey]) {
      if (!registry[superiorKey].subordinates) {
        registry[superiorKey].subordinates = []
      }
      if (!registry[superiorKey].subordinates.includes(agentName)) {
        registry[superiorKey].subordinates.push(agentName)
      }
    }

    fs.writeFileSync(registryPath, JSON.stringify(registry, null, 2), "utf-8")

    // 5. Initialize empty mailbox file (legacy — broadcast is now used for messaging,
    //    but the file is kept for backwards compat and monitoring tools)
    const mailboxPath = path.join(process.cwd(), ".agenticine", "mailbox", `${agentName}.json`)
    fs.mkdirSync(path.dirname(mailboxPath), { recursive: true })
    fs.writeFileSync(mailboxPath, JSON.stringify({ messages: [] }, null, 2), "utf-8")

    // 6. Initialize status file
    const statusPath = path.join(process.cwd(), ".agenticine", "status", `${agentName}.json`)
    fs.mkdirSync(path.dirname(statusPath), { recursive: true })
    fs.writeFileSync(statusPath, JSON.stringify({
      agent: agentName,
      status: "recruited",
      message: `Recruited by ${callerAgent}`,
      timestamp: new Date().toISOString(),
    }, null, 2), "utf-8")

    // 7. Log to memory
    const memDir = path.join(process.cwd(), ".agenticine", "memory")
    fs.mkdirSync(memDir, { recursive: true })
    const logPath = path.join(memDir, "recruitments.md")
    const logEntry = `- **[${new Date().toISOString()}]** ${callerAgent} recruited ${agentName} (${args.department || "unassigned"}, reports to ${args.reports_to})\n`
    fs.appendFileSync(logPath, logEntry, "utf-8")

    return `Agent ${agentName} created.
- File: ~/.config-agenticine/opencode/agent/${agentName}.md (GLOBAL — available in every project)
- Registry: .agenticine/agents.json updated (added ${agentName}, added to ${args.reports_to}'s subordinates)
- Mailbox: .agenticine/mailbox/${agentName}.json initialized
- Status: .agenticine/status/${agentName}.json initialized
- Editor can now spawn it via task({ subagent_type: "${agentName}" }).`
  },
}
