"use client";

import { Asset } from "@/lib/api";
import { ExternalLink, Trash2 } from "lucide-react";

const statusColors: Record<string, string> = {
  pending:    "bg-gray-800 text-gray-400",
  generating: "bg-yellow-900 text-yellow-400 animate-pulse",
  deploying:  "bg-blue-900 text-blue-400 animate-pulse",
  live:       "bg-green-900 text-green-400",
  optimizing: "bg-purple-900 text-purple-400",
  scaling:    "bg-teal-900 text-teal-400",
  killed:     "bg-red-950 text-red-500",
  error:      "bg-red-900 text-red-400",
};

interface Props {
  assets: Asset[];
  onDelete: (id: number) => void;
}

export default function AssetTable({ assets, onDelete }: Props) {
  if (assets.length === 0) {
    return (
      <div className="text-center py-16 text-gray-600">
        No hay activos aún. Lanza tu primer pipeline.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-800">
      <table className="w-full text-sm text-left">
        <thead className="bg-gray-900 text-gray-500 uppercase text-xs">
          <tr>
            {["ID", "Keyword", "Tipo", "Status", "Revenue", "Cost", "ROI", "Score", "URL", ""].map((h) => (
              <th key={h} className="px-4 py-3 whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {assets.map((a) => (
            <tr key={a.id} className="hover:bg-gray-900 transition-colors">
              <td className="px-4 py-3 text-gray-500">#{a.id}</td>
              <td className="px-4 py-3 font-medium text-white max-w-[180px] truncate">{a.keyword}</td>
              <td className="px-4 py-3 text-gray-400">{a.type.replace("_", " ")}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[a.status] ?? ""}`}>
                  {a.status}
                </span>
              </td>
              <td className="px-4 py-3 text-green-400">€{a.revenue.toFixed(2)}</td>
              <td className="px-4 py-3 text-red-400">€{a.cost.toFixed(2)}</td>
              <td className="px-4 py-3">
                <span className={a.roi >= 3 ? "text-green-400 font-bold" : a.roi < 1 ? "text-red-400" : "text-yellow-400"}>
                  {a.roi.toFixed(2)}x
                </span>
              </td>
              <td className="px-4 py-3 text-purple-400">{a.market_score.toFixed(1)}/10</td>
              <td className="px-4 py-3">
                {a.url ? (
                  <a href={a.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-blue-400 hover:text-blue-300">
                    <ExternalLink size={12} /> live
                  </a>
                ) : (
                  <span className="text-gray-600">—</span>
                )}
              </td>
              <td className="px-4 py-3">
                <button onClick={() => onDelete(a.id)}
                  className="text-gray-600 hover:text-red-400 transition-colors">
                  <Trash2 size={14} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
