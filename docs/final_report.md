# Final Report — Healthcare Imaging Equipment Utilization & Downtime Analysis

**Timeline:** January 2023 – March 2023

## Month 1 (January 2023) — Data collection & cleaning

- Defined the scope: a 9-machine imaging fleet (3 MRI, 3 CT, 3 X-ray) across three
  hospital sites (Riverside General, Lakeview Medical Center, St. Anne's Hospital).
- Generated 12 months of simulated equipment usage logs, maintenance tickets, and
  machine metadata (`data/`), since real hospital telemetry isn't publicly available.
- Cleaned the raw data: removed 33 duplicate log rows, imputed 17 missing usage-hour
  values per-machine, parsed all dates, and flagged still-open maintenance tickets
  instead of dropping them.

## Month 2 (February 2023) — SQL / Python analysis

- Loaded the cleaned CSVs into a SQLite database (`data/healthcare.db`) and wrote SQL
  queries for total downtime per machine, average downtime per site, MTBF, and MTTR
  (`sql/queries.sql`).
- Merged the three datasets in pandas and computed utilization rate per machine
  (`notebooks/02_utilization_and_downtime_analysis.ipynb`).
- Identified the top three downtime causes fleet-wide.

## Month 3 (March 2023) — Visualization, stats, and final report

- Ran a correlation and linear regression in R to test whether machine age predicts
  downtime (`notebooks/age_downtime_regression.R`).
- Built the downtime trend, utilization heatmap, and top-causes charts
  (`notebooks/03_visualizations.ipynb`), plus an interactive Plotly view.
- Exported the Excel summary workbook and wrote up findings and a preventive
  maintenance recommendation.

## Key findings

| Machine | Site | Total downtime (hrs) | Tickets | MTTR (hrs) | Age (yrs) |
|---|---|---|---|---|---|
| CT-202 | Lakeview Medical Center | 108.4 | 14 | 7.74 | 5.12 |
| MRI-101 | Riverside General | 96.0 | 9 | 10.66 | 7.05 |
| XR-301 | Riverside General | 86.4 | 10 | 8.64 | 8.78 |
| XR-302 | Lakeview Medical Center | 81.8 | 6 | 13.64 | 5.47 |
| CT-201 | Riverside General | 73.8 | 8 | 9.22 | 7.57 |
| XR-303 | St. Anne's Hospital | 38.0 | 4 | 9.50 | 3.17 |
| CT-203 | St. Anne's Hospital | 29.6 | 6 | 4.92 | 0.99 |
| MRI-102 | Lakeview Medical Center | 11.9 | 2 | 5.94 | 3.75 |
| MRI-103 | St. Anne's Hospital | 9.2 | 2 | 4.61 | 1.36 |

**Utilization** ranged from 31.2% (MRI-102) to 49.5% (XR-303) of available hours.
X-ray machines run at the highest utilization (~48–49%), CT machines in the middle
(~38–39%), and MRI machines lowest (~31–32%) — consistent with X-ray's higher patient
throughput per hour versus longer MRI/CT scan times.

**Top downtime causes fleet-wide:**

| Issue type | Occurrences | Total downtime (hrs) |
|---|---|---|
| Calibration drift | 15 | 137.5 |
| Generator fault | 6 | 86.0 |
| Detector fault | 9 | 73.4 |

**Age vs. downtime:** Pearson correlation r = 0.77 (p = 0.015, 95% CI [0.22, 0.95]).
Linear regression: `total_downtime_hours ≈ 8.22 + 10.66 × age_years`, R² = 0.595
(p = 0.015 for the age coefficient). Age alone explains roughly 60% of the
machine-to-machine variance in total downtime hours — a statistically significant and
practically meaningful relationship at this fleet size. Full output:
`outputs/regression_results.txt`.

## Recommendation: age-tiered preventive maintenance schedule

Because age is a significant predictor of downtime, and calibration drift is the
single largest downtime driver, an age-tiered schedule is recommended over a uniform
one:

| Age tier | PM frequency | Focus areas |
|---|---|---|
| 0–3 years | Annual | Standard PM checklist |
| 3–6 years | Semi-annual | Add calibration verification each visit |
| 6+ years | Quarterly | Calibration + dedicated generator/detector inspection |

**Immediate priorities:** CT-202 (highest ticket volume, 14 tickets) and Riverside
General's cluster of aging, high-downtime machines (CT-201, MRI-101, XR-301) should be
the first sites scheduled under the tightened cadence. Given the correlation strength
observed here, extending the fleet age dataset in future work (more machines, longer
history) would help validate whether the ~10.7 hour/year downtime slope holds at
scale.
