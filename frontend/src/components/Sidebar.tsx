"use client";

import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { useState, useEffect } from "react";
import {
  LayoutDashboard, Zap, Database, BarChart3, Bot, Search,
  CreditCard, Workflow, Cpu, Circle, Wallet, Activity, Target, BookOpen,
  LogOut,
} from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

const NAV = [
  { href: "/dashboard",    label: "Dashboard",        icon: LayoutDashboard },
  { href: "/agent",        label: "Agente IA",       icon: Bot,       badge: "AI" },
  { href: "/pipeline",     label: "Pipeline",         icon: Zap,      badge: "HOT" },
  { href: "/strategies",   label: "Estrategias",      icon: Target },
  { href: "/scanner",      label: "Scanner",          icon: Search,   badge: "NEW" },
  { href: "/blog",         label: "Blog IA",          icon: BookOpen },
  { href: "/assets",       label: "Assets",           icon: Database },
  { href: "/analytics",    label: "Analytics",        icon: BarChart3 },
  { href: "/wallet",       label: "Wallet",           icon: Wallet },
  { href: "/activity",     label: "Actividad",        icon: Activity },
  { href: "/billing",      label: "Billing",          icon: CreditCard },
  { href: "/automations",  label: "Automatizaciones", icon: Workflow },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, accessToken } = useAuthStore();
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const check = async () => {
      try { await api.health(); setOnline(true); }
      catch { setOnline(false); }
    };
    check();
    const t = setInterval(check, 15000);
    return () => clearInterval(t);
  }, []);

  // Hide sidebar on auth pages
  if (pathname === "/login" || pathname === "/register") return null;

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <aside className="w-56 shrink-0 bg-gray-950 border-r border-gray-800 flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-blue-500 flex items-center justify-center shrink-0">
            <Cpu size={13} className="text-white" />
          </div>
          <div>
            <div className="font-bold text-sm text-white leading-none">AROS</div>
            <div className="text-[10px] text-gray-600 mt-0.5">Revenue OS</div>
          </div>
        </div>
      </div>

      {/* User chip */}
      {user && (
        <div className="px-3 py-2.5 border-b border-gray-800/50">
          <div className="flex items-center gap-2 bg-gray-900 rounded-lg px-2.5 py-2">
            <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-[10px] font-bold text-white shrink-0">
              {user.username[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium text-gray-300 truncate">@{user.username}</div>
              <div className="text-[10px] text-green-400 font-mono">€{user.wallet_balance.toFixed(2)}</div>
            </div>
          </div>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon, badge }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link key={href} href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all",
                active
                  ? "bg-blue-500/10 text-blue-400 font-medium"
                  : "text-gray-500 hover:text-gray-200 hover:bg-gray-900",
              )}
            >
              <Icon size={15} className="shrink-0" />
              {label}
              {badge && (
                <span className="ml-auto text-[9px] font-semibold bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded-full">
                  {badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-3 py-3 border-t border-gray-800 space-y-2">
        {user && (
          <button onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-gray-600 hover:text-red-400 hover:bg-red-950/20 transition-colors">
            <LogOut size={12} />
            Cerrar sesión
          </button>
        )}
        {!user && (
          <Link href="/login"
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-blue-400 hover:bg-blue-950/20 transition-colors">
            Iniciar sesión
          </Link>
        )}
        <div className="flex items-center gap-1.5 px-1">
          <Circle size={6}
            className={clsx("fill-current shrink-0",
              online === null ? "text-gray-600" : online ? "text-green-400 animate-pulse" : "text-red-500")}
          />
          <span className="text-[10px] text-gray-600">
            {online === null ? "Conectando..." : online ? "Backend online" : "Backend offline"}
          </span>
        </div>
        <div className="text-[9px] text-gray-800 px-1">v2.0 · Investor Demo</div>
      </div>
    </aside>
  );
}
