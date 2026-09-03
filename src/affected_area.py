import json
from pathlib import Path
from math import radians, sin, cos, sqrt, atan2

print("AI-DLRC Global Affected Area Analysis")
print("-" * 40)

# ==========================================
# Load real earthquake data
# ==========================================

data_file = Path("data/earthquakes.json")

with open(data_file, "r", encoding="utf-8") as file:
    data = json.load(file)

print("Real earthquake data loaded.")
print("Total earthquakes:", len(data["features"]))


# ==========================================
# Haversine distance
# ==========================================

def calculate_distance(lat1, lon1, lat2, lon2):

    earth_radius = 6371

    lat1 = radians(lat1)
    lat2 = radians(lat2)

    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


# ==========================================
# Select strongest earthquake
# ==========================================

earthquakes = []

for earthquake in data["features"]:

    properties = earthquake["properties"]
    coordinates = earthquake["geometry"]["coordinates"]

    magnitude = properties["mag"]

    if magnitude is None:
        continue

    earthquakes.append({
        "place": properties["place"],
        "magnitude": magnitude,
        "longitude": coordinates[0],
        "latitude": coordinates[1],
        "depth": coordinates[2]
    })


if not earthquakes:
    print("No valid earthquake data found.")
    exit()


earthquakes.sort(
    key=lambda x: x["magnitude"],
    reverse=True
)

strongest = earthquakes[0]

earthquake_lat = strongest["latitude"]
earthquake_lon = strongest["longitude"]


print()
print("Selected earthquake:")
print("Place:", strongest["place"])
print("Magnitude:", strongest["magnitude"])
print("Latitude:", earthquake_lat)
print("Longitude:", earthquake_lon)
print("Depth:", strongest["depth"], "km")


# ==========================================
# Generate geographic analysis points
# ==========================================

# These points are generated around the earthquake
# only for testing the geographic calculation.

offsets = [
    (0.10, 0.10),
    (0.20, -0.15),
    (-0.15, 0.20),
    (-0.20, -0.10),
    (0.30, 0.25)
]

print()
print("Affected area estimation:")
print("-" * 40)


affected_locations = []

for index, (lat_offset, lon_offset) in enumerate(offsets, start=1):

    latitude = earthquake_lat + lat_offset
    longitude = earthquake_lon + lon_offset

    distance = calculate_distance(
        earthquake_lat,
        earthquake_lon,
        latitude,
        longitude
    )

    affected_locations.append({
        "id": f"Area_{index}",
        "latitude": latitude,
        "longitude": longitude,
        "distance": distance
    })

    print(
        f"Area_{index} -> "
        f"{round(distance, 2)} km from earthquake"
    )


# ==========================================
# Identify closest affected area
# ==========================================

closest_area = min(
    affected_locations,
    key=lambda x: x["distance"]
)

print()
print("Closest affected area:")
print(closest_area["id"])

print(
    "Distance:",
    round(closest_area["distance"], 2),
    "km"
)

print()
print("Global affected area analysis completed!")