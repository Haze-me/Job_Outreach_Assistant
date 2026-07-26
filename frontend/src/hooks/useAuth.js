import { useContext } from "react";

import { AuthContext } from "../store/authContext";

/** Reads the session. Throws if used outside the provider, which is a bug. */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used inside an <AuthProvider>.");
  }
  return context;
}
