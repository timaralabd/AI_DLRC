print("AI-DLRC Rescue Priority System")
print("-" * 40)

# Simulated disaster zones
zones = {
    "Zone_A": {
        "people": 120,
        "damage": 80,
        "distance": 5
    },
    "Zone_B": {
        "people": 40,
        "damage": 50,
        "distance": 3
    },
    "Zone_C": {
        "people": 200,
        "damage": 90,
        "distance": 8
    },
    "Zone_D": {
        "people": 70,
        "damage": 30,
        "distance": 2
    }
}

def calculate_priority(people, damage, distance):
    score = (
        people * 0.5
        + damage * 0.4
        - distance * 2
    )

    return round(score, 2)


results = []

for zone, data in zones.items():

    priority = calculate_priority(
        data["people"],
        data["damage"],
        data["distance"]
    )

    results.append({
        "zone": zone,
        "priority": priority
    })


# Sort zones by priority
results.sort(
    key=lambda x: x["priority"],
    reverse=True
)

print("Rescue Priority:")
print()

for rank, result in enumerate(results, start=1):

    print(
        f"{rank}. {result['zone']} "
        f"-> Priority Score: {result['priority']}"
    )

print()
print("Highest priority zone:")
print(results[0]["zone"])

print()
print("Rescue priority calculation completed!")