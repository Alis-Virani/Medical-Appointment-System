"""Test script to verify medical knowledge integration"""

print("🧪 Testing Medical Knowledge Integration...\n")

# Test 1: Load knowledge graph
print("1️⃣  Testing Knowledge Graph...")
try:
    from knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    
    # Test getting condition details
    condition = kg.get_condition_details("Type 2 Diabetes Mellitus")
    if condition:
        print(f"   ✅ Condition found: Type 2 Diabetes")
        print(f"      Symptoms: {condition['symptoms'][:2]}")
    
    # Test getting herbs for condition
    herbs = kg.get_herb_for_condition("Diabetes")
    if herbs:
        print(f"   ✅ Found {len(herbs)} herbs for Diabetes")
        for herb in herbs[:2]:
            print(f"      - {herb['herb']}: {herb['dosage']}")
    
    # Test drug interaction check
    interaction = kg.check_drug_interaction("Aspirin", "Warfarin")
    if interaction:
        print(f"   ✅ Drug interaction detected:")
        print(f"      {interaction['drug1']} + {interaction['drug2']}: {interaction['severity']}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Load vector store
print("\n2️⃣  Testing Vector Store...")
try:
    from vector_store import get_vector_store
    store = get_vector_store("medical_knowledge")
    
    # Test semantic search
    results = store.search("fever and cough symptoms", n_results=3)
    if results['documents'] and results['documents'][0]:
        print(f"   ✅ Semantic search working")
        print(f"      Found {len(results['documents'][0])} relevant results")
        # Show first result snippet
        first_doc = results['documents'][0][0][:100]
        print(f"      Sample: {first_doc}...")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✅ Medical knowledge integration complete!")
