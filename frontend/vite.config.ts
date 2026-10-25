import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiProxy = {
  "/bike-rentals/api": {
    target: "http://127.0.0.1:8003",
    changeOrigin: true,
    rewrite: (path: string) => path.replace("/bike-rentals", ""),
  },
};

export default defineConfig({
  base: "/bike-rentals/",
  plugins: [react()],
  server: { proxy: apiProxy },
  preview: { proxy: apiProxy },
  build: { chunkSizeWarningLimit: 650 },
});
