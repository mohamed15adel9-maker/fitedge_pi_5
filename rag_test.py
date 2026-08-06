from rag.retrieval import retrieve

print("=== TEST 1: protein/nutrition ===")
print(retrieve("how much protein should I eat to build muscle?"))

print("\n=== TEST 2: endurance ===")
print(retrieve("how do I improve endurance for a race?"))

print("\n=== TEST 3: hyrox ===")
print(retrieve("what is hyrox and how do I train for it?"))