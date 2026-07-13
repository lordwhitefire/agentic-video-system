/**
 * Inference Pattern Database
 * 
 * These patterns are checked against tool arguments BEFORE execution.
 * If any pattern matches, the tool call is BLOCKED and logged.
 */

export type Severity = "block" | "warn" | "log";

export interface InferencePattern {
  id: string;
  pattern: RegExp;
  severity: Severity;
  law: number;
  message: string;
  suggestion: string;
}

export const INFERENCE_PATTERNS: InferencePattern[] = [
  // ═══ Law 5 / Law 10: Textual Inference Patterns ═══
  {
    id: "INF-001",
    pattern: /\bI assume\b/gi,
    severity: "block",
    law: 5,
    message: "Inference detected: 'I assume' — you are guessing without evidence",
    suggestion: "Cite a source (e.g., 'Per design-spec.md §1.1...') or ask your superior via the question tool"
  },
  {
    id: "INF-002",
    pattern: /\bI guess\b/gi,
    severity: "block",
    law: 5,
    message: "Inference detected: 'I guess' — you are guessing without evidence",
    suggestion: "Cite a source or ask your superior via the question tool"
  },
  {
    id: "INF-003",
    pattern: /\bprobably\b/gi,
    severity: "block",
    law: 5,
    message: "Inference detected: 'probably' — you are guessing without evidence",
    suggestion: "Cite a source or ask your superior via the question tool"
  },
  {
    id: "INF-004",
    pattern: /\bI think this should\b/gi,
    severity: "block",
    law: 5,
    message: "Inference detected: 'I think this should' — you are guessing without evidence",
    suggestion: "Cite a source or ask your superior via the question tool"
  },
  {
    id: "INF-005",
    pattern: /\bI think the (?:theme|color|layout|font|style) should be\b/gi,
    severity: "block",
    law: 10,
    message: "Design inference detected: guessing visual properties without source",
    suggestion: "Check design-spec.md for the exact value, or ask Intelligence to research it"
  },
  {
    id: "INF-006",
    pattern: /\b(?:let's|lets) go with\b/gi,
    severity: "block",
    law: 5,
    message: "Inference detected: 'let's go with' — you are guessing without evidence",
    suggestion: "Cite a source or ask your superior via the question tool"
  },
  {
    id: "INF-007",
    pattern: /\bI'll use\b/gi,
    severity: "warn",
    law: 10,
    message: "Potential inference: 'I'll use' — are you citing a source for this decision?",
    suggestion: "Add a source citation (e.g., 'I'll use #E21818 per design-spec.md §1.1')"
  },
  {
    id: "INF-008",
    pattern: /\bmaybe (?:we|I) (?:should|could|can)\b/gi,
    severity: "warn",
    law: 5,
    message: "Potential inference: 'maybe we should' — are you guessing?",
    suggestion: "If you have evidence, cite it. If not, ask your superior via the question tool"
  },
  {
    id: "INF-009",
    pattern: /\bas far as I know\b/gi,
    severity: "block",
    law: 5,
    message: "Inference detected: 'as far as I know' — you are guessing without verified evidence",
    suggestion: "Cite a source or ask your superior via the question tool"
  },
  {
    id: "INF-010",
    pattern: /\bI believe\b/gi,
    severity: "block",
    law: 5,
    message: "Inference detected: 'I believe' — you are guessing without evidence",
    suggestion: "Cite a source or ask your superior via the question tool"
  },

  // ═══ Law 10: Design Inference Patterns ═══
  {
    id: "DES-001",
    pattern: /\b(?:dark|light) theme with (?:amber|gold|blue|green|purple|teal|cyan|orange|yellow) accents?\b/gi,
    severity: "block",
    law: 10,
    message: "Design inference: choosing a color scheme without citing the spec",
    suggestion: "Read design-spec.md §1 for exact colors. The accent is #E21818 (red), not amber/gold"
  },
  {
    id: "DES-002",
    pattern: /\blooks good\b/gi,
    severity: "warn",
    law: 10,
    message: "Design inference: 'looks good' is subjective — cite the spec",
    suggestion: "Replace with 'matches design-spec.md §X.Y' or take a screenshot comparison"
  },
  {
    id: "DES-003",
    pattern: /\b(?:should|will) use (?:amber|gold|slate|indigo|blue|teal|cyan)\b/gi,
    severity: "block",
    law: 10,
    message: "Design inference: choosing colors without citing the spec",
    suggestion: "Check design-spec.md — the accent is #E21818 (red), dark bg is #141618"
  },

  // ═══ Law 11: Missing Verification Proof ═══
  {
    id: "VER-001",
    pattern: /\b(?:done|complete|finished|built)\s*(?:\.|!|$)/gi,
    severity: "warn",
    law: 11,
    message: "Potential missing verification: reporting 'done' — include all 5 proof items",
    suggestion: "Include: (1) what built, (2) source citations, (3) comparison, (4) test results, (5) metrics"
  },
  {
    id: "VER-002",
    pattern: /\b(?:approved|verified|passed)\s*(?:\.|!|$)/gi,
    severity: "warn",
    law: 9,
    message: "Potential false approval: claiming 'approved' without proof",
    suggestion: "Include screenshot comparison, lint results, and spec compliance score"
  },

  // ═══ Law 7: Hierarchy Violations ═══
  {
    id: "HIE-001",
    pattern: /\bI (?:wrote|created|built|implemented) (?:the|a|this) (?:component|page|file|function|class|module)\b/gi,
    severity: "warn",
    law: 7,
    message: "Hierarchy warning: if you are a Head or Director, you should NOT write code yourself",
    suggestion: "Delegate to your team via task(). Only Seniors and Juniors write code."
  },
];

// ═══ Tool-specific checks ═══

export interface CheckResult {
  blocked: boolean;
  violations: {
    patternId: string;
    law: number;
    message: string;
    suggestion: string;
    matchedText: string;
  }[];
}

/**
 * Check safe_edit arguments for inference patterns.
 */
export function checkSafeEdit(args: any): CheckResult {
  const content = args?.content || "";
  const path = args?.path || "";
  
  const violations: CheckResult["violations"] = [];
  
  for (const pattern of INFERENCE_PATTERNS) {
    const matches = content.match(pattern.pattern);
    if (matches) {
      for (const match of matches) {
        violations.push({
          patternId: pattern.id,
          law: pattern.law,
          message: pattern.message,
          suggestion: pattern.suggestion,
          matchedText: match,
        });
      }
    }
  }
  
  // Check for missing source citations in code files
  if (path.endsWith(".tsx") || path.endsWith(".ts") || path.endsWith(".jsx") || path.endsWith(".js")) {
    const colorPattern = /#[0-9a-fA-F]{6}/g;
    const colors = content.match(colorPattern);
    if (colors) {
      const citationPattern = /(?:per|cite|spec|§)\s/i;
      for (const color of [...new Set(colors)] as string[]) {
        const colorIndex = content.indexOf(color);
        const surrounding = content.substring(Math.max(0, colorIndex - 100), colorIndex + 50);
        if (!citationPattern.test(surrounding)) {
          violations.push({
            patternId: "CITE-001",
            law: 10,
            message: `Missing source citation for color ${color}`,
            suggestion: `Add a comment: // ${color} per design-spec.md §X.Y`,
            matchedText: color,
          });
        }
      }
    }
  }
  
  const blocked = violations.some(v => 
    INFERENCE_PATTERNS.find(p => p.id === v.patternId)?.severity === "block"
  );
  
  return { blocked, violations };
}

/**
 * Check safe_bash arguments for inference patterns.
 */
export function checkSafeBash(args: any): CheckResult {
  const command = args?.command || "";
  const violations: CheckResult["violations"] = [];
  
  for (const pattern of INFERENCE_PATTERNS) {
    if (pattern.severity === "block") {
      const matches = command.match(pattern.pattern);
      if (matches) {
        violations.push({
          patternId: pattern.id,
          law: pattern.law,
          message: pattern.message,
          suggestion: pattern.suggestion,
          matchedText: matches[0],
        });
      }
    }
  }
  
  return { blocked: violations.length > 0, violations };
}

/**
 * Check broadcast arguments for "done" reports without verification proof.
 */
export function checkBroadcast(args: any): CheckResult {
  const message = args?.message || "";
  const violations: CheckResult["violations"] = [];
  
  const isDoneReport = /\b(?:done|complete|finished|built|approved)\b/gi.test(message);
  
  if (isDoneReport) {
    const hasWhatBuilt = /\b(?:file|files|component|page|deliverable|report)\b/i.test(message);
    const hasCitations = /\b(?:per|cite|spec|§)\b/i.test(message);
    const hasComparison = /\b(?:screenshot|comparison|match|pixel)\b/i.test(message);
    const hasTests = /\b(?:lint|test|pass|0 errors)\b/i.test(message);
    const hasMetrics = /\b(?:files?\s*(?:changed|added)?|lines?\s*(?:added|changed)?|violations?\s*:\s*0)\b/i.test(message);
    
    const missing: string[] = [];
    if (!hasWhatBuilt) missing.push("WHAT YOU BUILT");
    if (!hasCitations) missing.push("SOURCE CITATIONS");
    if (!hasComparison) missing.push("COMPARISON");
    if (!hasTests) missing.push("TEST RESULTS");
    if (!hasMetrics) missing.push("METRICS");
    
    if (missing.length > 0) {
      violations.push({
        patternId: "VER-003",
        law: 11,
        message: `Incomplete verification proof — missing: ${missing.join(", ")}`,
        suggestion: `Include all 5 items: ${missing.join(", ")} (Law 11)`,
        matchedText: message.substring(0, 100),
      });
    }
  }
  
  return { blocked: violations.length > 0, violations };
}

/**
 * General check for any tool — dispatches to the right checker.
 */
export function checkToolCall(toolName: string, args: any): CheckResult {
  switch (toolName) {
    case "safe_edit":
      return checkSafeEdit(args);
    case "safe_bash":
      return checkSafeBash(args);
    case "broadcast":
      return checkBroadcast(args);
    default:
      return { blocked: false, violations: [] };
  }
}
