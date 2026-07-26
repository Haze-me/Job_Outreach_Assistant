import { cn } from "../../utils/cn";

const VARIANTS = {
  error: {
    box: "bg-red-50 text-red-800 ring-red-200",
    // Errors are announced immediately; anything less and a screen-reader user
    // submits a form and hears nothing.
    role: "alert",
    live: "assertive",
  },
  success: {
    box: "bg-emerald-50 text-emerald-800 ring-emerald-200",
    role: "status",
    live: "polite",
  },
  info: {
    box: "bg-brand-50 text-brand-900 ring-brand-200",
    role: "status",
    live: "polite",
  },
  warning: {
    box: "bg-amber-50 text-amber-900 ring-amber-200",
    role: "status",
    live: "polite",
  },
};

export function Alert({ children, variant = "info", title, className }) {
  const { box, role, live } = VARIANTS[variant] ?? VARIANTS.info;

  return (
    <div
      role={role}
      aria-live={live}
      className={cn("rounded-lg px-4 py-3 text-sm ring-1 ring-inset", box, className)}
    >
      {title && <p className="mb-0.5 font-semibold">{title}</p>}
      <div>{children}</div>
    </div>
  );
}
