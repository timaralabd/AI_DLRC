import math
from typing import Dict, List

TEAM_DATA = [
    {
        "id": "TEAM-ALPHA",
        "name": "Medikal Müdahale 1",
        "team_type": "medical",
        "location": {"latitude": 37.102, "longitude": 37.362},
        "capacity": 20,
        "status": "ready",
    },
    {
        "id": "TEAM-BETA",
        "name": "Arama Kurtarma 1",
        "team_type": "rescue",
        "location": {"latitude": 37.128, "longitude": 37.346},
        "capacity": 30,
        "status": "ready",
    },
    {
        "id": "TEAM-GAMMA",
        "name": "Yardım Lojistiği 1",
        "team_type": "logistics",
        "location": {"latitude": 37.120, "longitude": 37.318},
        "capacity": 40,
        "status": "ready",
    },
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def team_score_for_request(team: Dict, request: Dict) -> float:
    request_lat = float(request.get("latitude", 0) or 0)
    request_lon = float(request.get("longitude", 0) or 0)
    team_lat = float(team["location"]["latitude"])
    team_lon = float(team["location"]["longitude"])
    distance_km = haversine_km(request_lat, request_lon, team_lat, team_lon)

    request_needs = [str(item).lower() for item in request.get("needs", []) or []]
    need_match = 0.0
    if team["team_type"] == "medical" and any(n in request_needs for n in {"medical", "hospital", "ambulance"}):
        need_match = 3.0
    elif team["team_type"] == "rescue" and any(n in request_needs for n in {"rescue", "shelter", "food"}):
        need_match = 2.5
    elif team["team_type"] == "logistics" and any(n in request_needs for n in {"water", "food", "blanket", "shelter"}):
        need_match = 2.0

    urgency = float(request.get("urgency", 0) or 0)
    people = float(request.get("people_affected", 0) or 0)
    injured = float(request.get("injured_people", 0) or 0)

    score = (
        need_match * 25
        + urgency * 8
        + people * 0.12
        + injured * 0.7
        - distance_km * 0.8
    )
    return score


def assign_team_for_request(request: Dict, teams: List[Dict] | None = None) -> Dict:
    ranked = []
    candidate_teams = teams if teams is not None else TEAM_DATA
    if not candidate_teams:
        raise ValueError("No available teams")
    for team in candidate_teams:
        ranked.append({
            "team": team,
            "score": team_score_for_request(team, request),
            "distance_km": round(
                haversine_km(
                    float(request.get("latitude", 0) or 0),
                    float(request.get("longitude", 0) or 0),
                    float(team["location"]["latitude"]),
                    float(team["location"]["longitude"]),
                ),
                2,
            ),
        })

    ranked.sort(key=lambda item: item["score"], reverse=True)
    best = ranked[0]
    return {
        "team_id": best["team"]["id"],
        "team_name": best["team"]["name"],
        "team_type": best["team"]["team_type"],
        "distance_km": best["distance_km"],
        "capacity": best["team"]["capacity"],
        "status": best["team"]["status"],
        "score": round(best["score"], 2),
    }


def get_all_teams() -> List[Dict]:
    return TEAM_DATA
