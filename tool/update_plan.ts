/**
 * Agenticine Update Plan — Editor uses this to update the shared plan file.
 *
 * The plan file at .agenticine/plan.md is the shared memory between Ralph Loop
 * iterations. Editor reads it at the start of each session and updates it
 * as work progresses. The loop script checks for "PROJECT COMPLETE" to stop.
 *
 * Place in: .opencode/tools/update_plan.ts
 */

export default {
  description: "Update the Agenticine plan file. Use this to mark tasks as done, in_progress, blocked, or remaining. Say project_complete=true ONLY when every task is verified done. This stops the Ralph Loop.",
  args: {
    task_id: {
      type: "string",
      description: "Task ID to update (e.g., 'task-001')",
    },
    status: {
      type: "string",
      description: "New status: 'done', 'in_progress', 'blocked', 'remaining'",
    },
    notes: {
      type: "string",
      description: "Notes about this update (what was done, what's blocking, etc.)",
    },
    project_complete: {
      type: "boolean",
      description: "Set to true ONLY when every task is verified done. This stops the Ralph Loop.",
    },
  },
  async execute(args, context) {
    const fs = await import("fs")
    const path = await import("path")

    const callerAgent = context.agent || "Unknown"
    const allowedPlanners = ["strategist", "audio-lead", "editor"]
    if (!allowedPlanners.includes(callerAgent.toLowerCase())) {
      return `BLOCKED: Only department heads (Strategist, Audio Lead, Editor) can update the plan. ${callerAgent} is not authorized.`
    }

    if (!args.task_id || !args.status) {
      return `BLOCKED: task_id and status are required.`
    }

    const validStatuses = ["done", "in_progress", "blocked", "remaining"]
    if (!validStatuses.includes(args.status)) {
      return `BLOCKED: status must be one of ${validStatuses.join(", ")}. Got: ${args.status}`
    }

    const planPath = path.join(process.cwd(), ".agenticine", "plan.md")
    const planDir = path.dirname(planPath)
    fs.mkdirSync(planDir, { recursive: true })

    // Read existing plan or create new one
    let content = ""
    if (fs.existsSync(planPath)) {
      content = fs.readFileSync(planPath, "utf-8")
    } else {
      content = `# Agenticine Project Plan

> This file is the shared memory between Ralph Loop iterations.
> Editor reads it at the start of each session and updates it as work progresses.
> The loop script checks for "PROJECT COMPLETE" to stop.

## Tasks

`
    }

    const timestamp = new Date().toISOString()
    const taskLine = `- **[${timestamp}]** ${args.task_id}: ${args.status.toUpperCase()} — ${args.notes || "(no notes)"}`

    // Update or add the task section
    const taskHeader = `### ${args.task_id}`
    if (content.includes(taskHeader)) {
      // Append update to existing task section
      const regex = new RegExp(`(${taskHeader}\\n(?:.*\\n)*?)(?=### |## |$)`, "g")
      if (regex.test(content)) {
        content = content.replace(regex, (match) => `${match}${taskLine}\n`)
      } else {
        content += `\n${taskHeader}\n${taskLine}\n`
      }
    } else {
      content += `\n${taskHeader}\n${taskLine}\n`
    }

    // Add PROJECT COMPLETE marker if requested
    if (args.project_complete) {
      if (!content.includes("## PROJECT COMPLETE")) {
        content += `\n## PROJECT COMPLETE\nAll tasks verified done at ${timestamp}.\n`
      }
    }

    // Law 6: enforce file length
    const lines = content.split("\n")
    if (lines.length > 300) {
      return `BLOCKED by Law 2: Plan file would have ${lines.length} lines (max 300). Archive old tasks or split the plan.`
    }

    fs.writeFileSync(planPath, content, "utf-8")

    return `Plan updated.
- Task: ${args.task_id}
- Status: ${args.status}
- Notes: ${args.notes || "(none)"}
- Plan file: .agenticine/plan.md${args.project_complete ? "\n- PROJECT COMPLETE marker set — loop will stop." : ""}`
  },
}
