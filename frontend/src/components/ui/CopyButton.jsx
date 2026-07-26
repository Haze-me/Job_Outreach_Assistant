import { useCopyToClipboard } from "../../hooks/useCopyToClipboard";
import { cn } from "../../utils/cn";

/** "Copy email" from the specification's contact management features. */
export function CopyButton({ value, label = "Copy", className }) {
  const { copy, copied } = useCopyToClipboard();
  const isCopied = copied === value;

  return (
    <button
      type="button"
      onClick={() => copy(value)}
      aria-label={`${label} ${value}`}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium transition-colors",
        isCopied
          ? "bg-emerald-50 text-emerald-700"
          : "text-slate-500 hover:bg-slate-100 hover:text-slate-700",
        className,
      )}
    >
      {isCopied ? (
        <svg className="size-3.5" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="m5 13 4 4L19 7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ) : (
        <svg className="size-3.5" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="9" y="9" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="2" />
          <path d="M5 15V5a2 2 0 0 1 2-2h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      )}
      {/* The live region announces the change for screen-reader users. */}
      <span aria-live="polite">{isCopied ? "Copied" : label}</span>
    </button>
  );
}
