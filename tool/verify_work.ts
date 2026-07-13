/**
 * Agenticine Verify Work Tool
 * 
 * Called by SUPERIORS (seniors, leads, directors, heads) to sign off on
 * their subordinate's work. This is the "checks and balances" half.
 * 
 * The superior reads the subordinate's metrics (from report_metrics),
 * runs their tier-specific review checklist, and records a verdict.
 * 
 * If APPROVED: the task can move to "done"
 * If REJECTED: the task goes back to the worker with specific feedback
 * 
 * Sign-offs are stored in .agenticine/memory/sign-offs.md
 * 
 * CRITICAL: This tool enforces the verification chain:
 *   Junior → Senior verifies → Lead verifies → Director verifies → Head verifies → Hermes verifies
 * No task is "done" until the full chain signs off.
 */

export default {
  description: "Sign off on a subordinate's work. Read their metrics, run your review checklist, and record approved/rejected. If rejected, provide specific feedback for what to fix. Sign-offs are logged permanently.",

  args: {
    task_id: {
      type: "string",
      description: "The task ID being verified (must match the report_metrics task_id)",
    },
    worker_name: {
      type: "string",
      description: "Name of the agent whose work you're verifying (your direct subordinate)",
    },
    verdict: {
      type: "string",
      description: "Your verdict: 'approved' or 'rejected'",
    },
    feedback: {
      type: "string",
      description: "If approved: why it passed. If rejected: specific issues to fix (be concrete — cite the spec section that was violated).",
    },
    review_checklist_passed: {
      type: "array",
      items: { type: "string" },
      description: "List of checklist items you verified (e.g., ['lint passes', 'spec compliance', 'integration checked'])",
    },
    review_checklist_failed: {
      type: "array",
      items: { type: "string" },
      description: "List of checklist items that failed (empty if all passed)",
    },
  },

  async execute(args: any, context: any) {
    const fs = await import("fs");
    const path = await import("path");

    const superiorName = context.agent || "Unknown";

    // ─── Guard 1: Must be a registered Agenticine agent ───
    const regPath = path.join(process.cwd(), ".agenticine", "agents.json");
    let registry: any = {};
    try {
      registry = JSON.parse(fs.readFileSync(regPath, "utf-8"));
    } catch {
      return `BLOCKED: Could not read .agenticine/agents.json.`;
    }

    const superiorInfo = Object.values(registry).find(
      (a: any) => a.name?.toLowerCase() === superiorName.toLowerCase()
    );
    if (!superiorInfo) {
      return `BLOCKED: ${superiorName} is not a registered Agenticine agent.`;
    }

    // ─── Guard 2: Must be a superior tier (not junior) ───
    const superiorTier = (superiorInfo as any).roleTier || (superiorInfo as any).tier || "junior";
    if (superiorTier === "junior") {
      return `BLOCKED: Juniors cannot verify work. Only seniors, leads, directors, and heads can call verify_work.`;
    }

    // ─── Guard 3: The worker must be a direct subordinate ───
    const subordinates = (superiorInfo as any).subordinates || [];
    const workerName = args.worker_name.toLowerCase();
    const isDirectSubordinate = subordinates.some(
      (s: string) => s.toLowerCase() === workerName
    );

    if (!isDirectSubordinate) {
      return `BLOCKED: ${args.worker_name} is not your direct subordinate. Your subordinates are: ${subordinates.join(", ") || "none"}. You can only verify work from your direct subordinates (Law 4: chain of command).`;
    }

    // ─── Guard 4: The worker must have reported metrics ───
    const metricsFile = path.join(
      process.cwd(), ".agenticine", "memory", "metrics", `${args.task_id}.json`
    );

    let metricsData: any = null;
    try {
      metricsData = JSON.parse(fs.readFileSync(metricsFile, "utf-8"));
    } catch {
      return `BLOCKED: No metrics found for task ${args.task_id}. ${args.worker_name} must call report_metrics before you can verify their work. Tell them to report their metrics first.`;
    }

    // ─── Guard 5: If verdict is "approved", the metrics must pass ───
    const { scoreMetrics, meetsTierMinimum, MINIMUM_SCORES } = await import("./lib/metrics.js");
    const score = scoreMetrics(metricsData.metrics);

    if (args.verdict === "approved") {
      // Check for blockers
      if (score.blockers.length > 0) {
        return `BLOCKED: Cannot approve — the metrics have blockers:\n${score.blockers.map((b: string) => `  ❌ ${b}`).join("\n")}\n\nThe worker must fix these before you can approve. Reject the work with specific feedback.`;
      }

      // Check tier minimum
      const workerTier = (registry[args.worker_name.toLowerCase()] as any)?.roleTier ||
                         (registry[args.worker_name.toLowerCase()] as any)?.tier ||
                         "junior";
      const minimum = MINIMUM_SCORES[workerTier] || 70;
      if (score.totalScore < minimum) {
        return `BLOCKED: Cannot approve — score ${score.totalScore}/100 is below the ${workerTier} minimum of ${minimum}. Reject the work and ask the worker to improve their score.`;
      }

      // Check that the review checklist was actually run
      if (!args.review_checklist_passed || args.review_checklist_passed.length === 0) {
        return `BLOCKED: Cannot approve — you must run your review checklist and list which items passed. Call verify_work again with review_checklist_passed items.`;
      }

      if (args.review_checklist_failed && args.review_checklist_failed.length > 0) {
        return `BLOCKED: Cannot approve — checklist items failed: ${args.review_checklist_failed.join(", ")}. Reject the work instead.`;
      }
    }

    // ─── Record the sign-off ───
    const signOff = {
      taskId: args.task_id,
      workerName: args.worker_name,
      superiorName,
      superiorTier,
      verdict: args.verdict,
      metricsSnapshot: metricsData.metrics,
      metricsScore: score.totalScore,
      metricsGrade: score.grade,
      feedback: args.feedback || "",
      checklistPassed: args.review_checklist_passed || [],
      checklistFailed: args.review_checklist_failed || [],
      timestamp: new Date().toISOString(),
    };

    // Save to sign-offs log
    const logDir = path.join(process.cwd(), ".agenticine", "memory");
    fs.mkdirSync(logDir, { recursive: true });
    const logPath = path.join(logDir, "sign-offs.md");

    const status = args.verdict === "approved" ? "✅ APPROVED" : "❌ REJECTED";
    const logEntry = `- **[${signOff.timestamp}]** ${status} — Task: ${args.task_id} | Worker: ${args.worker_name} | Superior: ${superiorName} (${superiorTier}) | Score: ${score.totalScore}/100 (${score.grade}) | Feedback: ${args.feedback || "(none)"}\n`;
    fs.appendFileSync(logPath, logEntry, "utf-8");

    // Save detailed sign-off to JSON
    const signOffFile = path.join(logDir, "metrics", `${args.task_id}-signoff.json`);
    fs.writeFileSync(signOffFile, JSON.stringify(signOff, null, 2), "utf-8");

    // ─── Return result ───
    let response = `Verification recorded.\n\n`;
    response += `Task: ${args.task_id}\n`;
    response += `Worker: ${args.worker_name}\n`;
    response += `Superior: ${superiorName} (${superiorTier})\n`;
    response += `Verdict: ${status}\n`;
    response += `Score: ${score.totalScore}/100 (${score.grade})\n\n`;

    if (args.verdict === "approved") {
      response += `The work is approved. ${args.worker_name} can now report "done" to the next level.\n`;
      response += `Sign-off recorded: .agenticine/memory/sign-offs.md\n`;
      response += `Detailed record: .agenticine/memory/metrics/${args.task_id}-signoff.json\n`;
    } else {
      response += `The work is REJECTED. Feedback for ${args.worker_name}:\n`;
      response += `  ${args.feedback}\n\n`;
      response += `${args.worker_name} must fix these issues and re-report their metrics.\n`;
      response += `Sign-off recorded: .agenticine/memory/sign-offs.md\n`;
    }

    return response;
  },
};
