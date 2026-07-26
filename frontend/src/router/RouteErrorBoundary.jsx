import { useRouteError } from "react-router-dom";

import { Button } from "../components/ui/Button";

/**
 * Last line of defence for an unhandled render error.
 *
 * Without this the router renders its own developer-facing stack trace, which
 * is not something a user should ever see. The message is only shown in
 * development, where it is useful.
 */
export function RouteErrorBoundary() {
  const error = useRouteError();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
      <h1 className="text-2xl font-semibold text-slate-900">Something went wrong</h1>
      <p className="max-w-md text-sm text-slate-500">
        The page failed to load. Reloading usually clears it.
      </p>

      {import.meta.env.DEV && error && (
        <pre className="max-w-xl overflow-x-auto rounded-lg bg-slate-900 p-4 text-left text-xs text-slate-100">
          {error.stack || error.message || String(error)}
        </pre>
      )}

      <Button onClick={() => window.location.assign("/")}>Back to the dashboard</Button>
    </div>
  );
}
