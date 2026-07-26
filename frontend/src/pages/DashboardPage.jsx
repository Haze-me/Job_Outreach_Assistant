import { Alert } from "../components/ui/Alert";
import { Card, CardHeader } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/ui/StatCard";
import { useAuth } from "../hooks/useAuth";
import { useDashboard } from "../hooks/useDashboard";
import { getErrorMessage } from "../utils/errors";

const STATUS_LABELS = {
  draft: "Draft",
  sent: "Sent",
  waiting: "Waiting",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
  closed: "Closed",
};

export function DashboardPage() {
  const { user } = useAuth();
  const { data, isPending, isError, error } = useDashboard();

  const greetingName = user?.first_name?.trim() || user?.email?.split("@")[0] || "there";

  return (
    <>
      <PageHeader
        title={`Welcome back, ${greetingName}`}
        description="Your outreach at a glance."
      />

      {isError && (
        <Alert variant="error" className="mb-6">
          {getErrorMessage(error)}
        </Alert>
      )}

      <section aria-label="Companies and contacts" className="mb-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Companies"
            value={data?.total_companies ?? 0}
            isLoading={isPending}
          />
          <StatCard
            label="Companies scanned"
            value={data?.companies_scanned ?? 0}
            hint="At least one completed scan"
            isLoading={isPending}
          />
          <StatCard
            label="Contacts found"
            value={data?.total_contacts ?? 0}
            tone="brand"
            isLoading={isPending}
          />
          <StatCard
            label="Favourites"
            value={data?.favourite_contacts ?? 0}
            isLoading={isPending}
          />
        </div>
      </section>

      <section aria-label="Applications">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Applications sent"
            value={data?.applications_sent ?? 0}
            hint="Anything past draft"
            isLoading={isPending}
          />
          <StatCard
            label="Pending"
            value={data?.pending_applications ?? 0}
            hint="Sent, awaiting a reply"
            tone="warning"
            isLoading={isPending}
          />
          <StatCard
            label="Interviews"
            value={data?.interviews ?? 0}
            tone="brand"
            isLoading={isPending}
          />
          <StatCard
            label="Offers"
            value={data?.offers ?? 0}
            tone="positive"
            isLoading={isPending}
          />
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Rejections"
            value={data?.rejections ?? 0}
            tone="negative"
            isLoading={isPending}
          />
          <StatCard label="Drafts" value={data?.drafts ?? 0} isLoading={isPending} />
          <StatCard
            label="Total applications"
            value={data?.total_applications ?? 0}
            isLoading={isPending}
          />
        </div>
      </section>

      <Card className="mt-8">
        <CardHeader
          title="Applications by status"
          description="Every application you have recorded, grouped by where it stands."
        />
        {isPending ? (
          <div className="h-24 animate-pulse rounded-lg bg-slate-100" aria-hidden="true" />
        ) : (
          <StatusBreakdown breakdown={data?.applications_by_status} />
        )}
      </Card>
    </>
  );
}

function StatusBreakdown({ breakdown }) {
  const entries = Object.entries(breakdown ?? {});
  const total = entries.reduce((sum, [, count]) => sum + count, 0);

  if (total === 0) {
    return (
      <p className="text-sm text-slate-500">
        No applications recorded yet. Once you add one, it will appear here.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {entries.map(([status, count]) => (
        <li key={status} className="flex items-center gap-4">
          <span className="w-24 shrink-0 text-sm text-slate-600">
            {STATUS_LABELS[status] ?? status}
          </span>
          <div
            className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100"
            role="img"
            aria-label={`${STATUS_LABELS[status] ?? status}: ${count} of ${total}`}
          >
            <div
              className="h-full rounded-full bg-brand-500"
              style={{ width: `${total ? (count / total) * 100 : 0}%` }}
            />
          </div>
          <span className="w-8 shrink-0 text-right text-sm font-medium tabular-nums text-slate-900">
            {count}
          </span>
        </li>
      ))}
    </ul>
  );
}
