"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Zap, Mail, Lock, User, Loader2, AlertCircle } from "lucide-react";
import { api, setTokenGetter } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { setTokens, setUser } = useAuthStore();

  const [form, setForm] = useState({
    email: "", username: "", password: "", full_name: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const tokens = await api.register(form.email, form.username, form.password, form.full_name || undefined);
      setTokens(tokens.access_token, tokens.refresh_token);
      setTokenGetter(() => tokens.access_token);
      const user = await api.me();
      setUser(user);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al registrar");
    } finally {
      setLoading(false);
    }
  };

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
              <Zap size={20} className="text-white" />
            </div>
            <span className="text-2xl font-bold text-white">AROS</span>
          </div>
          <p className="text-gray-500 text-sm">Comienza con €1,000 de capital demo</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
          <h1 className="text-xl font-bold text-white mb-6">Crear cuenta de inversor</h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">Nombre completo</label>
              <div className="relative">
                <User size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                <input type="text" value={form.full_name} onChange={set("full_name")}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-9 pr-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="Tu nombre" disabled={loading} />
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">Username</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600 text-sm">@</span>
                <input type="text" value={form.username} onChange={set("username")}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-9 pr-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="inversor_x" required minLength={3} disabled={loading} />
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">Email</label>
              <div className="relative">
                <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                <input type="email" value={form.email} onChange={set("email")}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-9 pr-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="tu@email.com" required disabled={loading} />
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">Contraseña</label>
              <div className="relative">
                <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                <input type="password" value={form.password} onChange={set("password")}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-9 pr-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="••••••••" required minLength={6} disabled={loading} />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 bg-red-950/30 border border-red-800/50 rounded-lg px-3 py-2">
                <AlertCircle size={13} className="text-red-400 shrink-0" />
                <span className="text-xs text-red-300">{error}</span>
              </div>
            )}

            <button type="submit" disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold rounded-xl py-3 text-sm flex items-center justify-center gap-2 transition-colors">
              {loading ? <><Loader2 size={14} className="animate-spin" />Creando cuenta…</> : "Crear cuenta + €1,000 demo"}
            </button>
          </form>

          <p className="text-center text-xs text-gray-600 mt-6">
            ¿Ya tienes cuenta?{" "}
            <Link href="/login" className="text-blue-400 hover:text-blue-300">Iniciar sesión</Link>
          </p>
        </div>

        <p className="text-center text-xs text-gray-700 mt-4">
          Los fondos demo no tienen valor real. Solo para presentaciones.
        </p>
      </div>
    </div>
  );
}
