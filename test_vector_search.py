#!/usr/bin/env python3
"""
Test script for Quadrant DB semantic search.
Run: python test_vector_search.py
"""

from vector_store import get_vector_store, SIMILARITY_THRESHOLD
import time

# Sample medical documents for testing
MEDICAL_DOCUMENTS = [
    "Fever is a temporary increase in body temperature, often in response to infection.",
    "Common symptoms of flu include cough, sore throat, body aches, and fatigue.",
    "Headache can be caused by stress, dehydration, caffeine withdrawal, or infection.",
    "A cold typically lasts 7-10 days and causes runny nose, sneezing, and cough.",
    "Diabetes is a chronic condition affecting blood sugar regulation.",
    "High blood pressure increases risk of heart disease and stroke.",
    "Allergies occur when the immune system reacts to harmless substances.",
    "Asthma is a respiratory condition causing difficulty breathing and wheezing.",
    "Migraine headaches are severe, often one-sided, and may include nausea.",
    "Anxiety disorders involve excessive worry and can cause physical symptoms.",
]

# Test queries - some should match well, some should match moderately
TEST_QUERIES = [
    ("What causes fever?", "fever"),
    ("Tell me about cold symptoms", "cold"),
    ("How to treat a headache", "headache"),
    ("I have body aches", "symptoms"),
    ("What is diabetes?", "medical condition"),
    ("Something unrelated to medicine", "off-topic"),
]


