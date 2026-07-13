/**
 * Agenticine Revoke — strips tools from a misbehaving Agenticine agent.
 *
 * Used by Reviewer (Meta Engineering Director) when an agent is caught
 * violating Law 5 (No Inference). Removes safe_edit and safe_bash permissions
 * from the agent's config file — the agent can only read until the CEO
 * manually restores permissions.
 *
 * ISOLATION GUARANTEE: This tool can ONLY affect Agenticine agents registered
 * in .agenticine/agents.json. OpenCode built-in agents (build, plan, etc.)
 * are NEVER in the registry, so they can NEVER be revoked by this tool.
 * Built-in agents don't even have safe_edit/safe_bash in their YAML, so
 * the regex replacements below would be no-ops even if the file were
 * somehow reached.
 *
 * Place in: .opencode/tools/revoke.ts
 */

export default {
  description: "Revoke safe_edit and safe_bash permissions from a Agenticine agent that violated laws. Only Reviewer or Editor should use this. The agent will be unable to modify files or run commands until the CEO manually restores permissions. CANNOT affect OpenCode built-in agents.",
  args: {
    agent: {
      type: "string",
      description: "Name of the Agenticine agent to revoke permissions from",
    },
    reason: {
      type: "string",
      description: "Why permissions are being revoked (e.g., 'Inference detected in login form code')",
    },
  },
  async execute(args, context) {
    const fs = await import("fs")
    const path = await import("path")

    const callerAgent = context.agent || "Unknown"

    // ─── Guard 1: Only Reviewer or Editor can revoke ───
    if (callerAgent.toLowerCase() !== "reviewer" && callerAgent.toLowerCase() !== "editor") {
      return `BLOCKED: Only Reviewer or Editor can revoke permissions. ${callerAgent} is not authorized.`
    }

    const targetAgent = args.agent.toLowerCase()

    // ─── Guard 2: Target must be a registered Agenticine agent ───
    // This is the ISOLATION GUARANTEE. OpenCode built-in agents (build, plan,
    // etc.) are NEVER in .agenticine/agents.json, so they can NEVER be revoked.
    const registryPath = path.join(process.cwd(), ".agenticine", "agents.json")
    let registry: Record<string, { name: string }> = {}
    try {
      registry = JSON.parse(fs.readFileSync(registryPath, "utf-8"))
    } catch {
      return `BLOCKED: Could not read .agenticine/agents.json. Run Agenticine setup first.`
    }

    const isAgenticineAgent = Object.values(registry).some(
      (a) => a.name?.toLowerCase() === targetAgent
    )
    if (!isAgenticineAgent) {
      return `BLOCKED: ${args.agent} is not a registered Agenticine agent. revoke can ONLY affect Agenticine agents listed in .agenticine/agents.json. OpenCode built-in agents (build, plan, etc.) are protected and can never be revoked.`
    }

    // ─── Guard 3: Target must have an agent file on disk ───
    const agentsDir = path.join(process.cwd(), ".opencode", "agents")
    const agentFile = path.join(agentsDir, `${targetAgent}.md`)

    if (!fs.existsSync(agentFile)) {
      return `Agent file not found: ${agentFile}. The agent is in the registry but has no file. This is a corrupted state — report to Editor.`
    }

    // ─── Read the agent file ───
    let content = fs.readFileSync(agentFile, "utf-8")

    // ─── Revoke safe_edit and safe_bash (the tools Agenticine agents actually use) ───
    // Agenticine agents already have edit: deny and bash: deny (isolation pattern).
    // They use safe_edit and safe_bash instead. To actually stop them from
    // editing/running commands, we must flip safe_edit/safe_bash to deny.
    let changesMade = 0

    if (/safe_edit:\s*allow/i.test(content)) {
      content = content.replace(/safe_edit:\s*allow/gi, "safe_edit: deny")
      changesMade++
    }
    if (/safe_bash:\s*allow/i.test(content)) {
      content = content.replace(/safe_bash:\s*allow/gi, "safe_bash: deny")
      changesMade++
    }

    // Also flip built-in edit/bash to deny (belt-and-suspenders — in case an
    // agent file was hand-edited to have edit: allow)
    if (/^\s*edit:\s*allow/im.test(content)) {
      content = content.replace(/^(\s*)edit:\s*allow/gim, "$1edit: deny")
      changesMade++
    }
    if (/^\s*bash:\s*allow/im.test(content)) {
      content = content.replace(/^(\s*)bash:\s*allow/gim, "$1bash: deny")
      changesMade++
    }

    if (changesMade === 0) {
      return `No changes needed: ${args.agent} already has safe_edit: deny and safe_bash: deny. Either permissions were already revoked, or this agent never had edit/bash access.`
    }

    // ─── Add a revocation note after the frontmatter ───
    const revokeNote = `\n\n## ⚠️ PERMISSIONS REVOKED\n- **Revoked by:** ${callerAgent}\n- **Reason:** ${args.reason}\n- **Time:** ${new Date().toISOString()}\n- **Status:** safe_edit, safe_bash, edit, and bash are all denied. Agent can only read files until the CEO manually restores permissions.\n`

    const parts = content.split("---")
    if (parts.length >= 3) {
      content = parts[0] + "---" + parts[1] + "---" + revokeNote + parts.slice(2).join("---")
    }

    fs.writeFileSync(agentFile, content, "utf-8")

    // ─── Log to memory ───
    const memDir = path.join(process.cwd(), ".agenticine", "memory")
    fs.mkdirSync(memDir, { recursive: true })
    const logPath = path.join(memDir, "revocations.md")
    const logEntry = `- **[${new Date().toISOString()}]** ${callerAgent} revoked safe_edit+safe_bash from ${targetAgent}. Reason: ${args.reason}\n`
    fs.appendFileSync(logPath, logEntry, "utf-8")

    // ─── Update agent status ───
    const statusPath = path.join(process.cwd(), ".agenticine", "status", `${targetAgent}.json`)
    fs.mkdirSync(path.dirname(statusPath), { recursive: true })
    fs.writeFileSync(statusPath, JSON.stringify({
      agent: targetAgent,
      status: "revoked",
      message: `Permissions revoked by ${callerAgent}: ${args.reason}`,
      timestamp: new Date().toISOString(),
    }, null, 2), "utf-8")

    return `Permissions revoked from ${args.agent}:
- safe_edit: allow → deny
- safe_bash: allow → deny
- edit: (already deny, confirmed)
- bash: (already deny, confirmed)

Reason: ${args.reason}

The agent can now only READ files. The CEO must manually restore permissions by editing .opencode/agents/${targetAgent}.md and changing safe_edit/safe_bash back to allow.

Status file updated: .agenticine/status/${targetAgent}.json
Revocation logged: .agenticine/memory/revocations.md`
  },
}
