# Calendar Bookings — фронтенд

UI приложения записи на приём (React + TypeScript + Vite, shadcn/ui + Tailwind). Все данные и действия — только через API по контракту (`../main.tsp` компилируется в OpenAPI).

## Первый запуск

1. В корне репозитория: `npm install`, затем `npm run mock` — поднимет Prism-мок API на `http://localhost:4010`.
2. Здесь: `npm install`, затем `npm run dev` — dev-сервер Vite.

## Команды

- `npm run api:types` — скомпилировать контракт и сгенерировать типы `src/api/schema.d.ts` (файл в gitignore; нужен для typecheck/build, вызывается ими автоматически).
- `npm run dev` — dev-сервер.
- `npm test` — тесты (Vitest) на утилитах дат/слотов и zod-схемах.
- `npm run typecheck`, `npm run lint`, `npm run build`.

## Подключение к настоящему бэкенду

Базовый URL задаётся переменной окружения `VITE_API_URL` (по умолчанию — Prism-мок `http://localhost:4010`).
