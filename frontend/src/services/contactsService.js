import apiClient from "./apiClient";
import { cleanParams } from "./companiesService";

export async function fetchContacts(params = {}) {
  const { data } = await apiClient.get("/contacts/", { params: cleanParams(params) });
  return data;
}

export async function fetchContact(id) {
  const { data } = await apiClient.get(`/contacts/${id}/`);
  return data;
}

/**
 * Notes and the favourite flag are the only writable fields -- contacts exist
 * because a scan discovered them, so email and classification are read-only.
 */
export async function updateContact({ id, notes, isFavourite }) {
  const payload = {};
  if (notes !== undefined) payload.notes = notes;
  if (isFavourite !== undefined) payload.is_favourite = isFavourite;

  const { data } = await apiClient.patch(`/contacts/${id}/`, payload);
  return data;
}
