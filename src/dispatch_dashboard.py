import json
from pathlib import Path

from src.data_store import (
    fetch_teams,
    save_dispatch_assignments,
    save_teams,
    update_request_status,
    update_team_status,
)
from src.dispatch_assignment import assign_team_for_request, get_all_teams
from src.priority_route_integration import load_ranked_requests

OUTPUT_PATH = Path("results/dispatch_assignment.json")


def build_dispatch_plan():
    save_teams(get_all_teams())
    requests = load_ranked_requests()
    assignments = []
    for request in requests:
        assignment = assign_team_for_request(request)
        assignments.append({
            "request_id": request.get("id"),
            "reporter": request.get("reporter"),
            "priority_score": request.get("priority_score"),
            "team_id": assignment["team_id"],
            "team_name": assignment["team_name"],
            "team_type": assignment["team_type"],
            "distance_km": assignment["distance_km"],
            "capacity": assignment["capacity"],
            "status": assignment["status"],
            "assignment_score": assignment["score"],
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump({"assignments": assignments}, file, indent=2, ensure_ascii=False)

    save_dispatch_assignments(assignments)
    return assignments


def dispatch_next_request():
    requests = load_ranked_requests()
    pending_requests = [
        request for request in requests
        if request.get("status", "waiting") in {"waiting", "unassigned"}
    ]
    available_teams = [team for team in fetch_teams() if team.get("status") == "ready"]
    if not pending_requests:
        return None
    if not available_teams:
        raise RuntimeError("Hazır ekip bulunamadı")

    request = pending_requests[0]
    assignment = assign_team_for_request(request, available_teams)
    assignment_row = {
        "request_id": request.get("id"),
        "reporter": request.get("reporter"),
        "priority_score": request.get("priority_score"),
        "team_id": assignment["team_id"],
        "team_name": assignment["team_name"],
        "team_type": assignment["team_type"],
        "distance_km": assignment["distance_km"],
        "capacity": assignment["capacity"],
        "status": "assigned",
        "assignment_score": assignment["score"],
    }
    save_dispatch_assignments([assignment_row])
    update_request_status(request["id"], "assigned")
    update_team_status(assignment["team_id"], "assigned")
    return assignment_row


def main():
    assignments = build_dispatch_plan()
    for item in assignments:
        print(f"{item['request_id']} -> {item['team_name']} ({item['team_type']}) | distance={item['distance_km']} km")


if __name__ == "__main__":
    main()
