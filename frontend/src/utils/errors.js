/**
 * Reading the API's error envelope.
 *
 * Every failure from the backend has the same shape, which is why the frontend
 * needs exactly one place that understands it:
 *
 *   { "error": { "code": "validation_error",
 *                "message": "Invalid input.",
 *                "details": { "website": ["Enter a valid URL."] } } }
 */

const FALLBACK_MESSAGE = "Something went wrong. Please try again.";

/** Pulls the `error` object out of an Axios error, if there is one. */
function getEnvelope(error) {
  const payload = error?.response?.data;
  return payload && typeof payload === "object" ? payload.error : undefined;
}

export function getErrorCode(error) {
  return getEnvelope(error)?.code ?? null;
}

/**
 * A single human-readable sentence suitable for an alert banner.
 *
 * Field-level validation errors are handled separately by `getFieldErrors`, so
 * this deliberately returns the summary rather than concatenating every field.
 */
export function getErrorMessage(error) {
  if (!error) return FALLBACK_MESSAGE;

  // No response at all: the request never reached the server.
  if (error.request && !error.response) {
    return "Could not reach the server. Check that the API is running.";
  }

  const status = error.response?.status;
  if (status === 429) {
    return "Too many attempts. Please wait a moment and try again.";
  }
  if (status === 500) {
    return "The server ran into a problem. Please try again shortly.";
  }

  const envelope = getEnvelope(error);
  if (envelope?.message) {
    // For a validation failure the summary is generic; the first field error
    // is far more useful in a banner.
    if (envelope.code === "validation_error") {
      const first = firstFieldMessage(envelope.details);
      if (first) return first;
    }
    return envelope.message;
  }

  return error.message || FALLBACK_MESSAGE;
}

function firstFieldMessage(details) {
  if (!details || typeof details !== "object") return null;
  for (const value of Object.values(details)) {
    if (Array.isArray(value) && value.length > 0) return String(value[0]);
    if (typeof value === "string") return value;
  }
  return null;
}

/**
 * Field-level errors keyed by field name, flattened to one string per field.
 *
 * Returns an empty object for non-validation failures, so a form can always
 * spread the result without checking first.
 */
export function getFieldErrors(error) {
  const details = getEnvelope(error)?.details;
  if (!details || typeof details !== "object" || Array.isArray(details)) return {};

  return Object.fromEntries(
    Object.entries(details).map(([field, messages]) => [
      field,
      Array.isArray(messages) ? messages.join(" ") : String(messages),
    ]),
  );
}

/** True when the failure is the user's credentials rather than their input. */
export function isAuthError(error) {
  return error?.response?.status === 401;
}
