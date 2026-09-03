import requests
import json
from pathlib import Path


print("AI-DLRC Türkiye + Syria Earthquake Data")
print("-" * 40)


# ==========================================
# Türkiye + Syria geographic bounding box
# ==========================================

MIN_LAT = 35.0
MAX_LAT = 42.0

MIN_LON = 26.0
MAX_LON = 45.0


# ==========================================
# USGS Earthquake API
# ==========================================

url = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    "?format=geojson"
    "&starttime=2023-01-01"
    "&minmagnitude=3.0"
    f"&minlatitude={MIN_LAT}"
    f"&maxlatitude={MAX_LAT}"
    f"&minlongitude={MIN_LON}"
    f"&maxlongitude={MAX_LON}"
    "&orderby=time"
    "&limit=1000"
)


print("Downloading real earthquake data...")
print("Region: Türkiye + Syria")


# ==========================================
# Download data
# ==========================================

response = requests.get(
    url,
    timeout=60
)

response.raise_for_status()

data = response.json()


print()
print("Earthquake data downloaded successfully!")
print("Total earthquakes:", len(data["features"]))


# ==========================================
# Save data
# ==========================================

output_dir = Path("data")
output_dir.mkdir(exist_ok=True)

output_file = (
    output_dir /
    "turkey_syria_earthquakes.json"
)

with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        data,
        file,
        indent=2,
        ensure_ascii=False
    )


print()
print("Data saved to:")
print(output_file)


# ==========================================
# Prepare earthquakes
# ==========================================

earthquakes = []

for earthquake in data["features"]:

    properties = earthquake["properties"]
    coordinates = earthquake["geometry"]["coordinates"]

    magnitude = properties.get("mag")

    if magnitude is None:
        continue

    earthquakes.append({
        "place": properties.get(
            "place",
            "Unknown"
        ),
        "magnitude": magnitude,
        "latitude": coordinates[1],
        "longitude": coordinates[0],
        "depth": coordinates[2],
        "time": properties.get("time")
    })


# ==========================================
# Sort by magnitude
# ==========================================

earthquakes.sort(
    key=lambda x: x["magnitude"],
    reverse=True
)


# ==========================================
# Display strongest earthquakes
# ==========================================

print()
print("Strongest earthquakes:")
print("-" * 40)

for index, earthquake in enumerate(
    earthquakes[:10],
    start=1
):

    print(
        f"{index}. {earthquake['place']}"
    )

    print(
        f"   Magnitude: "
        f"{earthquake['magnitude']}"
    )

    print(
        f"   Location: "
        f"{earthquake['latitude']}, "
        f"{earthquake['longitude']}"
    )

    print(
        f"   Depth: "
        f"{earthquake['depth']} km"
    )

    print()


print("Türkiye + Syria earthquake data collection completed!")