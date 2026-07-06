# Healthcare Imaging Equipment Utilization & Downtime Analysis

A data analysis project examining equipment downtime, utilization, and maintenance
patterns across a simulated hospital network's medical imaging fleet (MRI, CT, and
X-ray machines across three sites), with a preventive maintenance recommendation
based on the findings.

**Project timeline:** January 2023 – March 2023

## Objective

Hospitals lose imaging capacity every time an MRI, CT, or X-ray machine goes down for
repair. This project analyzes twelve months of equipment usage logs and maintenance
tickets to answer:

1. Which machines and sites carry the most downtime?
2. How does utilization compare across machines and sites?
3. What are the leading causes of failure?
4. Does machine age predict downtime, and can that relationship inform a preventive
   maintenance schedule?

## Data sources

Real hospital equipment telemetry is not publicly available, so this project
simulates three realistic datasets for a 9-machine fleet (3 MRI, 3 CT, 3 X-ray) across
three hospital sites, covering April 2022 – March 2023 (`data/generate_data.py`,
seeded for reproducibility):

| File | Rows | Description |
|---|---|---|
| `data/equipment_logs.csv` | 3,316 | Daily usage hours per machine |
| `data/maintenance_tickets.csv` | 61 | Repair tickets: issue type, reported/resolved dates, downtime hours, technician |
| `data/machine_metadata.csv` | 9 | Machine age, manufacturer, last service date |

Older machines were generated with a higher failure rate and longer repair times, to
reflect a realistic wear pattern.

## Project structure

```
data/         raw + generated CSVs, and the data generation script
sql/          SQLite schema, DB build script, and analysis queries
notebooks/    Python (pandas) cleaning/analysis notebooks, R regression script,
              visualization notebook, Excel export script
outputs/      generated figures, regression results, and exported CSVs/Excel
docs/         methodology notes and the final report
```

## Cleaning steps

Applied in `notebooks/01_data_cleaning_and_merging.ipynb` (via `notebooks/data_utils.py`):

- Removed 33 exact duplicate rows from `equipment_logs.csv`
- Parsed all date columns to proper datetime types
- Imputed 17 missing `daily_usage_hours` values using each machine's own median usage
  (more representative than a fleet-wide average, since usage varies a lot by modality)
- Flagged 2 maintenance tickets that were still open (no `resolved_date`) and capped
  their downtime at the observation window end rather than dropping them
- Merged usage logs with machine metadata for the age/downtime analysis

## Methodology

1. **SQL layer** (`sql/`) — loaded the three CSVs into a SQLite database
   (`data/healthcare.db`) and wrote queries for total downtime per machine, average
   downtime per hospital site, MTBF, and MTTR (`sql/queries.sql`).
2. **Python analysis** (`notebooks/01_...` and `02_...`) — cleaned and merged the
   datasets with pandas, computed `utilization_rate = actual usage hours / available
   hours` per machine, and ranked downtime causes.
3. **R statistical analysis** (`notebooks/age_downtime_regression.R`) — ran a Pearson
   correlation and simple linear regression testing whether machine age predicts total
   downtime hours.
4. **Visualization** (`notebooks/03_visualizations.ipynb`) — downtime trend by machine
   type, a utilization heatmap by site, and a top-failure-causes chart, plus an
   interactive Plotly scatter of age vs. downtime. Chart-ready aggregates are also
   exported as clean CSVs in `outputs/exports/` so the same charts can be rebuilt in
   Tableau.
5. **Excel summary** (`notebooks/export_excel.py`) — a workbook with Raw Data, Downtime
   Summary, Utilization Summary, and Top Downtime Causes sheets.

## Key findings

- **CT-202** (Lakeview Medical Center) had the highest total downtime at 108.4 hours
  across 14 tickets; **MRI-103** and **MRI-102** had the least, at roughly 9–12 hours
  each.
- Utilization ranged from **31%** (MRI machines) to **49%** (X-ray machines) of
  available hours — X-ray units are used far more intensively than MRI/CT, which also
  run longer individual scans.
- The top three causes of downtime fleet-wide were **calibration drift** (15 tickets,
  137.5 hours), **generator faults** (6 tickets, 86.0 hours), and **detector faults**
  (9 tickets, 73.4 hours).
- **Machine age significantly predicts total downtime** (Pearson r = 0.77, p = 0.015).
  A simple linear regression shows each additional year of age is associated with
  roughly **10.7 additional downtime hours** per year, and age alone explains about
  **59.5%** of the variance in downtime across the fleet (R² = 0.595). Full regression
  output: `outputs/regression_results.txt`.

## Recommendation

Because age is a strong, statistically significant predictor of downtime, maintenance
should shift from a uniform schedule to an **age-tiered preventive maintenance
program**:

- **0–3 years:** standard annual preventive maintenance visit.
- **3–6 years:** move to semi-annual preventive maintenance, with priority given to
  calibration checks (the single largest downtime driver).
- **6+ years:** quarterly preventive maintenance, plus a dedicated generator/detector
  inspection given their outsized share of total downtime hours.

Given CT-202's ticket volume and Riverside General's concentration of high-downtime
machines (CT-201, MRI-101, XR-301), these two should be the first candidates for the
tightened schedule. See `docs/final_report.md` for the full write-up.

## Reproducing this analysis

```bash
# 1. Generate the simulated raw data
python data/generate_data.py

# 2. Build the SQLite database and run the SQL layer
python sql/build_db.py
# sql/queries.sql contains the downtime/MTBF/MTTR queries to run against data/healthcare.db

# 3. Run the Python cleaning + analysis notebooks (in order)
jupyter nbconvert --to notebook --execute --inplace notebooks/01_data_cleaning_and_merging.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/02_utilization_and_downtime_analysis.ipynb

# 4. Run the R statistical test
Rscript notebooks/age_downtime_regression.R

# 5. Generate visualizations
jupyter nbconvert --to notebook --execute --inplace notebooks/03_visualizations.ipynb

# 6. Export the Excel summary workbook
python notebooks/export_excel.py
```

Requires Python 3.12 (pandas, numpy, matplotlib, seaborn, plotly, openpyxl, scipy,
statsmodels, jupyter) and R 4.5.
