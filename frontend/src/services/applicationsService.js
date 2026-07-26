import apiClient from "./apiClient";
import { cleanParams } from "./companiesService";

export async function fetchApplications(params = {}) {
  const { data } = await apiClient.get("/applications/", { params: cleanParams(params) });
  return data;
}

/** Maps the form's camelCase fields onto the API's snake_case payload. */
function toPayload({ company, contact, contactEmail, position, applicationDate, status, notes }) {
  return {
    company,
    // An empty select means "no linked contact", which the API expects as null
    // rather than an empty string.
    contact: contact || null,
    contact_email: contactEmail ?? "",
    position,
    application_date: applicationDate,
    status,
    notes: notes ?? "",
  };
}

export async function createApplication(values) {
  const { data } = await apiClient.post("/applications/", toPayload(values));
  return data;
}

export async function updateApplication({ id, ...values }) {
  const { data } = await apiClient.patch(`/applications/${id}/`, toPayload(values));
  return data;
}

export async function deleteApplication(id) {
  await apiClient.delete(`/applications/${id}/`);
  return id;
}
