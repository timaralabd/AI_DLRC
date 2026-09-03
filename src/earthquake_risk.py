import json
from pathlib import Path

print("AI-DLRC Earthquake Risk Analysis")
print("-" * 40)

# Load real earthquake data
data_file = Path("data/earthquakes.json")

with open(data_file, "r", encoding="utf-8") as file:
    data = json.load(file)

print("Real earthquake data loaded.")
print("Total earthquakes:", len(data["features"]))


def calculate_risk(magnitude, depth):
    """
    Calculate an earthquake risk score.

    Higher magnitude increases risk.
    Shallow earthquakes are considered more dangerous.
    """

    magnitude_score = magnitude * 10

    if depth <= 20:
        depth_score = 30
    elif depth <= 50:
        depth_score = 20
    elif depth <= 100:
        depth_score = 10
    else:
        depth_score = 5

    risk_score = magnitude_score + depth_score

    return round(risk_score, 2)


def classify_risk(score):

    if score >= 90:
        return "Critical"

    elif score >= 70:
        return "High"

    elif score >= 50:
        return "Medium"

    else:
        return "Low"


results = []

for earthquake in data["features"]:

    properties = earthquake["properties"]
    coordinates = earthquake["geometry"]["coordinates"]

    magnitude = properties["mag"]
    depth = coordinates[2]

    # Skip records without magnitude
    if magnitude is None:
        continue

    score = calculate_risk(
        magnitude,
        depth
    )

    risk_level = classify_risk(score)

    results.append({
        "place": properties["place"],
        "magnitude": magnitude,
        "depth": depth,
        "risk_score": score,
        "risk_level": risk_level
    })


# Sort by risk score
results.sort(
    key=lambda x: x["risk_score"],
    reverse=True
)


print()
print("Earthquake Risk Results")
print("-" * 40)

for i, result in enumerate(results[:10], start=1):

    print(
        f"{i}. {result['place']}"
    )

    print(
        f"   Magnitude: {result['magnitude']}"
    )

    print(
        f"   Depth: {result['depth']} km"
    )

    print(
        f"   Risk Score: {result['risk_score']}"
    )

    print(
        f"   Risk Level: {result['risk_level']}"
    )

    print()


print("Earthquake risk analysis completed!")