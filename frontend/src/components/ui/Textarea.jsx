import { useId } from "react";

import { cn } from "../../utils/cn";

export function Textarea({ label, error, hint, id, className, rows = 4, required = false, ...props }) {
  const generatedId = useId();
  const textareaId = id ?? generatedId;
  const errorId = `${textareaId}-error`;

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={textareaId} className="mb-1.5 block text-sm font-medium text-slate-700">
          {label}
          {required && (
            <span className="ml-0.5 text-red-600" aria-hidden="true">
              *
            </span>
          )}
        </label>
      )}

      <textarea
        id={textareaId}
        rows={rows}
        required={required}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          "block w-full rounded-lg border px-3 py-2 text-sm text-slate-900 shadow-xs",
          "placeholder:text-slate-400",
          error ? "border-red-400" : "border-slate-300",
          className,
        )}
        {...props}
      />

      {error ? (
        <p id={errorId} className="mt-1.5 text-sm text-red-600">
          {error}
        </p>
      ) : hint ? (
        <p className="mt-1.5 text-sm text-slate-500">{hint}</p>
      ) : null}
    </div>
  );
}
