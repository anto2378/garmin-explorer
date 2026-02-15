"""
SQLite persistence layer.

Database lives at data/garmin.db.
Tables: users, cached_activities, weekly_stats.
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "garmin.db"

# --- Schema ---

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT UNIQUE NOT NULL,          -- lowercase identifier (e.g. "anto")
    garmin_email TEXT UNIQUE,                  -- Garmin account email
    display_name TEXT,                         -- Garmin display name
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cached_activities (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name      TEXT NOT NULL,              -- references users.name
    garmin_id      INTEGER NOT NULL,           -- Garmin activityId
    activity_type  TEXT,
    distance_m     REAL DEFAULT 0,
    elevation_gain_m REAL DEFAULT 0,
    duration_s     REAL DEFAULT 0,
    calories       INTEGER DEFAULT 0,
    start_time     TEXT,                       -- ISO-8601
    activity_json  TEXT,                       -- full JSON blob
    fetched_at     TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_name, garmin_id)
);

CREATE TABLE IF NOT EXISTS weekly_stats (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name        TEXT NOT NULL,
    week_start       TEXT NOT NULL,            -- Monday date (YYYY-MM-DD)
    total_distance_m REAL DEFAULT 0,
    total_duration_s REAL DEFAULT 0,
    total_activities INTEGER DEFAULT 0,
    total_calories   INTEGER DEFAULT 0,
    computed_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_name, week_start)
);
"""


def migrate_add_last_synced() -> None:
    """Add last_synced_at column if it doesn't exist."""
    with get_db() as db:
        cursor = db.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}
        if "last_synced_at" not in columns:
            db.execute("ALTER TABLE users ADD COLUMN last_synced_at TEXT")
            logger.info("Added last_synced_at column to users table")


def migrate_add_elevation_gain() -> None:
    """Add elevation_gain_m column and backfill from activity_json."""
    with get_db() as db:
        cursor = db.execute("PRAGMA table_info(cached_activities)")
        columns = {row[1] for row in cursor.fetchall()}
        if "elevation_gain_m" not in columns:
            db.execute("ALTER TABLE cached_activities ADD COLUMN elevation_gain_m REAL DEFAULT 0")
            logger.info("Added elevation_gain_m column to cached_activities table")

            # Backfill elevation from activity_json
            rows = db.execute("SELECT id, activity_json FROM cached_activities").fetchall()
            updated = 0
            for row in rows:
                activity_id = row[0]
                activity_json = row[1]
                if activity_json:
                    try:
                        activity_data = json.loads(activity_json)
                        elevation_gain = activity_data.get("elevationGain", 0) or 0
                        db.execute(
                            "UPDATE cached_activities SET elevation_gain_m = ? WHERE id = ?",
                            (elevation_gain, activity_id)
                        )
                        updated += 1
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse activity_json for id {activity_id}")

            logger.info(f"Backfilled elevation_gain_m for {updated} activities")


def init_db() -> None:
    """Create database and tables if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_db() as db:
        db.executescript(_SCHEMA)
    migrate_add_last_synced()
    migrate_add_elevation_gain()


@contextmanager
def get_db():
    """Yield a sqlite3 connection with row_factory = Row."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# --- Users ---


def upsert_user(
    name: str,
    garmin_email: str | None = None,
    display_name: str | None = None,
    last_synced_at: str | None = None,
) -> None:
    """Insert or update a user."""
    with get_db() as db:
        db.execute(
            """
            INSERT INTO users (name, garmin_email, display_name, last_synced_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                garmin_email = excluded.garmin_email,
                display_name = excluded.display_name,
                last_synced_at = COALESCE(excluded.last_synced_at, last_synced_at)
            """,
            (name, garmin_email, display_name, last_synced_at),
        )


def get_all_users() -> list[dict]:
    """Return all registered users."""
    with get_db() as db:
        rows = db.execute("SELECT * FROM users ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def get_user_by_email(garmin_email: str) -> dict | None:
    """Get user by Garmin email. Returns None if not found."""
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE garmin_email = ?",
            (garmin_email,),
        ).fetchone()
        return dict(row) if row else None


