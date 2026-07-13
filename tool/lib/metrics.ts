/**
 * Agenticine Metrics System
 * 
 * Defines the concrete, measurable criteria for "success" in Agenticine.
 * Every task must have metrics reported before a superior can sign off.
 * 
 * Metrics are stored in .agenticine/memory/metrics/<task-id>.json
 * Sign-offs are stored in .agenticine/memory/sign-offs.md
 */

// ═══════════════════════════════════════════════════════════════
// Metric Types
// ═══════════════════════════════════════════════════════════════

export interface TaskMetrics {
  taskId: string;
  agentName: string;
  taskDescription: string;
  timestamp: string;

  // ── Code Metrics ──
  filesChanged: number;
  linesAdded: number;
  linesRemoved: number;
  maxFileSize: number;          // Largest file in the task (Law 2: max 300)

  // ── Quality Metrics ──
  lintErrors: number;           // Must be 0
  lintWarnings: number;
  typeErrors: number;           // TypeScript errors (must be 0)

  // ── Spec Compliance ──
  specChecksTotal: number;      // How many spec items apply to this task
  specChecksPassed: number;     // How many were verified compliant
  specCitations: number;        // How many source citations in code comments

  // ── Visual Metrics (for UI work) ──
  visualMatchScore: number | null;  // 0-100, null if N/A
  screenshotComparison: boolean;    // Was a screenshot comparison done?
  pixelDifferences: number | null;  // Number of pixel differences (lower = better)

  // ── Law Compliance ──
  inferenceViolations: number;      // Must be 0 (from guardrails log)
  guardrailsBlocks: number;         // How many times guardrails blocked this agent
  sourceCitationRate: number;       // % of design decisions with citations (0-100)

  // ── Delegation Metrics ──
  delegationBudgetUsed: number;     // How many task() calls used
  delegationBudgetMax: number;      // Max allowed for this tier
  subordinatesSpawned: number;      // How many subordinates were spawned

  // ── Test Metrics ──
  testsRun: number;
  testsPassed: number;
  testsFailed: number;

  // ─── Verification Proof ───
  verificationProof: {
    hasWhatBuilt: boolean;
    hasSourceCitations: boolean;
    hasComparison: boolean;
    hasTestResults: boolean;
    hasMetrics: boolean;
  };
}

// ═══════════════════════════════════════════════════════════════
// Sign-off Types
// ═══════════════════════════════════════════════════════════════

export interface SignOff {
  taskId: string;
  workerName: string;           // Who did the work
  superiorName: string;         // Who is signing off
  superiorTier: string;         // head or worker
  verdict: "approved" | "rejected";
  metricsSnapshot: TaskMetrics; // The metrics at time of sign-off
  feedback: string;             // Why approved or rejected
  timestamp: string;
}

// ═══════════════════════════════════════════════════════════════
// Scoring Functions
// ═══════════════════════════════════════════════════════════════

export interface ScoreResult {
  totalScore: number;           // 0-100
  grade: "A" | "B" | "C" | "D" | "F";
  canSignOff: boolean;          // True if score >= minimum threshold
  blockers: string[];           // Issues that prevent sign-off
  warnings: string[];           // Issues that don't block but need attention
}

