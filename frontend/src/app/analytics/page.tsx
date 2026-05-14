"use client";

import { useState, useEffect, useCallback } from "react";
import { RefreshCw, TrendingUp, Eye, ShoppingCart, DollarSign, BarChart3 } from "lucide-react";
import { api, Asset, AssetMetrics, PortfolioSummary } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";

function StatBox({ label, value, icon: Icon, color = "gray" }: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color?: "green" | "blue" | "purple" | "amber" | "gray";
}) {
  const colors = {
    green:  "text-green-400  bg-green-950/30  border-green-800/40",
    blue:   "text-blue-400   bg-blue-950/30   border-blue-800/40",
    purple: "text-purple-400 bg-purple-950/30 border-purple-800/40",
    amber:  "text-amber-400  bg-amber-950/30  border-amber-800/40",
    gray:   "text-gray-300   bg-gray-900      border-gray-800",
  };
  return (
    <div className={`rounded-xl border p-4 ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon size={14} className="opacity-70" />
        <p className="text-xs opacity-60 uppercase tracking-widest">{label}</p>
      </div>
      <p className="text-xl font-bold">{value}</p>
    </div>
  );
}

interface AssetRow {
  asset: Asset;
  metrics: AssetMetrics | null;
}

export default function AnalyticsPage() {
  const [summary,  setSummary]  = useState<PortfolioSummary | null>(null);
  const [rows,     setRows]     = useState<AssetRow[]>([]);
  const [loading,  setLoading]  = useState(true);

  const load = useCallback(async () => {
    try {
      const [sum, list] = await Promise.all([
        api.getPortfolioSummary(),
        api.getAssets("limit=50"),
      ]);
      setSummary(sum);

      const rowData: AssetRow[] = await Promise.all(
        list.items.map(async asset => {
          try {
            const metrics = await api.getAssetSummary(asset.id);
            return { asset, metrics };
          } catch {
            return { asset, metrics: null };
          }
        }),
      );
      setRows(rowData);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const totalVisits      = rows.reduce((s, r) => s + (r.metrics?.total_visits ?? 0), 0);
  const totalConversions = rows.reduce((s, r) => s + (r.metrics?.total_conversions ?? 0), 0);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 size={18} className="text-purple-400" />
            Analytics
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">Rendimiento del portfolio de activos</p>
        </div>
        <button
          onClick={load}
          className="p-2 text-gray-600 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      {/* Portfolio KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatBox label="Visitas Totales"    value={totalVisits.toLocaleString()}                         icon={Eye}          color="blue"   />
        <StatBox label="Conversiones"       value={totalConversions.toLocaleString()}                    icon={ShoppingCart} color="purple" />
        <StatBox label="Revenue Total"      value={`€${(summary?.total_revenue ?? 0).toFixed(2)}`}       icon={DollarSign}   color="green"  />
        <StatBox label="ROI Portfolio"      value={`${(summary?.portfolio_roi ?? 0).toFixed(2)}x`}       icon={TrendingUp}   color="amber"  />
      </div>

      {/* Per-asset table */}
      <div>
        <h2 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
          Métricas por Activo ({rows.length})
        </h2>
        {loading ? (
          <div className="border border-gray-800 rounded-xl py-12 text-center text-gray-600 text-sm">
            Cargando métricas…
          </div>
        ) : rows.length === 0 ? (
          <div className="border border-gray-800 rounded-xl py-12 text-center text-gray-600 text-sm">
            Sin datos todavía. Genera activos desde el Pipeline.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-800">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-900 border-b border-gray-800">
                <tr>
                  {["ID", "Keyword", "Status", "Visitas", "Conversiones", "Revenue", "Coste", "ROI", "C/R%"].map(h => (
                    <th key={h} className="px-4 py-3 text-xs text-gray-500 uppercase tracking-wider font-medium whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {rows.map(({ asset: a, metrics: m }) => {
                  const cr = m && m.total_visits > 0
                    ? ((m.total_conversions / m.total_visits) * 100).toFixed(1)
                    : "—";
                  return (
                    <tr key={a.id} className="hover:bg-gray-900/50 transition-colors">
                      <td className="px-4 py-3 text-gray-600 font-mono text-xs">#{a.id}</td>
                      <td className="px-4 py-3 text-white font-medium max-w-[180px] truncate">
                        {a.keyword}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={a.status} />
                      </td>
                      <td className="px-4 py-3 text-blue-400">
                        {m ? m.total_visits.toLocaleString() : "—"}
                      </td>
                      <td className="px-4 py-3 text-purple-400">
                        {m ? m.total_conversions.toLocaleString() : "—"}
                      </td>
                      <td className="px-4 py-3 text-green-400">
                        €{a.revenue.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-red-400">
                        €{a.cost.toFixed(2)}
                      </td>
                      <td className="px-4 py-3">
                        <span className={
                          a.roi >= 3
                            ? "text-green-400 font-semibold"
                            : a.roi < 1
                            ? "text-red-400"
                            : "text-yellow-400"
                        }>
                          {a.roi.toFixed(2)}x
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-400">{cr}{cr !== "—" ? "%" : ""}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Info box */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-xs text-gray-500">
        <p className="mb-1 font-medium text-gray-400">Cómo funciona el tracking</p>
        <p>
          Cada activo desplegado incluye un pixel de tracking que llama automáticamente a{" "}
          <code className="bg-gray-800 px-1 rounded text-blue-400">
            POST /api/analytics/&#123;id&#125;/track
          </code>{" "}
          en cada visita. Los datos se acumulan en tiempo real y alimentan el motor de optimización ROI.
        </p>
      </div>
    </div>
  );
}
