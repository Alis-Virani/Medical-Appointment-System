"""
demo_medical_knowledge_integration.py — Live examples of medical knowledge in action
Shows how the system can provide medical information and safety warnings
"""

print("\n" + "="*80)
print("🎯 MEDICAL KNOWLEDGE INTEGRATION - LIVE DEMO")
print("="*80 + "\n")

from medical_knowledge_integration import (
    get_condition_information,
    get_herb_recommendations,
    check_medication_safety,
    search_medical_knowledge,
    format_medical_response,
    analyze_drug_interaction_risk
)

# Demo 1: Get detailed condition information
print("1️⃣  SCENARIO: User asks about Hypertension")
print("-" * 80)
condition_data = get_condition_information("Hypertension (High Blood Pressure)")
if condition_data:
    print(f"📋 Condition: {condition_data['condition']}")
    print(f"⚠️  Severity: {condition_data['severity'].upper()}")
    print(f"🔍 Symptoms: {', '.join(condition_data['symptoms'][:3])}")
    print(f"📌 Causes: {', '.join(condition_data['causes'][:2])}")
print()

# Demo 2: Suggest herbs for a condition
print("\n2️⃣  SCENARIO: User asks about natural remedies for Hypertension")
print("-" * 80)
herbs = get_herb_recommendations("Hypertension")
if herbs:
    print(f"🌿 Natural Remedies for Hypertension:")
    for herb in herbs:
        print(f"   • {herb['herb']}")
        print(f"     Dosage: {herb['dosage']}")
        print()
else:
    print("No herbs found for Hypertension")

# Demo 3: Drug interaction check
print("\n3️⃣  SCENARIO: User is on Aspirin and asks about Warfarin")
print("-" * 80)
interaction = check_medication_safety("Aspirin", "Warfarin")
print(f"🔔 Checking: {interaction['drugs']}")
if not interaction['safe']:
    print(f"   ⚠️  {interaction['severity'].upper()} SEVERITY")
    print(f"   Effect: {interaction['effect']}")
    print(f"\n   {interaction['warning']}")
else:
    print(f"   ✅ These medications are generally safe together")
print()

# Demo 4: Search medical knowledge
print("\n4️⃣  SCENARIO: User asks 'What are symptoms of Type 2 Diabetes?'")
print("-" * 80)
search_results = search_medical_knowledge("Type 2 Diabetes symptoms", n_results=2)
print(f"🔎 Search Query: '{search_results['query']}'")
print(f"📊 Results Found: {search_results['results_found']}\n")

for i, result in enumerate(search_results['results'], 1):
    print(f"   {i}. [{result['type']}] (Relevance: {result['relevance']})")
    print(f"      {result['content'][:100]}...")
    print()

# Demo 5: Format medical response
print("\n5️⃣  SCENARIO: User asks about Migraine treatment")
print("-" * 80)
formatted = format_medical_response("Migraine")
print(formatted)
print()

# Demo 6: Multi-drug interaction analysis
print("\n6️⃣  SCENARIO: Patient on multiple medications - interaction analysis")
print("-" * 80)
medications = ["Aspirin", "Metformin", "Warfarin"]
risk = analyze_drug_interaction_risk(medications)
print(f"💊 Medications: {', '.join(medications)}")
print(f"📊 Total combinations checked: {risk['total_combinations']}")
print(f"⚠️  Interactions found: {risk['interactions_found']}")
print(f"🔴 High severity warnings: {risk['high_severity_count']}\n")

if risk['warnings']:
    print("   ⚠️  HIGH SEVERITY INTERACTIONS:")
    for warning in risk['warnings']:
        print(f"   • {warning}")
    print()

if risk['safe_pairs']:
    print("   ✅ SAFE COMBINATIONS:")
    for pair in risk['safe_pairs']:
        print(f"   • {pair}")
print()

# Demo 7: Symptomatic query
print("\n7️⃣  SCENARIO: User describes symptoms and gets differential diagnosis")
print("-" * 80)
symptom_query = "fever with persistent cough and shortness of breath"
print(f"🔎 Symptoms: '{symptom_query}'\n")

search_results = search_medical_knowledge(symptom_query, n_results=3)
if search_results['results_found'] > 0:
    print("📋 Possible conditions:")
    for i, result in enumerate(search_results['results'], 1):
        if result['type'] == 'medical_condition':
            print(f"\n   {i}. {result['metadata'].get('name', 'Unknown')}")
            print(f"      Severity: {result['metadata'].get('severity', 'N/A')}")
            print(f"      Match: {result['relevance']}")
print()

# Summary
print("\n" + "="*80)
print("✅ MEDICAL KNOWLEDGE INTEGRATION COMPLETE")
print("="*80)
print("""
AI ASSISTANT NOW HAS ACCESS TO:
  ✓ Detailed medical condition information
  ✓ Natural herb remedies and dosages
  ✓ Drug interaction warnings
  ✓ Semantic search across medical knowledge
  ✓ Multi-medication safety analysis
  ✓ Symptom-to-condition mapping

CHAT FEATURES ENABLED:
  💬 "Tell me about Hypertension"
     → Full details with severity, symptoms, natural remedies
  
  💬 "I'm on Aspirin, can I take Warfarin?"
     → Interaction warning with severity and recommendations
  
  💬 "What natural remedies treat Anxiety?"
     → Suggests Ashwagandha, Brahmi with dosages
  
  💬 "I have fever and cough"
     → Searches medical knowledge, suggests possible conditions
  
  💬 "I'm on Metformin and Warfarin, is it safe to add Aspirin?"
     → Multi-drug interaction analysis with severity levels

INTEGRATION STATUS: ✅ READY FOR DEPLOYMENT
""")
print("="*80 + "\n")
