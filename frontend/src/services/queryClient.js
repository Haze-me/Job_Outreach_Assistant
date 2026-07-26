import { QueryClient } from "@tanstack/react-query";

import { isAuthError } from "../utils/errors";

/**
 * React Query defaults for the whole app.
 *
 * The important one is the retry rule: retrying a 401 or a 4xx is pointless
 * work that only delays the error the user needs to see. Retries are reserved
 * for failures that might genuinely succeed on a second attempt.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Data is considered fresh for a minute: switching between pages should
      // feel instant rather than re-fetching everything.
      staleTime: 60_000,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        const status = error?.response?.status;
        if (isAuthError(error) || (status >= 400 && status < 500)) return false;
        return failureCount < 2;
      },
    },
    mutations: {
      // A mutation has side effects; replaying it automatically could create
      // the same record twice.
      retry: false,
    },
  },
});
