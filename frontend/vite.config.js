import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/health": "http://127.0.0.1:8000",
      "/showcase/bootstrap": "http://127.0.0.1:8000",
      "/rag/query": "http://127.0.0.1:8000",
      "/agent/run": "http://127.0.0.1:8000",
      "/agent/team/run": "http://127.0.0.1:8000"
    }
  }
});
