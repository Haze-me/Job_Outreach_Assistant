export function EmptyState({ title, description, action }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white/60 px-6 py-12 text-center">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      {description && <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">{description}</p>}
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  );
}
