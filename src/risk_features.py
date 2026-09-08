import json
import math
from pathlib import Path

RISK_PATH = Path("data/turkey_syria_earthquake_risk.json")


def load_risk_events(path=RISK_PATH):
    path = Path(path)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def distance_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(value))


def nearest_risk_features(request, events=None):
    events = load_risk_events() if events is None else events
    if not events:
        return {"nearest_distance_km": 0.0, "magnitude": 0.0, "depth_km": 0.0, "risk_score": 0.0}

    latitude = float(request.get("latitude", 0) or 0)
    longitude = float(request.get("longitude", 0) or 0)
    nearest = min(
        events,
        key=lambda event: distance_km(
            latitude,
            longitude,
            float(event["latitude"]),
            float(event["longitude"]),
        ),
    )
    return {
        "nearest_distance_km": round(distance_km(latitude, longitude, float(nearest["latitude"]), float(nearest["longitude"])), 2),
        "magnitude": float(nearest.get("magnitude", 0) or 0),
        "depth_km": float(nearest.get("depth", 0) or 0),
        "risk_score": float(nearest.get("risk_score", 0) or 0),
    }
