import networkx as nx

print("AI-DLRC Road Network Test")

graph = nx.Graph()

graph.add_edge("A", "B", distance=5)
graph.add_edge("A", "C", distance=2)
graph.add_edge("B", "D", distance=3)
graph.add_edge("C", "D", distance=10)
graph.add_edge("C", "B", distance=1)

start = "A"
destination = "D"

route = nx.shortest_path(
    graph,
    start,
    destination,
    weight="distance"
)

distance = nx.shortest_path_length(
    graph,
    start,
    destination,
    weight="distance"
)

print("Best route:", route)
print("Total distance:", distance)