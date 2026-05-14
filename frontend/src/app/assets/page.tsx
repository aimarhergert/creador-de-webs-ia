"use client";

import { useState, useEffect, useCallback } from "react";
import {
  RefreshCw, Trash2, ExternalLink, Eye, Search,
  Globe, Zap, Filter,
} from "lucide-react";
import Link from "next/link";
import { api, Asset, AssetStatus } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import AssetPreview from "@/components/AssetPreview";

const STATUS_FILTERS: { label: string; value: AssetStatus | "all" }[] = [
  { label: "Todos",       value: "all"       },
  { label: "Live",        value: "live"      },
  { label: "Generando",   value: "generating"},
  { label: "Error",       value: "error"     },
  { label: "Eliminados",  value: "killed"    },
];

export default function AssetsPage() {
  const [assets,   setAssets]   = useState<Asset[]>([]);
  const [total,    setTotal]    = useState(0);
  const [search,   setSearch]   = useState("");
  const [filter,   setFilter]   = useState<AssetStatus | "all">("all");
  const [preview,  setPreview]  = useState<{ url: string; keyword: string } | null>(null);
  const [toast,    setToast]    = useState("");
  const [deleting, setDeleting] = useState<number | null>(null);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(""), 3500);
  }, []);

  const load = useCallback(async () => {
    try {
      const list = await api.getAssets("limit=100");
      setAssets(list.items);
      setTotal(list.total);
    } catch {
      showToast("Error al cargar assets");
    }
  }, [showToast]);

  useEffect(() => {
    load();
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, [load]);

  const handleDelete = async (id: number) => {
    if (!confirm(`¿Eliminar asset #${id}?`)) return;
    setDeleting(id);
    try {
      await api.deleteAsset(id);
      showToast(`Asset #${id} eliminado`);
      load();
    } catch {
      showToast("Error al eliminar");
    } finally {
      setDeleting(null);
    }
  };

  const displayed = assets.filter(a => {
    const matchFilter = filter === "all" || a.status === filter;
    const matchSearch = !search || a.keyword.toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  return (
    <>
      <div className="p-6 max-w-7xl mx-auto space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Assets</h1>
            <p className="text-sm text-gray-500 mt-0.5">{total} activos digitales</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={load}
              className="p-2 text-gray-600 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <RefreshCw size={14} />
            </button>
            <Link
              href="/pipeline"
              className="flex items-center gap-1.5 text-sm bg-blue-600 hover:bg-blue-500 text-white px-3 py-2 rounded-lg font-medium transition-colors"
            >
              <Zap size={14} /> Nuevo
            </Link>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
            <input
              className="w-full bg-gray-900 border border-gray-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-gray-600 transition-colors"
              placeholder="Buscar por keyword…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-1.5">
            <Filter size={13} className="text-gray-600 shrink-0" />
            {STATUS_FILTERS.map(f => (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={`text-xs px-2.5 py-1.5 rounded-lg transition-colors ${
                  filter === f.value
                    ? "bg-gray-700 text-white"
                    : "text-gray-500 hover:text-gray-300 hover:bg-gray-900"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Grid */}
        {displayed.length === 0 ? (
          <div className="border border-gray-800 rounded-xl py-16 text-center">
            <p className="text-gray-600 text-sm mb-3">
              {total === 0 ? "Sin activos todavía." : "Ningún activo coincide con los filtros."}
            </p>
            {total === 0 && (
              <Link href="/pipeline" className="inline-flex items-center gap-1.5 text-blue-400 hover:text-blue-300 text-sm">
                <Zap size={13} /> Lanzar primer pipeline
              </Link>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {displayed.map(a => (
              <AssetCard
                key={a.id}
                asset={a}
                onPreview={a.url ? () => setPreview({ url: a.url!, keyword: a.keyword }) : undefined}
                onDelete={() => handleDelete(a.id)}
                deleting={deleting === a.id}
              />
            ))}
          </div>
        )}
      </div>

      {/* Preview modal */}
      {preview && (
        <AssetPreview
          url={preview.url}
          keyword={preview.keyword}
          onClose={() => setPreview(null)}
        />
      )}

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 bg-gray-800 border border-gray-700 text-white text-sm px-4 py-3 rounded-xl shadow-xl z-50">
          {toast}
        </div>
      )}
    </>
  );
}

function AssetCard({
  asset: a,
  onPreview,
  onDelete,
  deleting,
}: {
  asset: Asset;
  onPreview?: () => void;
  onDelete: () => void;
  deleting: boolean;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden hover:border-gray-700 transition-colors flex flex-col">
      {/* Preview thumbnail area */}
      <div
        className="h-24 bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center cursor-pointer relative group"
        onClick={onPreview}
      >
        {a.url ? (
          <>
            <Globe size={24} className="text-gray-700 group-hover:text-gray-500 transition-colors" />
            <div className="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/5 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all">
              <div className="bg-black/50 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
                <Eye size={10} /> Preview
              </div>
            </div>
          </>
        ) : (
          <span className="text-gray-700 text-xs">Sin URL</span>
        )}
        <div className="absolute top-2 right-2">
          <StatusBadge status={a.status} />
        </div>
      </div>

      {/* Info */}
      <div className="p-3 flex flex-col gap-1.5 flex-1">
        <div className="flex items-start justify-between gap-1">
          <span className="text-[10px] text-gray-600 font-mono">#{a.id}</span>
          <span className="text-[10px] text-gray-600">{a.type.replace("_"," ")}</span>
        </div>
        <p className="text-sm font-medium text-white leading-snug line-clamp-2 flex-1">
          {a.keyword}
        </p>
        <div className="flex items-center gap-2 text-xs mt-1">
          <span className="text-green-400">€{a.revenue.toFixed(2)}</span>
          <span className="text-gray-700">·</span>
          <span
            className={
              a.roi >= 3
                ? "text-green-400 font-semibold"
                : a.roi < 1
                ? "text-red-400"
                : "text-yellow-400"
            }
          >
            {a.roi.toFixed(1)}x
          </span>
          <span className="text-gray-700">·</span>
          <span className="text-purple-400">{a.market_score.toFixed(1)}/10</span>
        </div>
      </div>

      {/* Actions */}
      <div className="border-t border-gray-800 flex divide-x divide-gray-800">
        {onPreview && (
          <button
            onClick={onPreview}
            className="flex-1 flex items-center justify-center gap-1 py-2 text-xs text-gray-500 hover:text-white hover:bg-gray-800 transition-colors"
          >
            <Eye size={11} /> Preview
          </button>
        )}
        {a.url && (
          <a
            href={a.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-1 py-2 text-xs text-gray-500 hover:text-blue-400 hover:bg-gray-800 transition-colors"
          >
            <ExternalLink size={11} /> Live
          </a>
        )}
        <button
          onClick={onDelete}
          disabled={deleting}
          className="flex items-center justify-center px-3 py-2 text-xs text-gray-700 hover:text-red-400 hover:bg-gray-800 transition-colors disabled:opacity-30"
        >
          <Trash2 size={11} />
        </button>
      </div>
    </div>
  );
}
