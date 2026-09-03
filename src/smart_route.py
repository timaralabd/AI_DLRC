
import networkx as nx

print("AI-DLRC Smart Rescue Route System")
print("-" * 40)

# ==========================================
# 1. Road Network
# ==========================================

graph = nx.Graph()

graph.add_edge("A", "B", distance=5, damage=20)
graph.add_edge("A", "C", distance=2, damage=70)
graph.add_edge("C", "B", distance=1, damage=10)
graph.add_edge("B", "D", distance=3, damage=100)
graph.add_edge("C", "D", distance=10, damage=15)

print("Road network created.")

# ==========================================
# 2. Calculate Road Cost
# ==========================================

for u, v, data in graph.edges(data=True):

    if data["damage"] >= 100:
        data["cost"] = float("inf")

    else:
        data["cost"] = (
            data["distance"] *
            (1 + data["damage"] / 100)
        )

# ==========================================
# 3. Remove Blocked Roads
# ==========================================

available_graph = nx.Graph()

for u, v, data in graph.edges(data=True):

    if data["damage"] < 100:

        available_graph.add_edge(
            u,
            v,
            cost=data["cost"],
            distance=data["distance"],
            damage=data["damage"]
        )

print("Blocked roads removed.")

# ==========================================
# 4. Rescue Zone Priorities
# ==========================================

zones = {
    "Zone_A": {
        "node": "B",
        "priority": 82
    },
    "Zone_B": {
        "node": "C",
        "priority": 34
    },
    "Zone_C": {
        "node": "D",
        "priority": 120
    }
}

# ==========================================
# 5. Select Highest Priority Zone
# ==========================================

highest_priority_zone = max(
    zones,
    key=lambda zone: zones[zone]["priority"]
)

destination = zones[highest_priority_zone]["node"]

start = "A"

print()
print("Highest Priority Zone:")
print(highest_priority_zone)

print("Priority Score:",
      zones[highest_priority_zone]["priority"])

# ==========================================
# 6. Calculate Emergency Route
# ==========================================

route = nx.shortest_path(
    available_graph,
    start,
    destination,
    weight="cost"
)

total_cost = nx.shortest_path_length(
    available_graph,
    start,
    destination,
    weight="cost"
)

# ==========================================
# 7. Display Result
# ==========================================

print()
print("Emergency Route:")
print(" -> ".join(route))

print("Total Route Cost:",
      round(total_cost, 2))

print()
print("Road Information:")

for i in range(len(route) - 1):

    u = route[i]
    v = route[i + 1]

    data = available_graph[u][v]

    print(
        f"{u} -> {v} | "
        f"Distance: {data['distance']} | "
        f"Damage: {data['damage']}%"
    )

print()
print("Smart rescue route calculation completed!")