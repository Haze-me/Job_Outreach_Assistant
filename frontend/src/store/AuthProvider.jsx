import { useCallback, useEffect, useMemo, useReducer } from "react";
import { useQueryClient } from "@tanstack/react-query";

import * as authService from "../services/authService";
import { setSessionExpiredHandler } from "../services/apiClient";
import {
  clearTokens,
  getRefreshToken,
  hasTokens,
  setTokens,
} from "./tokenStorage";
import { AUTH_STATUS, AuthContext } from "./authContext";

const initialState = {
  status: AUTH_STATUS.LOADING,
  user: null,
};

function authReducer(state, action) {
  switch (action.type) {
    case "authenticated":
      return { status: AUTH_STATUS.AUTHENTICATED, user: action.user };
    case "anonymous":
      return { status: AUTH_STATUS.ANONYMOUS, user: null };
    case "userUpdated":
      return { ...state, user: { ...state.user, ...action.user } };
    default:
      return state;
  }
}

/**
 * Owns the session: who is signed in, and whether we know yet.
 *
 * Session state lives here rather than in React Query because routing depends
 * on it synchronously -- a route guard cannot wait on a query. Everything
 * else the app fetches is server state and belongs in React Query.
 */
export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const queryClient = useQueryClient();

  /** Drops every cached response so the next user never sees the last one's data. */
  const resetSession = useCallback(() => {
    clearTokens();
    queryClient.clear();
    dispatch({ type: "anonymous" });
  }, [queryClient]);

  // Restore the session on first load. Having tokens is not the same as having
  // a valid session, so they are verified against the API before the app
  // treats the user as signed in.
  useEffect(() => {
    let cancelled = false;

    async function restore() {
      if (!hasTokens()) {
        dispatch({ type: "anonymous" });
        return;
      }
      try {
        const user = await authService.fetchProfile();
        if (!cancelled) dispatch({ type: "authenticated", user });
      } catch {
        // The API client already attempted a refresh. Reaching here means the
        // session is genuinely unrecoverable.
        if (!cancelled) resetSession();
      }
    }

    restore();
    return () => {
      cancelled = true;
    };
  }, [resetSession]);

  // The API client signals here when a refresh fails mid-session.
  useEffect(() => {
    setSessionExpiredHandler(() => {
      queryClient.clear();
      dispatch({ type: "anonymous" });
    });
    return () => setSessionExpiredHandler(null);
  }, [queryClient]);

  const login = useCallback(async (credentials) => {
    const { access, refresh, user } = await authService.login(credentials);
    setTokens({ access, refresh });
    dispatch({ type: "authenticated", user });
    return user;
  }, []);

  const register = useCallback(async (details) => {
    // Registration returns a token pair, so a new account is signed in without
    // a second round trip holding the plaintext password.
    const { access, refresh, user } = await authService.register(details);
    setTokens({ access, refresh });
    dispatch({ type: "authenticated", user });
    return user;
  }, []);

  const logout = useCallback(async () => {
    const refresh = getRefreshToken();
    if (refresh) {
      try {
        await authService.logout({ refresh });
      } catch {
        // Best effort: if the token is already invalid the session is over
        // regardless, and the user must not be trapped in the app.
      }
    }
    resetSession();
  }, [resetSession]);

  const applyUserUpdate = useCallback((user) => {
    dispatch({ type: "userUpdated", user });
  }, []);

  const value = useMemo(
    () => ({
      status: state.status,
      user: state.user,
      isAuthenticated: state.status === AUTH_STATUS.AUTHENTICATED,
      isLoading: state.status === AUTH_STATUS.LOADING,
      login,
      register,
      logout,
      applyUserUpdate,
    }),
    [state.status, state.user, login, register, logout, applyUserUpdate],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
