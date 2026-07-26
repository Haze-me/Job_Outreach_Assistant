/** Display formatting helpers. */

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
});

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : dateFormatter.format(date);
}

export function formatDateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : dateTimeFormatter.format(date);
}

/** Today's date as `YYYY-MM-DD`, which is what `<input type="date">` expects. */
export function todayIso() {
  const now = new Date();
  const offsetMinutes = now.getTimezoneOffset();
  // Shift by the timezone offset before slicing, or a user east of UTC gets
  // yesterday's date after midnight local time.
  return new Date(now.getTime() - offsetMinutes * 60_000).toISOString().slice(0, 10);
}

/** Strips the scheme so a website reads as a domain in a table cell. */
export function displayUrl(url) {
  if (!url) return "";
  return url.replace(/^https?:\/\//, "").replace(/\/$/, "");
}

export function pluralize(count, singular, plural = `${singular}s`) {
  return count === 1 ? singular : plural;
}
