import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader } from "../components/ui/PageHeader";
import { Pagination } from "../components/ui/Pagination";
import { SearchInput } from "../components/ui/SearchInput";
import { Select } from "../components/ui/Select";
import { TableSkeleton } from "../components/ui/TableSkeleton";
import { useCompanies } from "../hooks/useCompanies";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { displayUrl, formatDate } from "../utils/format";
import { getErrorMessage } from "../utils/errors";

const PAGE_SIZE = 20;

const ORDERING_OPTIONS = [
  { value: "-created_at", label: "Newest first" },
  { value: "created_at", label: "Oldest first" },
  { value: "name", label: "Name (A–Z)" },
  { value: "-name", label: "Name (Z–A)" },
];

export function CompaniesPage() {
  const [search, setSearch] = useState("");
  const [industry, setIndustry] = useState("");
  const [country, setCountry] = useState("");
  const [ordering, setOrdering] = useState("-created_at");
  const [page, setPage] = useState(1);

  const debouncedSearch = useDebouncedValue(search);

  // Any filter change invalidates the current page number: being on page 3 of
  // a result set that now has one page would show an empty table.
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, industry, country, ordering]);

  const { data, isPending, isError, error, isPlaceholderData } = useCompanies({
    search: debouncedSearch,
    industry,
    country,
    ordering,
    page,
    page_size: PAGE_SIZE,
  });

  const companies = data?.results ?? [];
  const hasFilters = Boolean(debouncedSearch || industry || country);

  return (
    <>
      <PageHeader
        title="Companies"
        description="Companies you are tracking."
        action={
          <Link
            to="/companies/new"
            className="inline-flex items-center rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-700"
          >
            Add company
          </Link>
        }
      />

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search name, industry, country"
          label="Search companies"
          className="sm:col-span-2"
        />
        <input
          type="text"
          value={industry}
          onChange={(event) => setIndustry(event.target.value)}
          placeholder="Filter by industry"
          aria-label="Filter by industry"
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-xs placeholder:text-slate-400"
        />
        <input
          type="text"
          value={country}
          onChange={(event) => setCountry(event.target.value)}
          placeholder="Filter by country"
          aria-label="Filter by country"
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-xs placeholder:text-slate-400"
        />
      </div>

      <div className="mb-4 flex justify-end">
        <Select
          options={ORDERING_OPTIONS}
          value={ordering}
          onChange={(event) => setOrdering(event.target.value)}
          aria-label="Sort companies"
          className="w-48"
        />
      </div>

      {isError && (
        <Alert variant="error" className="mb-4">
          {getErrorMessage(error)}
        </Alert>
      )}

      <div className="overflow-hidden rounded-xl bg-white shadow-xs ring-1 ring-slate-200/70">
        {isPending ? (
          <TableSkeleton rows={5} columns={5} />
        ) : companies.length === 0 ? (
          <EmptyState
            title={hasFilters ? "No companies match those filters" : "No companies yet"}
            description={
              hasFilters
                ? "Try a different search term, or clear the filters."
                : "Add a company website and scan it to discover recruitment contacts."
            }
            action={
              hasFilters ? (
                <Button
                  variant="secondary"
                  onClick={() => {
                    setSearch("");
                    setIndustry("");
                    setCountry("");
                  }}
                >
                  Clear filters
                </Button>
              ) : (
                <Link
                  to="/companies/new"
                  className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
                >
                  Add your first company
                </Link>
              )
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[42rem] text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs tracking-wide text-slate-500 uppercase">
                <tr>
                  <th scope="col" className="px-4 py-3 font-medium">Company</th>
                  <th scope="col" className="px-4 py-3 font-medium">Industry</th>
                  <th scope="col" className="px-4 py-3 font-medium">Country</th>
                  <th scope="col" className="px-4 py-3 font-medium">Notes</th>
                  <th scope="col" className="px-4 py-3 font-medium">Added</th>
                </tr>
              </thead>
              <tbody
                className={`divide-y divide-slate-100 ${isPlaceholderData ? "opacity-60" : ""}`}
              >
                {companies.map((company) => (
                  <tr key={company.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <Link
                        to={`/companies/${company.id}`}
                        className="font-medium text-brand-700 hover:text-brand-800"
                      >
                        {company.name}
                      </Link>
                      <p className="text-xs text-slate-500">{displayUrl(company.website)}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{company.industry || "—"}</td>
                    <td className="px-4 py-3 text-slate-600">{company.country || "—"}</td>
                    <td className="px-4 py-3 text-slate-600 tabular-nums">
                      {company.notes_count}
                    </td>
                    <td className="px-4 py-3 text-slate-500">{formatDate(company.date_added)}</td>
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
        itemLabel="company"
        itemLabelPlural="companies"
      />
    </>
  );
}
