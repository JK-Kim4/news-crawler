import { AdminOverview } from "@/lib/types";

type AdminOverviewProps = {
  overview: AdminOverview;
};

const stats = [
  { key: "total_users", label: "Users" },
  { key: "total_contents", label: "Stories" },
  { key: "total_sources", label: "Sources" },
  { key: "active_sources", label: "Active" },
] as const;

export function AdminOverviewPanel({ overview }: AdminOverviewProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {stats.map((stat) => (
        <div key={stat.key} className="rounded-[1.75rem] bg-white p-6 shadow-panel">
          <p className="text-xs uppercase tracking-[0.3em] text-ink/40">{stat.label}</p>
          <p className="mt-4 font-display text-4xl text-ink">{overview[stat.key]}</p>
        </div>
      ))}
      <div className="rounded-[1.75rem] bg-moss p-6 text-white shadow-panel md:col-span-2 xl:col-span-4">
        <p className="text-xs uppercase tracking-[0.3em] text-white/70">Last Crawl</p>
        <p className="mt-3 font-display text-3xl">{overview.last_crawl_status ?? "No runs yet"}</p>
        <p className="mt-2 text-sm text-white/80">{overview.last_crawl_at ?? "Scheduler not started"}</p>
      </div>
    </div>
  );
}

