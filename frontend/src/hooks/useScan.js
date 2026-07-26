import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "../services/queryKeys";
import { fetchScanStatus, startScan } from "../services/scanService";

/** How often a running scan is polled, in milliseconds. */
const POLL_INTERVAL = 2000;

export function useStartScan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: startScan,
    onSuccess: (scan) => {
      queryClient.setQueryData(queryKeys.scans.status(scan.id), scan);
      // The company's `last_scan` has changed.
      queryClient.invalidateQueries({ queryKey: queryKeys.companies.all });
    },
  });
}

/**
 * Watches one scan.
 *
 * Polling stops as soon as the scan is no longer active, so a finished scan
 * does not keep making requests forever. When it completes, the contact and
 * dashboard caches are invalidated -- a scan is the only thing that creates
 * contacts, so those screens are stale by definition.
 */
export function useScanStatus(scanId, { enabled = true } = {}) {
  const queryClient = useQueryClient();

  return useQuery({
    queryKey: queryKeys.scans.status(scanId),
    queryFn: async () => {
      const scan = await fetchScanStatus(scanId);

      if (!scan.is_active) {
        queryClient.invalidateQueries({ queryKey: queryKeys.contacts.all });
        queryClient.invalidateQueries({ queryKey: queryKeys.companies.all });
        queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
      }
      return scan;
    },
    enabled: Boolean(scanId) && enabled,
    refetchInterval: (query) => (query.state.data?.is_active ? POLL_INTERVAL : false),
    // Progress must never be served from cache.
    staleTime: 0,
  });
}
