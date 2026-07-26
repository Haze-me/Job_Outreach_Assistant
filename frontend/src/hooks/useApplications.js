import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createApplication,
  deleteApplication,
  fetchApplications,
  updateApplication,
} from "../services/applicationsService";
import { queryKeys } from "../services/queryKeys";

export function useApplications(params) {
  return useQuery({
    queryKey: queryKeys.applications.list(params),
    queryFn: () => fetchApplications(params),
    placeholderData: keepPreviousData,
  });
}

function useApplicationMutation(mutationFn) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.applications.all });
      // Every dashboard application tile depends on status counts.
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
}

export const useCreateApplication = () => useApplicationMutation(createApplication);
export const useUpdateApplication = () => useApplicationMutation(updateApplication);
export const useDeleteApplication = () => useApplicationMutation(deleteApplication);
