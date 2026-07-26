import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: 5173,
      // Proxying /api to Django in development means the browser only ever
      // talks to one origin: no CORS preflights, and no absolute API URL baked
      // into the bundle. Deployments that serve the frontend from a different
      // origin set VITE_API_BASE_URL instead.
      proxy: {
        "/api": {
          target: env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000",
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: "dist",
      sourcemap: mode !== "production",
    },
  };
});
