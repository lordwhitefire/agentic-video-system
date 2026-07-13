/**
 * Agenticine Bash Tool — overrides OpenCode's built-in "bash" tool.
 *
 * Same enforcement pattern as edit.ts. See that file for the full
 * explanation of why this exists.
 *
 * Place in: tool/bash.ts (auto-discovered by OpenCode, overrides built-in)
 */

export default {
  description: "Run a shell command. Agenticine enforces per-agent permissions — agents with 'bash: deny' in their .md file are blocked here, regardless of whether they're a primary agent or a subagent.",
  args: {
    command: {
      type: "string",
      description: "Shell command to execute",
    },
  },
  async execute(args, context) {
    // ═══════════════════════════════════════════════════════════════
    // PERMISSION CHECK — FIRST LINE
    // ═══════════════════════════════════════════════════════════════
    const agentName = context.agent || context.agentName || "unknown"
    const { checkPermission, blockedMessage } = await import("./lib/permission-check.js")

    const perm = checkPermission(agentName, "bash")
    if (!perm.allowed) {
      return blockedMessage(agentName, "bash", perm.source)
    }

    // ═══════════════════════════════════════════════════════════════
    // PERMISSION PASSED — EXECUTE THE COMMAND
    // ═══════════════════════════════════════════════════════════════
    const { execSync } = await import("child_process")
    const { resolveProjectPath } = await import("./lib/agents-json.js")
    const projectPath = resolveProjectPath()

    let output
    try {
      output = execSync(args.command, {
        encoding: "utf-8",
        timeout: 60000,
        cwd: projectPath,
        maxBuffer: 1024 * 1024,
      })
    } catch (e) {
      output = `Command failed: ${e.message}`
    }

    if (output.length > 5000) {
      return output.slice(0, 5000) + "\n... (output truncated)"
    }
    return output || "(no output)"
  },
}
