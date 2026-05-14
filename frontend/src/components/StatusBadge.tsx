import clsx from "clsx";
import type { AssetStatus } from "@/lib/api";

const STYLES: Record<AssetStatus, string> = {
  pending:    "bg-gray-800  text-gray-400",
  generating: "bg-yellow-900/60 text-yellow-300 animate-pulse",
  created:    "bg-cyan-900/60 text-cyan-300",
  deploying:  "bg-blue-900/60 text-blue-300 animate-pulse",
  live:       "bg-green-900/60 text-green-300",
  optimizing: "bg-purple-900/60 text-purple-300",
  scaling:    "bg-teal-900/60 text-teal-300",
  killed:     "bg-red-950 text-red-500",
  error:      "bg-red-900/60 text-red-300",
};

const LABELS: Record<AssetStatus, string> = {
  pending:    "Pendiente",
  generating: "Generando…",
  created:    "Creado",
  deploying:  "Desplegando…",
  live:       "Live",
  optimizing: "Optimizando",
  scaling:    "Escalando",
  killed:     "Eliminado",
  error:      "Error",
};

export default function StatusBadge({ status }: { status: AssetStatus }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium",
        STYLES[status] ?? "bg-gray-800 text-gray-400",
      )}
    >
      {LABELS[status] ?? status}
    </span>
  );
}
