/** Placeholder rows shown while a list loads, sized to match the real table. */
export function TableSkeleton({ rows = 5, columns = 4 }) {
  return (
    <div className="divide-y divide-slate-100" aria-hidden="true">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex items-center gap-4 px-4 py-4">
          {Array.from({ length: columns }).map((__, columnIndex) => (
            <div
              key={columnIndex}
              className="h-4 animate-pulse rounded bg-slate-200"
              style={{ width: columnIndex === 0 ? "28%" : `${Math.max(12, 60 / columns)}%` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
