import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { FavouriteToggle } from "../components/contacts/FavouriteToggle";
import { Alert } from "../components/ui/Alert";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { CopyButton } from "../components/ui/CopyButton";
import { EmptyState } from "../components/ui/EmptyState";
import { Modal } from "../components/ui/Modal";
import { PageHeader } from "../components/ui/PageHeader";
import { Pagination } from "../components/ui/Pagination";
import { SearchInput } from "../components/ui/SearchInput";
import { Select } from "../components/ui/Select";
import { TableSkeleton } from "../components/ui/TableSkeleton";
import { Textarea } from "../components/ui/Textarea";
import { useCompanies } from "../hooks/useCompanies";
import { useContacts, useUpdateContact } from "../hooks/useContacts";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import {
  CONTACT_CLASSIFICATIONS,
  CONTACT_CLASSIFICATION_TONES,
} from "../utils/constants";
import { displayUrl, formatDate } from "../utils/format";
import { getErrorMessage } from "../utils/errors";

const PAGE_SIZE = 20;

export function ContactsPage() {
  // The company filter arrives in the URL from the company page and the scan
  // report, so the link is shareable and survives a reload.
  const [searchParams, setSearchParams] = useSearchParams();
  const companyFilter = searchParams.get("company") ?? "";

  const [search, setSearch] = useState("");
  const [classification, setClassification] = useState("");
  const [favouritesOnly, setFavouritesOnly] = useState(false);
  const [recruitmentOnly, setRecruitmentOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [editingContact, setEditingContact] = useState(null);

  const debouncedSearch = useDebouncedValue(search);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, classification, favouritesOnly, recruitmentOnly, companyFilter]);

  const { data, isPending, isError, error, isPlaceholderData } = useContacts({
    search: debouncedSearch,
    classification,
    company: companyFilter,
    is_favourite: favouritesOnly ? "true" : "",
    recruitment_only: recruitmentOnly ? "true" : "",
    page,
    page_size: PAGE_SIZE,
  });

  const { data: companiesPage } = useCompanies({ page_size: 100, ordering: "name" });
  const updateContact = useUpdateContact();

  const contacts = data?.results ?? [];
  const companyOptions = (companiesPage?.results ?? []).map((company) => ({
    value: company.id,
    label: company.name,
  }));

  function setCompanyFilter(value) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set("company", value);
    else next.delete("company");
    setSearchParams(next, { replace: true });
  }

  const hasFilters = Boolean(
    debouncedSearch || classification || companyFilter || favouritesOnly || recruitmentOnly,
  );

  return (
    <>
      <PageHeader
        title="Contacts"
        description="Publicly published addresses discovered by your scans."
      />

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search email, notes, company"
          label="Search contacts"
          className="sm:col-span-2"
        />
        <Select
          options={CONTACT_CLASSIFICATIONS}
          value={classification}
          onChange={(event) => setClassification(event.target.value)}
          placeholder="All classifications"
          aria-label="Filter by classification"
        />
        <Select
          options={companyOptions}
          value={companyFilter}
          onChange={(event) => setCompanyFilter(event.target.value)}
          placeholder="All companies"
          aria-label="Filter by company"
        />
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={recruitmentOnly}
            onChange={(event) => setRecruitmentOnly(event.target.checked)}
            className="size-4 rounded border-slate-300 text-brand-600"
          />
          Recruitment-related only
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={favouritesOnly}
            onChange={(event) => setFavouritesOnly(event.target.checked)}
            className="size-4 rounded border-slate-300 text-brand-600"
          />
          Favourites only
        </label>
        {hasFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setSearch("");
              setClassification("");
              setFavouritesOnly(false);
              setRecruitmentOnly(false);
              setCompanyFilter("");
            }}
          >
            Clear filters
          </Button>
        )}
      </div>

      {isError && (
        <Alert variant="error" className="mb-4">
          {getErrorMessage(error)}
        </Alert>
      )}

      <div className="overflow-hidden rounded-xl bg-white shadow-xs ring-1 ring-slate-200/70">
        {isPending ? (
          <TableSkeleton rows={6} columns={5} />
        ) : contacts.length === 0 ? (
          <EmptyState
            title={hasFilters ? "No contacts match those filters" : "No contacts yet"}
            description={
              hasFilters
                ? "Try widening the search, or clear the filters."
                : "Scan a company's website and any published addresses will appear here."
            }
            action={
              !hasFilters && (
                <Link
                  to="/companies"
                  className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
                >
                  Go to companies
                </Link>
              )
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[48rem] text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs tracking-wide text-slate-500 uppercase">
                <tr>
                  <th scope="col" className="w-10 px-2 py-3" />
                  <th scope="col" className="px-4 py-3 font-medium">Email</th>
                  <th scope="col" className="px-4 py-3 font-medium">Classification</th>
                  <th scope="col" className="px-4 py-3 font-medium">Company</th>
                  <th scope="col" className="px-4 py-3 font-medium">Found</th>
                  <th scope="col" className="px-4 py-3 font-medium">Notes</th>
                </tr>
              </thead>
              <tbody className={`divide-y divide-slate-100 ${isPlaceholderData ? "opacity-60" : ""}`}>
                {contacts.map((contact) => (
                  <tr key={contact.id} className="hover:bg-slate-50">
                    <td className="px-2 py-3">
                      <FavouriteToggle
                        isFavourite={contact.is_favourite}
                        disabled={updateContact.isPending}
                        onToggle={() =>
                          updateContact.mutate({
                            id: contact.id,
                            isFavourite: !contact.is_favourite,
                          })
                        }
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <a
                          href={`mailto:${contact.email}`}
                          className="font-medium text-slate-800 hover:text-brand-700"
                        >
                          {contact.email}
                        </a>
                        <CopyButton value={contact.email} />
                      </div>
                      {contact.source_url && (
                        <a
                          href={contact.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-slate-400 hover:text-slate-600"
                          title={contact.source_url}
                        >
                          from {displayUrl(contact.source_url)}
                        </a>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Badge tone={CONTACT_CLASSIFICATION_TONES[contact.classification] ?? "neutral"}>
                        {contact.classification_display}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        to={`/companies/${contact.company}`}
                        className="text-slate-600 hover:text-brand-700"
                      >
                        {contact.company_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-500">
                      {formatDate(contact.date_discovered)}
                    </td>
                    <td className="px-4 py-3">
                      <Button variant="ghost" size="sm" onClick={() => setEditingContact(contact)}>
                        {contact.notes ? "Edit note" : "Add note"}
                      </Button>
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
        itemLabel="contact"
      />

      <ContactNotesModal
        contact={editingContact}
        onClose={() => setEditingContact(null)}
        onSave={async (notes) => {
          await updateContact.mutateAsync({ id: editingContact.id, notes });
          setEditingContact(null);
        }}
      />
    </>
  );
}

function ContactNotesModal({ contact, onClose, onSave }) {
  const [notes, setNotes] = useState("");
  const [isSaving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Reset whenever a different contact is opened.
  useEffect(() => {
    setNotes(contact?.notes ?? "");
    setError(null);
  }, [contact]);

  if (!contact) return null;

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await onSave(notes);
    } catch (saveError) {
      setError(getErrorMessage(saveError));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open onClose={onClose} title="Contact notes" description={contact.email}>
      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}

      <Textarea
        label="Notes"
        value={notes}
        onChange={(event) => setNotes(event.target.value)}
        rows={5}
        placeholder="Emailed on Monday, waiting for a reply..."
      />

      <div className="mt-5 flex justify-end gap-3">
        <Button variant="secondary" onClick={onClose} disabled={isSaving}>
          Cancel
        </Button>
        <Button onClick={handleSave} isLoading={isSaving}>
          Save note
        </Button>
      </div>
    </Modal>
  );
}
