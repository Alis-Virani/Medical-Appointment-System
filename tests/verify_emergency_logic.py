import sys
import os
sys.path.append(os.getcwd())

from safety_layer import get_safety_manager, TriageSeverity
from dotenv import load_dotenv

load_dotenv()

def test_emergency_detection():
    safety = get_safety_manager()
    
    test_cases = [
        {
            "text": "I have severe chest pain and cannot breathe.",
            "expected_category": "ACUTE_EMERGENCY",
            "expected_emergency": True
        },
        {
            "text": "Patient Profile: Mr Tan Ah Kow. Diagnosed with Dementia and Stroke. Wheelchair-bound. Progressive cognitive decline. Prognosis: Not likely to regain mental capacity.",
            "expected_category": "INFORMATIONAL_REPORT",
            "expected_emergency": False
        },
        {
            "text": "How do I manage my chronic hypertension?",
            "expected_category": "NON_EMERGENCY_CHRONIC", 
            "expected_emergency": False
        }
    ]
    
    print("🧪 Running Emergency Detection Tests...\n")
    
    passed = 0
    for i, case in enumerate(test_cases):
        text = case["text"]
        print(f"Test Case {i+1}: '{text[:50]}...'")
        
        try:
            severity, is_emergency, category = safety.detect_emergency(text)
            
            print(f"  -> Detected: {category} (Emergency: {is_emergency})")
            
            # Allow some flexibility in category matching (INFORMATIONAL vs NON_EMERGENCY might overlap for some LLMs)
            # But specifically for the report, we want INFORMATIONAL_REPORT
            
            category_match = category == case["expected_category"]
            emergency_match = is_emergency == case["expected_emergency"]
            
            if category_match and emergency_match:
                print("  ✅ PASS")
                passed += 1
            else:
                print(f"  ❌ FAIL (Expected {case['expected_category']}, {case['expected_emergency']})")
                
        except Exception as e:
             print(f"  ❌ ERROR: {e}")
        
        print("-" * 30)

    print(f"\nResult: {passed}/{len(test_cases)} passed.")
    if passed == len(test_cases):
        print("✅ All verification steps passed!")
    else:
        print("⚠️ Some verification steps failed.")

if __name__ == "__main__":
    test_emergency_detection()
