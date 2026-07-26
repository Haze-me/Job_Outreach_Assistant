import { useState } from "react";

import { Alert } from "../ui/Alert";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Textarea } from "../ui/Textarea";
import { getErrorMessage, getFieldErrors } from "../../utils/errors";

const EMPTY = {
  name: "",
  website: "",
  industry: "",
  country: "",
  description: "",
  notes: "",
};

/**
 * Shared by "Add company" and the edit dialog.
 *
 * Field errors come from the API response rather than being duplicated here:
 * the server owns the rules (unique names, valid public URLs) and re-stating
 * them in the client is how the two drift apart.
 */
export function CompanyForm({ initialValues, onSubmit, submitLabel = "Save", onCancel }) {
  const [form, setForm] = useState({ ...EMPTY, ...initialValues });
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [isSubmitting, setSubmitting] = useState(false);

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

      <Input
        label="Company name"
        name="name"
        value={form.name}
        onChange={handleChange}
        error={fieldErrors.name}
        required
        autoFocus
      />

      <Input
        label="Website"
        name="website"
        value={form.website}
        onChange={handleChange}
        error={fieldErrors.website}
        placeholder="example.com"
        hint="The scheme is optional — 'example.com' becomes 'https://example.com'."
        required
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="Industry"
          name="industry"
          value={form.industry}
          onChange={handleChange}
          error={fieldErrors.industry}
        />
        <Input
          label="Country"
          name="country"
          value={form.country}
          onChange={handleChange}
          error={fieldErrors.country}
        />
      </div>

      <Textarea
        label="Description"
        name="description"
        value={form.description}
        onChange={handleChange}
        error={fieldErrors.description}
        rows={3}
      />

      <Textarea
        label="Notes"
        name="notes"
        value={form.notes}
        onChange={handleChange}
        error={fieldErrors.notes}
        rows={3}
        hint="A scratchpad on the company record. Dated notes live on the company page."
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
