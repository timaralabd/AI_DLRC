import networkx as nx

print("AI-DLRC Disaster Route System")
print("-" * 40)

# Create road network
graph = nx.Graph()

# Add roads
graph.add_edge("A", "B", distance=5, status="open")
graph.add_edge("A", "C", distance=2, status="open")
graph.add_edge("B", "D", distance=3, status="closed")
graph.add_edge("C", "D", distance=10, status="open")
graph.add_edge("C", "B", distance=1, status="open")

print("Road network created.")

# Remove closed roads
available_graph = nx.Graph()

for u, v, data in graph.edges(data=True):
    if data["status"] == "open":
        available_graph.add_edge(
            u,
            v,
            distance=data["distance"]
        )

print("Closed roads removed.")

# Find best available route
start = "A"
destination = "D"

route = nx.shortest_path(
    available_graph,
    start,
    destination,
    weight="distance"
)

distance = nx.shortest_path_length(
    available_graph,
    start,
    destination,
    weight="distance"
)

print()
print("Emergency Route:")
print(" -> ".join(route))

print("Total Distance:", distance)

print()
print("Route calculation completed successfully!")