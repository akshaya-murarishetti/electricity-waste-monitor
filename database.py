"""
Database setup and helper functions for Electricity Waste Monitor.
Uses SQLite with parameterized queries.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "electricity_monitor.db"


def get_connection():
    """Return a connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they do not exist."""
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS appliances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                power_watts REAL NOT NULL CHECK(power_watts >= 0),
                quantity INTEGER NOT NULL DEFAULT 1 CHECK(quantity > 0),
                hours_per_day REAL NOT NULL DEFAULT 0 CHECK(hours_per_day >= 0 AND hours_per_day <= 24),
                category TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS consumption_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_date TEXT NOT NULL,
                energy_kwh REAL NOT NULL CHECK(energy_kwh >= 0),
                tariff_per_kwh REAL NOT NULL CHECK(tariff_per_kwh >= 0),
                estimated_cost REAL NOT NULL CHECK(estimated_cost >= 0),
                source_type TEXT NOT NULL DEFAULT 'estimate'
                    CHECK(source_type IN ('estimate', 'sample', 'device')),
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                threshold_value REAL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'acknowledged', 'resolved')),
                FOREIGN KEY (record_id) REFERENCES consumption_records(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS device_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                power_watts REAL,
                energy_kwh REAL NOT NULL CHECK(energy_kwh >= 0),
                received_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            INSERT OR IGNORE INTO settings (key, value) VALUES
                ('default_tariff', '8.0'),
                ('high_usage_threshold_kwh', '15.0'),
                ('threshold_multiplier', '1.5');
            """
        )


def get_setting(key, default=None):
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default


def set_setting(key, value):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )


def get_default_tariff():
    return float(get_setting("default_tariff", "8.0"))


def get_high_usage_threshold():
    return float(get_setting("high_usage_threshold_kwh", "15.0"))


def get_threshold_multiplier():
    return float(get_setting("threshold_multiplier", "1.5"))


def add_appliance(name, power_watts, quantity, hours_per_day, category=None):
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO appliances (name, power_watts, quantity, hours_per_day, category)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name.strip(), float(power_watts), int(quantity), float(hours_per_day), category),
        )
        return cur.lastrowid


def get_all_appliances():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM appliances ORDER BY name COLLATE NOCASE"
        ).fetchall()
        return [dict(r) for r in rows]


def get_appliance(appliance_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM appliances WHERE id = ?", (appliance_id,)
        ).fetchone()
        return dict(row) if row else None


def update_appliance(appliance_id, name, power_watts, quantity, hours_per_day, category=None):
    with get_db() as conn:
        conn.execute(
            """
            UPDATE appliances
            SET name = ?, power_watts = ?, quantity = ?, hours_per_day = ?, category = ?
            WHERE id = ?
            """,
            (name.strip(), float(power_watts), int(quantity), float(hours_per_day), category, appliance_id),
        )


def delete_appliance(appliance_id):
    with get_db() as conn:
        conn.execute("DELETE FROM appliances WHERE id = ?", (appliance_id,))


def appliance_count():
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM appliances").fetchone()
        return row["c"]


def add_consumption_record(record_date, energy_kwh, tariff_per_kwh, source_type="estimate", notes=None):
    estimated_cost = round(float(energy_kwh) * float(tariff_per_kwh), 2)
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO consumption_records
                (record_date, energy_kwh, tariff_per_kwh, estimated_cost, source_type, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (record_date, float(energy_kwh), float(tariff_per_kwh), estimated_cost, source_type, notes),
        )
        return cur.lastrowid


def get_consumption_records(from_date=None, to_date=None, limit=None):
    query = "SELECT * FROM consumption_records WHERE 1=1"
    params = []
    if from_date:
        query += " AND record_date >= ?"
        params.append(from_date)
    if to_date:
        query += " AND record_date <= ?"
        params.append(to_date)
    query += " ORDER BY record_date DESC, id DESC"
    if limit:
        query += " LIMIT ?"
        params.append(int(limit))
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_consumption_record(record_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM consumption_records WHERE id = ?", (record_id,)
        ).fetchone()
        return dict(row) if row else None


def delete_consumption_record(record_id):
    with get_db() as conn:
        conn.execute("DELETE FROM consumption_records WHERE id = ?", (record_id,))


def get_total_energy(from_date=None, to_date=None):
    query = "SELECT COALESCE(SUM(energy_kwh), 0) AS total FROM consumption_records WHERE 1=1"
    params = []
    if from_date:
        query += " AND record_date >= ?"
        params.append(from_date)
    if to_date:
        query += " AND record_date <= ?"
        params.append(to_date)
    with get_db() as conn:
        row = conn.execute(query, params).fetchone()
        return float(row["total"])


def get_historical_average(exclude_date=None, days=30):
    query = """
        SELECT AVG(energy_kwh) AS avg_kwh, COUNT(*) AS cnt
        FROM consumption_records
        WHERE source_type IN ('estimate', 'sample', 'device')
    """
    params = []
    if exclude_date:
        query += " AND record_date != ?"
        params.append(exclude_date)
    with get_db() as conn:
        row = conn.execute(query, params).fetchone()
        if row and row["cnt"] and row["cnt"] >= 3:
            return float(row["avg_kwh"]), int(row["cnt"])
        return None, 0


def add_alert(alert_type, message, threshold_value=None, record_id=None):
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO alerts (record_id, alert_type, message, threshold_value, status)
            VALUES (?, ?, ?, ?, 'active')
            """,
            (record_id, alert_type, message, threshold_value),
        )
        return cur.lastrowid


def get_active_alerts(limit=20):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT a.*, c.record_date, c.energy_kwh
            FROM alerts a
            LEFT JOIN consumption_records c ON a.record_id = c.id
            WHERE a.status = 'active'
            ORDER BY a.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def alert_count():
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM alerts WHERE status = 'active'"
        ).fetchone()
        return row["c"]


def acknowledge_alert(alert_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE alerts SET status = 'acknowledged' WHERE id = ?", (alert_id,)
        )


def add_device_reading(device_id, timestamp, energy_kwh, power_watts=None):
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO device_readings (device_id, timestamp, power_watts, energy_kwh)
            VALUES (?, ?, ?, ?)
            """,
            (device_id, timestamp, power_watts, float(energy_kwh)),
        )
        return cur.lastrowid


def get_device_readings(limit=50):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM device_readings ORDER BY received_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def has_valid_device_readings():
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM device_readings"
        ).fetchone()
        return row["c"] > 0


def get_latest_device_info():
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM device_readings ORDER BY received_at DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
