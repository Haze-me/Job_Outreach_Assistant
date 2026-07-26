import { cn } from "../../utils/cn";

export function Card({ children, className, ...props }) {
  return (
    <div
      className={cn(
        "rounded-xl bg-white p-6 shadow-xs ring-1 ring-slate-200/70",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, description, action }) {
  return (
    <div className="mb-5 flex items-start justify-between gap-4">
      <div>
        <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
      </div>
      {action}
    </div>
  );
}
