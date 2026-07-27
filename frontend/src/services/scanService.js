import apiClient from "./apiClient";

/**
 * Starting a scan needs its own, much longer timeout.
 *
 * With a Celery worker the request returns in milliseconds. But in eager mode
 * (`CELERY_TASK_ALWAYS_EAGER=True`, the zero-infrastructure default) the crawl
 * runs inline inside the request, so the response only arrives once the whole
 * site has been fetched. A 25-page crawl with the default one-second
 * politeness delay takes over 30 seconds, which the client's normal timeout
 * would cut short -- reporting a network failure for a scan that actually
 * succeeded.
 */
const SCAN_START_TIMEOUT_MS = 300_000;

/**
 * Starts a crawl of a company's website.
 *
 * The API answers 202 with a pending scan; progress comes from polling
 * `fetchScanStatus`. Note the deliberate lack of a trailing slash -- that is
 * the spelling the specification defines, and the route accepts both.
 */
export async function startScan(companyId) {
  const { data } = await apiClient.post(`/scan/${companyId}`, null, {
    timeout: SCAN_START_TIMEOUT_MS,
  });
  return data;
}

export async function fetchScanStatus(scanId) {
  const { data } = await apiClient.get(`/scan/status/${scanId}`);
  return data;
}

/**
 * Stops a scan that has not finished.
 *
 * A queued scan is revoked outright. One already running is stopped
 * cooperatively -- the crawler notices between pages and shuts down cleanly,
 * so the pages and contacts already found are kept rather than discarded.
 * Returns 409 if the scan has already finished.
 */
export async function cancelScan(scanId) {
  const { data } = await apiClient.post(`/scan/cancel/${scanId}`);
  return data;
}
