import apiClient from "./apiClient";

export async function fetchDashboard() {
  const { data } = await apiClient.get("/dashboard/");
  return data;
}
