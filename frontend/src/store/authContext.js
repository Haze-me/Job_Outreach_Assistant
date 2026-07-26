import { createContext } from "react";

/**
 * Authentication state.
 *
 * `status` is a three-state machine rather than a boolean. "loading" is a real
 * state, not an absence of one: on a page reload the app has tokens but does
 * not yet know whether they are still valid, and treating that moment as
 * "signed out" would bounce the user to the login screen on every refresh.
 */
export const AUTH_STATUS = {
  LOADING: "loading",
  AUTHENTICATED: "authenticated",
  ANONYMOUS: "anonymous",
};

export const AuthContext = createContext(null);
