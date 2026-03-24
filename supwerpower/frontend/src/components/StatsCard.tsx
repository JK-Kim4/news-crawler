"use client";

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color?: string;
}

export default function StatsCard({
  title,
  value,
  icon,
  color = "text-accent-blue",
}: StatsCardProps) {
  return (
    <div className="card flex items-center gap-4">
      <div
        className={`w-12 h-12 rounded-xl flex items-center justify-center ${color} bg-current/10`}
        style={{ backgroundColor: "rgba(59, 130, 246, 0.1)" }}
      >
        <div className={color}>{icon}</div>
      </div>
      <div>
        <p className="text-sm text-gray-400">{title}</p>
        <p className="text-2xl font-bold text-gray-100">{value}</p>
      </div>
    </div>
  );
}
