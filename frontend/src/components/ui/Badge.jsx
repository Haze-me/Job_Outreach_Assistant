import { cn } from "../../utils/cn";

const TONES = {
  neutral: "bg-slate-100 text-slate-700",
  muted: "bg-slate-50 text-slate-500 ring-1 ring-inset ring-slate-200",
  brand: "bg-brand-50 text-brand-700",
  positive: "bg-emerald-50 text-emerald-700",
  warning: "bg-amber-50 text-amber-800",
  negative: "bg-red-50 text-red-700",
};

export function Badge({ children, tone = "neutral", className }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        TONES[tone] ?? TONES.neutral,
        className,
      )}
    >
      {children}
    </span>
  );
}
