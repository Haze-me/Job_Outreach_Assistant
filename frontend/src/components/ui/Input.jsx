import { useId } from "react";

import { cn } from "../../utils/cn";

/**
 * A labelled text input with inline error and hint support.
 *
 * The label is always rendered and always tied to the input by id, and errors
 * are wired up with `aria-describedby` + `aria-invalid` so a screen reader
 * announces them. Placeholder-as-label is not an accessible substitute.
 */
export function Input({
  label,
  error,
  hint,
  id,
  className,
  type = "text",
  required = false,
  ...props
}) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const errorId = `${inputId}-error`;
  const hintId = `${inputId}-hint`;

  return (
    <div className="w-full">
      <label htmlFor={inputId} className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
        {required && (
          <span className="ml-0.5 text-red-600" aria-hidden="true">
            *
          </span>
        )}
      </label>

      <input
        id={inputId}
        type={type}
        required={required}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={cn(error && errorId, hint && !error && hintId) || undefined}
        className={cn(
          "block w-full rounded-lg border px-3 py-2 text-sm text-slate-900 shadow-xs transition-colors",
          "placeholder:text-slate-400 disabled:bg-slate-50 disabled:text-slate-500",
          error
            ? "border-red-400 focus:border-red-500"
            : "border-slate-300 focus:border-brand-500",
          className,
        )}
        {...props}
      />

      {error ? (
        <p id={errorId} className="mt-1.5 text-sm text-red-600">
          {error}
        </p>
      ) : hint ? (
        <p id={hintId} className="mt-1.5 text-sm text-slate-500">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