def delete_user(user_name: str) -> None:
    """Delete a user and all their cached activities."""
    with get_db() as db:
        db.execute("DELETE FROM cached_activities WHERE user_name = ?", (user_name,))
        db.execute("DELETE FROM weekly_stats WHERE user_name = ?", (user_name,))
        db.execute("DELETE FROM users WHERE name = ?", (user_name,))


# --- Activities ---


def upsert_activities(user_name: str, activities: list[dict]) -> int:
    """
    Insert or update activities for a user.
    Returns the number of new activities inserted.
    """
    inserted = 0
    with get_db() as db:
        for a in activities:
            garmin_id = a.get("activityId")
            if not garmin_id:
                continue

            # Parse start time
            start_time = a.get("startTimeLocal") or a.get("startTimeGMT")

            # Extract elevation gain
            elevation_gain = a.get("elevationGain", 0) or 0

            cursor = db.execute(
                """
                INSERT INTO cached_activities
                    (user_name, garmin_id, activity_type, distance_m, elevation_gain_m,
                     duration_s, calories, start_time, activity_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_name, garmin_id) DO UPDATE SET
                    activity_type = excluded.activity_type,
                    distance_m    = excluded.distance_m,
                    elevation_gain_m = excluded.elevation_gain_m,
                    duration_s    = excluded.duration_s,
                    calories      = excluded.calories,
                    start_time    = excluded.start_time,
                    activity_json = excluded.activity_json,
                    fetched_at    = datetime('now')
                """,
                (
                    user_name,
                    garmin_id,
                    a.get("activityType", {}).get("typeKey", "unknown"),
                    a.get("distance", 0) or 0,
                    elevation_gain,
                    a.get("duration", 0) or 0,
                    a.get("calories", 0) or 0,
                    start_time,
                    json.dumps(a),
                ),
            )
            # rowcount = 1 for INSERT, 1 for UPDATE — use lastrowid trick
            if cursor.lastrowid:
                inserted += 1
    return inserted


def get_cached_activities(
    user_name: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """
    Fetch cached activities, optionally filtered by user.
    Returns newest first.
    """
    with get_db() as db:
        if user_name:
            rows = db.execute(
                """
                SELECT * FROM cached_activities
                WHERE user_name = ?
                ORDER BY start_time DESC
                LIMIT ?
                """,
                (user_name, limit),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT * FROM cached_activities
                ORDER BY start_time DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


def get_activity_count(user_name: str) -> int:
    """Count total cached activities for a user."""
    with get_db() as db:
        row = db.execute(
            "SELECT COUNT(*) as cnt FROM cached_activities WHERE user_name = ?",
            (user_name,),
        ).fetchone()
        return row["cnt"] if row else 0


# --- Weekly stats ---


def upsert_weekly_stats(
    user_name: str,
    week_start: str,
    total_distance_m: float,
    total_duration_s: float,
    total_activities: int,
    total_calories: int,
) -> None:
    """Insert or update weekly stats for a user."""
    with get_db() as db:
        db.execute(
            """
            INSERT INTO weekly_stats
                (user_name, week_start, total_distance_m, total_duration_s,
                 total_activities, total_calories)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_name, week_start) DO UPDATE SET
                total_distance_m = excluded.total_distance_m,
                total_duration_s = excluded.total_duration_s,
                total_activities = excluded.total_activities,
                total_calories   = excluded.total_calories,
                computed_at      = datetime('now')
            """,
            (
                user_name,
                week_start,
                total_distance_m,
                total_duration_s,
                total_activities,
                total_calories,
            ),
        )


def get_weekly_stats(user_name: str | None = None, weeks: int = 8) -> list[dict]:
    """Fetch weekly stats, newest first."""
    with get_db() as db:
        if user_name:
            rows = db.execute(
                """
                SELECT * FROM weekly_stats
                WHERE user_name = ?
                ORDER BY week_start DESC
                LIMIT ?
                """,
                (user_name, weeks),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT * FROM weekly_stats
                ORDER BY week_start DESC
                LIMIT ?
                """,
                (weeks,),
            ).fetchall()
        return [dict(r) for r in rows]


# Auto-init on import
init_db()
