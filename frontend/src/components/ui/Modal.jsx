import { useEffect, useRef } from "react";

import { cn } from "../../utils/cn";

/**
 * A dialog built on the native `<dialog>` element.
 *
 * Using the platform element rather than a div means focus trapping, the
 * inert background, Escape-to-close, and the top-layer stacking all come from
 * the browser -- all of which are easy to get subtly wrong by hand, and all of
 * which matter for keyboard and screen-reader users.
 */
export function Modal({ open, onClose, title, description, children, size = "md" }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  // Escape closes the dialog natively, which would leave React's `open` state
  // out of sync; this pushes that back up.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    function handleClose() {
      onClose?.();
    }
    dialog.addEventListener("close", handleClose);
    return () => dialog.removeEventListener("close", handleClose);
  }, [onClose]);

  function handleBackdropClick(event) {
    // A click lands on the <dialog> itself only when it hit the backdrop:
    // clicks inside the content are caught by the inner wrapper.
    if (event.target === dialogRef.current) {
      onClose?.();
    }
  }

  return (
    <dialog
      ref={dialogRef}
      onClick={handleBackdropClick}
      aria-labelledby={title ? "modal-title" : undefined}
      className={cn(
        "w-[calc(100%-2rem)] rounded-xl bg-white p-0 shadow-xl backdrop:bg-slate-900/50",
        size === "sm" ? "max-w-md" : size === "lg" ? "max-w-3xl" : "max-w-xl",
      )}
    >
      <div className="p-6">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            {title && (
              <h2 id="modal-title" className="text-base font-semibold text-slate-900">
                {title}
              </h2>
            )}
            {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="-mt-1 -mr-1 rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <svg className="size-5" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {children}
      </div>
    </dialog>
  );
}
