-- Analytical queries for the Healthcare Imaging Equipment Utilization &
-- Downtime Analysis project. Run against the SQLite database produced by
-- sql/build_db.py (data/healthcare.db).

-- ---------------------------------------------------------------------
-- 1. Total downtime per machine
-- ---------------------------------------------------------------------
SELECT
    m.machine_id,
    l.machine_type,
    l.hospital_site,
    ROUND(SUM(t.downtime_hours), 1) AS total_downtime_hours,
    COUNT(t.ticket_id) AS ticket_count
FROM machine_metadata m
JOIN (SELECT DISTINCT machine_id, machine_type, hospital_site FROM equipment_logs) l
    ON l.machine_id = m.machine_id
LEFT JOIN maintenance_tickets t
    ON t.machine_id = m.machine_id
GROUP BY m.machine_id
ORDER BY total_downtime_hours DESC;

-- ---------------------------------------------------------------------
-- 2. Average downtime per hospital site
-- ---------------------------------------------------------------------
SELECT
    l.hospital_site,
    ROUND(AVG(t.downtime_hours), 2) AS avg_downtime_hours_per_ticket,
    ROUND(SUM(t.downtime_hours), 1) AS total_downtime_hours,
    COUNT(t.ticket_id) AS ticket_count
FROM maintenance_tickets t
JOIN (SELECT DISTINCT machine_id, hospital_site FROM equipment_logs) l
    ON l.machine_id = t.machine_id
GROUP BY l.hospital_site
ORDER BY total_downtime_hours DESC;

-- ---------------------------------------------------------------------
-- 3. MTBF (Mean Time Between Failures, in days) per machine
--    Approximated as the observed service window divided by the number
--    of failures (tickets) recorded for that machine.
-- ---------------------------------------------------------------------
WITH ticket_stats AS (
    SELECT
        machine_id,
        COUNT(*) AS failure_count,
        MIN(reported_date) AS first_ticket,
        MAX(reported_date) AS last_ticket
    FROM maintenance_tickets
    GROUP BY machine_id
),
observation_window AS (
    SELECT
        machine_id,
        MIN(date) AS window_start,
        MAX(date) AS window_end
    FROM equipment_logs
    GROUP BY machine_id
)
SELECT
    o.machine_id,
    ts.failure_count,
    CAST(julianday(o.window_end) - julianday(o.window_start) AS REAL) AS observed_days,
    ROUND(
        (julianday(o.window_end) - julianday(o.window_start)) / ts.failure_count,
        1
    ) AS mtbf_days
FROM observation_window o
JOIN ticket_stats ts ON ts.machine_id = o.machine_id
ORDER BY mtbf_days ASC;

-- ---------------------------------------------------------------------
-- 4. MTTR (Mean Time To Repair, in hours) per machine
--    Only tickets with a resolved_date are counted (open tickets excluded).
-- ---------------------------------------------------------------------
SELECT
    machine_id,
    COUNT(*) AS resolved_ticket_count,
    ROUND(AVG(downtime_hours), 2) AS mttr_hours
FROM maintenance_tickets
WHERE resolved_date IS NOT NULL
GROUP BY machine_id
ORDER BY mttr_hours DESC;

-- ---------------------------------------------------------------------
-- 5. Top failure causes fleet-wide
-- ---------------------------------------------------------------------
SELECT
    issue_type,
    COUNT(*) AS occurrences,
    ROUND(SUM(downtime_hours), 1) AS total_downtime_hours
FROM maintenance_tickets
GROUP BY issue_type
ORDER BY occurrences DESC;
