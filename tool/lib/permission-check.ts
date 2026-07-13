/**
 * Shared permission checker for Agenticine tools.
 *
 * Reads an agent's .md file from the global config and parses the
 * permission block to determine if a specific tool is allowed.
 *
 * This is the enforcement mechanism that replaces OpenCode's broken
 * permission system (which doesn't work for subagents).
 */

import { readFileSync, existsSync } from "fs"
import { join } from "path"
import { homedir } from "os"

/** Built-in OpenCode agents that bypass Agenticine permission enforcement. */
const BUILT_IN_AGENTS = ["build", "plan", "general", "explore", "title", "summary", "compaction"]

export interface PermissionResult {
  allowed: boolean
  source: string
  agentFile: string | null
}

/**
 * Check if an agent has permission to use a specific tool.
 *
 * @param agentName - the calling agent's name (from context.agent)
 * @param toolName - the tool to check (e.g., "edit", "bash", "write", "task")
 * @returns PermissionResult with allowed boolean and source description
 */
export function checkPermission(agentName: string, toolName: string): PermissionResult {
  const globalAgentDir = join(homedir(), ".config-agenticine", "opencode", "agent")
  const agentMdPath = join(globalAgentDir, `${agentName}.md`)

  // Built-in agents bypass enforcement
  if (BUILT_IN_AGENTS.includes(agentName.toLowerCase())) {
    return {
      allowed: true,
      source: `built-in (${agentName})`,
      agentFile: null,
    }
  }

  if (!existsSync(agentMdPath)) {
    return {
      allowed: false,
      source: `agent file not found (${agentName}), default deny`,
      agentFile: null,
    }
  }

  try {
    const mdContent = readFileSync(agentMdPath, "utf-8")
    const fmMatch = mdContent.match(/^---\n([\s\S]*?)\n---/)
    if (!fmMatch) {
      return {
        allowed: false,
        source: `${agentName}.md (no frontmatter, default deny)`,
        agentFile: agentMdPath,
      }
    }

    const frontmatter = fmMatch[1]

    // Look for the tool permission line: "  <toolName>: allow" or "  <toolName>: deny"
    const toolMatch = frontmatter.match(new RegExp(`^  ${toolName}:\\s*(\\w+)`, "m"))
    if (toolMatch) {
      const allowed = toolMatch[1].toLowerCase() === "allow"
      return {
        allowed,
        source: `${agentName}.md (${toolName}: ${toolMatch[1]})`,
        agentFile: agentMdPath,
      }
    }

    // For "write", also check "edit" permission (they share the same gate)
    if (toolName === "write") {
      const editMatch = frontmatter.match(/^  edit:\s*(\w+)/m)
      if (editMatch) {
        const allowed = editMatch[1].toLowerCase() === "allow"
        return {
          allowed,
          source: `${agentName}.md (edit: ${editMatch[1]} — write uses edit permission)`,
          agentFile: agentMdPath,
        }
      }
    }

    // No explicit permission found — default deny
    return {
      allowed: false,
      source: `${agentName}.md (no ${toolName} field, default deny)`,
      agentFile: agentMdPath,
    }
  } catch {
    return {
      allowed: false,
      source: `${agentName}.md (parse error, default deny)`,
      agentFile: agentMdPath,
    }
  }
}

/**
 * Format a BLOCKED response message.
 */
export function blockedMessage(agentName: string, toolName: string, source: string): string {
  return `BLOCKED: ${agentName} does not have permission to use ${toolName}. (Source: ${source}) Agenticine enforces per-agent permissions at the tool level — this cannot be bypassed.`
}
