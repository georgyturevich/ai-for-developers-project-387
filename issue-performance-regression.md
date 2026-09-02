# perf: TBT regressed 92% (726ms → 1392ms) — bundle optimization needed

## Performance regression detected

Lighthouse audit (2026-09-02) shows **TBT (Total Blocking Time)** degraded **91.7%** from baseline:

| Metric | Baseline (2026-08-30) | Current | Change | Threshold |
|--------|----------------------|---------|--------|-----------|
| **TBT (INP proxy)** | 726 ms | 1392 ms | **+91.7%** | >10% regressed |
| **Max Potential FID** | 796 ms | 1150 ms | **+44.5%** | >10% regressed |
| LCP | 1879 ms | 1999 ms | +6.4% | OK |
| CLS | 0 | 0.003 | N/A | OK (abs value negligible) |

## Root cause analysis

The Lighthouse report pinpoints the main JS bundle (`index-CM9wqXT2.js`) as the sole blocking resource:

1. **Bundle size**: 469 KB uncompressed / 145 KB gzipped — **249 KB (53%) is unused code** per Lighthouse treemap data.
2. **Script evaluation**: 1449 ms of the 2262 ms total main-thread work is JS execution. The bundle alone takes 1637 ms CPU time (1417 ms scripting).
3. **Long tasks**: 5 long tasks all from the same bundle, the worst being a **single 1150 ms task** starting at ~1.9 s.
4. **No code splitting**: The entire SPA is in a single JS file — all routes, all dependencies, loaded eagerly.
5. **Heavy dependency tree**: `@tanstack/react-query`, `react-hook-form`, `zod`, `lucide-react`, `sonner`, `@base-ui/react`, `class-variance-authority` — many may not tree-shake fully.

## Recommendations

### Quick wins (do first)
- **Enable route-based code splitting** via `React.lazy()` + dynamic `import()` for each page in the router. This alone could cut initial JS by 40-60%.
- **Audit `lucide-react`**: import only icons actually used (`import { X } from "lucide-react"`) rather than the full library. Check if the barrel import is pulling the entire icon set.

### Medium effort
- **Lazy-load `sonner`** (toast notifications) — it's not needed on initial paint.
- **Check `@tanstack/react-query` devtools**: ensure they're tree-shaken out of production builds.
- **Evaluate `zod` usage**: if schemas are only used for form validation, consider deferring or code-splitting them.
- **Add `vite-plugin-compression`** or configure Brotli pre-compression for the static build to reduce transfer size.

### Longer term
- **Lighthouse "unused JS" audit** flagged 249 KB — run `rollup-plugin-visualizer` to identify the largest modules and whether they can be replaced with lighter alternatives.
- **Consider `react-router` lazy routes** (`createBrowserRouter` with `lazy` property) for declarative code splitting.
- **Add a performance budget** to CI (e.g., via `bundlesize` or Lighthouse CI) to prevent future regressions.

## Environment

- Lighthouse 13.4.1, HeadlessChrome/151 on simulated Moto G Power (2022)
- Deployed at `https://cal-bookings-production.up.railway.app/`
- Bundle hash: `index-CM9wqXT2.js`
