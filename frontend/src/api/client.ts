import createClient from "openapi-fetch";
import type { paths } from "./schema";

// По умолчанию — Prism-мок контракта (npm run mock в корне репозитория).
// Против настоящего бэкенда задаётся через VITE_API_URL.
export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_URL ?? "http://localhost:4010",
});
