import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined;
          }
          if (id.includes("firebase")) {
            return "firebase";
          }
          if (id.includes("recharts")) {
            return "charts";
          }
          if (
            id.includes("react") ||
            id.includes("scheduler") ||
            id.includes("react-router-dom")
          ) {
            return "react";
          }
          return undefined;
        },
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
  },
});
