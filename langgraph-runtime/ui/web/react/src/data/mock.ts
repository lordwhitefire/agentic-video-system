export type Agent = {
  id: string;
  name: string;
  color: string;
  headerColor?: string;
  icon: string;
  role: string;
  about: string;
  greeting: string;
  status: string;
  capabilities: string[];
  tools: string[];
};

export type SubAgent = {
  id: string;
  name: string;
  parent: string;
  status: string;
};

export type Workspace = {
  id: string;
  name: string;
};

export type Message = {
  id: string;
  role: "user" | "agent";
  paragraphs: string[];
  time: string;
  question?: boolean;
};

export const agents: Agent[] = [
  {
    id: "video-strategy",
    name: "Video Strategy Agent",
    color: "#7c3aed",
    headerColor: "#7134d7",
    icon: "target",
    role: "Your strategic partner for video success",
    about:
      "I specialize in helping you define the big picture: goals, audience, message, positioning, and strategic direction.",
    greeting:
      "I help you think through your video goals, audience, positioning, messaging, and overall approach.",
    status: "Online",
    capabilities: [
      "Market & Audience Insight",
      "Messaging & Positioning",
      "Strategy & Planning",
      "Success Frameworks",
      "Competitive Analysis",
    ],
    tools: ["Research Tools", "Trend Explorer", "Competitor Analyzer", "Reference Finder"],
  },
  {
    id: "creative-director",
    name: "Creative Director Agent",
    color: "#e6a900",
    icon: "bulb",
    role: "Your partner for bold creative direction",
    about:
      "I specialize in translating your strategy into a compelling concept, tone, and emotional direction that stands out.",
    greeting:
      "I help you shape concepts, tone, and visual style that turn your message into a memorable experience.",
    status: "Online",
    capabilities: [
      "Concept Direction",
      "Visual Identity",
      "Tone & Style",
      "Art Direction",
      "Storyboarding",
    ],
    tools: ["Moodboard Studio", "Trend Explorer", "Reference Finder", "Style Library"],
  },
  {
    id: "script-narrative",
    name: "Script & Narrative Agent",
    color: "#27a844",
    icon: "script",
    role: "Your partner for compelling storytelling",
    about:
      "I specialize in turning your message into a clear, engaging story with structure, pacing, and a voice your audience remembers.",
    greeting:
      "I help you structure your story, write the script, and shape the narrative arc from hook to resolution.",
    status: "Online",
    capabilities: [
      "Story Structure",
      "Script Writing",
      "Narrative Voice",
      "Dialogue & Pacing",
      "Story Arc Design",
    ],
    tools: ["Script Studio", "Knowledge Base", "Reference Finder", "Structure Templates"],
  },
  {
    id: "visual-design",
    name: "Visual Design Agent",
    color: "#1677d2",
    icon: "image",
    role: "Your partner for stunning visuals",
    about:
      "I specialize in defining the visual language — color, typography, imagery, and motion — that makes your video unmistakably yours.",
    greeting:
      "I help you design the visual language, look, and feel of your video so every frame is on brand.",
    status: "Online",
    capabilities: [
      "Visual Language",
      "Color & Typography",
      "Layout & Composition",
      "Motion Design",
      "Brand Consistency",
    ],
    tools: ["Design System", "Style Library", "Reference Finder", "Asset Toolkit"],
  },
  {
    id: "scene-planning",
    name: "Scene Planning Agent",
    color: "#ef6b25",
    icon: "calendar",
    role: "Your partner for shot-by-shot planning",
    about:
      "I specialize in breaking your story into scenes, shots, and sequences — planning what happens on screen from start to finish.",
    greeting:
      "I help you plan every scene and shot — timing, camera, and flow — so production runs without surprises.",
    status: "Online",
    capabilities: [
      "Shot Planning",
      "Scene Sequencing",
      "Timing & Pacing",
      "Camera Direction",
      "Continuity Planning",
    ],
    tools: ["Shot Planner", "Timeline Studio", "Camera Library", "Continuity Tools"],
  },
  {
    id: "asset-media",
    name: "Asset & Media Agent",
    color: "#159b9b",
    icon: "folder",
    role: "Your partner for sourcing and assets",
    about:
      "I specialize in finding and organizing every asset you need — footage, images, music, and references — ready for production.",
    greeting:
      "I help you gather, organize, and manage the media and assets your video needs, from sourcing to delivery.",
    status: "Online",
    capabilities: [
      "Media Sourcing",
      "Asset Organization",
      "Licensing Checks",
      "Media Cataloging",
      "Delivery Prep",
    ],
    tools: ["Media Manager", "Source Registry", "License Scanner", "Asset Library"],
  },
  {
    id: "review-feedback",
    name: "Review & Feedback Agent",
    color: "#7136d8",
    icon: "chat",
    role: "Your partner for quality and feedback",
    about:
      "I specialize in reviewing work against your goals, gathering feedback, and making sure the final video meets your standard.",
    greeting:
      "I help you review, critique, and refine the work — checking every version against the goals we set together.",
    status: "Online",
    capabilities: [
      "Quality Review",
      "Fidelity Checking",
      "Feedback Synthesis",
      "Revision Tracking",
      "Final Approval",
    ],
    tools: ["Fidelity Scanner", "Review Board", "Revision Tracker", "Law Watch"],
  },
  {
    id: "delivery-export",
    name: "Delivery & Export Agent",
    color: "#d62c7c",
    icon: "upload",
    role: "Your partner for export and delivery",
    about:
      "I specialize in preparing your finished video for delivery — formats, platforms, and final quality checks before release.",
    greeting:
      "I help you export, package, and deliver your finished video in the right formats for every platform you need.",
    status: "Online",
    capabilities: [
      "Export Planning",
      "Format Conversion",
      "Platform Delivery",
      "Quality Control",
      "Release Packaging",
    ],
    tools: ["Export Console", "Format Library", "Platform Targets", "Delivery Checklist"],
  },
];

