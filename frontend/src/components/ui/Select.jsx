import { useId } from "react";

import { cn } from "../../utils/cn";

export function Select({
  label,
  error,
  hint,
  id,
  options = [],
  placeholder,
  className,
  required = false,
  ...props
}) {
  const generatedId = useId();
  const selectId = id ?? generatedId;
  const errorId = `${selectId}-error`;

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={selectId} className="mb-1.5 block text-sm font-medium text-slate-700">
          {label}
          {required && (
            <span className="ml-0.5 text-red-600" aria-hidden="true">
              *
            </span>
          )}
        </label>
      )}

      <select
        id={selectId}
        required={required}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          "block w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 shadow-xs",
          "disabled:bg-slate-50 disabled:text-slate-500",
          error ? "border-red-400" : "border-slate-300",
          className,
        )}
        {...props}
      >
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

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
