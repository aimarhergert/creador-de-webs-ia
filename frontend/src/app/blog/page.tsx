"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  FileText, Plus, Eye, Globe, ExternalLink, Trash2, Edit3,
  Loader2, Search, Filter, BookOpen,
} from "lucide-react";
import { api, BlogPost } from "@/lib/api";

const CATEGORIES = ["seo", "affiliate", "saas", "ecommerce", "finance", "health", "tech", "education"];
const SECTORS = ["tech", "health", "finance", "ecommerce", "education", "travel", "realestate", "general"];

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: "bg-gray-500/10 text-gray-400 border-gray-500/20",
    published: "bg-green-500/10 text-green-400 border-green-500/20",
    archived: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  };
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${colors[status] || colors.draft}`}>
      {status.toUpperCase()}
    </span>
  );
}

export default function BlogPage() {
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [selected, setSelected] = useState<BlogPost | null>(null);
  const [toast, setToast] = useState("");

  // Create form
  const [title, setTitle] = useState("");
  const [keyword, setKeyword] = useState("");
  const [sector, setSector] = useState("general");
  const [category, setCategory] = useState("");
  const [standalone, setStandalone] = useState(true);

  const load = async () => {
    try {
      const r = await api.getBlogPosts("limit=30");
      setPosts(r.items);
      setTotal(r.total);
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setGenerating(true);
    try {
      await api.createBlogPost({
        title: title.trim(),
        focus_keyword: keyword.trim() || title.trim(),
        sector, category: category || null,
        is_standalone: standalone,
        generate_content: true,
        tags: keyword.trim() ? [keyword.trim()] : [],
      });
      showToast("Artículo generado por IA");
      setShowCreate(false); setTitle(""); setKeyword("");
      load();
    } catch (err) {
      showToast("Error: " + (err instanceof Error ? err.message : "falló"));
    } finally { setGenerating(false); }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("¿Eliminar artículo?")) return;
    try { await api.deleteBlogPost(id); showToast("Eliminado"); load(); }
    catch { showToast("Error al eliminar"); }
  };

  const handlePublish = async (post: BlogPost) => {
    try {
      await api.updateBlogPost(post.id, { status: "published" });
      showToast("Publicado ✓");
      load();
    } catch { showToast("Error"); }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-5">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <BookOpen size={20} className="text-blue-400" />
            Blog Manager
          </h1>
          <p className="text-sm text-gray-500 mt-1">{total} artículos — generados por IA</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl px-4 py-2.5 text-sm transition-colors">
          <Plus size={15} /> Nuevo Artículo
        </button>
      </motion.div>

      {/* Create panel */}
      {showCreate && (
        <motion.form initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
          onSubmit={handleCreate} className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Título</label>
              <input className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500"
                placeholder="Guía completa de..." value={title} onChange={e => setTitle(e.target.value)} required />
            </div>
            <div>
              <label className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Keyword principal</label>
              <input className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500"
                placeholder="keyword objetivo" value={keyword} onChange={e => setKeyword(e.target.value)} />
            </div>
            <div>
              <label className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Sector</label>
              <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                value={sector} onChange={e => setSector(e.target.value)}>
                {SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Categoría</label>
              <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                value={category} onChange={e => setCategory(e.target.value)}>
                <option value="">Sin categoría</option>
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1.5 text-xs text-gray-400">
              <input type="checkbox" checked={standalone} onChange={e => setStandalone(e.target.checked)} className="rounded" />
              Blog independiente
            </label>
          </div>
          <button type="submit" disabled={generating || !title.trim()}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold rounded-lg py-2.5 text-sm flex items-center justify-center gap-2">
            {generating ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
            {generating ? "IA generando..." : "Generar Artículo con IA"}
          </button>
        </motion.form>
      )}

      {/* Posts grid */}
      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="animate-spin text-blue-400" size={24} /></div>
      ) : posts.length === 0 ? (
        <div className="border border-gray-800 rounded-2xl py-16 text-center">
          <FileText size={28} className="text-gray-700 mx-auto mb-2" />
          <p className="text-gray-600 text-sm">Sin artículos todavía</p>
          <p className="text-xs text-gray-700 mt-1">Genera tu primer artículo con IA</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {posts.map(p => (
            <motion.div key={p.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
              onClick={() => setSelected(selected?.id === p.id ? null : p)}
              className={`bg-gray-900 border rounded-xl p-4 cursor-pointer transition-all ${
                selected?.id === p.id ? "border-blue-500/50 shadow-[0_0_30px_rgba(59,130,246,0.05)]" : "border-gray-800 hover:border-gray-700"
              }`}>
              <div className="flex items-start justify-between mb-2">
                <StatusBadge status={p.status} />
                <span className="text-[10px] text-gray-600 font-mono">#{p.id}</span>
              </div>
              <h3 className="text-sm font-semibold text-white line-clamp-2 leading-snug">{p.title}</h3>
              {p.excerpt && <p className="text-xs text-gray-500 mt-1 line-clamp-3">{p.excerpt}</p>}
              <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-800/50">
                <div className="flex items-center gap-2 text-[10px]">
                  {p.sector && <span className="text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded">{p.sector}</span>}
                  {p.generated_by && <span className="text-gray-600">{p.generated_by}</span>}
                </div>
                <div className="flex items-center gap-1">
                  {p.status === "draft" && (
                    <button onClick={(e) => { e.stopPropagation(); handlePublish(p); }}
                      className="text-[10px] text-green-400 hover:text-green-300 px-1.5 py-0.5">Publicar</button>
                  )}
                  <button onClick={(e) => { e.stopPropagation(); handleDelete(p.id); }}
                    className="text-gray-700 hover:text-red-400 p-1"><Trash2 size={11} /></button>
                </div>
              </div>

              {/* Expanded content preview */}
              {selected?.id === p.id && p.content_html && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                  className="mt-3 pt-3 border-t border-gray-800">
                  <div className="max-h-[300px] overflow-y-auto text-xs text-gray-300 leading-relaxed prose prose-invert prose-sm"
                    dangerouslySetInnerHTML={{ __html: p.content_html.slice(0, 2000) }} />
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      )}

      {toast && (
        <div className="fixed bottom-6 right-6 bg-gray-900 border border-gray-700 text-white text-sm px-4 py-3 rounded-xl shadow-xl z-50">
          {toast}
        </div>
      )}
    </div>
  );
}
