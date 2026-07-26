import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createNote, deleteNote, fetchNotes, updateNote } from "../services/notesService";
import { queryKeys } from "../services/queryKeys";

export function useNotes(params) {
  return useQuery({
    queryKey: queryKeys.notes.list(params),
    queryFn: () => fetchNotes(params),
    placeholderData: keepPreviousData,
  });
}

function useNoteMutation(mutationFn) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notes.all });
      // Company detail shows a note count.
      queryClient.invalidateQueries({ queryKey: queryKeys.companies.all });
    },
  });
}

export const useCreateNote = () => useNoteMutation(createNote);
export const useUpdateNote = () => useNoteMutation(updateNote);
export const useDeleteNote = () => useNoteMutation(deleteNote);
