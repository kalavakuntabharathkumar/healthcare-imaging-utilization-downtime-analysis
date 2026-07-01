"""
Data generation script for the Healthcare Imaging Equipment Utilization &
Downtime Analysis project.

Real hospital equipment logs are not publicly available, so this script
simulates three realistic datasets for a hospital network operating MRI, CT,
and X-ray machines across multiple sites over a 12-month period (2022-04-01
through 2023-03-31), with the actual analysis work carried out between
January and March 2023.

Run with:
    python data/generate_data.py
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta

RNG_SEED = 42
rng = np.random.default_rng(RNG_SEED)

OUTPUT_DIR = "data"

# ---------------------------------------------------------------------------
# Machine fleet definition
# ---------------------------------------------------------------------------

HOSPITAL_SITES = ["Riverside General", "Lakeview Medical Center", "St. Anne's Hospital"]

MACHINE_TYPES = {
    "MRI": {"base_daily_hours": 9.0, "std_daily_hours": 1.6},
    "CT": {"base_daily_hours": 11.0, "std_daily_hours": 1.8},
    "X-ray": {"base_daily_hours": 14.0, "std_daily_hours": 2.2},
}

MANUFACTURERS = {
    "MRI": ["Siemens Healthineers", "GE HealthCare"],
    "CT": ["GE HealthCare", "Philips"],
    "X-ray": ["Philips", "Canon Medical"],
}

ISSUE_TYPES_BY_MACHINE = {
    "MRI": ["Coil failure", "Helium/cooling issue", "Software fault", "Calibration drift", "Table motor fault"],
    "CT": ["Tube failure", "Detector fault", "Software fault", "Calibration drift", "Cooling system issue"],
    "X-ray": ["Detector fault", "Generator fault", "Software fault", "Calibration drift", "Mechanical wear"],
}

TECHNICIANS = [f"TECH-{i:03d}" for i in range(1, 7)]

# 9 machines spread across the three sites and three modalities.
MACHINES = [
    {"machine_id": "MRI-101", "machine_type": "MRI", "hospital_site": "Riverside General", "install_date": date(2016, 3, 12)},
    {"machine_id": "MRI-102", "machine_type": "MRI", "hospital_site": "Lakeview Medical Center", "install_date": date(2019, 7, 1)},
    {"machine_id": "MRI-103", "machine_type": "MRI", "hospital_site": "St. Anne's Hospital", "install_date": date(2021, 11, 20)},
    {"machine_id": "CT-201", "machine_type": "CT", "hospital_site": "Riverside General", "install_date": date(2015, 9, 5)},
    {"machine_id": "CT-202", "machine_type": "CT", "hospital_site": "Lakeview Medical Center", "install_date": date(2018, 2, 14)},
    {"machine_id": "CT-203", "machine_type": "CT", "hospital_site": "St. Anne's Hospital", "install_date": date(2022, 4, 3)},
    {"machine_id": "XR-301", "machine_type": "X-ray", "hospital_site": "Riverside General", "install_date": date(2014, 6, 18)},
    {"machine_id": "XR-302", "machine_type": "X-ray", "hospital_site": "Lakeview Medical Center", "install_date": date(2017, 10, 9)},
    {"machine_id": "XR-303", "machine_type": "X-ray", "hospital_site": "St. Anne's Hospital", "install_date": date(2020, 1, 27)},
]

STUDY_START = date(2022, 4, 1)
STUDY_END = date(2023, 3, 31)


def daterange(start: date, end: date):
    days = (end - start).days + 1
    for n in range(days):
        yield start + timedelta(n)


def machine_age_years(install_date: date, as_of: date) -> float:
    return round((as_of - install_date).days / 365.25, 2)


# ---------------------------------------------------------------------------
# 1. machine_metadata.csv
# ---------------------------------------------------------------------------

def build_machine_metadata() -> pd.DataFrame:
    rows = []
    for m in MACHINES:
        age = machine_age_years(m["install_date"], STUDY_END)
        # Older machines tend to have been serviced more recently out of necessity.
        days_since_service = int(rng.integers(10, 40)) if age > 6 else int(rng.integers(30, 120))
        last_service_date = STUDY_END - timedelta(days=days_since_service)
        rows.append({
            "machine_id": m["machine_id"],
            "age_years": age,
            "manufacturer": rng.choice(MANUFACTURERS[m["machine_type"]]),
            "last_service_date": last_service_date.isoformat(),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 2. equipment_logs.csv (daily usage per machine)
# ---------------------------------------------------------------------------

def build_equipment_logs() -> pd.DataFrame:
    rows = []
    for m in MACHINES:
        cfg = MACHINE_TYPES[m["machine_type"]]
        age_at_end = machine_age_years(m["install_date"], STUDY_END)
        # Slight downward drift in usage as machines age (more downtime eats into usage).
        age_penalty = min(age_at_end * 0.03, 0.6)
        for d in daterange(STUDY_START, STUDY_END):
            if d < m["install_date"]:
                continue
            weekday = d.weekday()
            if weekday == 6:  # Sunday: reduced elective imaging
                weekend_factor = 0.35
            elif weekday == 5:  # Saturday: reduced schedule
                weekend_factor = 0.6
            else:
                weekend_factor = 1.0

            mean_hours = max(cfg["base_daily_hours"] - age_penalty, 1.0) * weekend_factor
            hours = rng.normal(mean_hours, cfg["std_daily_hours"] * 0.5)
            hours = float(np.clip(hours, 0, 24))
            rows.append({
                "machine_id": m["machine_id"],
                "machine_type": m["machine_type"],
                "hospital_site": m["hospital_site"],
                "install_date": m["install_date"].isoformat(),
                "date": d.isoformat(),
                "daily_usage_hours": round(hours, 2),
            })
    df = pd.DataFrame(rows)
    # Introduce a small amount of realistic messiness for the cleaning step.
    dup_sample = df.sample(frac=0.01, random_state=RNG_SEED)
    df = pd.concat([df, dup_sample], ignore_index=True)
    missing_idx = df.sample(frac=0.005, random_state=RNG_SEED + 1).index
    df.loc[missing_idx, "daily_usage_hours"] = np.nan
    return df


# ---------------------------------------------------------------------------
# 3. maintenance_tickets.csv
# ---------------------------------------------------------------------------

def build_maintenance_tickets() -> pd.DataFrame:
    rows = []
    ticket_num = 1
    for m in MACHINES:
        age_at_end = machine_age_years(m["install_date"], STUDY_END)
        # Older machines fail more often: base rate scales with age.
        expected_tickets = max(3, round(age_at_end * 1.35))
        n_tickets = int(rng.poisson(expected_tickets))
        possible_days = [d for d in daterange(max(STUDY_START, m["install_date"]), STUDY_END)]
        report_days = rng.choice(possible_days, size=min(n_tickets, len(possible_days)), replace=False)
        for reported in sorted(report_days):
            issue_type = rng.choice(ISSUE_TYPES_BY_MACHINE[m["machine_type"]])
            # Older machines take somewhat longer to repair on average.
            base_repair_hours = 4 + age_at_end * 0.9
            downtime_hours = float(np.clip(rng.gamma(shape=2.0, scale=base_repair_hours / 2.0), 1, 240))
            resolved = pd.Timestamp(reported) + pd.Timedelta(hours=downtime_hours) + pd.Timedelta(hours=float(rng.integers(0, 12)))
            if resolved.date() > STUDY_END:
                resolved = pd.Timestamp(STUDY_END)
            rows.append({
                "ticket_id": f"TCK-{ticket_num:05d}",
                "machine_id": m["machine_id"],
                "issue_type": issue_type,
                "reported_date": pd.Timestamp(reported).isoformat(),
                "resolved_date": resolved.isoformat(),
                "downtime_hours": round(downtime_hours, 2),
                "technician_id": rng.choice(TECHNICIANS),
            })
            ticket_num += 1
    df = pd.DataFrame(rows)
    # A few tickets missing a resolved_date (still open at data pull time) -- cleaning step handles this.
    open_idx = df.sample(frac=0.03, random_state=RNG_SEED + 2).index
    df.loc[open_idx, "resolved_date"] = None
    return df


def main():
    machine_metadata = build_machine_metadata()
    equipment_logs = build_equipment_logs()
    maintenance_tickets = build_maintenance_tickets()

    machine_metadata.to_csv(f"{OUTPUT_DIR}/machine_metadata.csv", index=False)
    equipment_logs.to_csv(f"{OUTPUT_DIR}/equipment_logs.csv", index=False)
    maintenance_tickets.to_csv(f"{OUTPUT_DIR}/maintenance_tickets.csv", index=False)

    print(f"machine_metadata.csv: {len(machine_metadata)} rows")
    print(f"equipment_logs.csv:   {len(equipment_logs)} rows")
    print(f"maintenance_tickets.csv: {len(maintenance_tickets)} rows")
    print(f"Total rows: {len(machine_metadata) + len(equipment_logs) + len(maintenance_tickets)}")


if __name__ == "__main__":
    main()
