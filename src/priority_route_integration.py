import json
from pathlib import Path

import networkx as nx

from src.apply_damage_to_route import apply_damage, closest_node
from src.data_store import fetch_ranked_requests, save_ranked_requests

GRAPH_PATH = Path("data/real_damage_road_network.graphml")
DAMAGE_PATH = Path("results/damaged_roads.json")
REQUESTS_PATH = Path("data/emergency_requests.json")
PRIORITY_PATH = Path("results/rescue_priority_ranked.json")
OUTPUT_PATH = Path("results/priority_route_result.json")
MAP_PATH = Path("results/priority_route_map.html")
DEFAULT_DESTINATION = (37.09, 37.35)


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_ranked_requests():
    ranked = fetch_ranked_requests()
    if ranked:
        return ranked

    if PRIORITY_PATH.exists():
        data = load_json(PRIORITY_PATH)
        requests = data.get("requests", [])
        if requests:
            save_ranked_requests(requests)
            return requests

    data = load_json(REQUESTS_PATH)
    requests = data.get("requests", [])
    ranked = []
    for request in requests:
        score = 0.0
        score += float(request.get("people_affected", 0) or 0) * 0.6
        score += float(request.get("injured_people", 0) or 0) * 2.2
        score += float(request.get("urgency", 0) or 0) * 10
        needs = request.get("needs", []) or []
        for need in needs:
            need_lower = str(need).lower()
            if need_lower in {"medical", "ambulance", "hospital"}:
                score += 2.5 * 6
            elif need_lower in {"water", "food", "shelter", "rescue"}:
                score += 1.5 * 6
            else:
                score += 1.0 * 6
        ranked.append({**request, "priority_score": round(score, 2)})
    ranked.sort(key=lambda item: item["priority_score"], reverse=True)
    save_ranked_requests(ranked)
    return ranked


def choose_top_request():
    ranked = load_ranked_requests()
    if not ranked:
        raise ValueError("No emergency requests found.")
    return ranked[0]


def build_priority_route(start_lon, start_lat, end_lon, end_lat):
    graph = nx.read_graphml(str(GRAPH_PATH))
    for _, _, _, data in graph.edges(keys=True, data=True):
        data["length"] = float(data.get("length", 1.0))

    damage_report = load_json(DAMAGE_PATH)
    damaged_edges, unmatched_roads = apply_damage(graph, damage_report.get("blocked_roads", []), 1.0)

    start_node = closest_node(graph, (start_lon, start_lat))
    end_node = closest_node(graph, (end_lon, end_lat))
    route = nx.shortest_path(graph, start_node, end_node, weight="length")
    distance = nx.shortest_path_length(graph, start_node, end_node, weight="length")
    coordinates = [
        [float(graph.nodes[node]["x"]), float(graph.nodes[node]["y"])]
        for node in route
    ]

    return {
        "start": [start_lon, start_lat],
        "end": [end_lon, end_lat],
        "route_nodes": len(route),
        "distance_m": round(float(distance), 1),
        "coordinates": coordinates,
        "damaged_edges_removed": len(damaged_edges),
        "unmatched_roads": len(unmatched_roads),
    }


def generate_map_html(route_result, request):
    html = f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>AI-DLRC Öncelikli Rota</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    html, body, #map {{ height: 100%; margin: 0; }}
    body {{ font-family: Arial, sans-serif; }}
    .panel {{ position: absolute; z-index: 1000; left: 20px; top: 20px; background: rgba(255,255,255,0.95); padding: 16px 18px; border-radius: 10px; box-shadow: 0 8px 18px rgba(0,0,0,0.15); max-width: 320px; }}
    .title {{ margin: 0 0 8px; font-size: 20px; }}
    .meta {{ margin: 0; color: #444; line-height: 1.5; }}
    .badge {{ display: inline-block; padding: 4px 8px; border-radius: 12px; margin-top: 10px; background: #0c7462; color: white; font-weight: bold; }}
  </style>
</head>
<body>
  <div class="panel">
    <h1 class="title">Öncelikli acil rota</h1>
    <p class="meta"><strong>Talep ID:</strong> {request['id']}<br>
    <strong>Öncelik skoru:</strong> {request.get('priority_score', 0)}<br>
    <strong>Mesafe:</strong> {(route_result['distance_m'] / 1000):.2f} km<br>
    <strong>Yol sayısı:</strong> {route_result['route_nodes']}</p>
    <div class="badge">En yüksek öncelikli çağrı</div>
  </div>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const map = L.map('map').setView([37.08, 37.34], 13);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' }}).addTo(map);
    const route = {json.dumps(route_result['coordinates'])};
    const safeRoute = L.polyline(route.map(([lon, lat]) => [lat, lon]), {{ color: '#0c7462', weight: 6, opacity: 0.95 }}).addTo(map);
    L.circleMarker([{request['latitude']}, {request['longitude']}], {{ radius: 9, color: '#d65a4a', fillColor: '#d65a4a', fillOpacity: 1 }}).addTo(map).bindPopup('Acil çağrı: {request['id']}');
    L.circleMarker([37.09, 37.35], {{ radius: 8, color: '#2b77c4', fillColor: '#2b77c4', fillOpacity: 1 }}).addTo(map).bindPopup('Yardım merkezi / hedef');
    map.fitBounds(safeRoute.getBounds().pad(0.2));
  </script>
</body>
</html>
"""
    return html


def main():
    top_request = choose_top_request()
    destination = DEFAULT_DESTINATION
    route_result = build_priority_route(
        float(top_request.get("longitude", destination[1])),
        float(top_request.get("latitude", destination[0])),
        float(destination[1]),
        float(destination[0]),
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump({"request": top_request, "route": route_result}, file, indent=2, ensure_ascii=False)

    map_html = generate_map_html(route_result, top_request)
    MAP_PATH.write_text(map_html, encoding="utf-8")

    print(f"Top request: {top_request['id']} | priority={top_request.get('priority_score', 0)}")
    print(f"Route distance: {route_result['distance_m']:.1f} metres")
    print(f"Saved route result: {OUTPUT_PATH}")
    print(f"Saved map: {MAP_PATH}")


if __name__ == "__main__":
    main()
