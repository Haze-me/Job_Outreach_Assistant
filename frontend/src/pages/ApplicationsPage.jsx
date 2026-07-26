import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApplicationForm } from "../components/applications/ApplicationForm";
import { Alert } from "../components/ui/Alert";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { EmptyState } from "../components/ui/EmptyState";
import { Modal } from "../components/ui/Modal";
import { PageHeader } from "../components/ui/PageHeader";
import { Pagination } from "../components/ui/Pagination";
import { SearchInput } from "../components/ui/SearchInput";
import { Select } from "../components/ui/Select";
import { TableSkeleton } from "../components/ui/TableSkeleton";
import {
  useApplications,
  useCreateApplication,
  useDeleteApplication,
  useUpdateApplication,
} from "../hooks/useApplications";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { APPLICATION_STATUSES, APPLICATION_STATUS_TONES } from "../utils/constants";
import { formatDate } from "../utils/format";
import { getErrorMessage } from "../utils/errors";

const PAGE_SIZE = 20;

export function ApplicationsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [isCreating, setCreating] = useState(false);
  const [editing, setEditing] = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);

  const debouncedSearch = useDebouncedValue(search);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, status]);

  const { data, isPending, isError, error, isPlaceholderData } = useApplications({
    search: debouncedSearch,
    status,
    page,
    page_size: PAGE_SIZE,
  });

  const createApplication = useCreateApplication();
  const updateApplication = useUpdateApplication();
  const deleteApplication = useDeleteApplication();

  const applications = data?.results ?? [];
  const hasFilters = Boolean(debouncedSearch || status);

  return (
    <>
      <PageHeader
        title="Applications"
        description="Every application you have recorded, and where it stands."
        action={<Button onClick={() => setCreating(true)}>Record application</Button>}
      />

      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search position, company, email, notes"
          label="Search applications"
          className="sm:col-span-2"
        />
        <Select
          options={APPLICATION_STATUSES}
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          placeholder="All statuses"
          aria-label="Filter by status"
        />
      </div>

      {isError && (
        <Alert variant="error" className="mb-4">
          {getErrorMessage(error)}
        </Alert>
      )}

      <div className="overflow-hidden rounded-xl bg-white shadow-xs ring-1 ring-slate-200/70">
        {isPending ? (
          <TableSkeleton rows={6} columns={5} />
        ) : applications.length === 0 ? (
          <EmptyState
            title={hasFilters ? "No applications match those filters" : "No applications yet"}
            description={
              hasFilters
                ? "Try a different search term or status."
                : "Record an application to track where it stands."
            }
            action={
              hasFilters ? (
                <Button
                  variant="secondary"
                  onClick={() => {
                    setSearch("");
                    setStatus("");
                  }}
                >
                  Clear filters
                </Button>
              ) : (
                <Button onClick={() => setCreating(true)}>Record your first application</Button>
              )
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[46rem] text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs tracking-wide text-slate-500 uppercase">
                <tr>
                  <th scope="col" className="px-4 py-3 font-medium">Position</th>
                  <th scope="col" className="px-4 py-3 font-medium">Company</th>
                  <th scope="col" className="px-4 py-3 font-medium">Status</th>
                  <th scope="col" className="px-4 py-3 font-medium">Applied</th>
                  <th scope="col" className="px-4 py-3 font-medium">Contact</th>
                  <th scope="col" className="px-4 py-3 font-medium"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className={`divide-y divide-slate-100 ${isPlaceholderData ? "opacity-60" : ""}`}>
                {applications.map((application) => (
                  <tr key={application.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-800">{application.position}</td>
                    <td className="px-4 py-3">
                      <Link
                        to={`/companies/${application.company}`}
                        className="text-slate-600 hover:text-brand-700"
                      >
                        {application.company_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <Badge tone={APPLICATION_STATUS_TONES[application.status] ?? "neutral"}>
                        {application.status_display}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-slate-500">
                      {formatDate(application.application_date)}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {application.contact_email || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="sm" onClick={() => setEditing(application)}>
                          Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setPendingDelete(application)}
                        >
                          Delete
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Pagination
        page={data?.page ?? 1}
        totalPages={data?.total_pages ?? 1}
        count={data?.count ?? 0}
        pageSize={data?.page_size ?? PAGE_SIZE}
        onPageChange={setPage}
        itemLabel="application"
      />

      <Modal
        open={isCreating}
        onClose={() => setCreating(false)}
        title="Record an application"
        size="lg"
      >
        <ApplicationForm
          submitLabel="Save application"
          onCancel={() => setCreating(false)}
          onSubmit={async (values) => {
            await createApplication.mutateAsync(values);
            setCreating(false);
          }}
        />
      </Modal>

      <Modal
        open={Boolean(editing)}
        onClose={() => setEditing(null)}
        title="Edit application"
        size="lg"
      >
        {editing && (
          <ApplicationForm
            initialValues={{
              company: editing.company,
              contact: editing.contact ?? "",
              contactEmail: editing.contact_email ?? "",
              position: editing.position,
              applicationDate: editing.application_date,
              status: editing.status,
              notes: editing.notes ?? "",
            }}
            submitLabel="Save changes"
            onCancel={() => setEditing(null)}
            onSubmit={async (values) => {
              await updateApplication.mutateAsync({ id: editing.id, ...values });
              setEditing(null);
            }}
          />
        )}
      </Modal>

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        onClose={() => setPendingDelete(null)}
        onConfirm={async () => {
          await deleteApplication.mutateAsync(pendingDelete.id);
          setPendingDelete(null);
        }}
        title="Delete this application?"
        description={
          pendingDelete
            ? `"${pendingDelete.position}" at ${pendingDelete.company_name} will be removed. This cannot be undone.`
            : undefined
        }
        isLoading={deleteApplication.isPending}
        error={deleteApplication.isError ? getErrorMessage(deleteApplication.error) : null}
      />
    </>
  );
}
