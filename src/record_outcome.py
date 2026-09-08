import argparse
import json
from pathlib import Path

from src.data_quality import validate_all, validate_priority_training, validate_team_outcomes

PRIORITY_PATH = Path("data/priority_training.json")
TEAM_PATH = Path("data/team_outcomes.json")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def record_priority(path, request_id, observed_priority):
    data = read_json(path)
    for request in data.setdefault("requests", []):
        if request.get("id") == request_id:
            request["observed_priority"] = float(observed_priority)
            write_json(path, data)
            errors = validate_priority_training(path)
            if errors:
                raise ValueError("Invalid priority data: " + "; ".join(errors))
            return
    raise ValueError(f"Request not found: {request_id}")


def record_team_outcome(path, request_id, team_id, team_success, intervention_minutes, rescued_people, resolved):
    data = read_json(path)
    outcome = {
        "request_id": request_id,
        "team_id": team_id,
        "team_success": team_success,
        "intervention_minutes": float(intervention_minutes),
        "rescued_people": float(rescued_people),
        "resolved": resolved,
    }
    outcomes = data.setdefault("outcomes", [])
    outcomes[:] = [
        item for item in outcomes
        if not (item.get("request_id") == request_id and item.get("team_id") == team_id)
    ]
    outcomes.append(outcome)
    write_json(path, data)
    errors = validate_team_outcomes(path)
    if errors:
        raise ValueError("Invalid team outcome data: " + "; ".join(errors))


def main():
    parser = argparse.ArgumentParser(description="Record verified AI-DLRC field outcomes")
    parser.add_argument("--priority", type=float, help="Verified priority for a request")
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--team-id")
    parser.add_argument("--intervention-minutes", type=float)
    parser.add_argument("--rescued-people", type=float)
    parser.add_argument("--team-success", action="store_true")
    parser.add_argument("--resolved", action="store_true")
    args = parser.parse_args()

    if args.priority is not None:
        record_priority(PRIORITY_PATH, args.request_id, args.priority)
        print(f"Saved priority outcome for {args.request_id}")

    team_fields = (args.team_id, args.intervention_minutes, args.rescued_people)
    if any(value is not None for value in team_fields):
        if None in team_fields:
            parser.error("--team-id, --intervention-minutes, and --rescued-people are required together")
        record_team_outcome(
            TEAM_PATH,
            args.request_id,
            args.team_id,
            args.team_success,
            args.intervention_minutes,
            args.rescued_people,
            args.resolved,
        )
        print(f"Saved team outcome for {args.request_id}")

    validate_all(PRIORITY_PATH, TEAM_PATH)


if __name__ == "__main__":
    main()
