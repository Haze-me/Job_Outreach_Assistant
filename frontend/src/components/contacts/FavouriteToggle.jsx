import { cn } from "../../utils/cn";

export function FavouriteToggle({ isFavourite, onToggle, disabled }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled}
      // The pressed state is what a screen reader announces; the star alone
      // conveys nothing.
      aria-pressed={isFavourite}
      aria-label={isFavourite ? "Remove from favourites" : "Mark as favourite"}
      className={cn(
        "rounded-md p-1.5 transition-colors disabled:opacity-50",
        isFavourite ? "text-amber-500 hover:bg-amber-50" : "text-slate-300 hover:bg-slate-100 hover:text-slate-400",
      )}
    >
      <svg className="size-5" viewBox="0 0 24 24" fill={isFavourite ? "currentColor" : "none"} aria-hidden="true">
        <path
          d="m12 3.5 2.7 5.5 6 .9-4.3 4.2 1 6-5.4-2.8-5.4 2.8 1-6L3.3 9.9l6-.9L12 3.5Z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinejoin="round"
        />
      </svg>
    </button>
  );
}
