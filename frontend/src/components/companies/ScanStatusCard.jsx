import { Link } from "react-router-dom";

import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { SCAN_STATUS_TONES } from "../../utils/constants";
import { formatDateTime } from "../../utils/format";

/**
 * The scan panel on a company page.
 *
 * `lastScan` comes from the company detail payload, which is what lets this
 * survive a page reload: the scan id is otherwise only ever returned by the
 * request that started the scan.
 */
export function ScanStatusCard({ lastScan, onScan, isStarting, error, onCancel, isCancelling }) {
  const isActive = lastScan?.is_active;
  const canCancel = Boolean(lastScan?.can_be_cancelled);

  return (
    <div className="rounded-xl bg-white p-6 shadow-xs ring-1 ring-slate-200/70">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Website scan</h2>
          <p className="mt-1 text-sm text-slate-500">
            Crawls the company's public pages for recruitment contacts.
          </p>
        </div>
        {lastScan && (
          <Badge tone={SCAN_STATUS_TONES[lastScan.status] ?? "neutral"}>
            {lastScan.status_display ?? lastScan.status}
          </Badge>
        )}
      </div>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      {lastScan ? (
        <dl className="mb-5 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-slate-500">Pages scanned</dt>
            <dd className="mt-0.5 font-medium tabular-nums text-slate-900">
              {lastScan.pages_scanned} / {lastScan.pages_discovered}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Contacts found</dt>
            <dd className="mt-0.5 font-medium tabular-nums text-slate-900">
              {lastScan.contacts_found}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Progress</dt>
            <dd className="mt-0.5 font-medium tabular-nums text-slate-900">
              {lastScan.progress_percent}%
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Finished</dt>
            <dd className="mt-0.5 font-medium text-slate-900">
              {lastScan.finished_at ? formatDateTime(lastScan.finished_at) : "—"}
            </dd>
          </div>
        </dl>
      ) : (
        <p className="mb-5 text-sm text-slate-500">This company has not been scanned yet.</p>
      )}

      {lastScan?.error_message && (
        <p className="mb-5 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {lastScan.error_message}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={onScan} isLoading={isStarting} disabled={isActive}>
          {isActive ? "Scan in progress" : lastScan ? "Scan again" : "Scan website"}
        </Button>

        {/* Only offered while there is something to stop. A running crawl can
            take a couple of minutes, so leaving the user no way out but
            waiting is poor. */}
        {canCancel && onCancel && (
          <Button variant="secondary" onClick={onCancel} isLoading={isCancelling}>
            {isCancelling ? "Cancelling..." : "Cancel scan"}
          </Button>
        )}

        {lastScan && (
          <Link
            to={`/scans/${lastScan.id}`}
            className="text-sm font-medium text-brand-700 hover:text-brand-800"
          >
            View scan progress
          </Link>
        )}
      </div>
    </div>
  );
}
