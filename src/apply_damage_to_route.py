import argparse
import json
import math
from pathlib import Path

import networkx as nx

DEFAULT_GRAPH = Path("data/real_earthquake_road_network.graphml")
DEFAULT_DAMAGE_REPORT = Path("results/damaged_roads.json")
DEFAULT_OUTPUT_GRAPH = Path("results/road_network_without_damaged_edges.graphml")
DEFAULT_ROUTE_OUTPUT = Path("results/route_result.json")


def load_damage_report(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def node_position(graph, node):
    data = graph.nodes[node]
    return float(data["x"]), float(data["y"])


def point_distance(first, second):
    longitude_delta = (first[0] - second[0]) * 111.0
    latitude_delta = (first[1] - second[1]) * 111.0
    return math.hypot(longitude_delta, latitude_delta)


def graph_bounds(graph):
    positions = [node_position(graph, node) for node in graph.nodes]
    longitudes, latitudes = zip(*positions)
    return min(longitudes), max(longitudes), min(latitudes), max(latitudes)


def closest_node(graph, point):
    return min(
        graph.nodes,
        key=lambda node: point_distance(node_position(graph, node), point),
    )


def closest_edge(graph, point):
    nearest_node = closest_node(graph, point)
    candidates = []
    for start, end, key in graph.edges(nearest_node, keys=True):
        start_position = node_position(graph, start)
        end_position = node_position(graph, end)
        midpoint = (
            (start_position[0] + end_position[0]) / 2,
            (start_position[1] + end_position[1]) / 2,
        )
        candidates.append(
            (point_distance(midpoint, point), start, end, key)
        )
    return min(candidates)


def apply_damage(graph, damaged_roads, max_match_distance_km):
    damaged_edges = []
    unmatched_roads = []

    for road in damaged_roads:
        coordinates = road.get("coordinates", [])
        if not coordinates:
            unmatched_roads.append(road)
            continue

        midpoint = (
            sum(point[0] for point in coordinates) / len(coordinates),
            sum(point[1] for point in coordinates) / len(coordinates),
        )
        distance, start, end, key = closest_edge(graph, midpoint)

        if distance > max_match_distance_km:
            unmatched_roads.append(road)
            continue

        damaged_edges.append(
            {
                "feature_id": road["feature_id"],
                "name": road["name"],
                "distance_km": round(distance, 3),
                "start": start,
                "end": end,
                "key": key,
            }
        )

    removed_edges = set()
    for edge in damaged_edges:
        edge_id = (edge["start"], edge["end"], edge["key"])
        if edge_id not in removed_edges:
            graph.remove_edge(*edge_id)
            removed_edges.add(edge_id)

    return damaged_edges, unmatched_roads


def main():
    parser = argparse.ArgumentParser(
        description="Remove Copernicus-damaged roads from a GraphML network."
    )
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--damage-report", type=Path, default=DEFAULT_DAMAGE_REPORT)
    parser.add_argument("--output-graph", type=Path, default=DEFAULT_OUTPUT_GRAPH)
    parser.add_argument("--route-output", type=Path, default=DEFAULT_ROUTE_OUTPUT)
    parser.add_argument(
        "--max-match-distance-km",
        type=float,
        default=1.0,
        help="Maximum distance allowed between a damaged road and a graph edge.",
    )
    parser.add_argument("--start-lat", type=float)
    parser.add_argument("--start-lon", type=float)
    parser.add_argument("--end-lat", type=float)
    parser.add_argument("--end-lon", type=float)
    args = parser.parse_args()

    graph = nx.read_graphml(args.graph)
    for _, _, _, data in graph.edges(keys=True, data=True):
        data["length"] = float(data.get("length", 1.0))

    report = load_damage_report(args.damage_report)
    damaged_edges, unmatched_roads = apply_damage(
        graph,
        report.get("blocked_roads", []),
        args.max_match_distance_km,
    )

    if not damaged_edges:
        bounds = graph_bounds(graph)
        raise RuntimeError(
            "No damaged road matched the graph. "
            f"Graph bounds: lon {bounds[0]:.4f}-{bounds[1]:.4f}, "
            f"lat {bounds[2]:.4f}-{bounds[3]:.4f}. "
            "Use a road network covering the same AOI as the damage report."
        )

    print(f"Matched damaged graph edges: {len(damaged_edges)}")
    print(f"Unmatched damaged roads: {len(unmatched_roads)}")

    if all(value is not None for value in (
        args.start_lat,
        args.start_lon,
        args.end_lat,
        args.end_lon,
    )):
        start = closest_node(graph, (args.start_lon, args.start_lat))
        end = closest_node(graph, (args.end_lon, args.end_lat))
        route = nx.shortest_path(graph, start, end, weight="length")
        distance = nx.shortest_path_length(graph, start, end, weight="length")
        route_coordinates = [
            [float(graph.nodes[node]["x"]), float(graph.nodes[node]["y"])]
            for node in route
        ]
        args.route_output.parent.mkdir(parents=True, exist_ok=True)
        with args.route_output.open("w", encoding="utf-8") as file:
            json.dump(
                {
                    "start": [args.start_lon, args.start_lat],
                    "end": [args.end_lon, args.end_lat],
                    "route_nodes": len(route),
                    "distance_m": round(float(distance), 1),
                    "coordinates": route_coordinates,
                },
                file,
                indent=2,
            )
        print(f"Route nodes: {len(route)}")
        print(f"Route distance: {float(distance):.1f} metres")
        print(f"Route saved to: {args.route_output}")
    else:
        args.output_graph.parent.mkdir(parents=True, exist_ok=True)
        nx.write_graphml(graph, args.output_graph)
        print(f"Safe graph saved to: {args.output_graph}")
        print("No route requested; damaged edges were removed successfully.")


if __name__ == "__main__":
    main()
