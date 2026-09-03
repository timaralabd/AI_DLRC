import requests
import json
from pathlib import Path

print("AI-DLRC Earthquake Data System")
print("-" * 40)

# USGS earthquake API
url = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    "?format=geojson"
    "&starttime=2026-01-01"
    "&minmagnitude=4.5"
    "&limit=100"
    "&orderby=time"
)

print("Downloading real earthquake data...")

response = requests.get(url, timeout=30)

response.raise_for_status()

data = response.json()

print("Earthquake data downloaded successfully!")

print("Total earthquakes:", len(data["features"]))

# Create data directory
output_dir = Path("data")
output_dir.mkdir(exist_ok=True)

# Save raw data
output_file = output_dir / "earthquakes.json"

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)

print("Data saved to:", output_file)

print()
print("Recent earthquakes:")

for earthquake in data["features"][:10]:

    properties = earthquake["properties"]
    coordinates = earthquake["geometry"]["coordinates"]

    print()
    print("Place:", properties["place"])
    print("Magnitude:", properties["mag"])
    print("Longitude:", coordinates[0])
    print("Latitude:", coordinates[1])
    print("Depth:", coordinates[2])

print()
print("Earthquake data collection completed!")