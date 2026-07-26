import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchContact, fetchContacts, updateContact } from "../services/contactsService";
import { queryKeys } from "../services/queryKeys";

export function useContacts(params) {
  return useQuery({
    queryKey: queryKeys.contacts.list(params),
    queryFn: () => fetchContacts(params),
    placeholderData: keepPreviousData,
  });
}

export function useContact(id) {
  return useQuery({
    queryKey: queryKeys.contacts.detail(id),
    queryFn: () => fetchContact(id),
    enabled: Boolean(id),
  });
}

export function useUpdateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateContact,
    onSuccess: (contact) => {
      queryClient.setQueryData(queryKeys.contacts.detail(contact.id), contact);
      queryClient.invalidateQueries({ queryKey: queryKeys.contacts.all });
      // The dashboard counts favourites.
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
}
