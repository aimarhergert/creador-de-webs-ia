"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Zap, Mail, Lock, Loader2, AlertCircle } from "lucide-react";
import { api, setTokenGetter } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

export default function LoginPage() {
  const router = useRouter();
  const { setTokens, setUser, accessToken } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const tokens = await api.login(email, password);
      setTokens(tokens.access_token, tokens.refresh_token);

      // Wire token getter before calling /me
      setTokenGetter(() => tokens.access_token);
      const user = await api.me();
      setUser(user);

      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión");
    } finally {
      setLoading(false);
    }
  };

  // Quick demo login
  const loginDemo = async () => {
    setEmail("demo@aros.ai");
    setPassword("demo123");
    setError("");
    setLoading(true);
    try {
      const tokens = await api.login("demo@aros.ai", "demo123");
      setTokens(tokens.access_token, tokens.refresh_token);
      setTokenGetter(() => tokens.access_token);
      const user = await api.me();
      setUser(user);
      router.push("/dashboard");
    } catch {
      setError("Demo account not found. Register first.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
              <Zap size={20} className="text-white" />
            </div>
            <span className="text-2xl font-bold text-white">AROS</span>
          </div>
          <p className="text-gray-500 text-sm">Autonomous Revenue Operating System</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
          <h1 className="text-xl font-bold text-white mb-6">Iniciar sesión</h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">
                Email
              </label>
              <div className="relative">
                <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-9 pr-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="tu@email.com"
                  required
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">
                Contraseña
              </label>
              <div className="relative">
                <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-9 pr-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="••••••••"
                  required
                  disabled={loading}
                />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 bg-red-950/30 border border-red-800/50 rounded-lg px-3 py-2">
                <AlertCircle size={13} className="text-red-400 shrink-0" />
                <span className="text-xs text-red-300">{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold rounded-xl py-3 text-sm flex items-center justify-center gap-2 transition-colors"
            >
              {loading ? <><Loader2 size={14} className="animate-spin" />Entrando…</> : "Entrar"}
            </button>
          </form>

          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-800" />
            </div>
            <div className="relative flex justify-center">
              <span className="px-3 bg-gray-900 text-xs text-gray-600">o</span>
            </div>
          </div>

          <button
            onClick={loginDemo}
            disabled={loading}
            className="w-full bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-300 font-medium rounded-xl py-3 text-sm flex items-center justify-center gap-2 transition-colors border border-gray-700"
          >
            <Zap size={13} className="text-blue-400" />
            Acceder con cuenta demo
          </button>

          <p className="text-center text-xs text-gray-600 mt-6">
            ¿Sin cuenta?{" "}
            <Link href="/register" className="text-blue-400 hover:text-blue-300">
              Crear cuenta
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
