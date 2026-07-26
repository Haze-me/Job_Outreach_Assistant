import { useQuery } from "@tanstack/react-query";

import { fetchDashboard } from "../services/dashboardService";

/** Query keys live in one place so invalidation cannot typo its way to a no-op. */
export const dashboardKeys = {
  all: ["dashboard"],
};

export function useDashboard() {
  return useQuery({
    queryKey: dashboardKeys.all,
    queryFn: fetchDashboard,
  });
}
