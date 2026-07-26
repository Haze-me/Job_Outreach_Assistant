import { useState } from "react";
import { Outlet } from "react-router-dom";

import { Sidebar } from "../components/layout/Sidebar";
import { Topbar } from "../components/layout/Topbar";
import { cn } from "../utils/cn";

/**
 * The signed-in shell: fixed sidebar on desktop, slide-over drawer on mobile.
 */
export function AppLayout() {
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-60 border-r border-slate-200 bg-white lg:block">
        <Sidebar />
      </aside>

      {/* Mobile drawer */}
      <div
        className={cn(
          "fixed inset-0 z-30 lg:hidden",
          isSidebarOpen ? "pointer-events-auto" : "pointer-events-none",
        )}
        aria-hidden={!isSidebarOpen}
      >
        <div
          className={cn(
            "absolute inset-0 bg-slate-900/40 transition-opacity",
            isSidebarOpen ? "opacity-100" : "opacity-0",
          )}
          onClick={() => setSidebarOpen(false)}
        />
        <aside
          className={cn(
            "absolute inset-y-0 left-0 w-64 bg-white shadow-xl transition-transform",
            isSidebarOpen ? "translate-x-0" : "-translate-x-full",
          )}
        >
          <Sidebar onNavigate={() => setSidebarOpen(false)} />
        </aside>
      </div>

      <div className="lg:pl-60">
        <Topbar onOpenSidebar={() => setSidebarOpen(true)} />
        <main className="px-4 py-8 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
