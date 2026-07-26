/**
 * The single place JWTs live.
 *
 * Tokens are kept in localStorage so a page reload does not sign the user out.
 * The trade-off is explicit: localStorage is readable by any JavaScript running
 * on the page, so a cross-site-scripting bug would expose the tokens. The
 * safer alternative -- httpOnly cookies -- would require the backend to switch
 * from `Authorization: Bearer` to cookie authentication with CSRF protection,
 * which is a backend change, not a frontend one.
 *
 * Two things limit the blast radius as built: access tokens expire in 15
 * minutes, and refresh tokens rotate on every use, so a captured refresh token
 * is usable at most once.
 *
 * Every read and write goes through this module, so changing that storage
 * strategy later means editing one file.
 */

const ACCESS_TOKEN_KEY = "joa.accessToken";
const REFRESH_TOKEN_KEY = "joa.refreshToken";

/** Storage can throw in private-browsing modes; never let that crash the app. */
function safeGet(key) {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSet(key, value) {
  try {
    if (value === null || value === undefined) {
      window.localStorage.removeItem(key);
    } else {
      window.localStorage.setItem(key, value);
    }
  } catch {
    // Ignore: the session simply will not survive a reload.
  }
}

export function getAccessToken() {
  return safeGet(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return safeGet(REFRESH_TOKEN_KEY);
}

export function hasTokens() {
  return Boolean(getAccessToken() && getRefreshToken());
}

/**
 * Stores a token pair.
 *
 * The backend rotates refresh tokens, so the `refresh` value returned by a
 * refresh call must replace the old one -- reusing the previous token would
 * fail, because it is blacklisted the moment it is exchanged.
 */
export function setTokens({ access, refresh }) {
  if (access !== undefined) safeSet(ACCESS_TOKEN_KEY, access);
  if (refresh !== undefined) safeSet(REFRESH_TOKEN_KEY, refresh);
}

export function clearTokens() {
  safeSet(ACCESS_TOKEN_KEY, null);
  safeSet(REFRESH_TOKEN_KEY, null);
}
