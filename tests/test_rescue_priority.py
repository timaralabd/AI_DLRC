import json
import math
from pathlib import Path
import tempfile

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_store import (
    fetch_operation_log,
    fetch_ranked_requests,
    fetch_dispatch_assignments,
    fetch_teams,
    save_request,
    save_dispatch_assignments,
    save_teams,
    update_request_status,
    update_team_status,
)
from src.rescue_priority import calculate_priority, rank_requests
from src.ai_priority import evaluate_labeled_dataset, load_priority_model, predict_priority, train_from_labeled_data
from src.ai_dispatch import assign_team_ai, evaluate_team_outcomes, rank_team_assignments, train_team_model
from src.data_quality import validate_all, validate_priority_training, validate_team_outcomes
from src.record_outcome import record_priority, record_team_outcome
from src.risk_features import nearest_risk_features


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
    save_request({
        "id": "REQ-TEST-1",
        "reporter": "Test coordinator",
        "latitude": 37.1,
        "longitude": 37.3,
        "people_affected": 10,
        "injured_people": 1,
        "urgency": 4,
        "needs": ["medical"],
        "status": "waiting",
    })
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


def test_ai_priority_model_trains_and_predicts():
    requests = [
        {"people_affected": 10, "injured_people": 0, "urgency": 1, "needs": ["blanket"]},
        {"people_affected": 100, "injured_people": 12, "urgency": 5, "needs": ["medical", "water"]},
    ]

    scores, metadata = predict_priority(requests)

    assert metadata["model_type"] == "RandomForestRegressor"
    assert metadata["training_samples"] == 2
    assert len(scores) == 2
    assert scores[1] > scores[0]


def test_ai_priority_model_can_be_retrained_from_observed_labels():
    with tempfile.TemporaryDirectory() as directory:
        training_path = Path(directory) / "training.json"
        model_path = Path(directory) / "priority_model.joblib"
        training_path.write_text(json.dumps({"requests": [
            {"people_affected": 10, "urgency": 1, "needs": [], "observed_priority": 15},
            {"people_affected": 100, "urgency": 5, "needs": ["medical"], "observed_priority": 95},
        ]}), encoding="utf-8")

        _, metadata = train_from_labeled_data(training_path, model_path=model_path)

        assert metadata["training_labels"] == [15.0, 95.0]
        assert load_priority_model(model_path).n_estimators == 64


def test_ai_team_model_trains_and_assigns_team():
    request = {
        "people_affected": 80,
        "injured_people": 8,
        "urgency": 5,
        "needs": ["medical"],
    }
    model, metadata = train_team_model([request])
    assignment = assign_team_ai(request)

    assert model.n_estimators == 64
    assert metadata["training_pairs"] == 3
    assert assignment["team"]["id"]
    assert math.isfinite(assignment["ai_assignment_score"])


def test_ai_team_model_ranks_all_requests():
    requests = [
        {"id": "REQ-A", "people_affected": 10, "injured_people": 1, "urgency": 2, "needs": ["medical"]},
        {"id": "REQ-B", "people_affected": 50, "injured_people": 5, "urgency": 4, "needs": ["water"]},
    ]

    assignments, metadata = rank_team_assignments(requests)

    assert len(assignments) == 2
    assert all(item["team_id"] for item in assignments)
    assert metadata["training_pairs"] == 6


def test_evaluations_report_insufficient_real_data_honestly():
    request = {"people_affected": 10, "injured_people": 1, "urgency": 2, "needs": []}

    priority_evaluation = evaluate_labeled_dataset([request] * 3, [10, 20, 30])
    team_evaluation = evaluate_team_outcomes([])

    assert priority_evaluation["status"] == "insufficient_test_data"
    assert team_evaluation["status"] == "insufficient_test_data"


def test_labeled_data_validation_accepts_current_schemas():
    assert validate_priority_training("data/priority_training.json") == []
    assert validate_team_outcomes("data/team_outcomes.json") == []
    assert validate_all("data/priority_training.json", "data/team_outcomes.json") is True


def test_labeled_data_validation_rejects_invalid_outcome(tmp_path):
    invalid = tmp_path / "team_outcomes.json"
    invalid.write_text(json.dumps({"outcomes": [{
        "request_id": "REQ-001",
        "team_id": "TEAM-ALPHA",
        "team_success": True,
        "intervention_minutes": -1,
        "rescued_people": 2,
        "resolved": True,
    }]}), encoding="utf-8")

    assert "non-negative" in "\n".join(validate_team_outcomes(invalid))


def test_record_outcome_updates_priority_and_team_files(tmp_path):
    priority_path = tmp_path / "priority_training.json"
    team_path = tmp_path / "team_outcomes.json"
    priority_path.write_text(json.dumps({"requests": [{"id": "REQ-1"}]}), encoding="utf-8")
    team_path.write_text(json.dumps({"outcomes": []}), encoding="utf-8")

    record_priority(priority_path, "REQ-1", 74)
    record_team_outcome(team_path, "REQ-1", "TEAM-ALPHA", True, 40, 12, True)

    priority = json.loads(priority_path.read_text(encoding="utf-8"))
    outcomes = json.loads(team_path.read_text(encoding="utf-8"))
    assert priority["requests"][0]["observed_priority"] == 74
    assert outcomes["outcomes"][0]["intervention_minutes"] == 40


def test_request_risk_features_use_nearest_earthquake():
    features = nearest_risk_features(
        {"latitude": 38.01, "longitude": 37.2},
        [{"latitude": 38.0, "longitude": 37.2, "magnitude": 7.0, "depth": 8, "risk_score": 98}],
    )

    assert features["nearest_distance_km"] < 2
    assert features["magnitude"] == 7.0
    assert features["risk_score"] == 98
