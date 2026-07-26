import { useId } from "react";

import { cn } from "../../utils/cn";

export function SearchInput({ value, onChange, placeholder = "Search...", label = "Search", className }) {
  const id = useId();

  return (
    <div className={cn("relative", className)}>
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <svg
        className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400"
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
      >
        <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
        <path d="m20 20-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <input
        id={id}
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="block w-full rounded-lg border border-slate-300 bg-white py-2 pr-3 pl-9 text-sm shadow-xs placeholder:text-slate-400"
      />
    </div>
  );
}
