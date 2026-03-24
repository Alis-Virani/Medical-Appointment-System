"""
Enhanced Graph-based Agent with RAG
====================================
Replaces keyword matching with intelligent graph reasoning
"""

import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Optional, List, Dict
from knowledge_graph import get_knowledge_graph
from safety_layer import get_safety_manager, TriageSeverity

try:
    from pydantic import BaseModel, Field
except ImportError:
    from langchain_core.pydantic_v1 import BaseModel, Field


# ============================================================================
# STRUCTURED OUTPUTS
# ============================================================================

class SymptomAnalysis(BaseModel):
    """LLM output for symptom analysis"""
    symptoms: List[str] = Field(description="List of symptoms mentioned by user")
    severity: str = Field(description="Perceived severity: low, medium, high, critical")
    likely_conditions: List[str] = Field(description="Likely medical conditions")
    recommended_specialist: str = Field(description="Recommended medical specialist")
    confidence: float = Field(description="Confidence in recommendation (0-1)")


class GraphRAGAgent:
    """
    Graph-based Reasoning Agent with RAG
    
    Pipeline:
    1. User input → Safety checks (Emergency detection)
    2. LLM analysis → Extract symptoms
    3. Knowledge Graph → Multi-hop reasoning (Symptom → Disease → Specialist → Doctor)
    4. Ranking → Sort doctors by confidence + rating
    5. Response → Present best options with explanation
    """
    
    def __init__(self):
        self.kg = get_knowledge_graph()
        self.safety_manager = get_safety_manager()
        self.llm = None
        self.structured_llm = None
        self._initialize_llms()
    
    def _initialize_llms(self):
        """Initialize LLMs"""
        if not os.getenv("GROQ_API_KEY"):
            print("⚠️ GROQ_API_KEY not set. Some features will be limited.")
            return
        
        self.llm = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.3  # Lower temperature for medical accuracy
        )
        
        self.structured_llm = self.llm.with_structured_output(SymptomAnalysis)
    
    def process_user_input(self, user_input: str, user_city: Optional[str] = None,
                          session_history: List = None) -> Dict:
        """
        Simple conversational pipeline - remembers context
        """
        
        # Check for casual greetings
        greetings = ["hi", "hey", "hello", "hii", "hi there", "hey there", "howdy", "good morning", "good afternoon"]
        if user_input.lower().strip() in greetings:
            return {
                "safety_check": {"is_emergency": False, "severity": "low", "safe_to_proceed": True},
                "response": "👋 Hello! I'm your Agentic Medical Assistant. How can I help you today? Please describe your symptoms or health concerns.",
                "should_proceed": False,
                "doctors": None,
                "analysis": None
            }
        
        # ====== STEP 1: SAFETY CHECK ======
        safety_check = self._perform_safety_check(user_input)
        
        if safety_check["is_emergency"] and not safety_check["safe_to_proceed"]:
            return {
                "safety_check": safety_check,
                "response": safety_check["message"],
                "should_proceed": False,
                "doctors": None,
                "needs_hospital": True
            }
        
        # ====== STEP 2: SYMPTOM ANALYSIS ======
        analysis = self._analyze_symptoms(user_input, session_history)
        
        if not analysis:
            analysis = {
                "symptoms": ["general consultation"],
                "severity": "medium",
                "likely_conditions": [],
                "recommended_specialist": "General Physician",
                "confidence": 0.5
            }
        
        # Check conversation history for context
        has_symptom_already = self._has_previous_symptom(session_history)
        has_duration = self._has_time_keywords(user_input)
        has_location = self._has_city_mention(session_history)
        
        # New symptom detected in this message
        has_new_symptom = analysis.get("symptoms") and analysis["symptoms"][0] != "general consultation"
        
        # ====== CONVERSATIONAL FLOW ======
        
        # Case 1: New symptom detected → Ask when it started
        if has_new_symptom and not has_symptom_already:
            symptoms_str = ", ".join(analysis.get("symptoms", []))
            response_text = f"I understand you have **{symptoms_str}**. 🏥\n\n"
            response_text += "❓ **When did this start?** (e.g., since yesterday, 3 days ago, today, 2 hours ago)"
            return {
                "safety_check": safety_check,
                "analysis": analysis,
                "response": response_text,
                "doctors": None,
                "should_proceed": False
            }
        
        # Case 2: Duration provided (answering "when did it start") → Ask location
        if has_symptom_already and has_duration and not has_location:
            response_text = "Got it! 📝\n\n"
            response_text += "❓ **Which city are you in?** (Ahmedabad, Surat, Vadodara, Mumbai, etc.)\n\n"
            response_text += "I'll find the best doctors in your area."
            return {
                "safety_check": safety_check,
                "analysis": analysis,
                "response": response_text,
                "doctors": None,
                "should_proceed": False
            }
        
        # Case 3: We have symptom + duration + location → Show doctors
        if has_symptom_already and has_duration and has_location:
            city = self._extract_city_from_history(session_history) or user_city
            
            graph_results = self._perform_graph_rag(
                symptoms=analysis.get("symptoms", []),
                recommended_specialist=analysis.get("recommended_specialist", ""),
                city=city
            )
            
            doctors = self._rank_results(graph_results)
            response = self._format_response(analysis, doctors, safety_check)
            
            return {
                "safety_check": safety_check,
                "analysis": analysis,
                "graph_results": graph_results,
                "response": response,
                "doctors": doctors,
                "should_proceed": True,
                "severity": analysis.get("severity", "low")
            }
        
        # Case 4: User just provided duration, keep asking
        if has_symptom_already and has_duration:
            response_text = "❓ **Which city are you in?** (Ahmedabad, Surat, Vadodara, etc.)"
            return {
                "safety_check": safety_check,
                "analysis": analysis,
                "response": response_text,
                "doctors": None,
                "should_proceed": False
            }
        
        # Default: Ask for more details
        return {
            "safety_check": safety_check,
            "analysis": analysis,
            "response": "Could you please provide more details? (e.g., 'I have a headache', 'fever and cough', or describe your symptom more clearly?)",
            "should_proceed": False,
            "doctors": None
        }
    
    def _has_previous_symptom(self, session_history: List) -> bool:
        """Check if a symptom was already mentioned in conversation"""
        if not session_history or len(session_history) < 2:
            return False
        # If we have at least 2 messages, likely the first one was a symptom
        return True
    
    def _has_time_keywords(self, user_input: str) -> bool:
        """Check if user provided time-related information"""
        time_keywords = [
            "hour", "hours", "day", "days", "week", "weeks", "month", "months",
            "minute", "minutes", "second", "seconds",
            "ago", "yesterday", "today", "tonight", "morning", "afternoon", "evening",
            "yesterday", "last night", "since", "started", "began"
        ]
        lower_input = user_input.lower()
        return any(keyword in lower_input for keyword in time_keywords)
        """Check if session history contains any of the keywords"""
        if not session_history:
            return False
        history_text = ""
        for msg in session_history:
            if isinstance(msg, dict):
                history_text += msg.get("content", "") + " "
            elif hasattr(msg, "content"):
                history_text += msg.content + " "
        return any(keyword in history_text.lower() for keyword in keywords)
    
    def _has_city_mention(self, session_history: List) -> bool:
        """Check if city is mentioned in session history"""
        cities = ["ahmedabad", "surat", "vadodara", "mumbai", "delhi", "bangalore", "hyderabad", "pune"]
        if not session_history:
            return False
        history_text = ""
        for msg in session_history:
            if isinstance(msg, dict):
                history_text += msg.get("content", "") + " "
            elif hasattr(msg, "content"):
                history_text += msg.content + " "
        return any(city in history_text.lower() for city in cities)
    
    def _extract_city_from_history(self, session_history: List) -> Optional[str]:
        """Extract city name from session history"""
        cities = {
            "ahmedabad": "Ahmedabad",
            "surat": "Surat",
            "vadodara": "Vadodara",
            "mumbai": "Mumbai",
            "delhi": "Delhi",
            "bangalore": "Bangalore",
            "hyderabad": "Hyderabad",
            "pune": "Pune"
        }
        if not session_history:
            return None
        history_text = ""
        for msg in session_history:
            if isinstance(msg, dict):
                history_text += msg.get("content", "") + " "
            elif hasattr(msg, "content"):
                history_text += msg.content + " "
        history_text = history_text.lower()
        for city_lower, city_proper in cities.items():
            if city_lower in history_text:
                return city_proper
        return None
    
    # ========== STEP 1: SAFETY CHECK ==========
    
    def _perform_safety_check(self, user_input: str) -> Dict:
        """Perform emergency detection and safety validation"""
        severity, is_emergency = self.safety_manager.detect_emergency(user_input)
        
        is_safe, safety_msg = self.safety_manager.validate_response(user_input, severity)
        
        return {
            "is_emergency": is_emergency,
            "severity": severity.value,
            "safe_to_proceed": is_safe,
            "message": safety_msg or "",
            "should_book": self.safety_manager.should_book_doctor(severity)
        }
    
    # ========== STEP 2: LLM ANALYSIS ==========
    
    def _analyze_symptoms(self, user_input: str, session_history: List = None) -> Dict:
        """Use simple rule-based symptom analysis - fast and reliable"""
        try:
            # Use fallback analysis directly (no LLM delays)
            result = self._fallback_symptom_analysis(user_input)
            print(f"✓ Analysis result: {result}")  # Debug
            return result
        except Exception as e:
            print(f"✗ Analysis error: {e}")
            # Return safe default
            return {
                "symptoms": ["general consultation"],
                "severity": "medium",
                "likely_conditions": [],
                "recommended_specialist": "General Physician",
                "confidence": 0.5
            }
    
    def _fallback_symptom_analysis(self, user_input: str) -> Dict:
        """Simple symptom matching - just check what words are in the input"""
        lower_input = user_input.lower()
        
        # Simple keyword-to-specialist mapping
        symptom_map = {
            "headache": ("headache", "Neurologist"),
            "head pain": ("head pain", "Neurologist"),
            "migraine": ("migraine", "Neurologist"),
            "fever": ("fever", "General Physician"),
            "cold": ("cold", "General Physician"),
            "cough": ("cough", "Pulmonologist"),
            "chest pain": ("chest pain", "Cardiologist"),
            "chest": ("chest pain", "Cardiologist"),
            "heart": ("heart condition", "Cardiologist"),
            "stomach pain": ("stomach pain", "Gastroenterologist"),
            "stomach": ("stomach pain", "Gastroenterologist"),
            "eye pain": ("eye pain", "Ophthalmologist"),
            "eye": ("eye problem", "Ophthalmologist"),
            "rash": ("rash", "Dermatologist"),
            "skin": ("skin condition", "Dermatologist"),
            "throat": ("sore throat", "ENT"),
            "ear": ("ear infection", "ENT"),
            "back pain": ("back pain", "Orthopedic"),
            "joint pain": ("joint pain", "Orthopedic"),
            "bone": ("bone fracture", "Orthopedic"),
            "breathing": ("breathing problem", "Pulmonologist"),
            "asthma": ("asthma", "Pulmonologist"),
        }
        
        # Find first matching symptom
        for keyword, (symptom_name, specialist) in symptom_map.items():
            if keyword in lower_input:
                return {
                    "symptoms": [symptom_name],
                    "severity": "medium",
                    "likely_conditions": [],
                    "recommended_specialist": specialist,
                    "confidence": 0.7
                }
        
        # No match found
        return {
            "symptoms": ["general consultation"],
            "severity": "medium",
            "likely_conditions": [],
            "recommended_specialist": "General Physician",
            "confidence": 0.5
        }
    
    # ========== STEP 3: KNOWLEDGE GRAPH REASONING ==========
    
    def _perform_graph_rag(self, symptoms: List[str], recommended_specialist: str,
                          city: Optional[str] = None) -> List[Dict]:
        """
        Multi-hop graph reasoning:
        Symptom → Disease → Specialist → Doctor
        """
        results = []
        
        # Try symptom-to-specialist path for each symptom
        for symptom in symptoms:
            graph_results = self.kg.symptom_to_specialist(symptom, city)
            results.extend(graph_results)
        
        # If no results from symptom path, use direct specialist matching
        if not results and recommended_specialist:
            doctors = self.kg.recommend_doctors(recommended_specialist, city)
            for doc in doctors:
                results.append({
                    "disease": "General consultation",
                    "specialist": recommended_specialist,
                    "doctor_name": doc.get("name", "Unknown"),
                    "doctor_rating": doc.get("rating", 4.5),
                    "availability": doc.get("availability", ""),
                    "city": doc.get("city", ""),
                    "match_confidence": 0.7
                })
        
        return results
    
    # ========== STEP 4: RANKING ==========
    
    def _rank_results(self, graph_results: List[Dict]) -> List[Dict]:
        """
        Rank doctors by:
        1. Match confidence (from graph)
        2. Doctor rating
        3. Relevance
        """
        if not graph_results:
            return []
        
        # Score each doctor
        for result in graph_results:
            confidence = result.get("match_confidence", 0.7)
            rating = result.get("doctor_rating", 4.5) / 5.0
            
            # Combined score: 60% from match confidence, 40% from rating
            result["score"] = (confidence * 0.6) + (rating * 0.4)
        
        # Sort by score and remove duplicates
        sorted_results = sorted(graph_results, key=lambda x: x["score"], reverse=True)
        
        # Remove duplicate doctors, keep highest score
        seen = set()
        unique_results = []
        for result in sorted_results:
            doc_key = result.get("doctor_name", "")
            if doc_key not in seen:
                seen.add(doc_key)
                unique_results.append(result)
        
        return unique_results[:5]  # Top 5 doctors
    
    # ========== STEP 5: FORMAT RESPONSE ==========
    
    def _format_response(self, analysis: Dict, doctors: List[Dict], 
                        safety_check: Dict) -> str:
        """Format comprehensive response with precautions and clarifying questions"""
        response_parts = []
        
        # Safety alert if needed
        if safety_check["severity"] != "low":
            response_parts.append(f"⚠️ **Severity Level: {safety_check['severity'].upper()}** 🏥\n")
        
        # Analysis summary
        if analysis:
            symptoms_str = ", ".join(analysis.get("symptoms", []))
            response_parts.append(f"📋 **Symptoms detected**: {symptoms_str} 💊\n")
            
            if analysis.get("likely_conditions"):
                conditions_str = ", ".join(analysis["likely_conditions"][:2])
                response_parts.append(f"🔍 **Possible conditions**: {conditions_str}\n")
            
            response_parts.append(f"👨‍⚕️ **Recommended specialist**: {analysis['recommended_specialist']} 🏥\n")
            response_parts.append(f"💡 **Confidence**: {int(analysis.get('confidence', 0.6) * 100)}%\n")
        
        # Precautions & First Aid
        response_parts.append("\n💊 **Suggested Precautions & First Aid:**\n")
        precautions = self._get_precautions(analysis.get("likely_conditions", []))
        for precaution in precautions:
            response_parts.append(f"  • {precaution}\n")
        
        # Clarifying questions (if needed)
        response_parts.append("\n❓ **To better assist you:**\n")
        response_parts.append("  • How long have you had these symptoms?\n")
        response_parts.append("  • Any recent travel or exposure?\n")
        response_parts.append("  • Which city are you in? (for local doctor recommendations)\n")
        
        # Doctor recommendations
        if doctors:
            response_parts.append("\n**📍 Top Doctors for you:**\n")
            for i, doc in enumerate(doctors[:3], 1):
                response_parts.append(f"{i}. **Dr. {doc['doctor_name']}** ({doc['specialist']})")
                response_parts.append(f"   ⭐ {doc['doctor_rating']} | 📍 {doc['city']}")
                response_parts.append(f"   🕒 {doc['availability']}\n")
        else:
            response_parts.append("\n📌 **Please mention your city** so I can find doctors nearby for you.")
        
        # Call to action
        if safety_check["severity"] == "critical":
            response_parts.append("\n🚨 **Please seek IMMEDIATE medical attention. CALL 911 or visit ER NOW!**")
        elif doctors:
            response_parts.append("\n✅ **Ready to book?** Select a doctor above and I'll help you schedule.")
        
        return "".join(response_parts)
    
    def _get_precautions(self, conditions: List[str]) -> List[str]:
        """Get precautions/first-aid based on conditions"""
        precaution_map = {
            "malaria": [
                "Stay hydrated - drink plenty of water",
                "Rest in a cool environment",
                "Take paracetamol for fever (follow dosage)",
                "Use mosquito repellent",
                "Seek medical attention immediately"
            ],
            "pneumonia": [
                "Rest and avoid strenuous activities",
                "Stay warm and keep environment humid",
                "Drink warm fluids (tea, soup, water)",
                "Use a humidifier if available",
                "Seek immediate medical attention"
            ],
            "fever": [
                "Stay hydrated with water, coconut water, or electrolyte drinks",
                "Get complete bed rest",
                "Wear light clothing",
                "Use cool compress on forehead",
                "Avoid self-medication; consult a doctor"
            ],
            "headache": [
                "Rest in a dark, quiet room",
                "Stay hydrated",
                "Use cold or warm compress on temples",
                "Avoid bright screens",
                "Consult a doctor if persistent"
            ],
            "cough": [
                "Stay hydrated with warm liquids",
                "Use honey and lemon tea",
                "Avoid dust and pollutants",
                "Use saline gargle",
                "Seek medical attention if severe"
            ],
            "cold": [
                "Rest and stay warm",
                "Drink warm fluids",
                "Use saline nasal drops",
                "Avoid contact with others",
                "Wash hands frequently"
            ],
            "allergies": [
                "Identify and avoid triggers",
                "Use antihistamine if available",
                "Keep environment clean",
                "Wear mask if needed",
                "Consult allergist for proper diagnosis"
            ]
        }
        
        # Get precautions for detected conditions
        precautions = []
        for condition in conditions:
            condition_lower = condition.lower()
            for key in precaution_map:
                if key in condition_lower:
                    precautions.extend(precaution_map[key])
                    break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_precautions = []
        for p in precautions:
            if p not in seen:
                seen.add(p)
                unique_precautions.append(p)
        
        return unique_precautions[:5] if unique_precautions else [
            "Rest adequately",
            "Stay hydrated",
            "Monitor symptoms closely",
            "Avoid self-medication",
            "Consult a healthcare professional"
        ]


# ============================================================================
# SINGLETON
# ============================================================================

_graph_rag_agent = None

def get_graph_rag_agent() -> GraphRAGAgent:
    """Get or create the agent singleton"""
    global _graph_rag_agent
    if _graph_rag_agent is None:
        _graph_rag_agent = GraphRAGAgent()
    return _graph_rag_agent


if __name__ == "__main__":
    agent = get_graph_rag_agent()
    
    print("\n🧪 Testing Graph RAG Agent:\n")
    
    test_inputs = [
        ("I have high fever for 3 days and chills", "Ahmedabad"),
        ("Sharp pain in my lower right abdomen", "Surat"),
        ("I have a severe chest pain", None),
    ]
    
    for user_input, city in test_inputs:
        print(f"👤 User: {user_input}")
        print(f"📍 City: {city or 'Not specified'}\n")
        
        result = agent.process_user_input(user_input, city)
        
        print(f"Response:\n{result['response']}\n")
        print("=" * 80 + "\n")
