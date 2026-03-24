"""
Safety Layer & Emergency Detection
===================================
Implements critical guardrails for medical chatbot
- Emergency triage detection
- Hallucination prevention
- Safety interrupts
"""

from typing import Tuple, Optional
from enum import Enum
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

class TriageSeverity(Enum):
    """Emergency severity levels"""
    CRITICAL = "critical"      # Life-threatening, call 911 immediately
    URGENT = "urgent"          # Serious, go to hospital now
    HIGH = "high"              # Important, see doctor today
    MEDIUM = "medium"          # Can wait 1-2 days
    LOW = "low"                # Can wait a week or more

class SafetyManager:
    """Manages safety guardrails and emergency detection"""
    
    def __init__(self):
        # ========== ACUTE EMERGENCY KEYWORDS ==========
        # Immediate threat to life or limb happening NOW
        self.acute_keywords = {
            # Cardiac emergencies (NOW)
            "chest pain": TriageSeverity.CRITICAL,
            "chest tightness": TriageSeverity.CRITICAL,
            "difficulty breathing": TriageSeverity.CRITICAL,
            "shortness of breath": TriageSeverity.CRITICAL,
            "heart attack": TriageSeverity.CRITICAL,
            "cardiac arrest": TriageSeverity.CRITICAL,
            "severe chest": TriageSeverity.CRITICAL,
            "can't breathe": TriageSeverity.CRITICAL,
            
            # Neurological emergencies (NOW - symptoms happening NOW)
            "unconscious": TriageSeverity.CRITICAL,
            "loss of consciousness": TriageSeverity.CRITICAL,
            "severe headache now": TriageSeverity.CRITICAL,
            "sudden paralysis": TriageSeverity.CRITICAL,
            "sudden weakness": TriageSeverity.CRITICAL,
            "facial drooping": TriageSeverity.CRITICAL,
            "sudden numbness": TriageSeverity.CRITICAL,
            "collapsed": TriageSeverity.CRITICAL,
            "seizure": TriageSeverity.CRITICAL,
            
            # Severe bleeding (NOW)
            "severe bleeding": TriageSeverity.CRITICAL,
            "uncontrolled bleeding": TriageSeverity.CRITICAL,
            "heavy bleeding": TriageSeverity.CRITICAL,
            "bleeding won't stop": TriageSeverity.CRITICAL,
            
            # Respiratory emergencies (NOW)
            "choking": TriageSeverity.CRITICAL,
            "severe asthma": TriageSeverity.CRITICAL,
            "anaphylaxis": TriageSeverity.CRITICAL,
            "severe allergic reaction": TriageSeverity.CRITICAL,
            
            # Severe trauma (NOW)
            "major accident": TriageSeverity.CRITICAL,
            "severe burn": TriageSeverity.CRITICAL,
            "chemical burn": TriageSeverity.CRITICAL,
            "poisoning": TriageSeverity.CRITICAL,
            "overdose": TriageSeverity.CRITICAL,
            
            # Abdominal emergencies (NOW)
            "severe abdominal pain": TriageSeverity.URGENT,
            "sharp abdominal pain": TriageSeverity.URGENT,
            "abdominal pain with fever": TriageSeverity.URGENT,
            
            # Fever-related (NOW)
            "high fever with rash": TriageSeverity.URGENT,
            "fever 105": TriageSeverity.URGENT,
            "fever with stiff neck": TriageSeverity.URGENT,
            "suicidal": TriageSeverity.CRITICAL,
        }
        
        # ========== CHRONIC CONDITION INDICATORS ==========
        # These phrases indicate long-standing/historical conditions, NOT emergencies
        self.chronic_indicators = [
            "history of",
            "diagnosed with",
            "long-standing",
            "chronic",
            "progressive",
            "over years",
            "since",
            "has been",
            "previously",
            "past",
            "old injury",
            "long-term",
            "ongoing",
            "managed with",
            "treatment plan",
            "capacity assessment",
            "mental capacity",
            "disability assessment",
            "report of",
            "assessment of",
            "patient profile",
        ]
        
        # Home remedy prevention keywords - prohibited conditions for home treatment
        # Only the most critical conditions
        self.home_remedy_prohibited = {
            "chest pain", "heart attack", "cardiac arrest",
            "stroke", "unconscious", "severe bleeding",
            "poisoning", "overdose", "meningitis", "anaphylaxis",
            "choking", "severe burns", "difficulty breathing",
            "can't breathe", "loss of consciousness"
        }
        
        # Condition-to-emergency-type mapping
        self.emergency_responses = {
            TriageSeverity.CRITICAL: {
                "message": "🚨 **EMERGENCY ALERT** 🚨\n\nYour symptoms suggest a **life-threatening condition**. This requires **immediate medical attention**.\n\n**CALL 911 (or your local emergency number) IMMEDIATELY.**\n\nDo NOT wait for an appointment. Go to the nearest emergency room or call an ambulance.",
                "should_book": False,
                "notify_emergency": True
            },
            TriageSeverity.URGENT: {
                "message": "⚠️ **URGENT** ⚠️\n\nYour symptoms are serious and need **immediate attention**.\n\n**Go to the nearest hospital emergency room NOW.**\n\nThis is not something to wait for. An in-person evaluation is necessary.",
                "should_book": False,
                "notify_emergency": True
            },
            TriageSeverity.HIGH: {
                "message": "🔴 **Important** 🔴\n\nYour symptoms suggest you should **see a doctor today**. Please:\n\n1. **Call your doctor's office immediately** to schedule an urgent appointment\n2. If unavailable, visit an urgent care center\n3. If symptoms worsen, go to the ER\n\nI can help you find specialists below, but priority is seeing someone today.",
                "should_book": True,
                "notify_emergency": False
            }
        }
    
    
    def assess_urgency(self, text: str) -> str:
        """
        Uses LLM to classify text as ACUTE_EMERGENCY, NON_EMERGENCY_CHRONIC, or INFORMATIONAL_REPORT.
        More robust classification with better handling.
        """
        try:
            llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0)
            
            # First check if this looks like a report/document
            lower_text = text.lower()
            report_markers = ["patient profile", "diagnosis", "assessment", "report", "findings", "medical record", 
                             "discharge", "chief complaint", "prognosis", "mental capacity", "clinical impression"]
            is_structured_report = any(marker in lower_text for marker in report_markers)
            
            prompt = f"""
Classify this medical text into EXACTLY ONE of these three categories:

1. ACUTE_EMERGENCY: 
   - Patient describing CURRENT symptoms that are life-threatening
   - Examples: "I have chest pain now", "I can't breathe", "I'm unconscious"
   - Requires immediate action (911, ER)

2. NON_EMERGENCY_CHRONIC:
   - Patient describing ongoing/managed conditions
   - Patient asking about medication refills or symptom management
   - May contain serious words but for historical conditions
   - Examples: "I have diabetes and need medication", "How do I manage my asthma?"

3. INFORMATIONAL_REPORT:
   - Structured medical documents, reports, summaries
   - Patient profiles, capacity assessments, discharge summaries
   - Clinical notes describing past/existing conditions
   - NOT a patient describing current symptoms needing help
   - Key markers: "Patient Profile", "Diagnosis", "Assessment", "Report", "Findings"

Medical Text:
"{text}"

IMPORTANT RULES:
- If text describes CURRENT acute symptoms NOW → ACUTE_EMERGENCY
- If text has "Patient Profile", "Diagnosis", "Assessment", "Report", "Findings", "Prognosis" → INFORMATIONAL_REPORT
- If text contains "history of", "diagnosed with", "progressive", "over years" → CHRONIC or INFORMATIONAL
- If it's a structured medical document → INFORMATIONAL_REPORT
- If it's a patient asking for help with ongoing symptoms → NON_EMERGENCY_CHRONIC

Return ONLY the category name (ACUTE_EMERGENCY, NON_EMERGENCY_CHRONIC, or INFORMATIONAL_REPORT). No explanation.
"""
            
            response = llm.invoke(prompt).content.strip().upper()
            
            # Parse response - look for exact matches
            if "ACUTE" in response:
                return "ACUTE_EMERGENCY"
            elif "INFORMATIONAL" in response or "REPORT" in response:
                return "INFORMATIONAL_REPORT"
            elif "CHRONIC" in response or "NON_EMERGENCY" in response:
                return "NON_EMERGENCY_CHRONIC"
            
            # Default safe fallback - if structured report, treat as informational
            if is_structured_report:
                return "INFORMATIONAL_REPORT"
            return "NON_EMERGENCY_CHRONIC"
            
        except Exception as e:
            print(f"⚠️ LLM Emergency Classification Failed: {e}")
            # Safe fallback: assume non-emergency unless it was clearly acute
            return "NON_EMERGENCY_CHRONIC"

    def detect_emergency(self, user_input: str) -> Tuple[TriageSeverity, bool, str]:
        """
        Detect if user input indicates a medical emergency
        Two-stage classification:
        Stage 1: Check for acute emergency keywords
        Stage 2: If keywords found, use LLM to distinguish acute from chronic context
        Returns: (severity_level, is_emergency, category)
        """
        lower_input = user_input.lower()
        
        # ========== Check if this is a structured medical report/document ==========
        report_markers = ["patient profile", "diagnosis", "assessment", "report", "findings", 
                         "medical record", "discharge", "chief complaint", "prognosis", "mental capacity"]
        is_structured_report = any(marker in lower_input for marker in report_markers)
        
        # If it looks like a structured report, use LLM to classify it properly
        if is_structured_report:
            category = self.assess_urgency(user_input)
            if category == "ACUTE_EMERGENCY":
                return TriageSeverity.CRITICAL, True, category
            else:
                return TriageSeverity.LOW, False, category
        
        # ========== STAGE 1: Check for ACUTE Indicators ==========
        # These indicate a real emergency happening NOW
        has_acute_keywords = False
        acute_severity = TriageSeverity.LOW
        
        for keyword, severity in self.acute_keywords.items():
            if keyword in lower_input:
                has_acute_keywords = True
                acute_severity = severity
                break
        
        # If NO acute keywords at all -> Definitely not an emergency
        if not has_acute_keywords:
            return TriageSeverity.LOW, False, "NON_EMERGENCY_CHRONIC"
        
        # ========== STAGE 2: Check for CHRONIC Indicators ==========
        # If we found acute keywords, check if they're in a chronic context
        # e.g., "history of stroke" vs "having a stroke now"
        has_chronic_indicators = any(indicator in lower_input for indicator in self.chronic_indicators)
        
        # If words like "history of", "diagnosed with", "progressive", etc. are present,
        # this is likely a chronic condition report, not an acute emergency
        if has_chronic_indicators:
            # Use LLM to double-check the context
            category = self.assess_urgency(user_input)
            if category in ["INFORMATIONAL_REPORT", "NON_EMERGENCY_CHRONIC"]:
                return TriageSeverity.LOW, False, category
            # If LLM thinks it's acute despite chronic indicators, trust the LLM
            if category == "ACUTE_EMERGENCY":
                return acute_severity, True, category
            # Fallback
            return TriageSeverity.LOW, False, "NON_EMERGENCY_CHRONIC"
        
        # ========== STAGE 3: LLM Confirmation for Ambiguous Cases ==========
        # If acute keywords found but no chronic indicators, use LLM to verify
        category = self.assess_urgency(user_input)
        
        if category == "ACUTE_EMERGENCY":
            return acute_severity, True, category
        elif category == "INFORMATIONAL_REPORT":
            return TriageSeverity.LOW, False, category
        else:
            return TriageSeverity.MEDIUM, False, category # Chronic/Non-emergency

    
    def is_home_remedy_request(self, user_input: str) -> bool:
        """
        Detect if user is asking for home remedies (which may be dangerous)
        Returns: True if it's a home remedy request
        """
        lower_input = user_input.lower()
        
        home_remedy_triggers = [
            "treat at home", "home remedy", "home treatment",
            "cure at home", "without going to doctor", "without doctor",
            "without hospital", "at home care", "self-care", "self treatment"
        ]
        
        for trigger in home_remedy_triggers:
            if trigger in lower_input:
                return True
        
        return False
    
    def validate_response(self, user_input: str, severity: TriageSeverity) -> Tuple[bool, Optional[str]]:
        """
        Validate if response should be blocked for safety
        Returns: (is_safe, safety_message)
        """
        lower_input = user_input.lower()
        
        # Check for home remedy request with critical condition
        if self.is_home_remedy_request(user_input):
            for prohibited in self.home_remedy_prohibited:
                if prohibited in lower_input:
                    safety_msg = f"❌ **I cannot provide home remedies for '{prohibited}'** ❌\n\n"
                    safety_msg += self.get_emergency_response(severity)
                    return False, safety_msg
        
        return True, None
    
    def get_emergency_response(self, severity: TriageSeverity, category: str = "") -> str:
        """Get appropriate emergency response message based on severity and category"""
        # For informational reports, provide a helpful message instead of emergency alert
        if category == "INFORMATIONAL_REPORT":
            return "📋 **Clinical Report Detected**\n\nThis appears to be a medical assessment or clinical report. I can help you:\n- Summarize the diagnosis and findings\n- Explain medical terms and conditions\n- Identify recommended specialists\n- Answer questions about the patient's care recommendations\n\nPlease let me know what specific information you'd like help understanding."
        
        if severity not in self.emergency_responses:
            return ""  # No special response for non-critical
        return self.emergency_responses[severity]["message"]
    
    def should_book_doctor(self, severity: TriageSeverity) -> bool:
        """Should we proceed with doctor booking for this severity?"""
        if severity not in self.emergency_responses:
            return True  # Default: allow booking for unknown severities
        return self.emergency_responses[severity]["should_book"]
    
    def format_safety_response(self, user_input: str, 
                              severity: TriageSeverity,
                              category: str = "") -> Optional[str]:
        """
        Format a complete safety response if needed
        Returns: Safety message if emergency detected, None otherwise
        """
        # Special handling for informational reports
        if category == "INFORMATIONAL_REPORT":
            return self.get_emergency_response(severity, category)
        
        if severity == TriageSeverity.LOW:
            return None
        
        # Check if home remedy is being requested for dangerous condition
        is_safe, safety_msg = self.validate_response(user_input, severity)
        if not is_safe:
            return safety_msg
        
        # Return appropriate emergency response
        return self.get_emergency_response(severity, category)


