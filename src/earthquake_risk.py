import json
from pathlib import Path


print("AI-DLRC Türkiye + Syria Earthquake Risk Analysis")
print("-" * 50)


# ==========================================
# 1. Load real Türkiye + Syria data
# ==========================================

input_file = Path("data/turkey_syria_earthquakes.json")

with open(input_file, "r", encoding="utf-8") as file:
    data = json.load(file)

print("Real Türkiye + Syria earthquake data loaded.")
print("Total earthquakes:", len(data["features"]))


# ==========================================
# 2. Calculate risk score
# ==========================================

def calculate_risk(magnitude, depth):

    magnitude_score = magnitude * 10

    if depth <= 10:
        depth_score = 30

    elif depth <= 20:
        depth_score = 25

    elif depth <= 50:
        depth_score = 20

    elif depth <= 100:
        depth_score = 10

    else:
        depth_score = 5

    risk_score = magnitude_score + depth_score

    return round(risk_score, 2)


# ==========================================
# 3. Classify risk
# ==========================================

def classify_risk(score):

    if score >= 90:
        return "CRITICAL"

    elif score >= 70:
        return "HIGH"

    elif score >= 50:
        return "MEDIUM"

    else:
        return "LOW"


# ==========================================
# 4. Process earthquakes
# ==========================================

earthquakes = []

for earthquake in data["features"]:

    properties = earthquake["properties"]
    coordinates = earthquake["geometry"]["coordinates"]

    magnitude = properties.get("mag")

    if magnitude is None:
        continue

    depth = coordinates[2]

    risk_score = calculate_risk(
        magnitude,
        depth
    )

    risk_level = classify_risk(
        risk_score
    )

    earthquakes.append({
        "place": properties.get(
            "place",
            "Unknown"
        ),

        "magnitude": magnitude,

        "latitude": coordinates[1],

        "longitude": coordinates[0],

        "depth": depth,

        "risk_score": risk_score,

        "risk_level": risk_level
    })


# ==========================================
# 5. Sort earthquakes by risk
# ==========================================

earthquakes.sort(
    key=lambda x: x["risk_score"],
    reverse=True
)


# ==========================================
# 6. Display highest-risk earthquakes
# ==========================================

print()
print("Highest-risk earthquakes:")
print("-" * 50)

for index, earthquake in enumerate(
    earthquakes[:15],
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

    print(
        f"   Risk Score: "
        f"{earthquake['risk_score']}"
    )

    print(
        f"   Risk Level: "
        f"{earthquake['risk_level']}"
    )

    print()


# ==========================================
# 7. Count risk levels
# ==========================================

risk_counts = {
    "CRITICAL": 0,
    "HIGH": 0,
    "MEDIUM": 0,
    "LOW": 0
}

for earthquake in earthquakes:

    risk_counts[
        earthquake["risk_level"]
    ] += 1


print("Risk distribution:")
print("-" * 50)

for level, count in risk_counts.items():

    print(
        f"{level}: {count}"
    )


# ==========================================
# 8. Save risk analysis
# ==========================================

output_file = Path(
    "data/turkey_syria_earthquake_risk.json"
)

with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        earthquakes,
        file,
        indent=2,
        ensure_ascii=False
    )


print()
print("Risk analysis saved to:")
print(output_file)

print()
print("Türkiye + Syria earthquake risk analysis completed!")