import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { CompanyForm } from "../components/companies/CompanyForm";
import { ScanStatusCard } from "../components/companies/ScanStatusCard";
import { NoteComposer } from "../components/notes/NoteComposer";
import { NoteList } from "../components/notes/NoteList";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card, CardHeader } from "../components/ui/Card";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { Modal } from "../components/ui/Modal";
import { PageHeader } from "../components/ui/PageHeader";
import { FullPageSpinner } from "../components/ui/Spinner";
import { useCompany, useDeleteCompany, useUpdateCompany } from "../hooks/useCompanies";
import { useCreateNote, useDeleteNote, useNotes, useUpdateNote } from "../hooks/useNotes";
import { useContacts } from "../hooks/useContacts";
import { useStartScan } from "../hooks/useScan";
import { displayUrl, formatDate } from "../utils/format";
import { getErrorMessage } from "../utils/errors";

export function CompanyDetailPage() {
  const { companyId } = useParams();
  const navigate = useNavigate();

  const { data: company, isPending, isError, error, refetch: refetchCompany } = useCompany(companyId);
  const { data: notesPage } = useNotes({ company: companyId, page_size: 50 });
  const { data: contactsPage } = useContacts({ company: companyId, page_size: 5 });

  const updateCompany = useUpdateCompany();
  const deleteCompany = useDeleteCompany();
  const startScan = useStartScan();
  const createNote = useCreateNote();
  const updateNote = useUpdateNote();
  const deleteNote = useDeleteNote();

  const [isEditing, setEditing] = useState(false);
  const [isConfirmingDelete, setConfirmingDelete] = useState(false);
  const [scanError, setScanError] = useState(null);

  if (isPending) return <FullPageSpinner label="Loading company" />;

  if (isError) {
    return (
      <>
        <PageHeader title="Company" />
        <Alert variant="error">{getErrorMessage(error)}</Alert>
        <Link
          to="/companies"
          className="mt-4 inline-block text-sm font-medium text-brand-700 hover:text-brand-800"
        >
          Back to companies
        </Link>
      </>
    );
  }

  async function handleScan() {
    setScanError(null);
    const previousScanId = company.last_scan?.id ?? null;

    try {
      const scan = await startScan.mutateAsync(companyId);
      navigate(`/scans/${scan.id}`);
    } catch (startError) {
      // The request can fail *after* the server has already started the scan:
      // a client timeout, a dropped connection, a reload mid-request. The
      // server is the source of truth, so ask what actually happened before
      // telling the user it failed. A newer `last_scan` than the one we had
      // before clicking means the scan did start, and the progress page can
      // pick it up from there.
      try {
        const { data: refreshed } = await refetchCompany();
        const latest = refreshed?.last_scan;
        if (latest && latest.id !== previousScanId) {
          navigate(`/scans/${latest.id}`);
          return;
        }
      } catch {
        // Could not reach the server either; fall through to the real error.
      }

      // Genuinely failed. A 409 (a scan is already running) lands here too,
      // with a message that says so.
      setScanError(getErrorMessage(startError));
    }
  }

  const notes = notesPage?.results ?? [];
  const contacts = contactsPage?.results ?? [];

  return (
    <>
      <PageHeader
        title={company.name}
        description={
          <a
            href={company.website}
            target="_blank"
            rel="noopener noreferrer"
            className="text-brand-700 hover:text-brand-800"
          >
            {displayUrl(company.website)}
          </a>
        }
        action={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setEditing(true)}>
              Edit
            </Button>
            <Button variant="danger" onClick={() => setConfirmingDelete(true)}>
              Delete
            </Button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <ScanStatusCard
            lastScan={company.last_scan}
            onScan={handleScan}
            isStarting={startScan.isPending}
            error={scanError}
          />

          <Card>
            <CardHeader
              title="Notes"
              description="Dated entries tracking your outreach with this company."
            />
            <div className="mb-6">
              <NoteComposer
                onSubmit={(content) =>
                  createNote.mutateAsync({ company: companyId, content })
                }
              />
            </div>
            <NoteList
              notes={notes}
              onUpdate={(values) => updateNote.mutateAsync(values)}
              onDelete={(id) => deleteNote.mutateAsync(id)}
              emptyMessage="Track what you have sent and what came back."
            />
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader title="Details" />
            <dl className="space-y-3 text-sm">
              <Detail label="Industry" value={company.industry} />
              <Detail label="Country" value={company.country} />
              <Detail label="Added" value={formatDate(company.date_added)} />
              <Detail label="Notes" value={String(company.notes_count)} />
            </dl>

            {company.description && (
              <div className="mt-5 border-t border-slate-100 pt-4">
                <p className="mb-1 text-sm font-medium text-slate-700">Description</p>
                <p className="text-sm whitespace-pre-wrap text-slate-600">
                  {company.description}
                </p>
              </div>
            )}

            {company.notes && (
              <div className="mt-5 border-t border-slate-100 pt-4">
                <p className="mb-1 text-sm font-medium text-slate-700">Scratchpad</p>
                <p className="text-sm whitespace-pre-wrap text-slate-600">{company.notes}</p>
              </div>
            )}
          </Card>

          <Card>
            <CardHeader
              title="Contacts"
              description={`${contactsPage?.count ?? 0} discovered`}
              action={
                (contactsPage?.count ?? 0) > 0 && (
                  <Link
                    to={`/contacts?company=${companyId}`}
                    className="text-sm font-medium text-brand-700 hover:text-brand-800"
                  >
                    View all
                  </Link>
                )
              }
            />
            {contacts.length === 0 ? (
              <p className="text-sm text-slate-500">
                No contacts yet. Scan the website to look for published addresses.
              </p>
            ) : (
              <ul className="space-y-2">
                {contacts.map((contact) => (
                  <li key={contact.id} className="text-sm">
                    <span className="font-medium text-slate-800">{contact.email}</span>
                    <span className="ml-2 text-xs text-slate-500">
                      {contact.classification_display}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>

      <Modal open={isEditing} onClose={() => setEditing(false)} title="Edit company">
        <CompanyForm
          initialValues={{
            name: company.name,
            website: company.website,
            industry: company.industry,
            country: company.country,
            description: company.description,
            notes: company.notes,
          }}
          submitLabel="Save changes"
          onCancel={() => setEditing(false)}
          onSubmit={async (values) => {
            await updateCompany.mutateAsync({ id: companyId, ...values });
            setEditing(false);
          }}
        />
      </Modal>

      <ConfirmDialog
        open={isConfirmingDelete}
        onClose={() => setConfirmingDelete(false)}
        onConfirm={async () => {
          await deleteCompany.mutateAsync(companyId);
          navigate("/companies", { replace: true });
        }}
        title={`Delete ${company.name}?`}
        description="This also deletes its notes, discovered contacts, scan history, and any applications recorded against it. This cannot be undone."
        confirmLabel="Delete company"
        isLoading={deleteCompany.isPending}
        error={deleteCompany.isError ? getErrorMessage(deleteCompany.error) : null}
      />
    </>
  );
}

function Detail({ label, value }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-right font-medium text-slate-900">{value || "—"}</dd>
    </div>
  );
}
