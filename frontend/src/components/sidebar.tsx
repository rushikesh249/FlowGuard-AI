/**
 * Sidebar navigation — minimal, professional fintech aesthetic.
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "□" },
  { href: "/upload", label: "Upload Data", icon: "↑" },
  { href: "/process", label: "Process View", icon: "◇" },
  { href: "/anomalies", label: "Anomalies", icon: "!" },
  { href: "/reports", label: "Reports", icon: "↓" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="w-56 h-screen border-r border-slate-200 bg-white flex flex-col">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-slate-100">
        <h1 className="text-[15px] font-semibold tracking-tight text-slate-900">
          FlowGuard AI
        </h1>
        <p className="text-[11px] text-slate-400 mt-0.5 tracking-wide uppercase">
          Process Intelligence
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded text-[13px] font-medium transition-colors ${
                active
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <span className="text-[14px] w-4 text-center opacity-70">
                {item.icon}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="px-4 py-3 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <div className="min-w-0">
            <p className="text-[12px] font-medium text-slate-700 truncate">
              {user?.email}
            </p>
            <p className="text-[11px] text-slate-400">{user?.role}</p>
          </div>
          <button
            onClick={logout}
            className="text-[11px] text-slate-400 hover:text-slate-700 px-2 py-1"
          >
            Sign out
          </button>
        </div>
      </div>
    </aside>
  );
}
