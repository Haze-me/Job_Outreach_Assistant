import apiClient from "./apiClient";
import { cleanParams } from "./companiesService";

export async function fetchNotes(params = {}) {
  const { data } = await apiClient.get("/notes/", { params: cleanParams(params) });
  return data;
}

export async function createNote({ company, content }) {
  const { data } = await apiClient.post("/notes/", { company, content });
  return data;
}

export async function updateNote({ id, content }) {
  const { data } = await apiClient.patch(`/notes/${id}/`, { content });
  return data;
}

export async function deleteNote(id) {
  await apiClient.delete(`/notes/${id}/`);
  return id;
}
