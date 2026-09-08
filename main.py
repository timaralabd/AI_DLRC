import argparse
import json
from pathlib import Path

from src.ai_priority import run_priority_pipeline
from src.ai_dispatch import evaluate_team_outcomes, rank_team_assignments
from src.data_quality import validate_all


def main():
    parser = argparse.ArgumentParser(description="AI-DLRC afet karar destek sistemi")
    parser.add_argument("--input", type=Path, default=Path("data/emergency_requests.json"))
    parser.add_argument("--model", type=Path, default=Path("models/priority_model.joblib"))
    parser.add_argument("--training-data", type=Path, default=Path("data/priority_training.json"))
    parser.add_argument("--team-outcomes", type=Path, default=Path("data/team_outcomes.json"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/ai_priority_ranked.json"),
    )
    args = parser.parse_args()

    validate_all(args.training_data, args.team_outcomes)
    metadata, ranked = run_priority_pipeline(args.input, args.model, args.output, args.training_data)
    request_data = __import__("json").loads(args.input.read_text(encoding="utf-8"))
    assignments, team_metadata = rank_team_assignments(request_data["requests"])
    assignment_output = Path("results/ai_team_assignments.json")
    assignment_output.write_text(
        json.dumps(
            {"assignments": assignments, "model": team_metadata},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    team_outcome_evaluation = {"status": "not_run"}
    if args.team_outcomes.exists():
        outcomes = json.loads(args.team_outcomes.read_text(encoding="utf-8")).get("outcomes", [])
        team_outcome_evaluation = evaluate_team_outcomes(outcomes)
    evaluation_output = Path("results/model_evaluation.json")
    evaluation_output.write_text(
        json.dumps({
            "priority": metadata.get("evaluation", {"status": "not_run"}),
            "team": team_outcome_evaluation,
            "training_data": str(args.training_data),
            "team_outcomes": str(args.team_outcomes),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"AI-DLRC completed: {metadata['training_samples']} requests")
    print(f"Top request: {ranked[0]['id']} ({ranked[0]['ai_priority_score']})")
    print(f"Saved model: {args.model}")
    print(f"Saved report: {args.output}")
    print(f"Team model trained: {team_metadata['training_pairs']} request-team pairs")
    print(f"Team model MAE: {team_metadata['mae']}")
    print(f"Saved team assignments: {assignment_output}")
    print(f"Saved evaluation: {evaluation_output}")
    if "evaluation" in metadata:
        evaluation = metadata["evaluation"]
        print(f"Priority evaluation: {evaluation}")
    print(f"Team outcome evaluation: {team_outcome_evaluation}")


if __name__ == "__main__":
    main()