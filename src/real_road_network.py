import json
from pathlib import Path
import osmnx as ox


print("AI-DLRC Real Road Network")
print("-" * 50)


# ==========================================
# 1. Load earthquake risk data
# ==========================================

input_file = Path(
    "data/turkey_syria_earthquake_risk.json"
)

with open(
    input_file,
    "r",
    encoding="utf-8"
) as file:

    earthquakes = json.load(file)


print("Earthquake risk data loaded.")
print("Total earthquakes:", len(earthquakes))


# ==========================================
# 2. Select highest-risk earthquake
# ==========================================

earthquakes.sort(
    key=lambda x: x["risk_score"],
    reverse=True
)

selected_earthquake = earthquakes[0]


latitude = selected_earthquake["latitude"]
longitude = selected_earthquake["longitude"]


print()
print("Selected earthquake:")
print("-" * 50)

print(
    "Place:",
    selected_earthquake["place"]
)

print(
    "Magnitude:",
    selected_earthquake["magnitude"]
)

print(
    "Risk Score:",
    selected_earthquake["risk_score"]
)

print(
    "Risk Level:",
    selected_earthquake["risk_level"]
)

print(
    "Latitude:",
    latitude
)

print(
    "Longitude:",
    longitude
)

print(
    "Depth:",
    selected_earthquake["depth"],
    "km"
)


# ==========================================
# 3. Download real OpenStreetMap roads
# ==========================================

print()
print("Downloading real OpenStreetMap road network...")
print("Search radius: 10 km")
print("-" * 50)


try:

    graph = ox.graph.graph_from_point(
        (
            latitude,
            longitude
        ),
        dist=10_000,
        network_type="drive",
        simplify=True
    )

    print()
    print("Real road network downloaded successfully!")


except Exception as error:

    print()
    print("Road network download failed.")
    print("Error:", error)

    exit()


# ==========================================
# 4. Display network information
# ==========================================

print()
print("Road network information:")
print("-" * 50)

print(
    "Nodes:",
    len(graph.nodes)
)

print(
    "Edges:",
    len(graph.edges)
)


# ==========================================
# 5. Save road network
# ==========================================

output_dir = Path("data")
output_dir.mkdir(exist_ok=True)

output_file = (
    output_dir /
    "real_earthquake_road_network.graphml"
)


ox.io.save_graphml(
    graph,
    filepath=output_file
)


print()
print("Road network saved to:")
print(output_file)


# ==========================================
# 6. Final result
# ==========================================

print()
print("Real earthquake + real road network connected!")
print("AI-DLRC road network stage completed!")