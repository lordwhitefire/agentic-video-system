/**
 * Shared helpers for Agenticine tools.
 *
 * 1. resolveProjectPath(pathOverride?) — every tool uses this to find the
 *    project folder. Resolution order:
 *      a. Explicit `path` argument from the agent (override)
 *      b. ~/.config-agenticine/active-project.txt (the active project)
 *      c. process.cwd() (fallback — only used if no active project is set)
 *
 * 2. ensureAgentsJson(fs, path, projectPath) — auto-creates agents.json
 *    if it doesn't exist, so tools never crash on first run.
 *
 * 3. readAgentsJson / isAgenticineAgent — read + check helpers.
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs"
import { join } from "path"
import { homedir } from "os"

/**
 * Returns the path to the active project file (~/.config-agenticine/active-project.txt).
 * This file stores one line: the absolute path to the currently active project.
 */
export function activeProjectFilePath(): string {
  return join(homedir(), ".config-agenticine", "active-project.txt")
}

/**
 * Reads the active project path from active-project.txt.
 * Returns null if the file doesn't exist or is empty.
 */
export function readActiveProject(): string | null {
  try {
    const filePath = activeProjectFilePath()
    if (!existsSync(filePath)) return null
    const content = readFileSync(filePath, "utf-8").trim()
    return content || null
  } catch {
    return null
  }
}

/**
 * Writes the active project path to active-project.txt.
 * Called by activate_project when activating or switching projects.
 */
export function writeActiveProject(projectPath: string): void {
  const filePath = activeProjectFilePath()
  mkdirSync(join(filePath, ".."), { recursive: true })
  writeFileSync(filePath, projectPath, "utf-8")
}

/**
 * Resolve which project folder a tool should operate on.
 *
 * Resolution order:
 *   1. pathOverride (explicit `path` argument from the agent)
 *   2. ~/.config-agenticine/active-project.txt (the active project)
 *   3. process.cwd() (fallback — only if no active project is set)
 *
 * Every tool that touches .agenticine/ should call this at the top.
 */
export function resolveProjectPath(pathOverride?: string): string {
  if (pathOverride && pathOverride.trim()) {
    return pathOverride.trim()
  }

  const active = readActiveProject()
  if (active) return active

  return process.cwd()
}

/**
 * Ensure .agenticine/agents.json exists in the given project.
 * Auto-creates with an empty agents array if missing.
 * Returns the path to agents.json.
 */
export function ensureAgentsJson(fs: any, path: any, projectPath: string): string {
  const agenticineDir = path.join(projectPath, ".agenticine")
  const regPath = path.join(agenticineDir, "agents.json")

  if (!fs.existsSync(agenticineDir)) {
    fs.mkdirSync(agenticineDir, { recursive: true })
  }

  if (!fs.existsSync(regPath)) {
    fs.writeFileSync(regPath, JSON.stringify({ agents: [] }, null, 2), "utf-8")
  }

  return regPath
}

/**
 * Read agents.json from the given project. Auto-creates if missing.
 */
export function readAgentsJson(fs: any, path: any, projectPath: string): any {
  const regPath = ensureAgentsJson(fs, path, projectPath)
  try {
    return JSON.parse(fs.readFileSync(regPath, "utf-8"))
  } catch {
    return { agents: [] }
  }
}

/**
 * Check if an agent name is registered in the project's agents.json.
 */
export function isAgenticineAgent(fs: any, path: any, agentName: string, projectPath?: string): boolean {
  const resolvedPath = projectPath || resolveProjectPath()
  const reg = readAgentsJson(fs, path, resolvedPath)
  const agents = reg.agents || Object.values(reg)
  return agents.some((a: any) => a.name?.toLowerCase() === agentName.toLowerCase())
}
