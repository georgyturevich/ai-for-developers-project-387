import { defineConfig } from "@playwright/test";

// Drives the fully assembled system: real Chromium against the real Vite dev
// server and the real FastAPI backend (see docs/adr/0005-e2e-real-backend.md).
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "uv run uvicorn cal_bookings.app:create_app --factory --port 8000",
      cwd: "backend",
      url: "http://localhost:8000/event-types",
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run dev",
      cwd: "frontend",
      url: "http://localhost:5173",
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
      env: { VITE_API_URL: "http://localhost:8000" },
    },
  ],
});