export const subAgents: SubAgent[] = [
  { id: "audience-analyzer", name: "Audience Analyzer", parent: "video-strategy", status: "Available" },
  { id: "competitor-analyzer", name: "Competitor Analyzer", parent: "video-strategy", status: "Available" },
  { id: "market-research-analyzer", name: "Market Research Analyzer", parent: "video-strategy", status: "Available" },
  { id: "shot-analyzer", name: "Shot Analyzer", parent: "scene-planning", status: "Available" },
  { id: "clip-cutter", name: "Clip Cutter", parent: "scene-planning", status: "Available" },
  { id: "continuity-checker", name: "Continuity Checker", parent: "scene-planning", status: "Available" },
];

export const workspaces: Workspace[] = [
  { id: "cinematic-brand-film", name: "Cinematic Brand Film" },
  { id: "product-launch", name: "Product Launch" },
  { id: "brand-documentary", name: "Brand Documentary" },
];

export const resourceCategories = [
  "Knowledge Base",
  "Brand Kit",
  "Media Library",
  "Templates",
  "References",
];

export const resources: Record<string, string[]> = {
  "Knowledge Base": [
    "Brand Strategy.pdf",
    "Product Documentation.pdf",
    "Market Research.pdf",
    "Audience Research.pdf",
    "Competitor Analysis.pdf",
    "Customer Interview Notes.pdf",
  ],
  "Brand Kit": [
    "AVIS Logo.svg",
    "Brand Colors.json",
    "Typography Guidelines.pdf",
    "Visual Identity.pdf",
  ],
  "Media Library": [
    "Hero Product Image.jpg",
    "Office Footage.mp4",
    "Founder Portrait.jpg",
    "Product Closeup.mp4",
  ],
  Templates: ["Cinematic Brand Film", "Product Launch Film", "Social Campaign", "Founder Story"],
  References: ["Apple Brand Film", "Nike Campaign Reference", "Minimal Product Film"],
};

export const capabilityOptions = [
  "Market & Audience Insight",
  "Messaging & Positioning",
  "Strategy & Planning",
  "Concept Direction",
  "Success Frameworks",
];

export const toolOptions = [
  "Research Tools",
  "Trend Explorer",
  "Competitor Analyzer",
  "Reference Finder",
];

export const memoryOptions = [
  "Project Brief",
  "Audience Insights",
  "Brand Information",
  "Past Discussions",
];

