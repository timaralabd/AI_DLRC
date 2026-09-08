from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import r2_score

from src.dispatch_assignment import TEAM_DATA, team_score_for_request

MODEL_PATH = Path("models/team_assignment_model.joblib")
TEAM_TYPES = ("medical", "rescue", "logistics")


def pair_features(request, team):
    needs = {str(need).lower() for need in request.get("needs", []) or []}
    team_type = team.get("team_type", "")
    return [
        float(request.get("people_affected", 0) or 0),
        float(request.get("injured_people", 0) or 0),
        float(request.get("urgency", 0) or 0),
        float(team.get("capacity", 0) or 0),
        1.0 if team_type in TEAM_TYPES else 0.0,
        *[1.0 if need in needs and need_type == team_type else 0.0 for need_type in TEAM_TYPES for need in ("medical", "rescue", "water", "food", "shelter")],
    ]


def train_team_model(requests, teams=None, model_path=MODEL_PATH):
    teams = teams or TEAM_DATA
    pairs = [(request, team) for request in requests for team in teams]
    if len(pairs) < 2:
        raise ValueError("At least two request-team pairs are required")
    model = RandomForestRegressor(n_estimators=64, random_state=42, min_samples_leaf=1)
    features = [pair_features(request, team) for request, team in pairs]
    labels = [team_score_for_request(team, request) for request, team in pairs]
    model.fit(features, labels)
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    return model, {"model_type": "RandomForestRegressor", "training_pairs": len(pairs), "mae": round(mean_absolute_error(labels, model.predict(features)), 2)}


def outcome_score(outcome):
    """Convert verified field outcomes into a team-performance label."""
    resolved = 1.0 if outcome.get("resolved") else 0.0
    success = 1.0 if outcome.get("team_success") else 0.0
    rescued = float(outcome.get("rescued_people", 0) or 0)
    minutes = float(outcome.get("intervention_minutes", 0) or 0)
    return success * 50 + resolved * 30 + rescued * 2 - minutes * 0.1


def evaluate_team_outcomes(outcomes, teams=None):
    teams = teams or TEAM_DATA
    if len(outcomes) < 4:
        return {
            "status": "insufficient_test_data",
            "message": "At least four verified team outcomes are required",
            "samples": len(outcomes),
        }
    pairs = []
    labels = []
    for outcome in outcomes:
        team = next((item for item in teams if item["id"] == outcome.get("team_id")), None)
        if team is None:
            continue
        pairs.append(pair_features(outcome, team))
        labels.append(outcome_score(outcome))
    if len(pairs) < 4:
        return {"status": "insufficient_test_data", "samples": len(pairs)}
    model = RandomForestRegressor(n_estimators=64, random_state=42, min_samples_leaf=1)
    model.fit(pairs, labels)
    predictions = model.predict(pairs)
    return {
        "status": "evaluated",
        "samples": len(labels),
        "mae": round(float(mean_absolute_error(labels, predictions)), 2),
        "r2": round(float(r2_score(labels, predictions)), 2),
    }


def assign_team_ai(request, teams=None, model_path=MODEL_PATH, model=None):
    teams = teams or TEAM_DATA
    if model is None:
        model, _ = train_team_model([request], teams, model_path)
    ranked = sorted(
        ((model.predict([pair_features(request, team)])[0], team) for team in teams),
        key=lambda item: item[0],
        reverse=True,
    )
    score, team = ranked[0]
    return {"team": team, "ai_assignment_score": round(float(score), 2)}


def rank_team_assignments(requests, teams=None, model_path=MODEL_PATH):
    teams = teams or TEAM_DATA
    model, metadata = train_team_model(requests, teams, model_path)
    assignments = []
    for request in requests:
        assignment = assign_team_ai(request, teams, model=model)
        assignments.append({
            "request_id": request.get("id"),
            "team_id": assignment["team"]["id"],
            "team_name": assignment["team"]["name"],
            "team_type": assignment["team"]["team_type"],
            "ai_assignment_score": assignment["ai_assignment_score"],
        })
    return assignments, metadata
