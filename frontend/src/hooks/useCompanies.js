import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createCompany,
  deleteCompany,
  fetchCompanies,
  fetchCompany,
  updateCompany,
} from "../services/companiesService";
import { queryKeys } from "../services/queryKeys";

export function useCompanies(params) {
  return useQuery({
    queryKey: queryKeys.companies.list(params),
    queryFn: () => fetchCompanies(params),
    // Keeps the previous page on screen while the next one loads, so paging
    // and typing in the search box do not flash an empty table.
    placeholderData: keepPreviousData,
  });
}

export function useCompany(id) {
  return useQuery({
    queryKey: queryKeys.companies.detail(id),
    queryFn: () => fetchCompany(id),
    enabled: Boolean(id),
  });
}

export function useCreateCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createCompany,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.companies.all });
      // The dashboard counts companies, so it is stale now too.
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
}

export function useUpdateCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateCompany,
    onSuccess: (company) => {
      queryClient.setQueryData(queryKeys.companies.detail(company.id), company);
      queryClient.invalidateQueries({ queryKey: queryKeys.companies.all });
    },
  });
}

export function useDeleteCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteCompany,
    onSuccess: () => {
      // Deleting a company cascades to its notes, contacts, scans and
      // applications, so everything is invalidated rather than surgically
      // patched.
      queryClient.invalidateQueries({ queryKey: queryKeys.companies.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.notes.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.contacts.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.applications.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
}
