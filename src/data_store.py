import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "ai_dlrc.db"
REQUESTS_JSON_PATH = ROOT / "data" / "emergency_requests.json"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS emergency_requests (
            id TEXT PRIMARY KEY,
            reporter TEXT,
            latitude REAL,
            longitude REAL,
            people_affected INTEGER,
            injured_people INTEGER,
            urgency INTEGER,
            needs TEXT,
            status TEXT,
            message TEXT,
            priority_score REAL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS teams (
            id TEXT PRIMARY KEY,
            name TEXT,
            team_type TEXT,
            latitude REAL,
            longitude REAL,
            capacity INTEGER,
            status TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dispatch_assignments (
            request_id TEXT,
            team_id TEXT,
            team_name TEXT,
            team_type TEXT,
            distance_km REAL,
            capacity INTEGER,
            status TEXT,
            assignment_score REAL,
            PRIMARY KEY (request_id, team_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS operation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            request_id TEXT,
            team_id TEXT,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def seed_requests_from_json():
    if not REQUESTS_JSON_PATH.exists():
        return

    with REQUESTS_JSON_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    requests = payload.get("requests", [])
    if not requests:
        return

    conn = get_connection()
    for request in requests:
        conn.execute(
            """
            INSERT OR REPLACE INTO emergency_requests (
                id, reporter, latitude, longitude,
                people_affected, injured_people, urgency,
                needs, status, message, priority_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.get("id"),
                request.get("reporter"),
                float(request.get("latitude", 0) or 0),
                float(request.get("longitude", 0) or 0),
                int(request.get("people_affected", 0) or 0),
                int(request.get("injured_people", 0) or 0),
                int(request.get("urgency", 0) or 0),
                json.dumps(request.get("needs", []), ensure_ascii=False),
                request.get("status", "waiting"),
                request.get("message", ""),
                float(request.get("priority_score", 0) or 0),
            ),
        )
    conn.commit()
    conn.close()


def ensure_seeded():
    init_db()
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) FROM emergency_requests").fetchone()
    if row[0] == 0:
        seed_requests_from_json()
    conn.close()


def save_request(request):
    init_db()
    conn = get_connection()
    conn.execute(
        """
        INSERT OR REPLACE INTO emergency_requests (
            id, reporter, latitude, longitude,
            people_affected, injured_people, urgency,
            needs, status, message, priority_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request.get("id"),
            request.get("reporter", "Saha koordinasyonu"),
            float(request.get("latitude", 0) or 0),
            float(request.get("longitude", 0) or 0),
            int(request.get("people_affected", 0) or 0),
            int(request.get("injured_people", 0) or 0),
            int(request.get("urgency", 0) or 0),
            json.dumps(request.get("needs", []) or [], ensure_ascii=False),
            request.get("status", "waiting"),
            request.get("message", ""),
            float(request.get("priority_score", 0) or 0),
        ),
    )
    conn.commit()
    conn.close()


def update_team_status(team_id, status):
    init_db()
    conn = get_connection()
    conn.execute(
        "UPDATE teams SET status = ? WHERE id = ?",
        (status, team_id),
    )
    conn.execute(
        "INSERT INTO operation_log (event_type, team_id, status) VALUES (?, ?, ?)",
        ("team_status", team_id, status),
    )
    conn.commit()
    conn.close()


def update_request_status(request_id, status):
    init_db()
    conn = get_connection()
    conn.execute(
        "UPDATE emergency_requests SET status = ? WHERE id = ?",
        (status, request_id),
    )
    conn.execute(
        "INSERT INTO operation_log (event_type, request_id, status) VALUES (?, ?, ?)",
        ("request_status", request_id, status),
    )
    conn.commit()
    conn.close()


def fetch_operation_log(limit=20):
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM operation_log ORDER BY id DESC LIMIT ?",
        (int(limit),),
    ).fetchall()
    items = []
    for row in rows:
        items.append({
            "id": row["id"],
            "event_type": row["event_type"],
            "request_id": row["request_id"],
            "team_id": row["team_id"],
            "status": row["status"],
            "created_at": row["created_at"],
        })
    conn.close()
    return items


def save_ranked_requests(requests):
    init_db()
    conn = get_connection()
    for request in requests:
        conn.execute(
            """
            INSERT OR REPLACE INTO emergency_requests (
                id, reporter, latitude, longitude,
                people_affected, injured_people, urgency,
                needs, status, message, priority_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.get("id"),
                request.get("reporter"),
                float(request.get("latitude", 0) or 0),
                float(request.get("longitude", 0) or 0),
                int(request.get("people_affected", 0) or 0),
                int(request.get("injured_people", 0) or 0),
                int(request.get("urgency", 0) or 0),
                json.dumps(request.get("needs", []), ensure_ascii=False),
                request.get("status", "waiting"),
                request.get("message", ""),
                float(request.get("priority_score", 0) or 0),
            ),
        )
    conn.commit()
    conn.close()


def fetch_ranked_requests():
    ensure_seeded()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM emergency_requests ORDER BY priority_score DESC"
    ).fetchall()
    requests = []
    for row in rows:
        requests.append({
            "id": row["id"],
            "reporter": row["reporter"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "people_affected": row["people_affected"],
            "injured_people": row["injured_people"],
            "urgency": row["urgency"],
            "needs": json.loads(row["needs"] or "[]"),
            "status": row["status"],
            "message": row["message"],
            "priority_score": row["priority_score"],
        })
    conn.close()
    return requests


def save_teams(teams):
    init_db()
    conn = get_connection()
    for team in teams:
        location = team.get("location") or {}
        conn.execute(
            """
            INSERT OR REPLACE INTO teams (
                id, name, team_type, latitude, longitude, capacity, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                team.get("id"),
                team.get("name"),
                team.get("team_type"),
                float(location.get("latitude", 0) or 0),
                float(location.get("longitude", 0) or 0),
                int(team.get("capacity", 0) or 0),
                team.get("status", "ready"),
            ),
        )
    conn.commit()
    conn.close()


def fetch_teams():
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM teams ORDER BY team_type, name"
    ).fetchall()
    items = []
    for row in rows:
        items.append({
            "id": row["id"],
            "name": row["name"],
            "team_type": row["team_type"],
            "location": {
                "latitude": row["latitude"],
                "longitude": row["longitude"],
            },
            "capacity": row["capacity"],
            "status": row["status"],
        })
    conn.close()
    return items


def save_dispatch_assignments(assignments):
    init_db()
    conn = get_connection()
    for assignment in assignments:
        conn.execute(
            """
            INSERT OR REPLACE INTO dispatch_assignments (
                request_id, team_id, team_name, team_type,
                distance_km, capacity, status, assignment_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assignment.get("request_id"),
                assignment.get("team_id"),
                assignment.get("team_name"),
                assignment.get("team_type"),
                float(assignment.get("distance_km", 0) or 0),
                int(assignment.get("capacity", 0) or 0),
                assignment.get("status", "ready"),
                float(assignment.get("assignment_score", 0) or 0),
            ),
        )
    conn.commit()
    conn.close()


def fetch_dispatch_assignments():
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM dispatch_assignments ORDER BY assignment_score DESC"
    ).fetchall()
    items = []
    for row in rows:
        items.append({
            "request_id": row["request_id"],
            "team_id": row["team_id"],
            "team_name": row["team_name"],
            "team_type": row["team_type"],
            "distance_km": row["distance_km"],
            "capacity": row["capacity"],
            "status": row["status"],
            "assignment_score": row["assignment_score"],
        })
    conn.close()
    return items
