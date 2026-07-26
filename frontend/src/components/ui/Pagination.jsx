import { Button } from "./Button";
import { pluralize } from "../../utils/format";

/**
 * Page controls for a paginated list endpoint.
 *
 * Renders nothing when everything fits on one page -- controls that can only
 * be disabled are noise.
 */
export function Pagination({
  page,
  totalPages,
  count,
  pageSize,
  onPageChange,
  itemLabel = "result",
  // English plurals are not always "+s" ("company" -> "companies"), so callers
  // can pass the correct form rather than the naive one.
  itemLabelPlural,
}) {
  if (!count) return null;

  const first = (page - 1) * pageSize + 1;
  const last = Math.min(page * pageSize, count);

  return (
    <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm text-slate-500" aria-live="polite">
        Showing <span className="font-medium text-slate-700">{first}</span>–
        <span className="font-medium text-slate-700">{last}</span> of{" "}
        <span className="font-medium text-slate-700">{count}</span>{" "}
        {pluralize(count, itemLabel, itemLabelPlural)}
      </p>

      {totalPages > 1 && (
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
          >
            Previous
          </Button>
          <span className="text-sm text-slate-600">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
