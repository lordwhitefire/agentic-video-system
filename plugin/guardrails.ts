/**
 * Agenticine Guardrails Plugin
 * 
 * A pre-tool-call guardrails plugin for OpenCode that intercepts tool calls
 * BEFORE they execute, checks for inference patterns, and blocks violations.
 * 
 * This plugin enforces Laws 5, 7, 9, 10, and 11 in real-time:
 * - Law 5:  Blocks "I assume", "I guess", "probably", "I think" patterns
 * - Law 7:  Warns when heads/directors write code themselves
 * - Law 9:  Flags "approved/verified" claims without proof
 * - Law 10: Blocks design inference (choosing colors/layouts without citing spec)
 * - Law 11: Blocks "done" reports without all 5 verification items
 * 
 * How it works:
 * 1. Hooks into OpenCode's "tool.execute.before" lifecycle event
 * 2. Inspects the tool name + arguments
 * 3. Runs pattern checks against the arguments
 * 4. If BLOCKED: replaces the tool args with a warning message
 * 5. Logs the violation to .agenticine/memory/guardrails-log.md
 * 6. The tool still "runs" but with neutralized args — the agent sees the block message
 * 
 * Installation: add to opencode.json:
 *   "plugin": ["@agenticine/guardrails"]
 * 
 * Or for local development:
 *   "plugin": ["/path/to/agenticine-guardrails"]
 */

import { checkToolCall, type CheckResult } from "./lib/patterns.js";

import { writeFileSync, mkdirSync, appendFileSync, existsSync } from "fs";
import { join } from "path";

// ═══════════════════════════════════════════════════════════════
// Logging
// ═══════════════════════════════════════════════════════════════

const LOG_DIR = join(process.cwd(), ".agenticine", "memory");
const LOG_FILE = join(LOG_DIR, "guardrails-log.md");

function logViolation(
  toolName: string,
  agent: string,
  result: CheckResult,
  originalArgs: any
): void {
  try {
    if (!existsSync(LOG_DIR)) {
      mkdirSync(LOG_DIR, { recursive: true });
    }

    const timestamp = new Date().toISOString();
    
    for (const violation of result.violations) {
      const entry = `- **[${timestamp}]** ⛔ ${violation.patternId} (Law ${violation.law}) — Agent: ${agent} | Tool: ${toolName} | Matched: "${violation.matchedText}" | Action: ${result.blocked ? "BLOCKED" : "WARNED"} | Message: ${violation.message}\n`;
      appendFileSync(LOG_FILE, entry, "utf-8");
    }
  } catch (e) {
    // Logging is best-effort — don't crash the plugin
    console.error("[guardrails] Failed to log violation:", e);
  }
}

// ═══════════════════════════════════════════════════════════════
// Block message generator
// ═══════════════════════════════════════════════════════════════

function generateBlockMessage(toolName: string, result: CheckResult): string {
  const blockViolations = result.violations.filter(v => {
    // Get severity from patterns
    return true; // All violations in a blocked result are blocking
  });

  let msg = `⛔ BLOCKED BY GUARDRAILS\n\n`;
  msg += `The ${toolName} tool call was intercepted and blocked.\n\n`;
  msg += `Violations found: ${result.violations.length}\n\n`;
  
  for (const v of result.violations) {
    msg += `▸ ${v.patternId} (Law ${v.law}): ${v.message}\n`;
    msg += `  Matched: "${v.matchedText}"\n`;
    msg += `  Fix: ${v.suggestion}\n\n`;
  }
  
  msg += `The tool call has been neutralized. Fix the violations and try again.\n`;
  msg += `If you believe this is a false positive, ask your superior to review.\n`;
  
  return msg;
}

// ═══════════════════════════════════════════════════════════════
// Plugin entry point
// ═══════════════════════════════════════════════════════════════

export default function guardrailsPlugin(input: any, options?: any) {
  const { client, worktree } = input;

  return {
    // ═══ "tool.execute.before" — THE KEY HOOK ═══
    // This fires BEFORE any tool executes. We inspect the args,
    // check for inference patterns, and block if needed.
    "tool.execute.before": async (toolInput: any, output: any) => {
      const { tool, sessionID, callID } = toolInput;
      const args = output.args;

      // Skip non-Agenticine tools (built-in OpenCode tools are not checked)
      const agenticineTools = ["safe_edit", "safe_bash", "broadcast", "create_agent", "update_plan", "revoke", "status", "memory", "registry"];
      if (!agenticineTools.includes(tool)) {
        return;
      }

      // Get agent name from the session (best-effort)
      let agentName = "Unknown";
      try {
        const session = await client.session.get(sessionID);
        agentName = session?.data?.agent?.name || session?.agent?.name || "Unknown";
      } catch {
        // If we can't get the agent name, continue with "Unknown"
      }

      // Run the pattern checks
      const result = checkToolCall(tool, args);

      if (result.violations.length === 0) {
        // No violations — let the tool run normally
        return;
      }

      // Log all violations
      logViolation(tool, agentName, result, args);

      if (result.blocked) {
        // ═══ BLOCK: Replace the tool args with a block message ═══
        // The tool will still "run" but with neutralized args that
        // contain the block message instead of the original content.
        
        const blockMessage = generateBlockMessage(tool, result);

        if (tool === "safe_edit") {
          // Replace the content with the block message
          output.args = {
            ...args,
            content: `/*\n${blockMessage}\n*/\n// The original content was blocked by guardrails.\n// Fix the violations listed above and try again.\n`,
          };
        } else if (tool === "safe_bash") {
          // Replace the command with a no-op that prints the block message
          output.args = {
            ...args,
            command: `echo '${blockMessage.replace(/'/g, "'\\''")}'`,
          };
        } else if (tool === "broadcast") {
          // Replace the message with the block message
          output.args = {
            ...args,
            message: blockMessage,
          };
        } else {
          // For other tools, stringify the block message into the args
          output.args = {
            ...args,
            _guardrails_blocked: true,
            _guardrails_message: blockMessage,
          };
        }
      } else {
        // ═══ WARN: Let the tool run, but the violation is logged ═══
        // The agent will see the warning in the guardrails log
        // and Daedalus can review it
      }
    },

    // ═══ "tool.execute.after" — Post-execution logging ═══
    // After a blocked tool runs, we can add additional context
    "tool.execute.after": async (toolInput: any, output: any) => {
      const { tool, args } = toolInput;
      
      // If the tool was blocked, append a note to the output
      if (args?._guardrails_blocked || (args?.content && args.content.includes("BLOCKED BY GUARDRAILS"))) {
        output.title = `⛔ BLOCKED by guardrails — see guardrails-log.md`;
      }
    },

    // ═══ Config hook — verify guardrails is installed ═══
    "config": async (configInput: any) => {
      // Ensure the log directory exists
      if (!existsSync(LOG_DIR)) {
        mkdirSync(LOG_DIR, { recursive: true });
      }
      if (!existsSync(LOG_FILE)) {
        writeFileSync(LOG_FILE, 
          "# Agenticine Guardrails — Violation Log\n\n" +
          "> Auto-generated by the guardrails plugin. Every inference pattern\n" +
          "> detected by the pre-tool-call hook is logged here.\n\n",
          "utf-8"
        );
      }
    },
  };
}
