import { Outlet } from "react-router-dom";

/** Centred card shell for the signed-out pages. */
export function AuthLayout() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
            Job Outreach Assistant
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Find recruitment contacts and track your applications.
          </p>
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200/70 sm:p-8">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
