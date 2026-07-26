import { cn } from "../../utils/cn";

export function Spinner({ className, label = "Loading" }) {
  return (
    <svg
      className={cn("animate-spin text-current", className)}
      viewBox="0 0 24 24"
      fill="none"
      role="status"
      aria-label={label}
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

/** Fills the available space -- used while a route or page is loading. */
export function FullPageSpinner({ label = "Loading" }) {
  return (
    <div className="flex min-h-[60vh] w-full items-center justify-center">
      <Spinner className="size-8 text-brand-600" label={label} />
    </div>
  );
}
