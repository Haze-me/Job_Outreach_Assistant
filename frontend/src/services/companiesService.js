import apiClient from "./apiClient";

/**
 * Strips empty values before they become query parameters.
 *
 * `?industry=` is not the same as omitting `industry`: the API would filter on
 * an empty string and return nothing.
 */
export function cleanParams(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(
      ([, value]) => value !== "" && value !== null && value !== undefined,
    ),
  );
}

export async function fetchCompanies(params = {}) {
  const { data } = await apiClient.get("/companies/", { params: cleanParams(params) });
  return data;
}

export async function fetchCompany(id) {
  const { data } = await apiClient.get(`/companies/${id}/`);
  return data;
}

export async function createCompany(payload) {
  const { data } = await apiClient.post("/companies/", payload);
  return data;
}

export async function updateCompany({ id, ...payload }) {
  const { data } = await apiClient.patch(`/companies/${id}/`, payload);
  return data;
}

export async function deleteCompany(id) {
  await apiClient.delete(`/companies/${id}/`);
  return id;
}
