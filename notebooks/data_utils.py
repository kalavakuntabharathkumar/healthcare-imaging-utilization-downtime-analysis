"""
Shared cleaning / merging / metric helpers used by both notebooks in this
folder. Kept as a plain module (rather than duplicated notebook code) so the
cleaning logic is defined once and is unit-testable.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def load_raw():
    equipment_logs = pd.read_csv(DATA_DIR / "equipment_logs.csv")
    maintenance_tickets = pd.read_csv(DATA_DIR / "maintenance_tickets.csv")
    machine_metadata = pd.read_csv(DATA_DIR / "machine_metadata.csv")
    return equipment_logs, maintenance_tickets, machine_metadata


def clean_equipment_logs(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates()
    dupes_removed = before - len(df)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["install_date"] = pd.to_datetime(df["install_date"], errors="coerce")

    missing_usage = df["daily_usage_hours"].isna().sum()
    # Impute missing daily usage with the machine's own median usage -- more
    # representative than a fleet-wide average, since usage varies a lot by
    # modality and site.
    df["daily_usage_hours"] = df.groupby("machine_id")["daily_usage_hours"].transform(
        lambda s: s.fillna(s.median())
    )

    df["daily_usage_hours"] = df["daily_usage_hours"].clip(lower=0, upper=24)

    stats = {"duplicates_removed": int(dupes_removed), "missing_usage_imputed": int(missing_usage)}
    return df, stats


def clean_maintenance_tickets(df: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates()
    dupes_removed = before - len(df)

    df["reported_date"] = pd.to_datetime(df["reported_date"], errors="coerce")
    df["resolved_date"] = pd.to_datetime(df["resolved_date"], errors="coerce")

    still_open = df["resolved_date"].isna().sum()
    # Tickets still open at the data pull date: treat downtime as ongoing
    # through the observation window end for reporting purposes, but flag
    # them so aggregate MTTR calculations can exclude them if desired.
    df["is_open"] = df["resolved_date"].isna()
    df.loc[df["is_open"], "resolved_date"] = as_of

    stats = {"duplicates_removed": int(dupes_removed), "still_open_tickets": int(still_open)}
    return df, stats


def clean_machine_metadata(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates()
    df["last_service_date"] = pd.to_datetime(df["last_service_date"], errors="coerce")
    return df


def merge_all(equipment_logs, maintenance_tickets, machine_metadata) -> pd.DataFrame:
    merged = equipment_logs.merge(machine_metadata, on="machine_id", how="left")
    return merged


def compute_utilization(equipment_logs_clean: pd.DataFrame, hours_per_day: float = 24.0) -> pd.DataFrame:
    """utilization_rate = actual usage hours / available hours, per machine."""
    grouped = equipment_logs_clean.groupby(["machine_id", "machine_type", "hospital_site"]).agg(
        total_usage_hours=("daily_usage_hours", "sum"),
        days_observed=("date", "nunique"),
    ).reset_index()
    grouped["available_hours"] = grouped["days_observed"] * hours_per_day
    grouped["utilization_rate"] = (grouped["total_usage_hours"] / grouped["available_hours"]).round(4)
    return grouped


def top_downtime_causes(maintenance_tickets_clean: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    summary = (
        maintenance_tickets_clean.groupby("issue_type")
        .agg(occurrences=("ticket_id", "count"), total_downtime_hours=("downtime_hours", "sum"))
        .reset_index()
        .sort_values("total_downtime_hours", ascending=False)
    )
    summary["total_downtime_hours"] = summary["total_downtime_hours"].round(1)
    return summary.head(n)


def downtime_per_machine(maintenance_tickets_clean: pd.DataFrame) -> pd.DataFrame:
    summary = (
        maintenance_tickets_clean.groupby("machine_id")
        .agg(
            total_downtime_hours=("downtime_hours", "sum"),
            ticket_count=("ticket_id", "count"),
            mttr_hours=("downtime_hours", "mean"),
        )
        .reset_index()
    )
    summary["total_downtime_hours"] = summary["total_downtime_hours"].round(1)
    summary["mttr_hours"] = summary["mttr_hours"].round(2)
    return summary.sort_values("total_downtime_hours", ascending=False)
