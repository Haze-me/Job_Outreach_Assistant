import { useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "../ui/Button";
import { ConfirmDialog } from "../ui/ConfirmDialog";
import { EmptyState } from "../ui/EmptyState";
import { Textarea } from "../ui/Textarea";
import { formatDateTime } from "../../utils/format";
import { getErrorMessage } from "../../utils/errors";

/**
 * A list of dated notes with inline editing.
 *
 * `showCompany` is on for the global Notes page and off on a company's own
 * page, where repeating the company name on every row would be noise.
 */
export function NoteList({ notes, onUpdate, onDelete, showCompany = false, emptyMessage }) {
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState("");
  const [pendingDelete, setPendingDelete] = useState(null);
  const [isSaving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  function startEditing(note) {
    setEditingId(note.id);
    setDraft(note.content);
    setError(null);
  }

  async function saveEdit(noteId) {
    setSaving(true);
    setError(null);
    try {
      await onUpdate({ id: noteId, content: draft });
      setEditingId(null);
    } catch (saveError) {
      setError(getErrorMessage(saveError));
    } finally {
      setSaving(false);
    }
  }

  async function confirmDelete() {
    setSaving(true);
    setError(null);
    try {
      await onDelete(pendingDelete.id);
      setPendingDelete(null);
    } catch (deleteError) {
      setError(getErrorMessage(deleteError));
    } finally {
      setSaving(false);
    }
  }

  if (!notes?.length) {
    return (
      <EmptyState
        title="No notes yet"
        description={emptyMessage ?? "Notes you add will appear here, newest first."}
      />
    );
  }

  return (
    <>
      <ul className="space-y-3">
        {notes.map((note) => (
          <li key={note.id} className="rounded-lg bg-slate-50 p-4 ring-1 ring-slate-200/70">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <div className="text-xs text-slate-500">
                {showCompany && note.company_name && (
                  <>
                    <Link
                      to={`/companies/${note.company}`}
                      className="font-medium text-brand-700 hover:text-brand-800"
                    >
                      {note.company_name}
                    </Link>
                    <span aria-hidden="true"> · </span>
                  </>
                )}
                <time dateTime={note.created_at}>{formatDateTime(note.created_at)}</time>
              </div>

              {editingId !== note.id && (
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => startEditing(note)}>
                    Edit
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setPendingDelete(note)}>
                    Delete
                  </Button>
                </div>
              )}
            </div>

            {editingId === note.id ? (
              <div className="space-y-3">
                {error && <p className="text-sm text-red-600">{error}</p>}
                <Textarea
                  label="Edit note"
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  rows={3}
                />
                <div className="flex justify-end gap-2">
                  <Button variant="secondary" size="sm" onClick={() => setEditingId(null)}>
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => saveEdit(note.id)}
                    isLoading={isSaving}
                    disabled={!draft.trim()}
                  >
                    Save
                  </Button>
                </div>
              </div>
            ) : (
              <p className="text-sm whitespace-pre-wrap text-slate-700">{note.content}</p>
            )}
          </li>
        ))}
      </ul>

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        onClose={() => setPendingDelete(null)}
        onConfirm={confirmDelete}
        title="Delete this note?"
        description="This cannot be undone."
        isLoading={isSaving}
        error={pendingDelete ? error : null}
      />
    </>
  );
}
