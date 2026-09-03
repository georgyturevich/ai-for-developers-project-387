# perf: LCP degraded 14% and TBT degraded 127% vs baseline

## Performance regression detected (Lighthouse 2026-09-03 vs baseline 2026-08-30)

| Metric | Baseline | Current | Change | Threshold |
|--------|----------|---------|--------|-----------|
| **LCP** | 1879 ms | 2139 ms | **+13.8%** | < 10% |
| CLS | 0 | 0 | 0% | < 10% |
| **TBT (INP proxy)** | 726 ms | 1650 ms | **+127.3%** | < 10% |

CLS is unchanged and within target. LCP and TBT both regressed beyond the 10% noise threshold.

## Root-cause analysis

All changes since the baseline live in commit `75dff33` ("Add total bookings badge to header (#18)"). The Lighthouse report reveals the following bottlenecks:

### 1. Oversized single JS bundle — `index-CM9wqXT2.js`

- **Transfer size:** 146 KB (gzipped) / 471 KB (uncompressed)
- **Script evaluation time:** 1414 ms (the single largest CPU consumer)
- **Total CPU time:** 1912 ms

The app ships **all 7 page components in one chunk** (`frontend/src/App.tsx:18-27` eagerly imports every route component). There is no route-level code splitting — every visitor downloads and executes the full booking-form, confirmation, owner-bookings, slots, and event-type-new pages even if they only land on the catalog.

### 2. Heavy dependency stack on the main thread

| Dependency | Impact |
|-----------|--------|
| `@tanstack/react-query` | Hydrates query cache on mount; adds ~40 KB |
| `react-hook-form` + `@hookform/resolvers` + `zod` | Form validation schemas compiled eagerly for all routes |
| `lucide-react` | Barrel-imported icons; tree-shaking depends on bundler config |
| `sonner` (Toaster) | Mounted globally in `Layout` (`frontend/src/components/layout.tsx:41`); adds rendering cost on every page load |

### 3. No lazy loading of route components

`frontend/src/App.tsx` uses static imports for every page:

```tsx
import { BookingFormPage } from "@/pages/booking-form-page";
import { CatalogPage } from "@/pages/catalog-page";
// ... 5 more
```

`react-router` v8 supports `lazy` routes via `createBrowserRouter` + `React.lazy`, but the current setup uses `BrowserRouter` with eagerly-rendered `<Routes>`.

### 4. Main-thread work breakdown

| Category | Time |
|----------|------|
| Script Evaluation | 1503 ms |
| Other | 1336 ms |
| Style & Layout | 673 ms |
| Tasks > 50 ms | 5 |
| Tasks > 100 ms | 3 |

The 1650 ms TBT (baseline 726 ms) means the page blocks interactivity for over 1.5 seconds on load.

## Recommendations

### High impact (target TBT < 800 ms)

1. **Add route-level code splitting** — Replace static imports in `App.tsx` with `React.lazy()` + `<Suspense>`. The catalog page is the primary landing; slots/booking-form/confirmation/owner pages should only load when navigated to.

2. **Evaluate heavy dependencies** — Audit whether `react-hook-form` + `@hookform/resolvers` + `zod` are needed for the catalog page (they are not — they are only used on form routes). Lazy-load these per-route.

3. **Defer `sonner` (Toaster) mounting** — Move `<Toaster>` inside the route that actually shows toasts, or lazy-mount it, to avoid rendering cost on initial page load.

### Medium impact (target LCP < 1800 ms)

4. **Review lucide-react usage** — Switch to named imports (`import { Icon } from "lucide-react/dist/esm/icons/icon"`) instead of barrel imports to ensure tree-shaking eliminates unused icons.

5. **Add `font-display: swap`** for Geist web fonts — The two woff2 files (latin + cyrillic, 44 KB total) block rendering until loaded.

6. **Preload the main JS chunk** — Add `<link rel="modulepreload" href="...">` in `index.html` for the entry script.

### Low impact / follow-up

7. **Run `source-map-explorer` or `rollup-plugin-visualizer`** on the build output to identify the top-10 largest modules and check for unexpected transitive dependencies.

8. **Consider Tailwind v4 CSS purging** — The CSS bundle is 39 KB (uncompressed 7.7 KB transferred); audit whether unused utility classes are being purged.

## Steps to verify

After applying fixes:
1. `cd frontend && npm run build && npm run preview` — check bundle sizes
2. Run Lighthouse on `localhost:4173` (preview) for stable comparison
3. Update `docs/performance-baseline.md` with new values once metrics stabilize
