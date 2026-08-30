# Performance baseline

Initial performance baseline for the deployed app at
<https://cal-bookings-production.up.railway.app>. Captured from the Lighthouse
report produced by the `opencode-cron-code-lighthouse` workflow (see
`.github/workflows/opencode-cron-code-lighthouse.yml`).

The workflow compares the metrics below against this file on every audit run.
A metric that **degrades by more than 10%** from its baseline value is treated
as a regression and should trigger an issue with recommendations.

## Baseline (2026-08-30)

| Metric | Baseline value | Target | Status |
| --- | --- | --- | --- |
| LCP (Largest Contentful Paint) | 1879 ms | < 2500 ms (Web Vitals "good") | OK |
| CLS (Cumulative Layout Shift) | 0 | < 0.1 (Web Vitals "good") | OK |
| TBT (Total Blocking Time) | 726 ms | < 200 ms (Web Vitals proxy for interaction) | Needs improvement |
| Max Potential FID | 796 ms | < 300 ms | Needs improvement |
| Speed Index | 4010 ms | < 4300 ms (Lighthouse "good") | OK |
| FCP (First Contentful Paint) | 1879 ms | < 1800 ms (Lighthouse "good") | Borderline |
| TTI (Time to Interactive) | 2755 ms | < 3800 ms (Lighthouse "good") | OK |
| Performance score | 0.79 | >= 0.9 | Needs improvement |

## How regressions are detected

- Compare the latest **LCP**, **CLS**, and **INP**/**TBT** values from the
  current `lighthouse-report.json` with the baseline values above.
- Flag any metric whose value exceeds its baseline by more than 10% (accounting
  for noise; treat a one-off spike below the target as informational).
- **INP** is not directly reported by this Lighthouse version; use **TBT** as
  the interaction-responsiveness proxy. A `Max Potential FID` is reported too.

## Current known issues

- **TBT** and **Max Potential FID** are far above Web Vitals thresholds. This
  points to main-thread work on load (e.g. heavy JS bundle, unoptimized
  dependencies, or rendering churn). Re-check after frontend bundle changes.

## Recording new baselines

When a regression is fixed or the report intentionally changes (e.g. a new
frontend release), update this table with the new values and the new date.
Keep the Target column as the Web Vitals / Lighthouse thresholds so targets do
not drift with regressions.