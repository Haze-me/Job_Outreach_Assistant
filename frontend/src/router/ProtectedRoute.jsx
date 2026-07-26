import { Navigate, Outlet, useLocation } from "react-router-dom";

import { FullPageSpinner } from "../components/ui/Spinner";
import { useAuth } from "../hooks/useAuth";

/**
 * Gate for signed-in routes.
 *
 * The `loading` state must render a spinner rather than redirecting: on a page
 * reload the app has tokens but has not yet verified them, and treating that
 * as "signed out" would bounce the user to the login screen every time they
 * refreshed.
 *
 * The attempted location is passed along so the login page can return the user
 * where they were headed.
 */
export function ProtectedRoute() {
  const { isLoading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <FullPageSpinner label="Checking your session" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}
