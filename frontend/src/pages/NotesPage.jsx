import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { NoteComposer } from "../components/notes/NoteComposer";
import { NoteList } from "../components/notes/NoteList";
import { Alert } from "../components/ui/Alert";
import { Card, CardHeader } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader } from "../components/ui/PageHeader";
import { Pagination } from "../components/ui/Pagination";
import { SearchInput } from "../components/ui/SearchInput";
import { Select } from "../components/ui/Select";
import { useCompanies } from "../hooks/useCompanies";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useCreateNote, useDeleteNote, useNotes, useUpdateNote } from "../hooks/useNotes";
import { getErrorMessage } from "../utils/errors";

const PAGE_SIZE = 20;

export function NotesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const companyFilter = searchParams.get("company") ?? "";

  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const debouncedSearch = useDebouncedValue(search);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, companyFilter]);

  const { data, isPending, isError, error } = useNotes({
    search: debouncedSearch,
    company: companyFilter,
    page,
    page_size: PAGE_SIZE,
  });

  const { data: companiesPage } = useCompanies({ page_size: 100, ordering: "name" });
  const createNote = useCreateNote();
  const updateNote = useUpdateNote();
  const deleteNote = useDeleteNote();

  const notes = data?.results ?? [];
  const companies = companiesPage?.results ?? [];
  const companyOptions = companies.map((company) => ({
    value: company.id,
    label: company.name,
  }));

  function setCompanyFilter(value) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set("company", value);
    else next.delete("company");
    setSearchParams(next, { replace: true });
  }

  // A note must belong to a company, so composing needs one selected.
  const canCompose = Boolean(companyFilter);

  return (
    <>
      <PageHeader
        title="Notes"
        description="Everything you have recorded across your companies, newest first."
      />

      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search note content"
          label="Search notes"
          className="sm:col-span-2"
        />
        <Select
          options={companyOptions}
          value={companyFilter}
          onChange={(event) => setCompanyFilter(event.target.value)}
          placeholder="All companies"
          aria-label="Filter by company"
        />
      </div>

      {isError && (
        <Alert variant="error" className="mb-4">
          {getErrorMessage(error)}
        </Alert>
      )}

      {companies.length === 0 ? (
        <EmptyState
          title="No companies yet"
          description="Notes are attached to companies. Add a company first."
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader
                title={data?.count ? `${data.count} notes` : "Notes"}
                description={companyFilter ? "Filtered to one company." : "Across all companies."}
              />
              {isPending ? (
                <div className="space-y-3" aria-hidden="true">
                  {[0, 1, 2].map((row) => (
                    <div key={row} className="h-20 animate-pulse rounded-lg bg-slate-100" />
                  ))}
                </div>
              ) : (
                <NoteList
                  notes={notes}
                  showCompany
                  onUpdate={(values) => updateNote.mutateAsync(values)}
                  onDelete={(id) => deleteNote.mutateAsync(id)}
                />
              )}

              <Pagination
                page={data?.page ?? 1}
                totalPages={data?.total_pages ?? 1}
                count={data?.count ?? 0}
                pageSize={data?.page_size ?? PAGE_SIZE}
                onPageChange={setPage}
                itemLabel="note"
              />
            </Card>
          </div>

          <Card className="h-fit">
            <CardHeader
              title="Add a note"
              description={
                canCompose
                  ? "Added to the company selected above."
                  : "Choose a company above to add a note."
              }
            />
            {canCompose ? (
              <NoteComposer
                onSubmit={(content) =>
                  createNote.mutateAsync({ company: companyFilter, content })
                }
              />
            ) : (
              <p className="text-sm text-slate-500">
                Notes belong to a company. Select one from the filter to write a note against it.
              </p>
            )}
          </Card>
        </div>
      )}
    </>
  );
}
