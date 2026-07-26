import { useState } from "react";

import { useAuth } from "../../hooks/useAuth";
import { Button } from "../ui/Button";

export function Topbar({ onOpenSidebar }) {
  const { user, logout } = useAuth();
  const [isSigningOut, setIsSigningOut] = useState(false);

  async function handleLogout() {
    setIsSigningOut(true);
    try {
      await logout();
    } finally {
      // The component unmounts on success; resetting matters only if logout
      // somehow leaves the user on the page.
      setIsSigningOut(false);
    }
  }

  const displayName = user?.full_name?.trim() || user?.email || "";

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-4 border-b border-slate-200 bg-white/90 px-4 backdrop-blur lg:px-8">
      <button
        type="button"
        onClick={onOpenSidebar}
        aria-label="Open navigation"
        className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
      >
        <svg className="size-5" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </button>

      <div className="ml-auto flex items-center gap-3">
        <span className="hidden text-sm text-slate-600 sm:inline" title={user?.email}>
          {displayName}
        </span>
        <Button variant="secondary" size="sm" onClick={handleLogout} isLoading={isSigningOut}>
          Sign out
        </Button>
      </div>
    </header>
  );
}
