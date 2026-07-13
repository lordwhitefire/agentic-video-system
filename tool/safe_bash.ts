/**
 * Agenticine Safe Bash — for DOCUMENTATION department workers only.
 *
 * Checks:
 * - Blocks dangerous commands (rm -rf /, sudo, etc.)
 * - Blocks writing to .env files
 * - Logs all commands to memory (Law 6)
 *
 * WHO USES THIS: Documentation department workers only.
 * Build, quality, and meta workers use the built-in `bash` tool.
 *
 * The project path is resolved via resolveProjectPath():
 *   1. Explicit `project_path` argument from the agent
 *   2. ~/.config-agenticine/active-project.txt (the active project)
 *   3. process.cwd() (fallback)
 *
 * Place in: tool/safe_bash.ts (auto-discovered by OpenCode)
 */

export default {
  description: "Run a shell command safely (for documentation workers). Blocks dangerous commands, protects .env files, and logs to memory. Build/quality/meta workers should use the built-in bash tool instead. The project path is auto-detected from active-project.txt (or pass 'project_path' to override).",
  args: {
    command: {
      type: "string",
      description: "Shell command to execute",
    },
    project_path: {
      type: "string",
      description: "Project folder path (auto-detected from active-project.txt if omitted).",
      optional: true,
    },
  },
  async execute(args, context) {
    const { execSync } = await import("child_process")
    const fs = await import("fs")
    const path = await import("path")
    const { resolveProjectPath, isAgenticineAgent } = await import("./lib/agents-json.js")

    const agentName = context.agent || "Unknown"
    const command = args.command
    const projectPath = resolveProjectPath(args.project_path)

    // ─── Agenticine Tool Guard ───
    // Only registered Agenticine agents can use safe_bash.
    // OpenCode built-in agents (build, plan, etc.) are unaffected.
    if (!isAgenticineAgent(fs, path, agentName, projectPath)) {
      return `BLOCKED: ${agentName} is not a registered Agenticine agent. safe_bash only applies to Agenticine agents. Use the built-in bash tool instead.`
    }

    // Block dangerous commands
    const blocked = [
      { pattern: /rm\s+-rf\s+\//i, message: "BLOCKED: Cannot delete root directory" },
      { pattern: /rm\s+-rf\s+~/i, message: "BLOCKED: Cannot delete home directory" },
      { pattern: /sudo/i, message: "BLOCKED: Cannot use sudo" },
      { pattern: /chmod\s+777/i, message: "BLOCKED: Cannot set world-writable permissions" },
      { pattern: /\.env/i, message: "BLOCKED: Cannot access .env files (Law 4: security)" },
      { pattern: /DROP\s+TABLE/i, message: "BLOCKED: Cannot drop database tables" },
      { pattern: /git\s+push\s+.*main/i, message: "BLOCKED: Cannot push directly to main branch" },
      { pattern: /git\s+push\s+--force/i, message: "BLOCKED: Cannot force push" },
    ]

    for (const block of blocked) {
      if (block.pattern.test(command)) {
        return block.message
      }
    }

    // Execute the command
    let output
    try {
      output = execSync(command, {
        encoding: "utf-8",
        timeout: 60000,
        cwd: projectPath,
        maxBuffer: 1024 * 1024,
      })
    } catch (e) {
      output = `Command failed: ${e.message}`
    }

    // Law 6: Log to memory
    const memDir = path.join(projectPath, ".agenticine", "memory")
    fs.mkdirSync(memDir, { recursive: true })
    const logPath = path.join(memDir, "bash-log.md")
    const logEntry = `- **[${new Date().toISOString()}]** ${agentName} ran: \`${command.slice(0, 100)}\`\n`
    fs.appendFileSync(logPath, logEntry, "utf-8")

    // Return output (truncated if too long)
    if (output.length > 5000) {
      return output.slice(0, 5000) + "\n... (output truncated)"
    }
    return output || "(no output)"
  },
}
