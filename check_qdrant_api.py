from qdrant_client import QdrantClient

client = QdrantClient(":memory:")

# List all public methods
methods = sorted([m for m in dir(client) if not m.startswith('_')])
print("All public methods:")
for m in methods:
    if any(x in m.lower() for x in ['search', 'query', 'point', 'vector']):
        print(f"  ✓ {m}")