export const capabilityDetails: Record<string, { description: string; tools: string[] }> = {
  "Market & Audience Insight": {
    description: "Understand audience needs, motivations, segments and market context.",
    tools: ["Research Tools", "Trend Explorer", "Competitor Analyzer"],
  },
  "Messaging & Positioning": {
    description: "Shape the core message, positioning, and talking points for the film.",
    tools: ["Research Tools", "Reference Finder"],
  },
  "Strategy & Planning": {
    description: "Define goals, success frameworks, and the overall strategic direction.",
    tools: ["Research Tools", "Trend Explorer"],
  },
  "Concept Direction": {
    description: "Lead creative concepts, tone, and the emotional direction of the piece.",
    tools: ["Reference Finder", "Style Library"],
  },
  "Success Frameworks": {
    description: "Establish measurable outcomes and the metrics that define success.",
    tools: ["Research Tools"],
  },
};

export const workspaceContext: Record<
  string,
  { brief: string; audience: string; brand: string; discussions: { day: string; title: string }[] }
> = {
  "cinematic-brand-film": {
    brief:
      "A 60–90 second cinematic brand film introducing our new product to young professionals. Premium feel, product-led story, no voiceover until approved.",
    audience:
      "Young professionals aged 24–38, urban, mobile-first, value craft and authenticity over hype. Primary: US/EU markets.",
    brand:
      "AVIS — AI Video Intelligence System. Clean, confident, human. Primary color #7134D7. Tone: premium, calm, ambitious.",
    discussions: [
      { day: "Today", title: "Brand Film Strategy" },
      { day: "Today", title: "Audience Definition" },
      { day: "Yesterday", title: "Product Positioning" },
      { day: "Yesterday", title: "Campaign Goals" },
    ],
  },
  "product-launch": {
    brief:
      "A 30 second product launch teaser for social channels. Punchy, energetic, feature-forward with a clear CTA.",
    audience:
      "Early adopters and tech enthusiasts 22–40. Short attention spans, discovery-driven platforms.",
    brand:
      "AVIS — AI Video Intelligence System. Same visual identity, faster tempo, bolder color usage.",
    discussions: [
      { day: "Today", title: "Launch Teaser Angle" },
      { day: "Yesterday", title: "Social Cutdown Plan" },
    ],
  },
  "brand-documentary": {
    brief:
      "A 4–6 minute brand documentary about the people behind AVIS. Authentic, human, story-first with minimal product focus.",
    audience:
      "Business decision-makers and partners. Long-form viewing, desktop, in-office.",
    brand:
      "AVIS — AI Video Intelligence System. Documentary warmth, natural light, restrained branding.",
    discussions: [
      { day: "Today", title: "Documentary Structure" },
      { day: "Yesterday", title: "Interview Subjects" },
    ],
  },
};

export const suggestions = [
  { id: "goals", label: "Define Goals", memory: "Project Brief" },
  { id: "audience", label: "Understand Audience", memory: "Audience Insights" },
  { id: "message", label: "Key Message", memory: "Brand Information" },
  { id: "metrics", label: "Success Metrics", memory: "Project Brief" },
  { id: "references", label: "References", memory: "Past Discussions" },
];

export const notifications = [
  { id: "n1", title: "New project resource added", time: "2 minutes ago", read: false },
  { id: "n2", title: "Audience Insights updated", time: "8 minutes ago", read: false },
  { id: "n3", title: "All caught up", time: "", read: true },
];

export const agentById = (id: string): Agent => agents.find((a) => a.id === id) ?? agents[0];

export const subAgentsOf = (agentId: string): SubAgent[] =>
  subAgents.filter((s) => s.parent === agentId);

export const greetingMessages = (agent: Agent): Message[] => [
  {
    id: "greet-1",
    role: "agent",
    paragraphs: [`Hello! I'm your ${agent.name}.`, agent.greeting, "What are we working on today?"],
    time: "10:30 AM",
  },
];

export const questionMessage: Message = {
  id: "question-1",
  role: "agent",
  question: true,
  paragraphs: [
    "Great. To align our strategy, here's what I'd like to understand:",
    "1.  What is the core message or story you want the video to communicate?",
    "2.  What emotions should the video evoke?",
    "3.  Are there key differentiators or value points to highlight?",
    "4.  Any must-have elements or constraints I should know?",
    "Share as much or as little as you have — we'll build it together.",
  ],
  time: "10:32 AM",
};

export const exampleUserMessage: Message = {
  id: "user-1",
  role: "user",
  paragraphs: [
    "I want to plan a cinematic brand film for our new product.",
    "Target audience is young professionals.",
    "Duration around 60–90 seconds.",
  ],
  time: "10:31 AM",
};