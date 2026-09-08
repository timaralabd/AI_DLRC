import json
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from src.rescue_priority import calculate_priority
from src.risk_features import nearest_risk_features

MODEL_PATH = Path("models/priority_model.joblib")

NEED_FEATURES = ("medical", "water", "food", "shelter", "rescue", "blanket", "sanitation")
FEATURE_NAMES = (
    "people_affected",
    "injured_people",
    "urgency",
    "latitude",
    "longitude",
    *[f"need_{need}" for need in NEED_FEATURES],
    "nearest_distance_km",
    "nearest_magnitude",
    "nearest_depth_km",
    "nearest_risk_score",
)


def request_features(request):
    needs = {str(need).lower() for need in request.get("needs", []) or []}
    risk = nearest_risk_features(request)
    return [
        float(request.get("people_affected", 0) or 0),
        float(request.get("injured_people", 0) or 0),
        float(request.get("urgency", 0) or 0),
        float(request.get("latitude", 0) or 0),
        float(request.get("longitude", 0) or 0),
        *[1.0 if need in needs else 0.0 for need in NEED_FEATURES],
        risk["nearest_distance_km"],
        risk["magnitude"],
        risk["depth_km"],
        risk["risk_score"],
    ]


def train_priority_model(requests, labels=None, model_path=MODEL_PATH):
    if len(requests) < 2:
        raise ValueError("At least two requests are required to train the priority model")

    model = RandomForestRegressor(n_estimators=64, random_state=42, min_samples_leaf=1)
    features = [request_features(request) for request in requests]
    labels = [calculate_priority(request) for request in requests] if labels is None else labels
    if len(labels) != len(requests):
        raise ValueError("The number of labels must match the number of requests")
    model.fit(features, labels)

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model_type": "RandomForestRegressor",
        "feature_names": list(FEATURE_NAMES),
        "training_samples": len(requests),
        "training_labels": labels,
    }
    joblib.dump(model, model_path)
    model_path.with_suffix(".json").write_text(json.dumps(payload), encoding="utf-8")
    return model, payload


def load_priority_model(model_path=MODEL_PATH):
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Priority model not found: {model_path}")
    return joblib.load(model_path)


def train_from_labeled_data(path, model_path=MODEL_PATH):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    requests = []
    labels = []
    for item in data.get("requests", []):
        request = dict(item)
        labels.append(float(request.pop("observed_priority")))
        requests.append(request)
    return train_priority_model(requests, labels=labels, model_path=model_path)


def evaluate_priority_model(model, requests, labels):
    predictions = model.predict([request_features(request) for request in requests])
    return {
        "mae": round(float(mean_absolute_error(labels, predictions)), 2),
        "r2": round(float(r2_score(labels, predictions)), 2),
    }


def ranking_accuracy(actual, predicted):
    pairs = 0
    correct = 0
    for left in range(len(actual)):
        for right in range(left + 1, len(actual)):
            actual_order = actual[left] - actual[right]
            predicted_order = predicted[left] - predicted[right]
            if actual_order == 0:
                continue
            pairs += 1
            if actual_order * predicted_order > 0:
                correct += 1
    return round(correct / pairs, 2) if pairs else None


def evaluate_labeled_dataset(requests, labels, test_size=0.25):
    if len(requests) < 4:
        return {
            "status": "insufficient_test_data",
            "message": "At least four labeled requests are required for a holdout test",
            "samples": len(requests),
        }

    train_requests, test_requests, train_labels, test_labels = train_test_split(
        requests,
        labels,
        test_size=test_size,
        random_state=42,
    )
    model = RandomForestRegressor(n_estimators=64, random_state=42, min_samples_leaf=1)
    model.fit([request_features(item) for item in train_requests], train_labels)
    predictions = model.predict([request_features(item) for item in test_requests])
    return {
        "status": "evaluated",
        "train_samples": len(train_requests),
        "test_samples": len(test_requests),
        "mae": round(float(mean_absolute_error(test_labels, predictions)), 2),
        "r2": round(float(r2_score(test_labels, predictions)), 2) if len(test_labels) > 1 else None,
        "ranking_accuracy": ranking_accuracy(test_labels, predictions),
    }


def predict_priority(requests):
    model, metadata = train_priority_model(requests)
    predictions = model.predict([request_features(request) for request in requests])
    return [round(float(score), 2) for score in predictions], metadata


def run_priority_pipeline(input_path, model_path=MODEL_PATH, ranked_output=Path("results/ai_priority_ranked.json"), training_path=None):
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    requests = data.get("requests", [])
    labels = None
    if training_path and Path(training_path).exists():
        training_data = json.loads(Path(training_path).read_text(encoding="utf-8"))
        labels_by_id = {
            item["id"]: float(item["observed_priority"])
            for item in training_data.get("requests", [])
        }
        if all(request.get("id") in labels_by_id for request in requests):
            labels = [labels_by_id[request["id"]] for request in requests]
    model, metadata = train_priority_model(requests, labels=labels, model_path=model_path)
    if labels is not None:
        metadata["evaluation"] = evaluate_labeled_dataset(requests, labels)
    scores = [
        round(float(score), 2)
        for score in model.predict([request_features(request) for request in requests])
    ]
    ranked = [
        {**request, "ai_priority_score": score}
        for request, score in zip(requests, scores)
    ]
    ranked.sort(key=lambda request: request["ai_priority_score"], reverse=True)
    ranked_output = Path(ranked_output)
    ranked_output.parent.mkdir(parents=True, exist_ok=True)
    ranked_output.write_text(
        json.dumps({"requests": ranked, "model": metadata}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return metadata, ranked


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Train the AI emergency priority model.")
    parser.add_argument("--input", type=Path, default=Path("data/emergency_requests.json"))
    parser.add_argument("--output", type=Path, default=MODEL_PATH)
    parser.add_argument(
        "--ranked-output",
        type=Path,
        default=Path("results/ai_priority_ranked.json"),
    )
    args = parser.parse_args()

    metadata, _ = run_priority_pipeline(args.input, args.output, args.ranked_output)
    print(f"Model trained: {metadata['training_samples']} requests")
    print(f"Saved model: {args.output}")
    print(f"Saved ranked requests: {args.ranked_output}")


if __name__ == "__main__":
    main()
