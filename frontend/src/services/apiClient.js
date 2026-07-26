/**
 * The Axios instance every service uses.
 *
 * Two interceptors do all the work:
 *
 *   Request  -- attaches the access token.
 *   Response -- on a 401, refreshes the token pair once and replays the
 *               original request.
 *
 * The refresh is single-flight: if five queries fire at the moment the access
 * token expires, all five get 401s, but only one refresh request is made and
 * the other four wait for it. Without that, five refresh calls race, four of
 * them present a token that rotation has already blacklisted, and the user is
 * signed out for no reason.
 */

import axios from "axios";

import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from "../store/tokenStorage";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

/** Endpoints that must never carry a token or trigger a refresh. */
const AUTH_ENDPOINTS = ["/auth/login/", "/auth/register/", "/auth/refresh/"];

function isAuthEndpoint(url = "") {
  return AUTH_ENDPOINTS.some((endpoint) => url.includes(endpoint));
}

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

/**
 * A bare client for the refresh call itself.
 *
 * It deliberately has no interceptors: a failing refresh must not re-enter the
 * refresh logic and loop.
 */
const refreshClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// ---------------------------------------------------------------------------
// Session-expiry notification
// ---------------------------------------------------------------------------
let onSessionExpired = null;

/**
 * Registers the callback fired when a session cannot be recovered.
 *
 * The auth store registers its `logout` here. A callback rather than a global
 * event keeps this module free of any React or router dependency.
 */
export function setSessionExpiredHandler(handler) {
  onSessionExpired = handler;
}

function endSession() {
  clearTokens();
  onSessionExpired?.();
}

// ---------------------------------------------------------------------------
// Single-flight refresh
// ---------------------------------------------------------------------------
let refreshPromise = null;

function refreshSession() {
  if (refreshPromise) return refreshPromise;

  const refresh = getRefreshToken();
  if (!refresh) return Promise.reject(new Error("No refresh token available."));

  refreshPromise = refreshClient
    .post("/auth/refresh/", { refresh })
    .then((response) => {
      // Rotation is enabled server-side: the response carries a NEW refresh
      // token, and the one just used is now blacklisted. Storing both is not
      // optional.
      const { access, refresh: rotated } = response.data;
      setTokens({ access, refresh: rotated });
      return access;
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

// ---------------------------------------------------------------------------
// Interceptors
// ---------------------------------------------------------------------------
apiClient.interceptors.request.use((config) => {
  if (!isAuthEndpoint(config.url)) {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;

    // Only a 401 is recoverable. A 403 means the token is fine but the action
    // is not allowed, and refreshing would achieve nothing.
    if (status !== 401 || !original || original._retried || isAuthEndpoint(original.url)) {
      return Promise.reject(error);
    }

    if (!getRefreshToken()) {
      endSession();
      return Promise.reject(error);
    }

    original._retried = true;

    try {
      const access = await refreshSession();
      original.headers = { ...original.headers, Authorization: `Bearer ${access}` };
      return apiClient(original);
    } catch (refreshError) {
      // The refresh token is expired, blacklisted, or rejected: this session
      // is genuinely over.
      endSession();
      return Promise.reject(refreshError);
    }
  },
);

export default apiClient;
