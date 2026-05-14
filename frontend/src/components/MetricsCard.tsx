"use client";

interface MetricsCardProps {
  label: string;
  value: string | number;
  sub?: string;
  color?: "green" | "blue" | "purple" | "amber";
}

const colors = {
  green:  "bg-green-950 border-green-700 text-green-400",
  blue:   "bg-blue-950  border-blue-700  text-blue-400",
  purple: "bg-purple-950 border-purple-700 text-purple-400",
  amber:  "bg-amber-950  border-amber-700  text-amber-400",
};

export default function MetricsCard({ label, value, sub, color = "blue" }: MetricsCardProps) {
  return (
    <div className={`rounded-xl border p-5 ${colors[color]}`}>
      <p className="text-xs uppercase tracking-widest opacity-60 mb-1">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
      {sub && <p className="text-xs opacity-50 mt-1">{sub}</p>}
    </div>
  );
}
