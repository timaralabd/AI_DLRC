import json
from pathlib import Path

PRIORITY_FIELDS = ("id", "observed_priority")
TEAM_OUTCOME_FIELDS = (
    "request_id",
    "team_id",
    "team_success",
    "intervention_minutes",
    "rescued_people",
    "resolved",
)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_priority_training(path):
    data = load_json(path)
    errors = []
    records = data.get("requests", [])
    for index, record in enumerate(records):
        missing = [field for field in PRIORITY_FIELDS if field not in record]
        if missing:
            errors.append(f"requests[{index}] missing: {', '.join(missing)}")
        if "observed_priority" in record:
            try:
                value = float(record["observed_priority"])
                if value < 0:
                    errors.append(f"requests[{index}].observed_priority must be non-negative")
            except (TypeError, ValueError):
                errors.append(f"requests[{index}].observed_priority must be numeric")
    return errors


def validate_team_outcomes(path):
    data = load_json(path)
    errors = []
    records = data.get("outcomes", [])
    for index, record in enumerate(records):
        missing = [field for field in TEAM_OUTCOME_FIELDS if field not in record]
        if missing:
            errors.append(f"outcomes[{index}] missing: {', '.join(missing)}")
        if "intervention_minutes" in record:
            try:
                if float(record["intervention_minutes"]) < 0:
                    errors.append(f"outcomes[{index}].intervention_minutes must be non-negative")
            except (TypeError, ValueError):
                errors.append(f"outcomes[{index}].intervention_minutes must be numeric")
        if "rescued_people" in record:
            try:
                if float(record["rescued_people"]) < 0:
                    errors.append(f"outcomes[{index}].rescued_people must be non-negative")
            except (TypeError, ValueError):
                errors.append(f"outcomes[{index}].rescued_people must be numeric")
    return errors


def validate_all(priority_path, team_path):
    errors = validate_priority_training(priority_path)
    errors.extend(validate_team_outcomes(team_path))
    if errors:
        raise ValueError("Invalid labeled data:\n- " + "\n- ".join(errors))
    return True
