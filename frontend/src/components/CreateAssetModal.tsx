"use client";

import { useState } from "react";
import { X, Zap } from "lucide-react";
import { api, AssetType, MonetizationModel } from "@/lib/api";

interface Props {
  onClose: () => void;
  onCreated: (msg: string) => void;
}

export default function CreateAssetModal({ onClose, onCreated }: Props) {
  const [keyword, setKeyword] = useState("");
  const [type, setType] = useState<AssetType>("landing_page");
  const [monetization, setMonetization] = useState<MonetizationModel>("affiliates");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.triggerPipeline(keyword.trim(), type, monetization);
      onCreated(res.message);
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-950 border border-gray-800 rounded-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-white">Nuevo Activo Digital</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Keyword / Nicho</label>
            <input
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              placeholder="ej: best ergonomic office chair"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Tipo de Activo</label>
            <select
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              value={type}
              onChange={(e) => setType(e.target.value as AssetType)}
            >
              <option value="landing_page">Landing Page</option>
              <option value="blog">Blog SEO</option>
              <option value="ecommerce">Mini Ecommerce</option>
              <option value="lead_gen">Lead Generation</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Modelo de Monetización</label>
            <select
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              value={monetization}
              onChange={(e) => setMonetization(e.target.value as MonetizationModel)}
            >
              <option value="affiliates">Afiliados (Amazon)</option>
              <option value="ads">Publicidad (AdSense)</option>
              <option value="ecommerce">Ecommerce (Stripe)</option>
              <option value="leads">Lead Generation</option>
            </select>
          </div>

          {error && (
            <p className="text-red-400 text-xs bg-red-950 rounded-lg px-3 py-2">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg px-4 py-3 flex items-center justify-center gap-2 transition-colors"
          >
            <Zap size={16} />
            {loading ? "Lanzando pipeline..." : "Lanzar Pipeline"}
          </button>
        </form>
      </div>
    </div>
  );
}
