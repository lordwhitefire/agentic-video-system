/**
 * Agenticine Activate Project Tool
 *
 * Called by Hermes when entering a project folder for the first time.
 * Also manages the "active project" — the project Agenticine is currently
 * working on. This survives compaction because it's stored in a file.
 *
 * Actions:
 *   - check            — check if a project is activated (uses active-project.txt if no path given)
 *   - activate_new     — create .agenticine/ structure in a new project + set as active
 *   - mark_subfolder   — mark this folder as a subfolder of a parent project
 *   - switch_project   — switch the active project to a new path (activates if needed)
 *   - get_active       — return the currently active project path
 *
 * Place in: tool/activate_project.ts (auto-discovered by OpenCode)
 */

export default {
  description: "Manage the active Agenticine project. Call with action='check' on startup to see if the project is activated. Call with action='activate_new' to set up a new project. Call with action='switch_project' to change which project Agenticine works on. The active project is stored in ~/.config-agenticine/active-project.txt so it survives compaction.",
  args: {
    action: {
      type: "string",
      description: "Action: 'check' (default) | 'activate_new' | 'mark_subfolder' | 'switch_project' | 'get_active'",
      optional: true,
    },
    path: {
      type: "string",
      description: "Project folder path. If omitted, uses the active project from active-project.txt (or cwd as fallback).",
      optional: true,
    },
    parent_project_path: {
      type: "string",
      description: "For 'mark_subfolder': the path to the parent project that has memory.",
      optional: true,
    },
  },
  async execute(args, context) {
    const fs = await import("fs")
    const path = await import("path")
    const { resolveProjectPath, readActiveProject, writeActiveProject } = await import("./lib/agents-json.js")

    const action = args.action || "check"

    // ─── GET_ACTIVE: return the currently active project ───
    if (action === "get_active") {
      const active = readActiveProject()
      if (active) {
        return `ACTIVE_PROJECT: ${active}`
      }
      return `NO_ACTIVE_PROJECT: No project is currently active. Ask the user which project to work on, then call activate_project with action='switch_project' and path='<project-path>'.`
    }

    // ─── SWITCH_PROJECT: change the active project ───
    if (action === "switch_project") {
      if (!args.path) {
        return `BLOCKED: Must provide 'path' for switch_project action.`
      }

      const newPath = path.resolve(args.path)
      if (!fs.existsSync(newPath)) {
        return `BLOCKED: Path does not exist: ${newPath}`
      }

      // Write to active-project.txt
      writeActiveProject(newPath)

      // Check if it's activated
      const memoryDir = path.join(newPath, ".agenticine", "memory")
      const subfolderMarker = path.join(newPath, ".agenticine-subfolder")

      if (fs.existsSync(subfolderMarker)) {
        const parentPath = fs.readFileSync(subfolderMarker, "utf-8").trim()
        return `SWITCHED: Active project is now ${newPath}. NOTE: This is a subfolder of ${parentPath}. Use the parent's memory at ${parentPath}/.agenticine/memory/.`
      }

      if (fs.existsSync(memoryDir) && fs.existsSync(path.join(memoryDir, "STATE.md"))) {
        return `SWITCHED: Active project is now ${newPath}. Project is already activated. Read .agenticine/PROJECT.md and .agenticine/memory/work-log.md to continue.`
      }

      return `SWITCHED: Active project is now ${newPath}. Project is NOT activated yet. Ask the user: "Is this a new project, or a subfolder of an existing project?" Then call activate_project with action='activate_new' or action='mark_subfolder'.`
    }

    // ─── For check, activate_new, mark_subfolder — resolve the project path ───
    const projectPath = path.resolve(resolveProjectPath(args.path))

    // Verify the path exists
    if (!fs.existsSync(projectPath)) {
      return `BLOCKED: Project path does not exist: ${projectPath}`
    }

    const agenticineDir = path.join(projectPath, ".agenticine")
    const memoryDir = path.join(agenticineDir, "memory")
    const subfolderMarker = path.join(projectPath, ".agenticine-subfolder")

    // ─── CHECK: is this project activated? ───
    if (action === "check") {
      // Check for subfolder marker first
      if (fs.existsSync(subfolderMarker)) {
        const parentPath = fs.readFileSync(subfolderMarker, "utf-8").trim()
        return `SUBFOLDER: ${projectPath} is a subfolder of ${parentPath}. Use the parent project's memory at ${parentPath}/.agenticine/memory/. Do not create separate memory here.`
      }

      // Check for existing memory
      if (fs.existsSync(memoryDir) && fs.existsSync(path.join(memoryDir, "STATE.md"))) {
        // Update active-project.txt to this path (in case it changed)
        writeActiveProject(projectPath)
        return `ACTIVATED: ${projectPath} is already activated. Read .agenticine/PROJECT.md and .agenticine/memory/work-log.md to continue. Active project file updated.`
      }

      return `NOT_ACTIVATED: ${projectPath} has no Agenticine memory. Ask the user: "Is this a new project, or is it a subfolder of an existing Agenticine project?" Then call activate_project with action='activate_new' or action='mark_subfolder' with the parent path.`
    }

    // ─── ACTIVATE_NEW: create the .agenticine/ structure ───
    if (action === "activate_new") {
      if (fs.existsSync(memoryDir)) {
        // Already activated — just set as active and return
        writeActiveProject(projectPath)
        return `ALREADY_ACTIVATED: ${projectPath} already has .agenticine/. Active project file updated.`
      }

      // Create directory structure
      fs.mkdirSync(agenticineDir, { recursive: true })
      fs.mkdirSync(memoryDir, { recursive: true })
      fs.mkdirSync(path.join(memoryDir, "decisions"), { recursive: true })
      fs.mkdirSync(path.join(memoryDir, "research"), { recursive: true })
      fs.mkdirSync(path.join(agenticineDir, "areas"), { recursive: true })
      fs.mkdirSync(path.join(agenticineDir, "mailbox"), { recursive: true })
      fs.mkdirSync(path.join(agenticineDir, "status"), { recursive: true })
      fs.mkdirSync(path.join(agenticineDir, "repo-agents"), { recursive: true })

      // Create initial STATE.md
      const stateContent = `# Project State

## Status
**Activated:** ${new Date().toISOString()}

## Current Phase
Project initialization — intelligence department scanning codebase

## What's Done
- [ ] Project activated
- [ ] Intelligence scan complete
- [ ] Area documentation written
- [ ] PROJECT.md overview written
- [ ] First task assigned

## What's In Progress
- Waiting for intelligence department to scan the codebase

## What's Blocked
(none)
`
      fs.writeFileSync(path.join(memoryDir, "STATE.md"), stateContent, "utf-8")

      // Create empty work-log.md
      fs.writeFileSync(
        path.join(memoryDir, "work-log.md"),
        "# Agenticine Work Log\n\n> Auto-generated by activate_project. Every agent action is logged here.\n\n",
        "utf-8"
      )

      // Create empty constraints.md, errors-and-fixes.md, preferences.md, PROJECT.md
      fs.writeFileSync(
        path.join(agenticineDir, "constraints.md"),
        "# Project Constraints\n\n> Real-world constraints discovered during intelligence scan.\n\n",
        "utf-8"
      )
      fs.writeFileSync(
        path.join(agenticineDir, "errors-and-fixes.md"),
        "# Errors and Fixes\n\n> Every error encountered + how it was fixed. Auto-appended by safe_edit/safe_bash.\n\n",
        "utf-8"
      )
      fs.writeFileSync(
        path.join(agenticineDir, "preferences.md"),
        "# Developer Preferences\n\n> Accumulated preferences stated by the CEO. Not area-specific.\n\n",
        "utf-8"
      )
      fs.writeFileSync(
        path.join(agenticineDir, "PROJECT.md"),
        "# Project Overview\n\n> This file is the entry point. Hermes reads this first. To be filled in by the documentation department after the intelligence scan.\n\n## Project Name\n(To be filled)\n\n## Goal\n(To be filled)\n\n## Tech Stack Summary\n(To be filled)\n\n## Current Status\nProject initialization — awaiting intelligence scan\n",
        "utf-8"
      )

      // Create empty plan.md
      fs.writeFileSync(
        path.join(agenticineDir, "plan.md"),
        "# Project Plan\n\n> Updated by Hermes via the update_plan tool. The Ralph Loop checks for '## PROJECT COMPLETE'.\n\n## Tasks\n\n- [ ] Intelligence scan\n- [ ] Documentation\n- [ ] Build\n\n## PROJECT COMPLETE\n\n(Remove this line when complete)\n",
        "utf-8"
      )

      // Try to copy agents.json from the global template
      const possiblePaths = [
        path.join(__dirname, "..", "project-template", "agents.json"),
        path.join(process.env.HOME || "", ".config-agenticine", "opencode", "project-template", "agents.json"),
      ]

      let agentsJsonCopied = false
      for (const p of possiblePaths) {
        try {
          if (fs.existsSync(p)) {
            fs.copyFileSync(p, path.join(agenticineDir, "agents.json"))
            agentsJsonCopied = true
            break
          }
        } catch {}
      }

      if (!agentsJsonCopied) {
        fs.writeFileSync(
          path.join(agenticineDir, "agents.json"),
          JSON.stringify({ agents: [] }, null, 2),
          "utf-8"
        )
      }

      // Set as active project
      writeActiveProject(projectPath)

      return `ACTIVATED: Created .agenticine/ structure at ${projectPath}. Active project file updated. Now delegate to Athena (Intelligence) to scan the codebase. Intelligence will write findings to .agenticine/memory/research/. Then Documentation department will write area docs to .agenticine/areas/ and fill in PROJECT.md.`
    }

    // ─── MARK_SUBFOLDER: create the marker file ───
    if (action === "mark_subfolder") {
      if (!args.parent_project_path) {
        return `BLOCKED: Must provide parent_project_path for mark_subfolder action.`
      }

      const parentPath = path.resolve(args.parent_project_path)
      const parentMemory = path.join(parentPath, ".agenticine", "memory")
      if (!fs.existsSync(parentMemory)) {
        return `BLOCKED: Parent project at ${parentPath} does not have .agenticine/memory/. Are you sure it's a Agenticine project?`
      }

      // Create the marker file
      fs.writeFileSync(subfolderMarker, parentPath, "utf-8")

      // Set parent as active project (since this is a subfolder)
      writeActiveProject(parentPath)

      return `MARKED: ${projectPath} is now marked as a subfolder of ${parentPath}. Agenticine will use the parent's memory. Active project set to the parent. You will not be asked again.`
    }

    return `Unknown action: ${action}. Use 'check', 'activate_new', 'mark_subfolder', 'switch_project', or 'get_active'.`
  },
}
