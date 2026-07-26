import { useEffect, useState } from "react";

import { Alert } from "../ui/Alert";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { Textarea } from "../ui/Textarea";
import { useCompanies } from "../../hooks/useCompanies";
import { useContacts } from "../../hooks/useContacts";
import { APPLICATION_STATUSES } from "../../utils/constants";
import { todayIso } from "../../utils/format";
import { getErrorMessage, getFieldErrors } from "../../utils/errors";

const EMPTY = {
  company: "",
  contact: "",
  contactEmail: "",
  position: "",
  applicationDate: todayIso(),
  status: "draft",
  notes: "",
};

export function ApplicationForm({ initialValues, onSubmit, onCancel, submitLabel = "Save" }) {
  const [form, setForm] = useState({ ...EMPTY, ...initialValues });
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [isSubmitting, setSubmitting] = useState(false);

  const { data: companiesPage } = useCompanies({ page_size: 100, ordering: "name" });
  // The API rejects a contact belonging to a different company, so the picker
  // only offers contacts from the selected one.
  const { data: contactsPage } = useContacts({
    company: form.company,
    page_size: 100,
  });

  const companyOptions = (companiesPage?.results ?? []).map((company) => ({
    value: company.id,
    label: company.name,
  }));
  const contactOptions = (contactsPage?.results ?? []).map((contact) => ({
    value: contact.id,
    label: `${contact.email} (${contact.classification_display})`,
  }));

  // Changing company invalidates a contact chosen from the previous one.
  useEffect(() => {
    setForm((current) => {
      if (!current.contact) return current;
      const stillValid = (contactsPage?.results ?? []).some((c) => c.id === current.contact);
      return stillValid ? current : { ...current, contact: "" };
    });
  }, [contactsPage]);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({ ...current, [name]: undefined }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    setFieldErrors({});

    try {
      await onSubmit(form);
    } catch (error) {
      setFormError(getErrorMessage(error));
      setFieldErrors(getFieldErrors(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      {formError && <Alert variant="error">{formError}</Alert>}

      <Select
        label="Company"
        name="company"
        options={companyOptions}
        value={form.company}
        onChange={handleChange}
        placeholder="Select a company"
        error={fieldErrors.company}
        required
      />

      <Input
        label="Position applied for"
        name="position"
        value={form.position}
        onChange={handleChange}
        error={fieldErrors.position}
        required
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <Select
          label="Status"
          name="status"
          options={APPLICATION_STATUSES}
          value={form.status}
          onChange={handleChange}
          error={fieldErrors.status}
          required
        />
        <Input
          label="Application date"
          name="applicationDate"
          type="date"
          value={form.applicationDate}
          onChange={handleChange}
          error={fieldErrors.application_date}
        />
      </div>

      <Select
        label="Contact"
        name="contact"
        options={contactOptions}
        value={form.contact}
        onChange={handleChange}
        placeholder={form.company ? "No linked contact" : "Select a company first"}
        disabled={!form.company}
        error={fieldErrors.contact}
        hint="Linking a discovered contact fills the email in automatically."
      />

      <Input
        label="Contact email"
        name="contactEmail"
        type="email"
        value={form.contactEmail}
        onChange={handleChange}
        error={fieldErrors.contact_email}
        hint="Optional — use this if you wrote to an address a scan did not find."
      />

      <Textarea
        label="Notes"
        name="notes"
        value={form.notes}
        onChange={handleChange}
        error={fieldErrors.notes}
        rows={3}
      />

      <div className="flex justify-end gap-3 pt-2">
        {onCancel && (
          <Button variant="secondary" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
        )}
        <Button type="submit" isLoading={isSubmitting}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
