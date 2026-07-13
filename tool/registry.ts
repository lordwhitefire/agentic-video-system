/**
 * Agenticine Registry Tool — look up agent info and check relationships.
 *
 * Place in: .opencode/tools/registry.ts
 */

export default {
  description: "Look up agent information from the Agenticine registry. Check who reports to whom, what tools an agent has, or find agents by department.",
  args: {
    action: {
      type: "string",
      description: "Action: 'lookup', 'subordinates', 'superior', or 'department'",
    },
    agent: {
      type: "string",
      description: "Agent name (for 'lookup', 'subordinates', 'superior')",
    },
    department: {
      type: "string",
      description: "Department name (for 'department'): strategy, audio, production, quality, personnel",
    },
  },
  async execute(args, context) {
    const fs = await import("fs")
    const path = await import("path")

    const callerAgent = context.agent || "Unknown"

    const registryPath = path.join(process.cwd(), ".agenticine", "agents.json")
    interface AgentInfo {
      name: string;
      title?: string;
      department?: string;
      roleTier?: string;
      reportsTo?: string | null;
      subordinates?: string[];
      skillFile?: string | null;
    }
    let registry: Record<string, AgentInfo> = {}
    try {
      registry = JSON.parse(fs.readFileSync(registryPath, "utf-8"))
    } catch {
      return "Registry not found. Run Agenticine setup first."
    }

    // ─── Agenticine Tool Guard ───
    // Only registered Agenticine agents can use registry.
    // OpenCode built-in agents are unaffected.
    const _isAgenticineAgent = Object.values(registry).some(
      (a) => a.name?.toLowerCase() === callerAgent.toLowerCase()
    )
    if (!_isAgenticineAgent) {
      return `BLOCKED: ${callerAgent} is not a registered Agenticine agent. registry only applies to Agenticine agents.`
    }

    const agents = Object.values(registry)

    if (args.action === "lookup") {
      const agent = agents.find(a => a.name.toLowerCase() === args.agent?.toLowerCase())
      if (!agent) return `Agent not found: ${args.agent}`
      return JSON.stringify({
        name: agent.name,
        title: agent.title,
        department: agent.department,
        roleTier: agent.roleTier,
        reportsTo: agent.reportsTo,
        subordinates: agent.subordinates,
        skillFile: agent.skillFile,
      }, null, 2)
    }

    if (args.action === "subordinates") {
      const agent = agents.find(a => a.name.toLowerCase() === args.agent?.toLowerCase())
      if (!agent) return `Agent not found: ${args.agent}`
      return `Subordinates of ${agent.name}: ${agent.subordinates?.join(", ") || "none"}`
    }

    if (args.action === "superior") {
      const agent = agents.find(a => a.name.toLowerCase() === args.agent?.toLowerCase())
      if (!agent) return `Agent not found: ${args.agent}`
      return `Superior of ${agent.name}: ${agent.reportsTo || "none (top of chain)"}`
    }

    if (args.action === "department") {
      const deptAgents = agents.filter(a => a.department === args.department)
      return `Agents in ${args.department}: ${deptAgents.map(a => a.name).join(", ")}`
    }

    return "Unknown action. Use 'lookup', 'subordinates', 'superior', or 'department'."
  },
}
