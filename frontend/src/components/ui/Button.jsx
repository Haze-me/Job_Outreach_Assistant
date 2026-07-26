import { cn } from "../../utils/cn";
import { Spinner } from "./Spinner";

const VARIANTS = {
  primary:
    "bg-brand-600 text-white hover:bg-brand-700 active:bg-brand-800 disabled:bg-brand-300",
  secondary:
    "bg-white text-slate-700 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 disabled:text-slate-400",
  danger: "bg-red-600 text-white hover:bg-red-700 active:bg-red-800 disabled:bg-red-300",
  ghost: "bg-transparent text-slate-600 hover:bg-slate-100 disabled:text-slate-400",
};

const SIZES = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-2.5 text-base",
};

export function Button({
  children,
  variant = "primary",
  size = "md",
  isLoading = false,
  disabled = false,
  className,
  type = "button",
  ...props
}) {
  return (
    <button
      type={type}
      // A loading button must also be disabled, or a double-click fires the
      // request twice.
      disabled={disabled || isLoading}
      aria-busy={isLoading || undefined}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors",
        "disabled:cursor-not-allowed",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...props}
    >
      {isLoading && <Spinner className="size-4" />}
      {children}
    </button>
  );
}
