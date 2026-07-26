import { useState } from "react";

import { Alert } from "../ui/Alert";
import { Button } from "../ui/Button";
import { Textarea } from "../ui/Textarea";
import { getErrorMessage } from "../../utils/errors";

/** Adds a dated note to a company. */
export function NoteComposer({ onSubmit, placeholder = "Add a note..." }) {
  const [content, setContent] = useState("");
  const [error, setError] = useState(null);
  const [isSubmitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!content.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await onSubmit(content);
      setContent("");
    } catch (submitError) {
      setError(getErrorMessage(submitError));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && <Alert variant="error">{error}</Alert>}
      <Textarea
        label="New note"
        value={content}
        onChange={(event) => setContent(event.target.value)}
        placeholder={placeholder}
        rows={3}
      />
      <div className="flex justify-end">
        <Button type="submit" size="sm" isLoading={isSubmitting} disabled={!content.trim()}>
          Add note
        </Button>
      </div>
    </form>
  );
}
