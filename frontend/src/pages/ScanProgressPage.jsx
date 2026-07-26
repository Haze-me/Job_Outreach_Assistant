import { Link, useParams } from "react-router-dom";

import { Alert } from "../components/ui/Alert";
import { Badge } from "../components/ui/Badge";
import { Card, CardHeader } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { FullPageSpinner } from "../components/ui/Spinner";
import { StatCard } from "../components/ui/StatCard";
import { useScanStatus } from "../hooks/useScan";
import { PAGE_TYPE_LABELS, SCAN_STATUS_TONES } from "../utils/constants";
import { displayUrl, formatDateTime } from "../utils/format";
import { getErrorMessage } from "../utils/errors";

export function ScanProgressPage() {
  const { scanId } = useParams();
  const { data: scan, isPending, isError, error } = useScanStatus(scanId);

  if (isPending) return <FullPageSpinner label="Loading scan" />;

  if (isError) {
    return (
      <>
        <PageHeader title="Scan" />
        <Alert variant="error">{getErrorMessage(error)}</Alert>
      </>
    );
  }

  const pages = scan.pages ?? [];

  return (
    <>
      <PageHeader
        title="Scan progress"
        description={
          <>
            <Link
              to={`/companies/${scan.company}`}
              className="font-medium text-brand-700 hover:text-brand-800"
            >
              {scan.company_name}
            </Link>
            <span className="text-slate-400"> · {displayUrl(scan.target_url)}</span>
          </>
        }
        action={<Badge tone={SCAN_STATUS_TONES[scan.status] ?? "neutral"}>{scan.status_display}</Badge>}
      />

      {scan.is_active && (
        <Alert variant="info" className="mb-6">
          The scan is running. This page updates automatically — you can leave and come back.
        </Alert>
      )}

      {scan.status === "failed" && (
        <Alert variant="error" title="The scan failed" className="mb-6">
          {scan.error_message || "The website could not be crawled."}
        </Alert>
      )}

      <div className="mb-6">
        <div
          className="h-2 overflow-hidden rounded-full bg-slate-200"
          role="progressbar"
          aria-valuenow={scan.progress_percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Scan progress"
        >
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              scan.status === "failed" ? "bg-red-500" : "bg-brand-500"
            }`}
            style={{ width: `${scan.progress_percent}%` }}
          />
        </div>
        <p className="mt-2 text-sm text-slate-500">{scan.progress_percent}% complete</p>
      </div>

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Pages scanned" value={scan.pages_scanned} />
        <StatCard label="Pages discovered" value={scan.pages_discovered} />
        <StatCard label="Contacts found" value={scan.contacts_found} tone="brand" />
        <StatCard
          label="Finished"
          value={scan.finished_at ? formatDateTime(scan.finished_at) : "—"}
        />
      </div>

      <Card>
        <CardHeader
          title="Pages visited"
          description="Every public page the crawler fetched, and how many addresses each contained."
        />

        {pages.length === 0 ? (
          <p className="text-sm text-slate-500">
            No pages recorded yet. The crawl starts at the homepage.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[36rem] text-left text-sm">
              <thead className="border-b border-slate-200 text-xs tracking-wide text-slate-500 uppercase">
                <tr>
                  <th scope="col" className="py-2 pr-4 font-medium">Page</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Type</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Status</th>
                  <th scope="col" className="py-2 font-medium">Emails</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {pages.map((page) => (
                  <tr key={page.id}>
                    <td className="max-w-md py-2.5 pr-4">
                      <a
                        href={page.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block truncate text-slate-700 hover:text-brand-700"
                        title={page.url}
                      >
                        {displayUrl(page.url)}
                      </a>
                    </td>
                    <td className="py-2.5 pr-4">
                      <Badge tone={page.page_type === "careers" || page.page_type === "jobs" ? "brand" : "neutral"}>
                        {PAGE_TYPE_LABELS[page.page_type] ?? page.page_type}
                      </Badge>
                    </td>
                    <td className="py-2.5 pr-4 tabular-nums text-slate-600">
                      {/* No status code means the fetch failed; the attempt is
                          still recorded so the report is honest. */}
                      {page.status_code ?? <span className="text-red-600">failed</span>}
                    </td>
                    <td className="py-2.5 tabular-nums text-slate-600">{page.emails_found}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {!scan.is_active && scan.contacts_found > 0 && (
        <div className="mt-6">
          <Link
            to={`/contacts?company=${scan.company}`}
            className="inline-flex items-center rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            View the {scan.contacts_found} contacts found
          </Link>
        </div>
      )}
    </>
  );
}
