"use client";

interface TagBadgeProps {
  tag: string;
}

export default function TagBadge({ tag }: TagBadgeProps) {
  return (
    <span className="inline-block bg-accent-blue/15 text-accent-blue text-xs font-medium px-2.5 py-1 rounded-full">
      {tag}
    </span>
  );
}
