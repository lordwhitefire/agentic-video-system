/**
 * Agenticine Safe Edit — for DOCUMENTATION files only.
 *
 * Enforces:
 * - Law 2: File must not exceed 300 lines after edit (keeps docs manageable)
 * - Law 5: Scans content for inference patterns (Flagger)
 * - Law 6: Logs the edit to project memory
 *
 * WHO USES THIS: Documentation department workers only.
 * Code files should use the built-in `edit` tool (no line limit).
 *
 * The project path is resolved via resolveProjectPath():
 *   1. Explicit `project_path` argument from the agent
 *   2. ~/.config-agenticine/active-project.txt (the active project)
 *   3. process.cwd() (fallback)
 *
 * Place in: tool/safe_edit.ts (auto-discovered by OpenCode)
 */

export default {
  description: "Edit a DOCUMENTATION file safely. Enforces 300-line limit (Law 2), logs to memory (Law 6), scans for inference (Law 5). For docs/memory files only — use the built-in edit tool for code files. The project path is auto-detected from active-project.txt (or pass 'project_path' to override).",
  args: {
    path: {
      type: "string",
      description: "File path to edit (relative or absolute)",
    },
    content: {
      type: "string",
      description: "New file content",
    },
    project_path: {
      type: "string",
      description: "Project folder path (auto-detected from active-project.txt if omitted).",
      optional: true,
    },
  },
  async execute(args, context) {
    const fs = await import("fs")
    const path = await import("path")
    const { resolveProjectPath, isAgenticineAgent } = await import("./lib/agents-json.js")

    const agentName = context.agent || "Unknown"
    const projectPath = resolveProjectPath(args.project_path)

    // The file path to edit (handle absolute vs relative)
    const filePath = path.isAbsolute(args.path) ? args.path : path.join(projectPath, args.path)

    // ─── Agenticine Tool Guard ───
    // Only registered Agenticine agents can use safe_edit.
    // OpenCode built-in agents (build, plan, etc.) are unaffected.
    if (!isAgenticineAgent(fs, path, agentName, projectPath)) {
      return `BLOCKED: ${agentName} is not a registered Agenticine agent. safe_edit only applies to Agenticine agents. Use the built-in edit tool instead.`
    }

    // Law 2: Check file length
    const lines = (args.content || "").split("\n")
    if (lines.length > 300) {
      return `BLOCKED by Law 2: File would have ${lines.length} lines (max 300). Split the content into smaller files.`
    }

    // Law 5: Scan for inference patterns (Flagger)
    const inferenceFlags = []
    const patterns = [
      { regex: /I assume/gi, message: "Agent wrote 'I assume' — possible inference" },
      { regex: /I guess/gi, message: "Agent wrote 'I guess' — possible inference" },
      { regex: /probably/gi, message: "Agent wrote 'probably' — possible inference" },
      { regex: /I think this should/gi, message: "Agent wrote 'I think this should' — possible inference" },
      { regex: /sk-[a-zA-Z0-9]{20,}/gi, message: "Possible API key found in code" },
      { regex: /password\s*=\s*["'][^"']+["']/gi, message: "Hardcoded password found" },
    ]
    for (const p of patterns) {
      if (p.regex.test(args.content)) {
        inferenceFlags.push(p.message)
      }
    }

    // Write the file
    fs.mkdirSync(path.dirname(filePath), { recursive: true })
    fs.writeFileSync(filePath, args.content, "utf-8")

    // Law 6: Log to memory
    const memDir = path.join(projectPath, ".agenticine", "memory")
    fs.mkdirSync(memDir, { recursive: true })
    const logPath = path.join(memDir, "edit-log.md")
    const logEntry = `- **[${new Date().toISOString()}]** ${agentName} edited ${args.path} (${lines.length} lines)\n`
    fs.appendFileSync(logPath, logEntry, "utf-8")

    // Build response
    let response = `File edited: ${args.path} (${lines.length} lines). Logged to memory. (project: ${projectPath})`
    if (inferenceFlags.length > 0) {
      response += `\n\n⚠️ FLIGGER DETECTED ${inferenceFlags.length} POTENTIAL ISSUE(S):\n`
      inferenceFlags.forEach(f => response += `  - ${f}\n`)
      response += `\nThese have been logged for review by the Reviewer agent.`
    }

    return response
  },
}
