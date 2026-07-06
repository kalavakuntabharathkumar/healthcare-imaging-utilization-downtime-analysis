# Methodology

## Data generation

Real hospital imaging telemetry is not publicly available, so `data/generate_data.py`
simulates a 9-machine fleet (3 MRI, 3 CT, 3 X-ray) spread across three hospital sites,
covering April 2022 – March 2023. The generator is seeded (`numpy.random.default_rng(42)`)
for reproducibility and deliberately injects realistic imperfections so the cleaning
step has real work to do:

- Machine-type-specific daily usage baselines (X-ray highest throughput, MRI lowest),
  with weekday/weekend effects and machine-specific age penalties.
- Maintenance ticket frequency and repair duration scaled to machine age — older
  machines fail more often (Poisson-distributed ticket counts) and take longer to
  repair (Gamma-distributed downtime hours).
- ~1% duplicate rows and ~0.5% missing `daily_usage_hours` values in the equipment
  logs, and a handful of maintenance tickets left "open" (no `resolved_date`) to
  simulate an in-progress data pull.

## Cleaning

Implemented once in `notebooks/data_utils.py` and applied from
`notebooks/01_data_cleaning_and_merging.ipynb`:

- **Duplicates:** dropped via `drop_duplicates()` on each raw table.
- **Missing usage hours:** imputed per-machine using that machine's own median usage,
  since usage baselines differ substantially by modality and site — a fleet-wide mean
  would bias low-usage MRI machines upward and high-usage X-ray machines downward.
- **Open tickets:** flagged with an `is_open` column rather than dropped, and their
  downtime is capped at the observation window end date so they still contribute to
  MTTR/downtime totals without introducing an unbounded duration.
- **Date parsing:** all date-like columns are coerced to `datetime64` with
  `pd.to_datetime(..., errors="coerce")`.

## Metrics

- **Utilization rate** = total usage hours / available hours, where available hours
  assumes a 24-hour operating window per machine over the days it was observed in
  service (`notebooks/data_utils.py::compute_utilization`).
- **MTBF (Mean Time Between Failures)** — approximated in SQL (`sql/queries.sql`) as
  the observed service window in days divided by the ticket count for that machine.
- **MTTR (Mean Time To Repair)** — mean `downtime_hours` across resolved tickets for a
  machine, computed both in SQL and in `notebooks/data_utils.py::downtime_per_machine`.
- **Top downtime causes** — tickets grouped by `issue_type`, ranked by total downtime
  hours contributed.

## Statistical test

`notebooks/age_downtime_regression.R` runs a Pearson correlation and a simple linear
regression of `total_downtime_hours ~ age_years` at the machine level (n = 9), against
the per-machine table produced by the Python notebooks
(`outputs/exports/utilization_downtime_by_machine.csv`). Full numeric output, including
the regression coefficient table and a written interpretation, is saved to
`outputs/regression_results.txt`.

## Visualization

`notebooks/03_visualizations.ipynb` builds three static charts (matplotlib/seaborn,
saved to `outputs/figures/*.png` at 150 DPI) plus one interactive Plotly scatter
(`outputs/figures/age_vs_downtime_interactive.html`). The same chart-ready aggregates
are exported as clean CSVs to `outputs/exports/` so they can be recreated in Tableau
without re-running the notebooks.
