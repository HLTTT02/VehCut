import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Keeps `npm run dev` usable alongside the Docker API. Production Docker
// traffic is proxied by nginx instead (see frontend/nginx.conf).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8001",
      "/health": "http://localhost:8001",
      "/storage": "http://localhost:8001",
    },
  },
});
