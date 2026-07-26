import { Navigate, Outlet } from "react-router-dom";

import { FullPageSpinner } from "../components/ui/Spinner";
import { useAuth } from "../hooks/useAuth";

/**
 * Keeps a signed-in user off the login and register screens.
 *
 * Without this, an authenticated user following a bookmarked /login link sees
 * a form that would only sign them in as themselves again.
 */
export function PublicOnlyRoute() {
  const { isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return <FullPageSpinner />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