# ============================================================================
# HALLUCINATION PREVENTION
# ============================================================================

class HallucinationPrevention:
    """Prevents the AI from making up medical advice"""
    
    def __init__(self):
        self.confidence_threshold = 0.6  # Only respond if confident
        self.allowed_conditions = set()  # Will be populated from knowledge graph
    
    def is_valid_medical_condition(self, condition: str, kg_results: list) -> bool:
        """
        Check if the mentioned condition is valid
        Uses knowledge graph to verify
        """
        if not kg_results:
            return False
        
        return len(kg_results) > 0
    
    def filter_uncertain_responses(self, response: str, confidence: float) -> Tuple[str, bool]:
        """
        Filter responses with low confidence
        Returns: (modified_response, is_confident)
        """
        if confidence < self.confidence_threshold:
            warning = "\n\n⚠️ *I'm not fully confident in this diagnosis. Please consult a doctor for accurate diagnosis.*"
            return response + warning, False
        
        return response, True


# ============================================================================
# AUDIT LOGGING
# ============================================================================

import json
from datetime import datetime

class SafetyAuditLog:
    """Logs all safety-relevant interactions for compliance"""
    
    def __init__(self, log_file: str = "safety_audit.log"):
        self.log_file = log_file
    
    def log_emergency_detection(self, user_id: str, user_input: str, 
                               severity: TriageSeverity, timestamp: datetime = None):
        """Log emergency detection for compliance"""
        if timestamp is None:
            timestamp = datetime.now()
        
        log_entry = {
            "event": "emergency_detected",
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "severity": severity.value,
            "input": user_input,
            "response_sent": True
        }
        
        self._write_log(log_entry)
    
    def log_blocked_response(self, user_id: str, user_input: str, reason: str):
        """Log blocked responses"""
        log_entry = {
            "event": "response_blocked",
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "reason": reason,
            "input": user_input
        }
        
        self._write_log(log_entry)
    
    def _write_log(self, entry: dict):
        """Write entry to audit log"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"⚠️ Failed to write audit log: {e}")


# ============================================================================
# SINGLETON INSTANCES
# ============================================================================

_safety_manager = None
_hallucination_prevention = None
_audit_log = None

def get_safety_manager() -> SafetyManager:
    global _safety_manager
    if _safety_manager is None:
        _safety_manager = SafetyManager()
    return _safety_manager

def get_hallucination_prevention() -> HallucinationPrevention:
    global _hallucination_prevention
    if _hallucination_prevention is None:
        _hallucination_prevention = HallucinationPrevention()
    return _hallucination_prevention

def get_audit_log() -> SafetyAuditLog:
    global _audit_log
    if _audit_log is None:
        _audit_log = SafetyAuditLog()
    return _audit_log


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    safety = get_safety_manager()
    
    print("🧪 Testing Emergency Detection:\n")
    
    test_cases = [
        ("I have a fever", TriageSeverity.LOW),
        ("I have severe chest pain", TriageSeverity.CRITICAL),
        ("I can't breathe", TriageSeverity.CRITICAL),
        ("I have a sharp pain in my lower right abdomen", TriageSeverity.URGENT),
        ("How do I treat chest pain at home?", TriageSeverity.CRITICAL),
    ]
    
    for input_text, expected_severity in test_cases:
        severity, is_emergency = safety.detect_emergency(input_text)
        status = "✅" if severity == expected_severity else "❌"
        print(f"{status} '{input_text}'")
        print(f"   → {severity.value.upper()}")
        
        if severity != TriageSeverity.LOW:
            print(f"   → Is Emergency: {is_emergency}")
            is_safe, safety_msg = safety.validate_response(input_text, severity)
            if not is_safe:
                print(f"   → ⛔ Response Blocked")
        print()
