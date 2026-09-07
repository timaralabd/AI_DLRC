import json
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_store import (
    fetch_operation_log,
    fetch_ranked_requests,
    fetch_teams,
    save_dispatch_assignments,
    save_teams,
    update_request_status,
    update_team_status,
)
from src.rescue_priority import calculate_priority, rank_requests


def test_team_store_and_dispatch_store_round_trip():
    save_teams([
        {
            "id": "TEAM-TEST-1",
            "name": "Test Team",
            "team_type": "medical",
            "location": {"latitude": 37.1, "longitude": 37.3},
            "capacity": 10,
            "status": "ready",
        }
    ])
    save_dispatch_assignments([
        {
            "request_id": "REQ-TEST-1",
            "team_id": "TEAM-TEST-1",
            "team_name": "Test Team",
            "team_type": "medical",
            "distance_km": 3.5,
            "capacity": 10,
            "status": "assigned",
            "assignment_score": 90.0,
        }
    ])

    teams = fetch_teams()
    assignments = fetch_dispatch_assignments()

    assert any(team["id"] == "TEAM-TEST-1" for team in teams)
    assert any(item["request_id"] == "REQ-TEST-1" for item in assignments)


def test_request_and_team_status_update_round_trip():
    update_team_status("TEAM-TEST-1", "en-route")
    update_request_status("REQ-TEST-1", "assigned")

    teams = fetch_teams()
    requests = fetch_ranked_requests()

    assert any(team["id"] == "TEAM-TEST-1" and team["status"] == "en-route" for team in teams)
    assert any(request["id"] == "REQ-TEST-1" and request["status"] == "assigned" for request in requests)

    log_entries = fetch_operation_log(limit=10)
    assert any(entry.get("request_id") == "REQ-TEST-1" and entry.get("event_type") == "request_status" for entry in log_entries)
    assert any(entry.get("team_id") == "TEAM-TEST-1" and entry.get("event_type") == "team_status" for entry in log_entries)


def test_calculate_priority_counts_impact():
    request = {
        "people_affected": 85,
        "injured_people": 12,
        "urgency": 5,
        "needs": ["medical", "water"],
    }

    score = calculate_priority(request)

    assert score > 0
    assert score > 80


def test_rank_requests_returns_sorted_list():
    requests = [
        {"id": "REQ-1", "people_affected": 10, "injured_people": 0, "urgency": 1, "needs": ["blanket"]},
        {"id": "REQ-2", "people_affected": 100, "injured_people": 12, "urgency": 5, "needs": ["medical", "water"]},
    ]

    ranked = rank_requests(requests)

    assert ranked[0]["id"] == "REQ-2"
    assert ranked[0]["priority_score"] >= ranked[1]["priority_score"]
