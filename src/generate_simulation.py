import json
from pathlib import Path

from src.dispatch_assignment import TEAM_DATA, team_score_for_request

OUTPUT_DIR = Path("data")

BASE_REQUESTS = [
    {"id": "SIM-001", "reporter": "Simulasyon saha 1", "latitude": 37.0742, "longitude": 37.3385, "people_affected": 85, "injured_people": 12, "urgency": 5, "needs": ["medical", "water"]},
    {"id": "SIM-002", "reporter": "Simulasyon saha 2", "latitude": 37.0815, "longitude": 37.346, "people_affected": 140, "injured_people": 4, "urgency": 4, "needs": ["food", "shelter"]},
    {"id": "SIM-003", "reporter": "Simulasyon saha 3", "latitude": 37.0685, "longitude": 37.329, "people_affected": 35, "injured_people": 0, "urgency": 2, "needs": ["blanket"]},
]


def build_requests():
    requests = []
    for repeat in range(4):
        for base in BASE_REQUESTS:
            request = dict(base)
            request["id"] = f"SIM-{len(requests) + 1:03d}"
            request["people_affected"] += repeat * 8
            request["injured_people"] += repeat % 2
            request["urgency"] = min(5, request["urgency"] + (1 if repeat == 3 else 0))
            request["observed_priority"] = round(
                request["people_affected"] * 0.55
                + request["injured_people"] * 2.5
                + request["urgency"] * 9
                + len(request["needs"]) * 7,
                2,
            )
            requests.append(request)
    return requests


def build_outcomes(requests):
    outcomes = []
    for index, request in enumerate(requests):
        team = TEAM_DATA[index % len(TEAM_DATA)]
        outcomes.append({
            "request_id": request["id"],
            "team_id": team["id"],
            "team_success": True,
            "intervention_minutes": 30 + index * 3,
            "rescued_people": min(request["people_affected"], 5 + index),
            "resolved": index % 4 != 0,
            "assignment_quality": round(team_score_for_request(team, request), 2),
        })
    return outcomes


def main():
    requests = build_requests()
    outcomes = build_outcomes(requests)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "simulated_requests.json").write_text(json.dumps({"dataset": "synthetic_simulation", "requests": [{k: v for k, v in item.items() if k != "observed_priority"} for item in requests]}, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "simulated_priority_training.json").write_text(json.dumps({"label_source": "synthetic_simulation", "label_status": "not_real_field_data", "requests": requests}, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "simulated_team_outcomes.json").write_text(json.dumps({"label_source": "synthetic_simulation", "label_status": "not_real_field_data", "outcomes": outcomes}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(requests)} simulated requests and {len(outcomes)} simulated outcomes")


if __name__ == "__main__":
    main()
