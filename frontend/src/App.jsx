import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";

import { router } from "./router";
import { queryClient } from "./services/queryClient";
import { AuthProvider } from "./store/AuthProvider";

/**
 * Provider order matters:
 *
 *   QueryClientProvider -> AuthProvider -> RouterProvider
 *
 * AuthProvider clears the query cache on sign-out, so it must sit inside the
 * query provider. The router sits innermost so every route can read the
 * session, and route guards can redirect on it.
 */
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  );
}
