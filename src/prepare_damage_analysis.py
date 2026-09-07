import argparse
import json
from collections import Counter
from pathlib import Path


DEFAULT_INPUT = Path(
    "data/damage/extracted/"
    "EMSR648_AOI01_GRA_MONIT01_transportationL_r1_v1.json"
)
DEFAULT_OUTPUT = Path("results/damaged_roads.json")
BLOCKING_DAMAGE_LEVELS = {"Damaged", "Destroyed", "Collapsed"}


def load_roads(input_file):
    with input_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError("Input file must be a GeoJSON FeatureCollection.")

    return data.get("features", [])


def build_damage_report(features):
    damage_counts = Counter()
    damaged_roads = []

    for index, feature in enumerate(features, start=1):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        damage_level = properties.get("damage_gra", "Unknown")
        damage_counts[damage_level] += 1

        if damage_level in BLOCKING_DAMAGE_LEVELS:
            damaged_roads.append(
                {
                    "feature_id": index,
                    "name": properties.get("name", "Unknown"),
                    "road_type": properties.get("info", "Unknown"),
                    "damage_level": damage_level,
                    "blocked": True,
                    "coordinates": geometry.get("coordinates", []),
                }
            )

    return {
        "source": DEFAULT_INPUT.name,
        "total_roads": len(features),
        "damage_counts": dict(sorted(damage_counts.items())),
        "blocked_road_count": len(damaged_roads),
        "blocked_roads": damaged_roads,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create a route-ready summary from Copernicus road damage data."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    features = load_roads(args.input)
    report = build_damage_report(features)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("Damage analysis completed.")
    print(f"Total road features: {report['total_roads']}")
    print(f"Blocked or damaged roads: {report['blocked_road_count']}")
    print(f"Report saved to: {args.output}")


if __name__ == "__main__":
    main()
