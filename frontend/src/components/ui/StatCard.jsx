import { cn } from "../../utils/cn";

const TONES = {
  default: "text-slate-900",
  brand: "text-brand-700",
  positive: "text-emerald-700",
  warning: "text-amber-700",
  negative: "text-red-700",
};

/**
 * A single dashboard figure.
 *
 * `isLoading` renders a skeleton at the same dimensions as the real value, so
 * the grid does not jump when the data arrives.
 */
export function StatCard({ label, value, hint, tone = "default", isLoading = false }) {
  return (
    <div className="rounded-xl bg-white p-5 shadow-xs ring-1 ring-slate-200/70">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      {isLoading ? (
        <div className="mt-2 h-9 w-16 animate-pulse rounded bg-slate-200" aria-hidden="true" />
      ) : (
        <p className={cn("mt-2 text-3xl font-semibold tabular-nums", TONES[tone])}>{value}</p>
      )}
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}
