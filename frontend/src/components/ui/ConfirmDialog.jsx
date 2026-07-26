import { Alert } from "./Alert";
import { Button } from "./Button";
import { Modal } from "./Modal";

/**
 * Confirmation before a destructive action.
 *
 * Deletes cascade on the server (removing a company also removes its notes,
 * contacts, scans and applications), so `description` should say what else
 * goes with it rather than just asking "are you sure?".
 */
export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = "Are you sure?",
  description,
  confirmLabel = "Delete",
  isLoading = false,
  error,
}) {
  return (
    <Modal open={open} onClose={onClose} title={title} size="sm">
      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}

      {description && <p className="text-sm text-slate-600">{description}</p>}

      <div className="mt-6 flex justify-end gap-3">
        <Button variant="secondary" onClick={onClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button variant="danger" onClick={onConfirm} isLoading={isLoading}>
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}
