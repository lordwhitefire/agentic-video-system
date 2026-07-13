/**
 * Agenticine Write Tool — overrides OpenCode's built-in "write" tool.
 *
 * Same enforcement pattern as edit.ts. Write uses the "edit" permission
 * (they share the same gate — if you can edit, you can write).
 *
 * Place in: tool/write.ts (auto-discovered by OpenCode, overrides built-in)
 */

export default {
  description: "Write content to a file. Agenticine enforces per-agent permissions — agents with 'edit: deny' in their .md file are blocked here (write uses the edit permission), regardless of whether they're a primary agent or a subagent.",
  args: {
    path: {
      type: "string",
      description: "File path to write (relative to project or absolute)",
    },
    content: {
      type: "string",
      description: "File content to write",
    },
  },
  async execute(args, context) {
    const fs = await import("fs")
    const path = await import("path")

    // ═══════════════════════════════════════════════════════════════
    // PERMISSION CHECK — FIRST LINE
    // ═══════════════════════════════════════════════════════════════
    const agentName = context.agent || context.agentName || "unknown"
    const { checkPermission, blockedMessage } = await import("./lib/permission-check.js")

    // write uses the edit permission
    const perm = checkPermission(agentName, "write")
    if (!perm.allowed) {
      return blockedMessage(agentName, "write", perm.source)
    }

    // ═══════════════════════════════════════════════════════════════
    // PERMISSION PASSED — WRITE THE FILE
    // ═══════════════════════════════════════════════════════════════
    const { resolveProjectPath } = await import("./lib/agents-json.js")
    const projectPath = resolveProjectPath()

    const filePath = path.isAbsolute(args.path) ? args.path : path.join(projectPath, args.path)

    fs.mkdirSync(path.dirname(filePath), { recursive: true })
    fs.writeFileSync(filePath, args.content, "utf-8")

    const lines = args.content.split("\n").length
    return `File written: ${args.path} (${lines} lines) — by ${agentName} (permission: ${perm.source})`
  },
}