export function scoreMetrics(metrics: TaskMetrics): ScoreResult {
  const blockers: string[] = [];
  const warnings: string[] = [];
  let score = 100;

  // ── Blockers (these prevent sign-off entirely) ──

  if (metrics.lintErrors > 0) {
    blockers.push(`Lint errors: ${metrics.lintErrors} (must be 0)`);
    score -= 20;
  }

  if (metrics.typeErrors > 0) {
    blockers.push(`Type errors: ${metrics.typeErrors} (must be 0)`);
    score -= 20;
  }

  if (metrics.maxFileSize > 300) {
    blockers.push(`File over 300 lines: ${metrics.maxFileSize} (Law 2 violation)`);
    score -= 15;
  }

  if (metrics.inferenceViolations > 0) {
    blockers.push(`Inference violations: ${metrics.inferenceViolations} (must be 0)`);
    score -= 25;
  }

  // Verification proof must be complete
  const proof = metrics.verificationProof;
  const missingProof = [
    !proof.hasWhatBuilt && "WHAT YOU BUILT",
    !proof.hasSourceCitations && "SOURCE CITATIONS",
    !proof.hasComparison && "COMPARISON",
    !proof.hasTestResults && "TEST RESULTS",
    !proof.hasMetrics && "METRICS",
  ].filter(Boolean);

  if (missingProof.length > 0) {
    blockers.push(`Missing verification proof items: ${missingProof.join(", ")}`);
    score -= 20;
  }

  // Visual work must have a comparison
  if (metrics.visualMatchScore !== null && !metrics.screenshotComparison) {
    blockers.push("Visual task without screenshot comparison");
    score -= 15;
  }

  // ── Warnings (don't block, but reduce score) ──

  if (metrics.lintWarnings > 0) {
    warnings.push(`Lint warnings: ${metrics.lintWarnings}`);
    score -= 2;
  }

  if (metrics.specChecksPassed < metrics.specChecksTotal) {
    const missed = metrics.specChecksTotal - metrics.specChecksPassed;
    warnings.push(`Spec checks missed: ${missed}/${metrics.specChecksTotal}`);
    score -= 5 * missed;
  }

  if (metrics.sourceCitationRate < 80) {
    warnings.push(`Source citation rate: ${metrics.sourceCitationRate}% (should be ≥80%)`);
    score -= 5;
  }

  if (metrics.visualMatchScore !== null && metrics.visualMatchScore < 80) {
    warnings.push(`Visual match score: ${metrics.visualMatchScore}% (should be ≥80%)`);
    score -= 10;
  }

  if (metrics.delegationBudgetUsed > metrics.delegationBudgetMax) {
    blockers.push(`Delegation budget exceeded: ${metrics.delegationBudgetUsed}/${metrics.delegationBudgetMax}`);
    score -= 15;
  }

  if (metrics.testsFailed > 0) {
    warnings.push(`Tests failed: ${metrics.testsFailed}`);
    score -= 5 * metrics.testsFailed;
  }

  // Clamp score
  score = Math.max(0, Math.min(100, score));

  // Grade
  const grade: ScoreResult["grade"] =
    score >= 90 ? "A" :
    score >= 80 ? "B" :
    score >= 70 ? "C" :
    score >= 60 ? "D" : "F";

  const canSignOff = blockers.length === 0 && score >= 70;

  return { totalScore: score, grade, canSignOff, blockers, warnings };
}

// ═══════════════════════════════════════════════════════════════
// Tier-specific minimum scores
// ═══════════════════════════════════════════════════════════════

export const MINIMUM_SCORES: Record<string, number> = {
  worker: 70,      // Workers must score at least 70
  head: 85,        // Heads must score at least 85
};

export function meetsTierMinimum(score: number, tier: string): boolean {
  const minimum = MINIMUM_SCORES[tier] || 70;
  return score >= minimum;
}

// ═══════════════════════════════════════════════════════════════
// Helper: Create empty metrics
// ═══════════════════════════════════════════════════════════════

export function emptyMetrics(taskId: string, agentName: string, taskDescription: string): TaskMetrics {
  return {
    taskId,
    agentName,
    taskDescription,
    timestamp: new Date().toISOString(),
    filesChanged: 0,
    linesAdded: 0,
    linesRemoved: 0,
    maxFileSize: 0,
    lintErrors: 0,
    lintWarnings: 0,
    typeErrors: 0,
    specChecksTotal: 0,
    specChecksPassed: 0,
    specCitations: 0,
    visualMatchScore: null,
    screenshotComparison: false,
    pixelDifferences: null,
    inferenceViolations: 0,
    guardrailsBlocks: 0,
    sourceCitationRate: 0,
    delegationBudgetUsed: 0,
    delegationBudgetMax: 0,
    subordinatesSpawned: 0,
    testsRun: 0,
    testsPassed: 0,
    testsFailed: 0,
    verificationProof: {
      hasWhatBuilt: false,
      hasSourceCitations: false,
      hasComparison: false,
      hasTestResults: false,
      hasMetrics: false,
    },
  };
}
