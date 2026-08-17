import type { ReactNode } from "react";

function inline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\))/g);
  return parts.map((part, i) => {
    if (!part) return null;
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={i}>{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("[") && part.includes("](")) {
      const m = part.match(/^\[([^\]]+)\]\(([^)\s]+)\)$/);
      if (m) {
        return (
          <a key={i} href={m[2]} target="_blank" rel="noreferrer">
            {m[1]}
          </a>
        );
      }
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return part.split("\n").flatMap((line, j, arr) =>
      j === arr.length - 1
        ? [line]
        : [line, <br key={`${i}-${j}`} />],
    );
  });
}

function block(text: string): ReactNode {
  const trimmed = text.trim();
  const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
  if (heading) {
    const Tag = `h${heading[1].length}` as "h1" | "h2" | "h3";
    return <Tag>{inline(heading[2])}</Tag>;
  }
  const lines = trimmed.split("\n");
  if (lines.every((l) => /^[-*]\s+/.test(l))) {
    return (
      <ul>
        {lines.map((l, i) => (
          <li key={i}>{inline(l.replace(/^[-*]\s+/, ""))}</li>
        ))}
      </ul>
    );
  }
  if (lines.every((l) => /^\d+\.\s+/.test(l))) {
    return (
      <ol>
        {lines.map((l, i) => (
          <li key={i}>{inline(l.replace(/^\d+\.\s+/, ""))}</li>
        ))}
      </ol>
    );
  }
  return <p>{inline(trimmed)}</p>;
}

export function Markdown({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/).filter((b) => b.trim().length > 0);
  if (blocks.length === 0) return null;
  return (
    <div className="markdown">
      {blocks.map((b, i) => (
        <div key={i}>{block(b)}</div>
      ))}
    </div>
  );
}