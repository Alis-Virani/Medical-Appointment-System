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
        # Critical keywords that indicate life-threatening emergencies
        self.critical_keywords = {
            # Cardiac emergencies
            "chest pain": TriageSeverity.CRITICAL,
            "chest tightness": TriageSeverity.CRITICAL,
            "difficulty breathing": TriageSeverity.CRITICAL,
            "shortness of breath": TriageSeverity.CRITICAL,
            "heart attack": TriageSeverity.CRITICAL,
            "cardiac arrest": TriageSeverity.CRITICAL,
            "severe chest": TriageSeverity.CRITICAL,
            
            # Neurological emergencies
            "stroke": TriageSeverity.CRITICAL,
            "unconscious": TriageSeverity.CRITICAL,
            "severe headache": TriageSeverity.CRITICAL,
            "loss of consciousness": TriageSeverity.CRITICAL,
            "paralysis": TriageSeverity.CRITICAL,
            "facial drooping": TriageSeverity.CRITICAL,
            "sudden numbness": TriageSeverity.CRITICAL,
            
            # Severe bleeding
            "severe bleeding": TriageSeverity.CRITICAL,
            "uncontrolled bleeding": TriageSeverity.CRITICAL,
            "heavy bleeding": TriageSeverity.CRITICAL,
            "bleeding won't stop": TriageSeverity.CRITICAL,
            
            # Respiratory emergencies
            "can't breathe": TriageSeverity.CRITICAL,
            "choking": TriageSeverity.CRITICAL,
            "severe asthma": TriageSeverity.CRITICAL,
            "anaphylaxis": TriageSeverity.CRITICAL,
            "severe allergic reaction": TriageSeverity.CRITICAL,
            
            # Severe trauma
            "major accident": TriageSeverity.CRITICAL,
            "severe burn": TriageSeverity.CRITICAL,
            "chemical burn": TriageSeverity.CRITICAL,
            "poisoning": TriageSeverity.CRITICAL,
            "overdose": TriageSeverity.CRITICAL,
            
            # Abdominal emergencies
            "severe abdominal pain": TriageSeverity.URGENT,
            "sharp abdominal pain": TriageSeverity.URGENT,
            "abdominal pain with fever": TriageSeverity.URGENT,
            
            # Fever-related
            "high fever with rash": TriageSeverity.URGENT,
            "fever 105": TriageSeverity.URGENT,
            "fever with stiff neck": TriageSeverity.URGENT,
            "meningitis": TriageSeverity.CRITICAL,
        }
        
        # Home remedy prevention keywords
        # If user asks "how to treat X at home" for critical conditions
        self.home_remedy_prohibited = {
            "chest pain", "heart attack", "stroke", "severe bleeding",
            "poisoning", "overdose", "meningitis", "anaphylaxis",
            "unconscious", "severe burns", "choking"
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
    
    def detect_emergency(self, user_input: str) -> Tuple[TriageSeverity, bool]:
        """
        Detect if user input indicates a medical emergency
        Returns: (severity_level, is_emergency)
        """
        lower_input = user_input.lower()
        
        # Check against critical keywords
        for keyword, severity in self.critical_keywords.items():
            if keyword in lower_input:
                return severity, True
        
        return TriageSeverity.LOW, False
    
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
    
    def get_emergency_response(self, severity: TriageSeverity) -> str:
        """Get appropriate emergency response message"""
        if severity not in self.emergency_responses:
            return ""  # No special response for non-critical
        return self.emergency_responses[severity]["message"]
    
    def should_book_doctor(self, severity: TriageSeverity) -> bool:
        """Should we proceed with doctor booking for this severity?"""
        if severity not in self.emergency_responses:
            return True  # Default: allow booking for unknown severities
        return self.emergency_responses[severity]["should_book"]
    
    def format_safety_response(self, user_input: str, 
                              severity: TriageSeverity) -> Optional[str]:
        """
        Format a complete safety response if needed
        Returns: Safety message if emergency detected, None otherwise
        """
        if severity == TriageSeverity.LOW:
            return None
        
        # Check if home remedy is being requested for dangerous condition
        is_safe, safety_msg = self.validate_response(user_input, severity)
        if not is_safe:
            return safety_msg
        
        # Return appropriate emergency response
        return self.get_emergency_response(severity)


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
