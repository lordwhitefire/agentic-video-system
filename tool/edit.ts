/**
 * Agenticine Edit Tool — overrides OpenCode's built-in "edit" tool.
 *
 * WHY THIS EXISTS:
 * OpenCode's permission system (the "permission: edit: deny" block in agent
 * .md files) only works for the primary agent — NOT for subagents spawned
 * via the task tool. This is a confirmed OpenCode bug (issues #7474, #12566,
 * #23519). Plugin-based hooks also don't catch subagent calls (issue #5894).
 *
 * THE FIX:
 * By naming this tool "edit" (same as the built-in), OpenCode uses OUR
 * version instead of the native one. There is no unguarded native tool left
 * to fall back on. The permission check is the FIRST line of code — it runs
 * unconditionally every single time, for every agent (subagent or direct).
 *
 * HOW IT WORKS:
 * 1. OpenCode passes the calling agent's name into context.agent
 * 2. We check that agent's .md file for the "edit" permission
 * 3. If denied → return BLOCKED immediately, do not touch any files
 * 4. If allowed → perform the edit (write file content)
 *
 * Place in: tool/edit.ts (auto-discovered by OpenCode, overrides built-in)
 */

export default {
  description: "Edit a file (write new content). Agenticine enforces per-agent permissions — agents with 'edit: deny' in their .md file are blocked here, regardless of whether they're a primary agent or a subagent.",
  args: {
    path: {
      type: "string",
      description: "File path to edit (relative to project or absolute)",
    },
    content: {
      type: "string",
      description: "New file content",
    },
  },
  async execute(args, context) {
    const fs = await import("fs")
    const path = await import("path")

    // ═══════════════════════════════════════════════════════════════
    // PERMISSION CHECK — FIRST LINE, BEFORE ANYTHING ELSE
    // ═══════════════════════════════════════════════════════════════
    const agentName = context.agent || context.agentName || "unknown"
    const { checkPermission, blockedMessage } = await import("./lib/permission-check.js")

    const perm = checkPermission(agentName, "edit")
    if (!perm.allowed) {
      return blockedMessage(agentName, "edit", perm.source)
    }

    // ═══════════════════════════════════════════════════════════════
    // PERMISSION PASSED — PERFORM THE EDIT
    // ═══════════════════════════════════════════════════════════════
    const { resolveProjectPath } = await import("./lib/agents-json.js")
    const projectPath = resolveProjectPath()

    // Resolve the file path (handle absolute vs relative)
    const filePath = path.isAbsolute(args.path) ? args.path : path.join(projectPath, args.path)

    // Write the file
    fs.mkdirSync(path.dirname(filePath), { recursive: true })
    fs.writeFileSync(filePath, args.content, "utf-8")

    const lines = args.content.split("\n").length
    return `File edited: ${args.path} (${lines} lines) — by ${agentName} (permission: ${perm.source})`
  },
}
