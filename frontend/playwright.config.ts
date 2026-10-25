import { defineConfig, devices } from "@playwright/test";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const python =
  process.env.PYTHON ??
  (process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python");

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  use: { baseURL: "http://127.0.0.1:4173", trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `${python} -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8003`,
      cwd: root,
      url: "http://127.0.0.1:8003/api/health",
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run preview -- --port 4173",
      url: "http://127.0.0.1:4173/bike-rentals/",
      reuseExistingServer: !process.env.CI,
    },
  ],
});
