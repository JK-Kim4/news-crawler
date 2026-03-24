import { ReactNode } from "react";

type SectionShellProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
};

export function SectionShell({ eyebrow, title, description, children }: SectionShellProps) {
  return (
    <section className="rounded-[2rem] border border-ink/10 bg-white/80 p-8 shadow-panel backdrop-blur">
      <p className="text-xs font-semibold uppercase tracking-[0.35em] text-ember">{eyebrow}</p>
      <div className="mt-3 mb-8 flex flex-col gap-2">
        <h2 className="font-display text-3xl text-ink">{title}</h2>
        <p className="max-w-3xl text-sm leading-7 text-ink/70">{description}</p>
      </div>
      {children}
    </section>
  );
}

