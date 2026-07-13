/**
 * Agenticine Report Metrics Tool
 * 
 * Called by workers to report their task metrics.
 * The metrics are stored in .agenticine/memory/metrics/<task-id>.json
 * Superiors read these metrics before signing off.
 * 
 * This tool is the "metrics" half of the checks-and-balances system.
 * The other half is verify_work (called by superiors to sign off).
 */

import { emptyMetrics, type TaskMetrics } from "./lib/metrics.js";

export default {
  description: "Report your task metrics. Call this BEFORE reporting 'done' to your superior. Your superior will read these metrics to decide whether to approve your work. Include ALL fields — missing fields will flag as incomplete verification proof.",

  args: {
    task_id: {
      type: "string",
      description: "Task identifier (e.g., 'ticket-001', 'build-header')",
    },
    task_description: {
      type: "string",
      description: "Brief description of what you built",
    },
    files_changed: {
      type: "number",
      description: "Number of files created or modified",
    },
    lines_added: {
      type: "number",
      description: "Total lines added across all files",
    },
    max_file_size: {
      type: "number",
      description: "Line count of the largest file (must be ≤300 per Law 2)",
    },
    lint_errors: {
      type: "number",
      description: "Number of lint errors (must be 0)",
    },
    lint_warnings: {
      type: "number",
      description: "Number of lint warnings",
    },
    spec_checks_total: {
      type: "number",
      description: "How many spec items apply to this task",
    },
    spec_checks_passed: {
      type: "number",
      description: "How many spec items were verified compliant",
    },
    spec_citations: {
      type: "number",
      description: "How many source citations in code comments (e.g., '// per design-spec.md §1.1')",
    },
    visual_match_score: {
      type: "number",
      description: "Visual match score 0-100 (null if not a visual task)",
    },
    screenshot_comparison: {
      type: "boolean",
      description: "Did you do a screenshot comparison? (required for visual tasks)",
    },
    inference_violations: {
      type: "number",
      description: "Number of inference violations from guardrails (must be 0)",
    },
    source_citation_rate: {
      type: "number",
      description: "Percentage of design decisions with source citations (0-100, should be ≥80)",
    },
    delegation_used: {
      type: "number",
      description: "How many task() calls you used this session",
    },
    delegation_max: {
      type: "number",
      description: "Your tier's max delegation budget (worker: 0, head: 6)",
    },
    tests_run: {
      type: "number",
      description: "Number of tests run",
    },
    tests_passed: {
      type: "number",
      description: "Number of tests passed",
    },
    has_what_built: {
      type: "boolean",
      description: "Verification proof item 1: Did you list what you built?",
    },
    has_citations: {
      type: "boolean",
      description: "Verification proof item 2: Did you cite sources for decisions?",
    },
    has_comparison: {
      type: "boolean",
      description: "Verification proof item 3: Did you do a comparison (screenshot/spec)?",
    },
    has_test_results: {
      type: "boolean",
      description: "Verification proof item 4: Did you include test/lint results?",
    },
    has_metrics: {
      type: "boolean",
      description: "Verification proof item 5: Did you include metrics? (always true if you're calling this tool)",
    },
  },

  async execute(args: any, context: any) {
    const fs = await import("fs");
    const path = await import("path");

    const agentName = context.agent || "Unknown";

    // ─── Agenticine Tool Guard ───
    const regPath = path.join(process.cwd(), ".agenticine", "agents.json");
    let isAgenticine = false;
    try {
      const reg = JSON.parse(fs.readFileSync(regPath, "utf-8"));
      isAgenticine = Object.values(reg).some(
        (a: any) => a.name?.toLowerCase() === agentName.toLowerCase()
      );
    } catch {}
    if (!isAgenticine) {
      return `BLOCKED: ${agentName} is not a registered Agenticine agent.`;
    }

    // ─── Build metrics object ───
    const metrics: TaskMetrics = {
      taskId: args.task_id,
      agentName,
      taskDescription: args.task_description || "",
      timestamp: new Date().toISOString(),
      filesChanged: args.files_changed || 0,
      linesAdded: args.lines_added || 0,
      linesRemoved: 0,
      maxFileSize: args.max_file_size || 0,
      lintErrors: args.lint_errors ?? 0,
      lintWarnings: args.lint_warnings ?? 0,
      typeErrors: 0,
      specChecksTotal: args.spec_checks_total || 0,
      specChecksPassed: args.spec_checks_passed || 0,
      specCitations: args.spec_citations || 0,
      visualMatchScore: args.visual_match_score ?? null,
      screenshotComparison: args.screenshot_comparison || false,
      pixelDifferences: null,
      inferenceViolations: args.inference_violations ?? 0,
      guardrailsBlocks: 0,
      sourceCitationRate: args.source_citation_rate ?? 0,
      delegationBudgetUsed: args.delegation_used || 0,
      delegationBudgetMax: args.delegation_max || 0,
      subordinatesSpawned: 0,
      testsRun: args.tests_run || 0,
      testsPassed: args.tests_passed || 0,
      testsFailed: (args.tests_run || 0) - (args.tests_passed || 0),
      verificationProof: {
        hasWhatBuilt: args.has_what_built || false,
        hasSourceCitations: args.has_citations || false,
        hasComparison: args.has_comparison || false,
        hasTestResults: args.has_test_results || false,
        hasMetrics: true, // They're calling this tool, so metrics are included
      },
    };

    // ─── Score the metrics ───
    const { scoreMetrics } = await import("./lib/metrics.js");
    const score = scoreMetrics(metrics);

    // ─── Save metrics to disk ───
    const metricsDir = path.join(process.cwd(), ".agenticine", "memory", "metrics");
    fs.mkdirSync(metricsDir, { recursive: true });
    const metricsFile = path.join(metricsDir, `${args.task_id}.json`);
    fs.writeFileSync(metricsFile, JSON.stringify({
      metrics,
      score,
    }, null, 2), "utf-8");

    // ─── Log to memory ───
    const logPath = path.join(process.cwd(), ".agenticine", "memory", "metrics-log.md");
    const logEntry = `- **[${metrics.timestamp}]** ${agentName} reported metrics for ${args.task_id}: Score ${score.totalScore}/100 (${score.grade}). ${score.canSignOff ? "✅ Can sign off" : "❌ BLOCKED — " + score.blockers.join("; ")}\n`;
    fs.appendFileSync(logPath, logEntry, "utf-8");

    // ─── Return result to the worker ───
    let response = `Metrics reported for task: ${args.task_id}\n\n`;
    response += `Score: ${score.totalScore}/100 (${score.grade})\n`;
    response += `Can sign off: ${score.canSignOff ? "YES ✅" : "NO ❌"}\n\n`;

    if (score.blockers.length > 0) {
      response += `BLOCKERS (must fix before your superior can approve):\n`;
      for (const b of score.blockers) {
        response += `  ❌ ${b}\n`;
      }
      response += `\n`;
    }

    if (score.warnings.length > 0) {
      response += `WARNINGS (should fix but won't block):\n`;
      for (const w of score.warnings) {
        response += `  ⚠️ ${w}\n`;
      }
      response += `\n`;
    }

    response += `Metrics saved: .agenticine/memory/metrics/${args.task_id}.json\n`;
    response += `Log: .agenticine/memory/metrics-log.md\n\n`;

    if (score.canSignOff) {
      response += `You can now report 'done' to your superior (${context.superior || "your superior"}).`;
      response += ` Include a reference to these metrics in your broadcast message.`;
      response += ` Your superior will call verify_work to sign off.\n`;
    } else {
      response += `Fix the blockers above, then re-report your metrics.\n`;
      response += `Do NOT report 'done' until your score is ≥70 and all blockers are resolved.\n`;
    }

    return response;
  },
};