def print_separator(title=""):
    """Print a visual separator."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    else:
        print("-" * 60)


def test_add_documents():
    """Test 1: Add documents to vector store."""
    print_separator("TEST 1: Adding Documents")
    
    vs = get_vector_store(collection_name="test_medical")
    
    print(f"Adding {len(MEDICAL_DOCUMENTS)} medical documents...")
    for i, doc in enumerate(MEDICAL_DOCUMENTS, 1):
        metadata = {
            "doc_id": i,
            "category": "general_knowledge",
            "source": "test_database"
        }
        vs.add_texts([doc], [metadata], [f"doc_{i}"])
        print(f"  [+] Added doc_{i}: {doc[:50]}...")
    
    print("\n[OK] Documents added successfully!")
    return vs


def test_semantic_search(vs):
    """Test 2: Semantic search with various queries."""
    print_separator("TEST 2: Semantic Search Results")
    
    print(f"Similarity Threshold: {SIMILARITY_THRESHOLD} (0=nothing, 1=identical)\n")
    
    for query, expected_topic in TEST_QUERIES:
        print(f"Query: \"{query}\"")
        print(f"Expected topic: {expected_topic}")
        print()
        
        results = vs.search(query, n_results=3)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        scores = results.get("distances", [[]])[0]
        
        if not docs:
            print("  [FAIL] NO RESULTS (below similarity threshold)")
        else:
            for j, (doc, meta, score) in enumerate(zip(docs, metas, scores), 1):
                quality = "[***]" if score > 0.8 else "[**]" if score > 0.7 else "[*]"
                print(f"  {j}. [{quality} score: {score:.3f}] {doc[:60]}...")
                print(f"     Source: {meta.get('source')}, Doc ID: {meta.get('doc_id')}")
        
        print_separator()


def test_user_scoped_search(vs):
    """Test 3: User-scoped search."""
    print_separator("TEST 3: User-Scoped Search")
    
    # Add documents for different users
    print("Adding user-specific documents...\n")
    
    user1_docs = [
        ("Patient A: Suffering from persistent cough for 2 weeks", "user_1"),
        ("Patient A: Body temperature elevated to 102F", "user_1"),
    ]
    
    user2_docs = [
        ("Patient B: Complains of dizziness and headache", "user_2"),
        ("Patient B: Blood pressure readings are abnormal", "user_2"),
    ]
    
    for doc, user_id in user1_docs + user2_docs:
        metadata = {"user_id": user_id, "source": "patient_notes"}
        vs.add_texts([doc], [metadata], [f"{user_id}_note_{int(time.time()*1000)}"])
        print(f"  [+] Added for {user_id}: {doc[:50]}...")
    
    print("\n" + "="*60)
    print("  Searching for 'cough symptoms' for User 1 only")
    print("="*60 + "\n")
    
    results_user1 = vs.search_by_user("cough symptoms", user_id="user_1", n_results=3)
    docs = results_user1.get("documents", [[]])[0]
    metas = results_user1.get("metadatas", [[]])[0]
    scores = results_user1.get("distances", [[]])[0]
    
    if docs:
        for doc, meta, score in zip(docs, metas, scores):
            print(f"  [+] [{score:.3f}] {doc[:60]}...")
            print(f"    User: {meta.get('user_id')}")
    else:
        print("  [FAIL] No results for this user")
    
    print_separator()


def test_quality_check():
    """Test 4: Detailed quality check."""
    print_separator("TEST 4: Quality Verification")
    
    vs = get_vector_store(collection_name="test_medical_quality")
    
    # Add a specific set of documents
    docs_to_add = [
        ("Fever causes include viral infections, bacterial infections, and vaccinations.", "medical_fact"),
        ("To reduce fever: rest, hydration, and acetaminophen or ibuprofen.", "treatment"),
        ("Normal body temperature ranges from 97°F to 99°F.", "normal_range"),
        ("Cough can be dry or productive and may indicate various conditions.", "symptom"),
    ]
    
    print("Adding focused test documents...\n")
    for doc, category in docs_to_add:
        metadata = {"category": category}
        vs.add_texts([doc], [metadata], [f"test_{int(time.time()*1000)}"])
    
    # Perform exact test
    test_query = "What causes fever?"
    print(f"Query: \"{test_query}\"\n")
    
    results = vs.search(test_query, n_results=4)
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    scores = results.get("distances", [[]])[0]
    
    print("Expected behavior:")
    print("  1st result should be about 'fever causes' (highest score ~0.85-0.95)")
    print("  2nd result might be 'fever treatment' (score ~0.70-0.80)")
    print("  3rd result unlikely (score <0.65)")
    print("\nActual results:\n")
    
    if not docs:
        print("  [FAIL] FAIL: No results returned")
        return False
    
    success = True
    for i, (doc, meta, score) in enumerate(zip(docs, metas, scores), 1):
        print(f"  Result {i} (score: {score:.3f})")
        print(f"    Category: {meta.get('category')}")
        print(f"    Text: {doc[:70]}...")
        
        # Check score quality
        if i == 1 and score < 0.7:
            print(f"    [WARN] WARNING: First result score is low ({score:.3f})")
            success = False
        elif i == 1 and score >= 0.7:
            print(f"    [OK] Good! First result has strong match")
        
        print()
    
    if success:
        print("[OK] Quality check PASSED")
    else:
        print("[WARN] Quality check found issues")
    
    return success


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  QUADRANT DB SEMANTIC SEARCH TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: Add documents
        vs = test_add_documents()
        time.sleep(0.5)  # Small delay for DB to settle
        
        # Test 2: Semantic search
        test_semantic_search(vs)
        time.sleep(0.5)
        
        # Test 3: User-scoped search
        test_user_scoped_search(vs)
        time.sleep(0.5)
        
        # Test 4: Quality check
        quality_ok = test_quality_check()
        
        # Final summary
        print_separator("SUMMARY")
        print("[OK] All tests completed!")
        print("\nHow to interpret results:")
        print("  • Score > 0.80: Excellent match (relevant)")
        print("  • Score 0.70-0.80: Good match (somewhat relevant)")
        print("  • Score 0.60-0.70: Moderate match (tangentially related)")
        print("  • Score < 0.60: Filtered out (not relevant)")
        print("\n[OK] If you see documents appear with scores > 0.6, search is working!")
        print("\n" + "="*60 + "\n")
        
        return quality_ok
        
    except Exception as e:
        print(f"\n[ERR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
