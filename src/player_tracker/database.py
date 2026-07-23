import sqlite3
import json
from datetime import datetime
from typing import Optional
import uuid
from pathlib import Path


class TrackerDatabase:
    def __init__(self, db_path: str = "player_tracker.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS train_sessions (
                    id TEXT PRIMARY KEY,
                    steam_id TEXT NOT NULL,
                    server_code TEXT NOT NULL,
                    server_name TEXT NOT NULL,
                    train_number TEXT NOT NULL,
                    train_name TEXT NOT NULL,
                    start_station TEXT NOT NULL,
                    end_station TEXT NOT NULL,
                    vehicle TEXT NOT NULL,
                    joined_at TEXT NOT NULL,
                    left_at TEXT,
                    distance_meters INTEGER,
                    points INTEGER,
                    baseline_distance INTEGER,
                    baseline_points INTEGER
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS station_sessions (
                    id TEXT PRIMARY KEY,
                    steam_id TEXT NOT NULL,
                    server_code TEXT NOT NULL,
                    server_name TEXT NOT NULL,
                    station_name TEXT NOT NULL,
                    station_prefix TEXT NOT NULL,
                    joined_at TEXT NOT NULL,
                    left_at TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS train_station_passages (
                    id TEXT PRIMARY KEY,
                    train_session_id TEXT NOT NULL,
                    station_name TEXT NOT NULL,
                    passed_at TEXT NOT NULL,
                    stop_type TEXT NOT NULL,
                    FOREIGN KEY (train_session_id) REFERENCES train_sessions(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS steam_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    steam_id TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    total_score INTEGER NOT NULL,
                    total_distance_meters INTEGER NOT NULL,
                    total_dispatcher_time_minutes INTEGER NOT NULL
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_train_steam_id ON train_sessions(steam_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_station_steam_id ON station_sessions(steam_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_steam_stats_steam_id ON steam_stats(steam_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_steam_stats_recorded_at ON steam_stats(recorded_at)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_train_passages_session ON train_station_passages(train_session_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_train_passages_station ON train_station_passages(station_name)
            """)

            # Create unique constraint to prevent duplicate station passages
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_train_passages_unique
                ON train_station_passages(train_session_id, station_name)
            """)

            conn.commit()

            # Migration: Add baseline columns if they don't exist
            cursor = conn.execute("PRAGMA table_info(train_sessions)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'baseline_distance' not in columns:
                conn.execute("""
                    ALTER TABLE train_sessions ADD COLUMN baseline_distance INTEGER
                """)
                conn.commit()

            if 'baseline_points' not in columns:
                conn.execute("""
                    ALTER TABLE train_sessions ADD COLUMN baseline_points INTEGER
                """)
                conn.commit()

            # Migration: Add vehicle composition columns if they don't exist
            cursor = conn.execute("PRAGMA table_info(train_sessions)")
            columns = [row[1] for row in cursor.fetchall()]

            # Rename 'vehicle' to 'vehicle_summary' if needed
            if 'vehicle' in columns and 'vehicle_summary' not in columns:
                # SQLite doesn't support RENAME COLUMN directly in older versions
                # We'll add new column and copy data
                conn.execute("""
                    ALTER TABLE train_sessions ADD COLUMN vehicle_summary TEXT
                """)
                conn.execute("""
                    UPDATE train_sessions SET vehicle_summary = vehicle
                """)
                conn.commit()

            if 'traction_type' not in columns:
                conn.execute("""
                    ALTER TABLE train_sessions ADD COLUMN traction_type TEXT
                """)
                conn.commit()

            if 'locomotive_names' not in columns:
                conn.execute("""
                    ALTER TABLE train_sessions ADD COLUMN locomotive_names TEXT
                """)
                conn.commit()

            if 'num_locomotives' not in columns:
                conn.execute("""
                    ALTER TABLE train_sessions ADD COLUMN num_locomotives INTEGER
                """)
                conn.commit()

            if 'num_wagons' not in columns:
                conn.execute("""
                    ALTER TABLE train_sessions ADD COLUMN num_wagons INTEGER
                """)
                conn.commit()

            if 'total_vehicles' not in columns:
                conn.execute("""
                    ALTER TABLE train_sessions ADD COLUMN total_vehicles INTEGER
                """)
                conn.commit()

            if 'total_length' not in columns:
                conn.execute("""
                    ALTER TABLE train_sessions ADD COLUMN total_length REAL
                """)
                conn.commit()

            if 'total_weight' not in columns:
                conn.execute("""
                    ALTER TABLE train_sessions ADD COLUMN total_weight REAL
                """)
                conn.commit()

            if 'composition_json' not in columns:
                conn.execute("""
                    ALTER TABLE train_sessions ADD COLUMN composition_json TEXT
                """)
                conn.commit()

    def create_train_session(
        self,
        steam_id: str,
        server_code: str,
        server_name: str,
        train_number: str,
        train_name: str,
        start_station: str,
        end_station: str,
        vehicle: str,
        baseline_distance: Optional[int] = None,
        baseline_points: Optional[int] = None,
        vehicle_composition: Optional[dict] = None,
    ) -> str:
        """Create a new train session.

        Args:
            vehicle_composition: Optional dict with vehicle composition data:
                {
                    "traction_type": "LOCOMOTIVE" | "EMU" | "MULTIPLE_UNIT",
                    "locomotives": [{"displayName": str, "typeIdentifier": str, ...}],
                    "num_wagons": int,
                    "total_vehicles": int,
                    "total_length": float,
                    "total_weight": float
                }
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        # Extract composition data if provided
        vehicle_summary = vehicle
        traction_type = None
        locomotive_names = None
        num_locomotives = None
        num_wagons = None
        total_vehicles = None
        total_length = None
        total_weight = None
        composition_json = None

        if vehicle_composition:
            traction_type = vehicle_composition.get("traction_type")
            locomotives = vehicle_composition.get("locomotives", [])

            if locomotives:
                locomotive_names = ", ".join(loc["displayName"] for loc in locomotives)
                num_locomotives = len(locomotives)

                # Build summary string
                if num_locomotives == 1:
                    vehicle_summary = locomotive_names
                else:
                    vehicle_summary = f"{locomotive_names} (double-headed)"

                num_wagons = vehicle_composition.get("num_wagons", 0)
                if num_wagons > 0:
                    vehicle_summary += f" + {num_wagons} wagons"

            total_vehicles = vehicle_composition.get("total_vehicles")
            total_length = vehicle_composition.get("total_length")
            total_weight = vehicle_composition.get("total_weight")

            # Store full composition as JSON
            composition_json = json.dumps(vehicle_composition)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO train_sessions (
                    id, steam_id, server_code, server_name, train_number,
                    train_name, start_station, end_station, vehicle, vehicle_summary, joined_at,
                    baseline_distance, baseline_points,
                    traction_type, locomotive_names, num_locomotives, num_wagons,
                    total_vehicles, total_length, total_weight, composition_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    steam_id,
                    server_code,
                    server_name,
                    train_number,
                    train_name,
                    start_station,
                    end_station,
                    vehicle,  # Keep original vehicle for NOT NULL constraint
                    vehicle_summary,
                    now,
                    baseline_distance,
                    baseline_points,
                    traction_type,
                    locomotive_names,
                    num_locomotives,
                    num_wagons,
                    total_vehicles,
                    total_length,
                    total_weight,
                    composition_json,
                ),
            )
            conn.commit()

        return session_id

    def end_train_session(
        self, session_id: str, distance_meters: int, points: int
    ):
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE train_sessions
                SET left_at = ?, distance_meters = ?, points = ?
                WHERE id = ?
                """,
                (now, distance_meters, points, session_id),
            )
            conn.commit()

    def get_active_train_session(self, steam_id: str) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM train_sessions
                WHERE steam_id = ? AND left_at IS NULL
                ORDER BY joined_at DESC
                LIMIT 1
                """,
                (steam_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_train_session_by_id(self, session_id: str) -> Optional[dict]:
        """Get a specific train session by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM train_sessions
                WHERE id = ?
                """,
                (session_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_station_session(
        self,
        steam_id: str,
        server_code: str,
        server_name: str,
        station_name: str,
        station_prefix: str,
    ) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO station_sessions (
                    id, steam_id, server_code, server_name, station_name,
                    station_prefix, joined_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    steam_id,
                    server_code,
                    server_name,
                    station_name,
                    station_prefix,
                    now,
                ),
            )
            conn.commit()

        return session_id

    def end_station_session(self, session_id: str):
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE station_sessions
                SET left_at = ?
                WHERE id = ?
                """,
                (now, session_id),
            )
            conn.commit()

    def record_train_station_passage(
        self, train_session_id: str, station_name: str, stop_type: str
    ):
        """Record a station passage during a train session.

        Silently ignores duplicates due to unique constraint on (train_session_id, station_name).
        """
        passage_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO train_station_passages (
                        id, train_session_id, station_name, passed_at, stop_type
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (passage_id, train_session_id, station_name, now, stop_type),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # Duplicate passage - station already recorded for this session
                # This can happen if tracker polls at exact moment between time_type transitions
                pass

    def get_active_station_session(self, steam_id: str) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM station_sessions
                WHERE steam_id = ? AND left_at IS NULL
                ORDER BY joined_at DESC
                LIMIT 1
                """,
                (steam_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_train_sessions(
        self, steam_id: str, limit: int = 50
    ) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM train_sessions
                WHERE steam_id = ?
                ORDER BY joined_at DESC
                LIMIT ?
                """,
                (steam_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_station_sessions(
        self, steam_id: str, limit: int = 50
    ) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM station_sessions
                WHERE steam_id = ?
                ORDER BY joined_at DESC
                LIMIT ?
                """,
                (steam_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self, steam_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            # Train stats
            train_cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as session_count,
                    COALESCE(SUM(distance_meters), 0) as total_distance,
                    COALESCE(SUM(points), 0) as total_points,
                    COALESCE(SUM(
                        CASE WHEN left_at IS NOT NULL
                        THEN (julianday(left_at) - julianday(joined_at)) * 86400
                        ELSE 0 END
                    ), 0) as total_time
                FROM train_sessions
                WHERE steam_id = ? AND left_at IS NOT NULL
                """,
                (steam_id,),
            )
            train_stats = train_cursor.fetchone()

            # Station stats
            station_cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as session_count,
                    COALESCE(SUM(
                        CASE WHEN left_at IS NOT NULL
                        THEN (julianday(left_at) - julianday(joined_at)) * 86400
                        ELSE 0 END
                    ), 0) as total_time
                FROM station_sessions
                WHERE steam_id = ? AND left_at IS NOT NULL
                """,
                (steam_id,),
            )
            station_stats = station_cursor.fetchone()

            # Per-vehicle stats
            vehicle_cursor = conn.execute(
                """
                SELECT
                    vehicle,
                    COALESCE(SUM(distance_meters), 0) as distance,
                    COALESCE(SUM(points), 0) as points,
                    COALESCE(SUM(
                        CASE WHEN left_at IS NOT NULL
                        THEN (julianday(left_at) - julianday(joined_at)) * 86400
                        ELSE 0 END
                    ), 0) as time
                FROM train_sessions
                WHERE steam_id = ? AND left_at IS NOT NULL
                GROUP BY vehicle
                """,
                (steam_id,),
            )
            trains_by_type = {
                row[0]: {"distance": row[1], "points": row[2], "time": int(row[3])}
                for row in vehicle_cursor.fetchall()
            }

            # Per-station stats
            station_time_cursor = conn.execute(
                """
                SELECT
                    station_name,
                    COALESCE(SUM(
                        CASE WHEN left_at IS NOT NULL
                        THEN (julianday(left_at) - julianday(joined_at)) * 86400
                        ELSE 0 END
                    ), 0) as time
                FROM station_sessions
                WHERE steam_id = ? AND left_at IS NOT NULL
                GROUP BY station_name
                """,
                (steam_id,),
            )
            stations_by_name = {
                row[0]: int(row[1]) for row in station_time_cursor.fetchall()
            }

            # Station passages during train sessions
            passages_cursor = conn.execute(
                """
                SELECT
                    tsp.station_name,
                    COUNT(*) as passage_count,
                    SUM(CASE WHEN tsp.stop_type = 'PASSENGER' THEN 1 ELSE 0 END) as passenger_stops,
                    SUM(CASE WHEN tsp.stop_type = 'TECHNICAL' THEN 1 ELSE 0 END) as technical_stops,
                    SUM(CASE WHEN tsp.stop_type = 'NONE' THEN 1 ELSE 0 END) as pass_through
                FROM train_station_passages tsp
                JOIN train_sessions ts ON tsp.train_session_id = ts.id
                WHERE ts.steam_id = ?
                GROUP BY tsp.station_name
                """,
                (steam_id,),
            )
            station_passages = {
                row[0]: {
                    "total": row[1],
                    "passenger_stops": row[2],
                    "technical_stops": row[3],
                    "pass_through": row[4],
                }
                for row in passages_cursor.fetchall()
            }

            return {
                "total_distance_meters": train_stats[1],
                "total_points": train_stats[2],
                "total_train_time_seconds": int(train_stats[3]),
                "total_dispatcher_time_seconds": int(station_stats[1]),
                "train_sessions": train_stats[0],
                "station_sessions": station_stats[0],
                "trains_by_type": trains_by_type,
                "stations_by_name": stations_by_name,
                "station_passages": station_passages,
            }

    def save_steam_stats(
        self, steam_id: str, score: int, distance_meters: int, dispatcher_time_minutes: int
    ):
        """Save a snapshot of Steam stats."""
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO steam_stats (
                    steam_id, recorded_at, total_score, total_distance_meters,
                    total_dispatcher_time_minutes
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (steam_id, now, score, distance_meters, dispatcher_time_minutes),
            )
            conn.commit()

    def get_latest_steam_stats(self, steam_id: str) -> Optional[dict]:
        """Get the most recent Steam stats snapshot."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM steam_stats
                WHERE steam_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
                """,
                (steam_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_steam_stats_history(self, steam_id: str, limit: int = 100) -> list[dict]:
        """Get Steam stats history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM steam_stats
                WHERE steam_id = ?
                ORDER BY recorded_at DESC
                LIMIT ?
                """,
                (steam_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]
