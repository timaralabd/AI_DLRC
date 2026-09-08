import argparse
import json
from pathlib import Path

DEFAULT_REQUESTS_PATH = Path("data/emergency_requests.json")
DEFAULT_OUTPUT_PATH = Path("results/rescue_priority_ranked.json")


def calculate_need_weight(needs):
    weight = 0.0
    for need in needs or []:
        need_lower = str(need).lower()
        if need_lower in {"medical", "ambulance", "hospital"}:
            weight += 2.5
        elif need_lower in {"water", "food", "shelter", "rescue"}:
            weight += 1.5
        elif need_lower in {"blanket", "warm", "sanitation"}:
            weight += 1.0
        else:
            weight += 1.0
    return weight


def calculate_priority(request):
    people_affected = float(request.get("people_affected", 0) or 0)
    injured = float(request.get("injured_people", 0) or 0)
    urgency = float(request.get("urgency", 0) or 0)
    need_weight = calculate_need_weight(request.get("needs", []))

    score = (
        people_affected * 0.6
        + injured * 2.2
        + urgency * 10
        + need_weight * 6
    )

    return round(score, 2)


def rank_requests(requests):
    requests = list(requests)
    try:
        from src.ai_priority import predict_priority
        ai_scores, _ = predict_priority(requests)
    except (ImportError, ValueError):
        ai_scores = [calculate_priority(request) for request in requests]

    ranked = []
    for request, priority_score in zip(requests, ai_scores):
        ranked.append({
            "id": request.get("id", "UNKNOWN"),
            "reporter": request.get("reporter", "Unknown"),
            "latitude": request.get("latitude"),
            "longitude": request.get("longitude"),
            "people_affected": request.get("people_affected", 0),
            "injured_people": request.get("injured_people", 0),
            "urgency": request.get("urgency", 0),
            "needs": request.get("needs", []),
            "status": request.get("status", "waiting"),
            "priority_score": priority_score,
            "message": request.get("message", ""),
        })

    ranked.sort(key=lambda item: item["priority_score"], reverse=True)
    return ranked


def load_requests(path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data.get("requests", [])


def main():
    parser = argparse.ArgumentParser(description="Rank emergency requests by rescue priority.")
    parser.add_argument("--input", type=Path, default=DEFAULT_REQUESTS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    requests = load_requests(args.input)
    ranked = rank_requests(requests)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump({"requests": ranked}, file, indent=2, ensure_ascii=False)

    print("Rescue priority ranking:")
    for rank, item in enumerate(ranked, start=1):
        print(f"{rank}. {item['id']} -> score {item['priority_score']} ({item['reporter']})")

    print(f"\nSaved ranked output to: {args.output}")


if __name__ == "__main__":
    main()
