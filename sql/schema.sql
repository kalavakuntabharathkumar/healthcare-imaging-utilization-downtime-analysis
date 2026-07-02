-- Schema for the Healthcare Imaging Equipment Utilization & Downtime Analysis
-- SQLite database. Loaded from data/*.csv by sql/build_db.py.

DROP TABLE IF EXISTS equipment_logs;
DROP TABLE IF EXISTS maintenance_tickets;
DROP TABLE IF EXISTS machine_metadata;

CREATE TABLE machine_metadata (
    machine_id        TEXT PRIMARY KEY,
    age_years         REAL NOT NULL,
    manufacturer      TEXT NOT NULL,
    last_service_date TEXT NOT NULL
);

CREATE TABLE equipment_logs (
    machine_id         TEXT NOT NULL,
    machine_type       TEXT NOT NULL,
    hospital_site       TEXT NOT NULL,
    install_date        TEXT NOT NULL,
    date                 TEXT NOT NULL,
    daily_usage_hours   REAL,
    FOREIGN KEY (machine_id) REFERENCES machine_metadata (machine_id)
);

CREATE TABLE maintenance_tickets (
    ticket_id       TEXT PRIMARY KEY,
    machine_id      TEXT NOT NULL,
    issue_type      TEXT NOT NULL,
    reported_date   TEXT NOT NULL,
    resolved_date   TEXT,
    downtime_hours  REAL NOT NULL,
    technician_id   TEXT NOT NULL,
    FOREIGN KEY (machine_id) REFERENCES machine_metadata (machine_id)
);

CREATE INDEX idx_equipment_logs_machine ON equipment_logs (machine_id);
CREATE INDEX idx_equipment_logs_date ON equipment_logs (date);
CREATE INDEX idx_maintenance_tickets_machine ON maintenance_tickets (machine_id);
