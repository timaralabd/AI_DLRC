import json
from pathlib import Path

import osmnx as ox

DAMAGE_REPORT = Path("results/damaged_roads.json")
OUTPUT_FILE = Path("data/real_damage_road_network.graphml")
SEARCH_DISTANCE_METERS = 10_000
OVERPASS_ENDPOINT = "https://overpass.kumi.systems/api"


def damage_center(report):
    coordinates = [
        coordinate
        for road in report["blocked_roads"]
        for coordinate in road["coordinates"]
    ]
    if not coordinates:
        raise ValueError("The damage report contains no road coordinates.")

    longitude = sum(point[0] for point in coordinates) / len(coordinates)
    latitude = sum(point[1] for point in coordinates) / len(coordinates)
    return latitude, longitude


def main():
    with DAMAGE_REPORT.open("r", encoding="utf-8") as file:
        report = json.load(file)

    latitude, longitude = damage_center(report)
    print(f"Downloading roads near latitude={latitude:.6f}, longitude={longitude:.6f}")

    ox.settings.overpass_endpoint = OVERPASS_ENDPOINT
    ox.settings.requests_timeout = 180

    graph = ox.graph.graph_from_point(
        (latitude, longitude),
        dist=SEARCH_DISTANCE_METERS,
        network_type="drive",
        simplify=True,
    )
    ox.io.save_graphml(graph, filepath=OUTPUT_FILE)

    print(f"Nodes: {len(graph.nodes)}")
    print(f"Edges: {len(graph.edges)}")
    print(f"Road network saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
