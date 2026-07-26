import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-4 text-center">
      <p className="text-sm font-semibold text-brand-600">404</p>
      <h1 className="text-2xl font-semibold text-slate-900">Page not found</h1>
      <p className="max-w-sm text-sm text-slate-500">
        The page you were looking for does not exist or has moved.
      </p>
      <Link
        to="/dashboard"
        className="mt-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
      >
        Back to the dashboard
      </Link>
    </div>
  );
}
