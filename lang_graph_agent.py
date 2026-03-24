
from typing import TypedDict, Annotated, List, Dict, Union
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from knowledge_graph import get_knowledge_graph
from safety_layer import get_safety_manager, TriageSeverity
from vector_store import get_vector_store
from memory_layer import get_patient_memory
from tools import get_booking_history_tool
from database import find_doctors_in_db, find_doctor_by_name, add_doctor_dynamic, find_medicines_for_symptoms, search_doctors_smart
import json
import os
from dotenv import load_dotenv

load_dotenv()

# --- SINGLETON LLM INSTANCES ---
# Create once at module load — avoids reconnecting on every node call
_llm_fast = None    # temperature=0   for classification / extraction
_llm_chat = None    # temperature=0.5 for conversational responses
_llm_analysis = None  # temperature=0.3 for report analysis

def get_llm(temperature: float = 0):
    """Return a cached LLM instance for the given temperature bucket."""
    global _llm_fast, _llm_chat, _llm_analysis
    if temperature == 0:
        if _llm_fast is None:
            _llm_fast = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0)
        return _llm_fast
    elif temperature <= 0.3:
        if _llm_analysis is None:
            _llm_analysis = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0.3)
        return _llm_analysis
    else:
        if _llm_chat is None:
            _llm_chat = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0.5)
        return _llm_chat

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    messages: List[BaseMessage]
    user_id: str
    user_role: str  # "patient" or "doctor"
    symptoms: List[str]
    severity: str
    diagnosis: str
    specialist: str
    city: str
    doctors: List[Dict]
    is_emergency: bool
    safe_to_proceed: bool
    needs_more_info: bool
    memory_context: str
    input_type: str # "general", "medical", or "analysis" (NEW)
    ask_for_city: bool 
    booking_requested: bool
    emergency_category: str # (NEW) Category of emergency or report
    medical_info_request: bool

# ... (nodes) ...

# --- NODE FUNCTIONS ---

def input_guardrails(state: AgentState):
    """Check for emergency and safety"""
    last_msg = state["messages"][-1].content
    safety = get_safety_manager()
    severity, is_emergency, category = safety.detect_emergency(last_msg)
    
    # Critical Emergency -> Block everything
    if is_emergency:
        return {
            "severity": severity.value, 
            "is_emergency": True,
            "safe_to_proceed": False,
            "emergency_category": category
        }
    
    # Informational Report -> Mark as analysis (but don't force it if user is asking to book)
    # Check if current message contains explicit booking/appointment requests
    lower_msg = last_msg.lower()
    booking_keywords = ["book", "appointment", "schedule", "reserve", "doctor needed"]
    is_booking_request = any(keyword in lower_msg for keyword in booking_keywords)
    
    if category == "INFORMATIONAL_REPORT" and not is_booking_request:
        # Force analysis mode only if NOT a booking request
        return {
            "is_emergency": False,
            "safe_to_proceed": True,
            "input_type": "analysis",
            "emergency_category": category
        }
    
    # Otherwise, let router classify normally
    return {
        "is_emergency": False,
        "safe_to_proceed": True,
        "emergency_category": category
    }

# Off-topic keywords that have nothing to do with health/appointments
_OFF_TOPIC_PATTERNS = [
    # politics / government
    "prime minister", "president", " pm of", "chief minister", "election", "parliament",
    "minister", "politician", "government", "bjp", "congress party", "modi", "rahul gandhi",
    # geography / capital cities (non-medical)
    "capital of", "currency of", "population of", "largest country",
    # entertainment
    "cricket", "ipl", "football", "movie", "actor", "actress", "bollywood", "celebrity",
    # technology (non-medical)
    "programming", "coding", "javascript", "python tutorial", "machine learning",
    # other
    "recipe", "cook", "weather today", "stock price", "stock market",
]

def _is_off_topic(text: str) -> bool:
    lower = text.lower()
    return any(p in lower for p in _OFF_TOPIC_PATTERNS)

def router_node(state: AgentState):
    """Classify intent: Booking History, Medical, Analysis, or General"""
    if state.get("ask_for_city"):
        return {"input_type": "medical"}

    if state["is_emergency"]:
        return {"input_type": "medical"} 
    
    last_msg = state["messages"][-1].content
    lower_msg = last_msg.lower().strip()
    
    # ← NEW: Simple greetings/small talk ALWAYS go to general chat
    # This prevents "hey", "hi", "hello", "ok thanks" from being misclassified
    simple_greetings = [
        "hey", "hi", "hello", "hey there", "hi there", "howdy",
        "thanks", "thank you", "ok", "okay", "sure", "yes", "no",
        "bye", "goodbye", "see you", "thanks!", "thanks so much",
        "cool", "great", "perfect", "got it", "understood",
        "ok thanks", "thanks ok", "alright", "sounds good"
    ]
    if lower_msg in simple_greetings or len(lower_msg) < 4:  # Very short phrases
        return {"input_type": "general"}

    # --- REPORT CONTEXT always wins: must be checked FIRST ---
    # If the message contains an uploaded report, the user is asking about it.
    # Never let booking state or any keyword override this.
    if "[MEDICAL REPORT CONTEXT]" in last_msg:
        return {"input_type": "analysis", "booking_requested": False}

    # --- If already mid-booking-flow, keep the context alive ---
    # Short follow-up answers ("yes", "orthopedic", "Jamnagar") should continue
    # the booking conversation, not be re-classified from scratch.
    if state.get("booking_requested"):
        # Only break out if user clearly wants something else
        cancel_phrases = ["cancel", "nevermind", "forget it", "stop", "no thanks"]
        if not any(p in lower_msg for p in cancel_phrases):
            return {"input_type": "medical", "booking_requested": True}

    # --- NEW BOOKING detection must come FIRST ---
    # These phrases unambiguously mean the user wants to CREATE a new appointment.
    # BUT: Doctors cannot book appointments (they can only see patients)
    explicit_booking_phrases = [
        "book me", "book an", "book a", "book appointment",
        "schedule an", "schedule a", "make an appointment", "fix an appointment",
        "i want to book", "help me book", "i want to see a doctor",
        "reserve an", "want to schedule", "need an appointment",
    ]
    if any(phrase in lower_msg for phrase in explicit_booking_phrases):
        # Doctors cannot book appointments - they manage their own schedules
        if state.get("user_role") == "doctor":
            return {"input_type": "medical", "booking_requested": False}
        return {"input_type": "medical", "booking_requested": True}

    # --- BOOKING HISTORY check (only after ruling out new bookings) ---
    booking_history_keywords = ["previous appointment", "last appointment", "past appointment",
                                "upcoming appointment", "my appointment", "when was my",
                                "when did i see", "past visit", "last visit", "booking history"]
    if any(keyword in lower_msg for keyword in booking_history_keywords):
        return {"input_type": "booking_history"}
    
    llm = get_llm(0)
    
    # Updated Prompt to detect analysis requests
    prompt = f"""
    Classify the user's INTENT into one of four categories.
    NOTE: The text may contain a [MEDICAL REPORT CONTEXT] block — ignore its content when classifying; focus only on what the user is asking.

    Categories:
    1. "analysis": User asks to read, analyze, explain, summarize, or ask a question about an uploaded document/report.
    2. "booking": User explicitly wants to BOOK or SCHEDULE a new appointment (e.g., "book me a doctor", "I want to schedule").
    3. "medical": User describes symptoms, asks about a disease, or asks a general health question.
    4. "general": User is greeting, saying hello/bye, or making small talk.
    
    User text: "{last_msg[-600:]}"
    
    Return ONLY the category name (lowercase).
    """
    
    try:
        category = llm.invoke(prompt).content.strip().lower()
        if "analysis" in category or "report" in category or "document" in category:
            return {"input_type": "analysis"}
        elif "booking" in category:
            # Doctors cannot book appointments
            if state.get("user_role") == "doctor":
                return {"input_type": "medical", "booking_requested": False}
            return {"input_type": "medical", "booking_requested": True}
        elif "medical" in category:
            return {"input_type": "medical"}
        else:
            return {"input_type": "general"}
    except:
        return {"input_type": "general"}

def general_chat_node(state: AgentState):
    """Handle general conversation — medical scope only"""
    last_msg = state["messages"][-1].content

    # Fast off-topic block — no LLM call needed
    if _is_off_topic(last_msg):
        return {"messages": [AIMessage(
            content="I'm MediCare AI, a medical appointment assistant. "
                    "I can only help with health-related questions, symptoms, "
                    "doctor bookings, and medical reports. "
                    "Please ask me something related to your health! 🩺"
        )]}

    llm = get_llm(0.5)
    system_prompt = (
        "You are MediCare AI, a medical appointment assistant. "
        "Your ONLY purpose is to help users with: health symptoms, medical conditions, "
        "doctor appointments, medical reports, and general health advice. "
        "STRICT RULE: If the user asks ANYTHING unrelated to health or medicine "
        "(politics, sports, entertainment, geography, cooking, technology, etc.), "
        "respond ONLY with: 'I'm a medical assistant and can only help with health-related topics. "
        "Please ask me about your symptoms, health concerns, or doctor appointments.' "
        "Do NOT answer off-topic questions under any circumstances."
    )
    response = llm.invoke([SystemMessage(content=system_prompt), state["messages"][-1]])
    return {"messages": [response]}

def booking_history_node(state: AgentState):
    """Handle booking history queries"""
    llm = get_llm(0.3)
    last_msg = state["messages"][-1].content
    user_id = state.get("user_id", "default_user")
    
    # Determine query type from the message
    lower_msg = last_msg.lower()
    if "upcoming" in lower_msg or "next" in lower_msg or "scheduled" in lower_msg:
        query_type = "upcoming"
    elif "past" in lower_msg or "previous" in lower_msg or "old" in lower_msg:
        query_type = "past"
    elif "all" in lower_msg or "show all" in lower_msg or "list all" in lower_msg:
        query_type = "all"
    else:
        query_type = "last"  # Default to last booking
    
    # Get booking history
    booking_data = get_booking_history_tool(user_id, query_type)
    
    # Format the response
    system_prompt = f"""
    You are MediCare AI medical assistant. The user asked about their booking history.
    
    Booking Data Retrieved:
    {json.dumps(booking_data, indent=2)}
    
    Your Task:
    1. If there are bookings, present them in a friendly, easy-to-read format
    2. Include doctor name, specialty, city, and appointment date/time
    3. If no bookings found, let them know kindly and offer to help them book a new appointment
    4. For "last booking", emphasize when it was
    5. For "upcoming", highlight the next appointments
    
    Keep the response concise and helpful.
    """
    
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=last_msg)])
    return {"messages": [response]}

def analysis_node(state: AgentState):
    """Handle document/report analysis and general medical questions"""
    llm = get_llm(0.3)

    last_msg_content = state["messages"][-1].content

    # ── Semantic search: find relevant past reports from ChromaDB ──
    # Extract the user's actual question (without the [MEDICAL REPORT CONTEXT] block)
    search_query = last_msg_content
    if "[MEDICAL REPORT CONTEXT]" in search_query:
        parts = search_query.split("User Question:")
        search_query = parts[-1].strip() if len(parts) > 1 else search_query[-300:]

    past_reports_section = ""
    user_id = str(state.get("user_id", ""))
    try:
        import concurrent.futures
        def _do_vector_search():
            vs = get_vector_store(collection_name="patient_reports")
            if not vs.collection:
                return ""
            # Use user-scoped search so results are isolated per patient
            if user_id:
                results = vs.search_by_user(search_query, user_id=user_id, n_results=3)
            else:
                results = vs.search(search_query, n_results=3)
            docs  = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]
            if not docs:
                return ""
            snippets = []
            seen_files: set = set()
            for doc, meta, dist in zip(docs, metas, dists):
                fname = meta.get("filename", "previous report")
                chunk_idx = meta.get("chunk_index", 0)
                # One snippet per file to avoid repeating the same report
                file_key = fname
                if file_key in seen_files:
                    continue
                seen_files.add(file_key)
                confidence = f"{(1 - dist) * 100:.0f}%"  # cosine similarity %
                snippets.append(
                    f"[Past Report — {fname} | relevance {confidence}]\n{doc[:800]}"
                )
            if not snippets:
                return ""
            return (
                "\n\nRelevant Past Reports Retrieved from Your History:\n"
                + "\n\n".join(snippets)
                + "\n(Use these ONLY if the current report does not contain the answer.)"
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_do_vector_search)
            try:
                past_reports_section = future.result(timeout=5)  # max 5 seconds
            except concurrent.futures.TimeoutError:
                past_reports_section = ""  # skip silently if model not cached yet
    except Exception:
        pass  # Non-critical — degrade gracefully

    system_prompt = f"""
    You are an intelligent medical report analyzer.
    The user has provided a clinical report (labeled [MEDICAL REPORT CONTEXT]).

    Category Detected: {state.get('emergency_category', 'general')}

    ⚠️ ANTI-HALLUCINATION RULES — STRICTLY FOLLOW:
    - PRIMARY source: Answer from [MEDICAL REPORT CONTEXT] first.
    - SECONDARY source: If the current report doesn't contain the answer, you may reference the past reports below.
    - Do NOT mix values between reports (e.g. don't apply cholesterol from a past report to a current one).
    - If neither source contains the information, say: "The provided reports do not contain information about [topic]."
    - Do NOT invent test results, diagnoses, medications, dosages, or doctor names.
    - If you are uncertain, say so clearly.
    {past_reports_section}

    🎯 STRUCTURED ANALYSIS REQUIRED — EXTRACT AND ORGANIZE BY SECTIONS:
    
    SECTION 1: PATIENT INFORMATION
    - Extract: Age, gender, symptoms/complaints, duration
    
    SECTION 2: TESTS CONDUCTED
    - List all tests, scans, investigations mentioned
    - Include results (normal or abnormal findings)
    
    SECTION 3: KEY FINDINGS
    - Abnormal results only
    - What was discovered
    
    SECTION 4: RISK ASSESSMENT
    - Determine overall risk: High/Medium/Low
    - Based on severity of findings
    
    SECTION 5: CLINICAL INTERPRETATION
    - What do the findings suggest?
    - Most likely condition or pattern
    
    SECTION 6: RECOMMENDED FOLLOW-UP
    - Next steps for patient
    - What to do/avoid
    
    SECTION 7: WARNING SIGNS
    - When should patient see a doctor immediately?
    - Red flags to watch for

    Your Task:
    1. If category is "INFORMATIONAL_REPORT", START with: "🟡 **Clinical Report Detected**: This appears to be a medical assessment report. I can help interpret the findings."
    2. Extract information in the EXACT sections above
    3. Provide CONFIDENCE SCORE (0-100%) for your analysis accuracy
    4. Assign RISK LEVEL (Low/Medium/High/Critical)
    5. Use plain language, easy to understand
    6. If no diagnosis appears anywhere in the provided context, clearly state that

    Be helpful, professional, transparent, and concise.
    """

    try:
        response = llm.invoke([SystemMessage(content=system_prompt), state["messages"][-1]])
        response_text = response.content
        
        # Extract confidence score from response
        import re
        confidence_score = 60
        match = re.search(r'[Cc]onfidence[:\s]*(\d+)', response_text)
        if match:
            confidence_score = int(match.group(1))
        
        # Get severity from state
        severity = state.get("severity", "medium")
        
        # Format into professional report structure with severity
        formatted_response = _format_report_response(response_text, confidence_score, severity)
        
        # Add follow-up if confidence is low
        follow_up = ""
        if confidence_score < 50:
            follow_up = "\n\n❓ **Need more info:** Could you clarify what specific findings or values from the report concern you most?"
        
        return {"messages": [AIMessage(content=formatted_response + follow_up)]}
    except:
        return {"messages": [AIMessage(content="I'm having trouble analyzing this report. Could you share the specific details or questions about it?")]}

def extract_info(state: AgentState):
    """Extract symptoms, city, SEVERITY, and BOOKING INTENT"""
    # ... (Keep existing extraction logic) ...
    # [Rest of extract_info implementation matches original file]
    existing_symptoms = state.get("symptoms", [])
    existing_city = state.get("city")
    existing_booking = state.get("booking_requested", False)
    
    if state.get("input_type") == "general":
        return {"symptoms": existing_symptoms, "city": existing_city}
        
    llm = get_llm(0)
    last_msg = state["messages"][-1].content
    lower_msg = last_msg.lower().strip()

    info_question_markers = [
        "what are symptoms of", "symptoms of", "what causes", "causes of",
        "tell me about", "what is ", "how does ", "how to prevent",
        "prevention of", "treatment of", "signs of", "is fever",
        "when ", "when does", "when do", "when will", "why does", "why do",
    ]
    self_report_markers = [
        "i have", "i am having", "i'm having", "i feel", "i am feeling",
        "my ", "me ", "for me", "suffering from", "since yesterday",
        "since morning", "having ", "got ", "my child has",
    ]
    if any(marker in lower_msg for marker in info_question_markers) and not any(
        marker in lower_msg for marker in self_report_markers
    ):
        return {
            "symptoms": existing_symptoms,
            "city": existing_city,
            "severity": state.get("severity", "low"),
            "booking_requested": existing_booking,
            "medical_info_request": True,
        }
    
    # Get conversation context (last 3 messages for symptom recall)
    recent_messages = state["messages"][-4:-1] if len(state["messages"]) > 1 else []
    def _msg_type(m):
        """Safely get message type whether m is a BaseMessage or a plain dict."""
        if isinstance(m, dict):
            return m.get("role", "unknown")
        return m.type
    def _msg_content(m):
        if isinstance(m, dict):
            return m.get("content", "")
        return m.content
    context = "\n".join([f"{_msg_type(msg)}: {_msg_content(msg)}" for msg in recent_messages])
    
    prompt = f"""
    Extract the following from the user text, considering the conversation context:
    - Symptoms (list detected symptoms from current message)
    - City (if mentioned, else null)
    - Severity (low, medium, high, critical) based on the user's tone and description.
    - Booking (true/false): Does the user explicitly ask to "book", "appointment", "see doctor", or "schedule"?
    - New_Request (true/false): Is this a COMPLETELY NEW request unrelated to previous symptoms?
      Examples of new requests:
      * "I want to check my blood report at Modi Laboratory" (NEW - lab service, not related to previous symptoms)
      * "Book appointment for blood test" (NEW - specific service)
      * "I want to see a dermatologist for skin checkup" (NEW if previous was about fever)
      * "Book me for general checkup" (CONTINUE if asking about same symptoms)
    
    Conversation Context:
    {context}
    
    Current User Text: "{last_msg}"
    
    IMPORTANT RULES:
    1. If new_request=true, IGNORE previous symptoms and only extract from current message
    2. If new_request=false AND user is requesting booking, you can recall previous symptoms
    3. If user mentions a specific lab/hospital/service (like "Modi Laboratory", "blood test"), treat as new_request=true
    
    - Medical_Info_Request (true/false): Is the user asking for general information about a condition or symptom rather than describing their own current symptoms?

    Return ONLY JSON: {{ "symptoms": [], "city": "...", "severity": "...", "booking": true/false, "new_request": true/false, "medical_info_request": true/false }}
    """
    try:
        response = llm.invoke(prompt).content
        text = response
        if "```json" in text: text = text.split("```json")[1].split("```")[0]
        elif "```" in text: text = text.split("```")[1].split("```")[0]
            
        data = json.loads(text.strip())
        
        new_symptoms = data.get("symptoms", [])
        new_booking = data.get("booking", False)
        is_new_request = data.get("new_request", False)
        
        # CONTEXT SWITCH DETECTION:
        if is_new_request:
            merged_symptoms = new_symptoms
        elif new_booking and not new_symptoms and existing_symptoms:
            merged_symptoms = existing_symptoms
        else:
            merged_symptoms = list(set(existing_symptoms + new_symptoms))
        
        new_city = data.get("city")
        merged_city = new_city if new_city else existing_city
        
        # Severity merging
        new_severity = data.get("severity", "medium").lower()
        existing_severity = state.get("severity", "medium").lower()
        severity_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        
        if is_new_request:
            merged_severity = new_severity
        else:
            if severity_order.get(existing_severity, 0) > severity_order.get(new_severity, 0):
                merged_severity = existing_severity
            else:
                merged_severity = new_severity

        return {
            "symptoms": merged_symptoms,
            "city": merged_city,
            "severity": merged_severity,
            "booking_requested": new_booking or existing_booking,
            "medical_info_request": data.get("medical_info_request", False),
        }
    except Exception as e:
        print(f"Extraction Error: {e}")
        return {
            "symptoms": existing_symptoms, 
            "city": existing_city, 
            "severity": state.get("severity", "low"),
            "booking_requested": state.get("booking_requested", False),
            "medical_info_request": False,
        }

def medical_info_node(state: AgentState):
    """Answer general medical information questions without treating them as active symptoms."""
    llm = get_llm(0.3)
    last_msg = state["messages"][-1].content

    system_prompt = (
        "You are a medical information assistant. "
        "The user is asking for general health information, not describing their own symptoms. "
        "Provide clear, well-structured information.\n\n"
        "FORMAT YOUR RESPONSE LIKE THIS:\n\n"
        "📚 **Information:**\n"
        "- Point 1\n"
        "- Point 2\n"
        "- Point 3\n"
        "- Point 4 (if relevant)\n\n"
        "📊 **Confidence: X%** (how reliable this general information is)\n\n"
        "💡 **Key Takeaway:**\n"
        "[One important point to remember]\n\n"
        "⚠️ **When to see a doctor:**\n"
        "- If any concerning symptoms appear\n"
        "- For personalized advice\n\n"
        "Keep the tone practical, easy to understand, and concise."
    )
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=last_msg)])
        response_text = response.content
        
        # Format output
        if "📚" not in response_text:
            # Simple fallback formatting
            response_text = f"📚 **Information:**\n{response_text}\n\n📊 **Confidence: 75%**\n\n⚠️ For personalized medical advice, consult a healthcare provider."
        
        return {"messages": [AIMessage(content=response_text)]}
    except:
        return {"messages": [AIMessage(content="I can help with health information. Could you rephrase your question?")]}

def booking_inquiry_node(state: AgentState):
    """
    Collect city + specialist, search DB by name or specialty, add unknown facilities dynamically.
    - If city or specialist is unknown → asks the user in-chat.
    - If both are known → searches DB (by name first, then specialty), sets them in state.
    """
    import re as _re

    # ── IMPORTANT: Doctors cannot book appointments ──────────────────────────────
    if state.get("user_role") == "doctor":
        msg = (
            "⚠️ **Doctors cannot book patient appointments!**\n\n"
            "As a doctor, you don't need to book appointments as a patient. "
            "Instead, please:\n\n"
            "• Use the **👨‍⚕️ Doctor Dashboard** to manage your schedule\n"
            "• View patient appointments\n"
            "• Update your availability\n\n"
            "If you're looking for something else, how can I help?"
        )
        return {"messages": [AIMessage(content=msg)], "booking_requested": False}

    city       = state.get("city")
    specialist = state.get("specialist")
    symptoms   = state.get("symptoms", [])

    # ── 0. Extract user's actual message (strip report context block) ──────────
    last_user_msg = ""
    if state.get("messages"):
        last_user_msg = state["messages"][-1].content.strip()
        if "[MEDICAL REPORT CONTEXT]" in last_user_msg:
            _parts = last_user_msg.split("User Question:")
            last_user_msg = _parts[-1].strip() if len(_parts) > 1 else ""

    # ── 0a. Detect explicit facility/doctor name in message ────────────────────
    # Matches e.g. "Modi Laboratory", "Apollo Diagnostic Centre", "City Hospital"
    explicit_facility = None
    _FACILITY_PAT = (
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+'
        r'(?:laboratory|lab|hospital|clinic|centre|center'
        r'|diagnostic|diagnostics|pathology|nursing\s+home|dispensary))\b'
    )
    _fac_match = _re.search(_FACILITY_PAT, last_user_msg, _re.IGNORECASE)
    if _fac_match:
        explicit_facility = _fac_match.group(1).strip()

    # ── 0b. Map service keywords → specialty ───────────────────────────────────
    _SERVICE_TO_SPEC = {
        "blood test": "Pathology/Laboratory",
        "blood checkup": "Pathology/Laboratory",
        "blood work": "Pathology/Laboratory",
        "lab test": "Pathology/Laboratory",
        "urine test": "Pathology/Laboratory",
        "x-ray": "Radiology", "xray": "Radiology",
        "mri": "Radiology", "ct scan": "Radiology",
        "ultrasound": "Radiology/Sonography",
        "sonography": "Radiology/Sonography",
        "ecg": "Cardiology/Diagnostics",
        "eye test": "Ophthalmologist",
        "dental": "Dentist",
        "physiotherapy": "Physiotherapist",
    }
    _lower_msg = last_user_msg.lower()
    if not specialist:
        for _svc, _spec in _SERVICE_TO_SPEC.items():
            if _svc in _lower_msg:
                specialist = _spec
                break

    # ── 0c. ANTI-HALLUCINATION: Reject non-doctor services ──────────────────────
    # These are diagnostic/lab services, not doctor appointments
    _NON_DOCTOR_SERVICES = {
        "pathology/laboratory": ["blood test", "blood checkup", "urine", "culture", "lab"],
        "radiology": ["xray", "x-ray", "mri", "ct scan", "ultrasound", "sonography"],
        "cardiology/diagnostics": ["ecg", "ekg"],
    }
    
    # Check if specialist is a lab/diagnostic service (not a doctor)
    is_non_doctor_service = False
    if specialist:
        specialist_lower = specialist.lower()
        for service_type in _NON_DOCTOR_SERVICES.keys():
            if service_type in specialist_lower:
                is_non_doctor_service = True
                break
    
    # OR check if explicit facility is a lab/diagnostic facility
    if explicit_facility and not is_non_doctor_service:
        facility_lower = explicit_facility.lower()
        lab_indicators = ["laboratory", "lab", "diagnostic", "diagnostics", "pathology", "radiology", "imaging"]
        if any(indicator in facility_lower for indicator in lab_indicators):
            is_non_doctor_service = True
    
    # If it's a non-doctor service, reject and provide guidance
    if is_non_doctor_service:
        msg = (
            f"💡 I see you're looking for a **diagnostic/lab service** "
            f"{'('+explicit_facility+')' if explicit_facility else ''}, "
            f"not a doctor appointment.\n\n"
            "**We specialize in doctor bookings only.** For lab tests, pathology, imaging (X-ray, MRI, ultrasound), "
            "or other diagnostic services, please contact the facility directly.\n\n"
            "**Can I help you with something else?**\n"
            "- 🩺 Find a doctor in your area?\n"
            "- 💊 Discuss symptoms?\n"
            "- 📋 Analyze a medical report?"
        )
        return {"messages": [AIMessage(content=msg)], "booking_requested": False}

    # ── 1. Pick up specialist from user message ─────────────────────────
    # (handles replies like "orthopedic", "cardiologist", "skin doctor", etc.)
    if not specialist and last_user_msg:
        KNOWN_SPECIALISTS = [
            "cardiologist", "orthopedic", "orthopedist", "dermatologist",
            "neurologist", "pediatrician", "general physician", "gynaecologist",
            "gynecologist", "psychiatrist", "ophthalmologist", "ent specialist",
            "urologist", "nephrologist", "oncologist", "endocrinologist",
            "pulmonologist", "gastroenterologist", "rheumatologist",
            "general surgeon", "dentist", "physiotherapist",
        ]
        _lower = last_user_msg.lower()
        for _spec in KNOWN_SPECIALISTS:
            if _re.search(r'\b' + _re.escape(_spec) + r'\b', _lower):
                specialist = _spec.title()
                break
        SYMPTOM_TO_SPEC = {
            "skin": "Dermatologist", "heart": "Cardiologist",
            "bone": "Orthopedic", "brain": "Neurologist",
            "child": "Pediatrician", "eye": "Ophthalmologist",
            "teeth": "Dentist", "tooth": "Dentist",
        }
        if not specialist:
            for _kw, _sp in SYMPTOM_TO_SPEC.items():
                if _re.search(r'\b' + _kw + r'\b', _lower):
                    specialist = _sp
                    break

    # Try to infer specialist from symptoms if not already known
    if not specialist and symptoms:
        llm = get_llm(0)
        try:
            result = llm.invoke(
                f"Based on these symptoms: {symptoms}, what single medical specialist is most needed? "
                f"Reply with ONLY the specialist name (e.g. Cardiologist, Dermatologist, Orthopedic, General Physician, Neurologist)."
            )
            specialist = result.content.strip().split('\n')[0]
        except:
            specialist = None

    # Ask for whichever piece of info is still missing
    if not city and not specialist:
        msg = (
            "To find the right doctor and book your appointment, I need two quick details:\n\n"
            "1. 🏙️ **Which city are you in?** (e.g., Jamnagar, Ahmedabad, Surat, Vadodara, Rajkot)\n"
            "2. 🩺 **What type of specialist are you looking for?** "
            "(e.g., Cardiologist, Orthopedic, General Physician, Dermatologist)"
        )
        return {"messages": [AIMessage(content=msg)], "booking_requested": True}

    if not city:
        msg = (
            f"I can search for **{specialist}** doctors for you! 🩺\n\n"
            "Which **city** are you in? "
            "(e.g., Jamnagar, Ahmedabad, Surat, Vadodara, Rajkot, Bhavnagar, Mumbai)"
        )
        return {"messages": [AIMessage(content=msg)], "booking_requested": True, "specialist": specialist}

    if not specialist:
        msg = (
            f"Searching in **{city}**! 📍\n\n"
            "What type of doctor are you looking for?\n"
            "(e.g., Cardiologist, Orthopedic, General Physician, Dermatologist, Neurologist, Pediatrician)"
        )
        return {"messages": [AIMessage(content=msg)], "booking_requested": True, "city": city}

    # Both city and specialist are known — search DB
    # Priority: 1) named facility, 2) specialty + city, 3) specialty only
    db_results = search_doctors_smart(
        name=explicit_facility,
        specialty=specialist,
        city=city
    )

    # If named facility not found anywhere — add it dynamically so it’s bookable
    if explicit_facility and not db_results:
        inferred_spec = specialist or "General Physician"
        inferred_city = city or "Unknown"
        added = add_doctor_dynamic(
            name=explicit_facility,
            specialty=inferred_spec,
            city=inferred_city,
        )
        if added:
            db_results = [(explicit_facility, inferred_spec, "Mon-Sat 9am-6pm", inferred_city)]

    if db_results:
        doctors = [
            {
                "doctor_name": r[0],
                "specialist": r[1],
                "availability": r[2],
                "city": r[3],
                "consultation_fee": 500,
                "match_confidence": 1.0,
            }
            for r in db_results
        ]
        msg = (
            f"✅ Found **{len(doctors)}** {specialist}(s)"  
            + (f" in **{city}**" if city else "") +
            "! Please use the **📅 Book Appointment** form in the sidebar to select "
            "your preferred doctor, date and time."
        )
        return {
            "messages": [AIMessage(content=msg)],
            "doctors": doctors[:5],
            "specialist": specialist,
            "booking_requested": True,
        }
    else:
        msg = (
            f"Sorry, I couldn't find a **{specialist}** in **{city}** in our database right now. "
            "You can still fill the booking form in the sidebar to request a general appointment, "
            "or try asking for a different city or specialty."
        )
        return {"messages": [AIMessage(content=msg)], "booking_requested": True}


def _format_report_response(raw_response: str, confidence: int = 60, severity: str = "medium") -> str:
    """
    Format clinical report into CLEAN, SIMPLE, SCANNABLE format (not AI dump).
    
    Philosophy: Make it look like a smart student project, not a technical research paper.
    - Remove jargon where possible
    - Limit bullets to 3 key items
    - Add whitespace for readability
    - Focus on "what matters" not "everything"
    """
    # If already well-formatted with emojis, return as-is
    if raw_response.count('🩺') >= 2 or raw_response.count('📄') >= 1:
        return raw_response
    
    lines = raw_response.split('\n')
    sections = {
        'patient_info': [],
        'tests': [],
        'findings': [],
        'interpretation': [],
        'action': [],
        'warnings': [],
        'risk_level': 'Low'
    }
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line or 'SECTION' in line.upper():  # ← Skip lines with "SECTION X:"
            continue
        
        line_lower = line.lower()
        
        # Detect sections from content
        if any(word in line_lower for word in ['patient', 'age', 'year old', 'complaint', 'duration']):
            current_section = 'patient_info'
        elif any(word in line_lower for word in ['test', 'mri', 'scan', 'ultrasound', 'ecg', 'conducted', 'result']):
            current_section = 'tests'
        elif any(word in line_lower for word in ['finding', 'detected', 'observed', 'abnormal', 'normal']):
            current_section = 'findings'
        elif any(word in line_lower for word in ['interpretation', 'suggest', 'likely', 'appear', 'related', 'means']):
            current_section = 'interpretation'
        elif any(word in line_lower for word in ['action', 'suggest', 'recommend', 'treatment', 'continue', 'physio']):
            current_section = 'action'
        elif any(word in line_lower for word in ['when to', 'consult', 'emergency', 'warning', 'alert', 'contact']):
            current_section = 'warnings'
        elif any(word in line_lower for word in ['risk', 'critical', 'high risk', 'low risk', 'medium risk']):
            if 'high' in line_lower or 'critical' in line_lower:
                sections['risk_level'] = 'High'
            elif 'medium' in line_lower or 'moderate' in line_lower:
                sections['risk_level'] = 'Medium'
            else:
                sections['risk_level'] = 'Low'
        
        # Add content to sections
        if current_section and line and not any(cat in line_lower for cat in ['test', 'finding', 'risk', 'interpretation', 'action', 'warning', 'section']):
            # Clean up the line
            clean_line = line.lstrip('•-*').strip()
            if clean_line and len(clean_line) > 3:  # Skip very short lines
                sections[current_section].append(clean_line)
    
    # Determine risk level color
    risk_colors = {
        'High': '🔴',
        'Medium': '🟡',
        'Low': '🟢'
    }
    risk_emoji = risk_colors.get(sections['risk_level'], '🟢')
    
    # Map severity to emoji
    severity_lower = severity.lower() if severity else "medium"
    severity_map = {"critical": "🔴", "high": "🔴", "urgent": "🔴", "medium": "🟡", "low": "🟢"}
    severity_emoji = severity_map.get(severity_lower, "🟡")
    
    # Build CLEAN formatted output
    output = []
    output.append("🩺 **Report Summary:**")
    output.append("")
    
    # Patient Information (TOP 3 ONLY)
    if sections['patient_info']:
        for item in sections['patient_info'][:3]:
            output.append(f"• {item}")
        output.append("")
    
    # Tests Conducted (TOP 3 ONLY)
    if sections['tests']:
        output.append("🧪 **Tests Done:**")
        for item in sections['tests'][:3]:
            output.append(f"• {item}")
        output.append("")
    
    # Key Findings (TOP 3 ONLY)
    if sections['findings']:
        output.append("📊 **Key Findings:**")
        for item in sections['findings'][:3]:
            output.append(f"• {item}")
        output.append("")
    
    # Risk Level + Severity (SIMPLE, NOT SCARY)
    output.append(f"⚠️ **Risk Level:** {sections['risk_level']}")
    output.append("")
    
    # Interpretation (What does it MEAN in simple terms)
    if sections['interpretation']:
        output.append("💡 **What it means:**")
        for item in sections['interpretation'][:2]:
            output.append(f"• {item}")
        output.append("")
    
    # Recommended Actions (Actionable only)
    if sections['action']:
        output.append("💊 **Suggested Action:**")
        for item in sections['action'][:3]:
            output.append(f"• {item}")
        output.append("")
    
    # When to Contact Doctor (if needed)
    if sections['warnings']:
        output.append("🚨 **When to Contact a Doctor:**")
        for item in sections['warnings'][:2]:
            output.append(f"• {item}")
        output.append("")
    
    # Footer
    output.append("⚠️ **Disclaimer:** This is AI-assisted advice. Please consult a doctor.")
    
    return "\n".join(output).strip() if output else raw_response


def _format_medical_response(raw_response: str, confidence: int = 0, severity: str = "medium") -> str:
    """
    Format raw LLM response into structured medical output.
    Extracts condition, medications, advice and reformats with clear sections.
    Properly separates condition from medication with clear visual breaks.
    """
    # If already well-formatted, return as-is
    if raw_response.count('🩺') >= 2 or raw_response.count('📊') >= 1:
        return raw_response
    
    # Clean up the response
    lines = raw_response.split('\n')
    condition = ""
    explanation = ""
    medications = []
    advice = []
    warnings = []
    
    current_section = None
    skip_next = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        if skip_next:
            skip_next = False
            continue
        if not line:
            continue
        line_lower = line.lower()
        
        # Detect sections - IMPROVED PARSING
        if any(word in line_lower for word in ["condition", "disease", "diagnosis", "possible", "suspect"]):
            # Extract just the condition name (next line or after colon)
            if ":" in line:
                condition_part = line.split(":", 1)[1].strip()
                # Only take first 1-2 words (the actual condition name, not medication)
                # Medication comes later under 💊 section
                if condition_part and not any(med_word in condition_part.lower() for med_word in ["paracetamol", "ibuprofen", "aspirin", "mg", "tablet", "dose"]):
                    condition = condition_part
                    skip_next = True  # Skip the immediately following line if it looks like medication
            current_section = "condition"
        elif any(word in line_lower for word in ["medication", "medicine", "treatment", "drug", "recommended medicine"]):
            current_section = "medication"
        elif any(word in line_lower for word in ["advice", "care", "home", "rest", "hydrate"]):
            current_section = "advice"
        elif any(word in line_lower for word in ["when to see", "emergency", "warning", "critical", "alert"]):
            current_section = "warning"
        elif any(word in line_lower for word in ["explanation", "reason", "because", "based on"]):
            current_section = "explanation"
        else:
            # Add to current section ONLY if it looks like a bullet point
            if current_section == "medication" and ("•" in line or "-" in line or "format:" in line_lower):
                med_text = line.lstrip("•- ").strip()
                if med_text and not med_text.startswith(("Based", "Explanation", "Summary")):
                    medications.append(med_text)
            elif current_section == "advice" and ("•" in line or "-" in line):
                advice.append(line.lstrip("•- "))
            elif current_section == "warning" and ("•" in line or "-" in line):
                warnings.append(line.lstrip("•- "))
            elif current_section == "explanation" and line and not any(x in line_lower for x in ["medication", "medicine"]):
                explanation += line + " "
    
    # Map severity to emoji
    severity_lower = severity.lower() if severity else "medium"
    severity_map = {"critical": "🔴", "high": "🔴", "urgent": "🔴", "medium": "🟡", "low": "🟢"}
    severity_emoji = severity_map.get(severity_lower, "🟡")
    
    # Build structured response
    output = []
    
    # ← Possible Condition (ONLY the condition, not medication)
    if condition:
        output.append(f"🩺 **Possible Condition:**\n{condition}\n")
    
    # ← NEW: Severity display
    if severity:
        output.append(f"{severity_emoji} **Severity:**\n{severity_lower.upper()}\n")
    
    if confidence > 0:
        level = "Low" if confidence < 40 else "Medium" if confidence < 70 else "High"
        output.append(f"📊 **Confidence: {confidence}% ({level})**\n")
    
    if explanation:
        output.append(f"📌 **Explanation:**\n{explanation.strip()}\n")
    
    # ← Medication (SEPARATED from condition)
    if medications:
        output.append("💊 **Recommended Medication:**")
        for med in medications[:5]:
            output.append(f"  • {med}")
        output.append("")
    
    if advice:
        output.append("⚠️ **Advice:**")
        for adv in advice[:5]:
            output.append(f"  • {adv}")
        output.append("")
    
    if warnings:
        output.append("🚨 **When to See a Doctor:**")
        for warn in warnings[:5]:
            output.append(f"  • {warn}")
        output.append("")
    
    return "\n".join(output).strip() if output else raw_response


def remedy_node(state: AgentState):
    """Provide context-aware medical consultation with personalized advice based on patient history"""
    llm_analysis = get_llm(0.3)  # For context extraction
    llm_response = get_llm(0.5)  # For natural response
    symptoms = state.get("symptoms", [])
    
    # ── STEP 0: Check for uploaded report context ──────────────────────────────────
    # If user uploaded a report, use its context for remedies
    messages = state.get("messages", [])
    
    report_context = ""
    for msg in messages[-10:]:  # Look back last 10 messages
        if "[MEDICAL REPORT CONTEXT]" in msg.content:
            # Extract report context
            report_context = msg.content
            break
    
    # If have report context, extract condition from it
    if report_context:
        extract_prompt = f"""From this medical report context, extract:
1. What is the main CONDITION or FINDING?
2. What REMEDIES or TREATMENTS are mentioned?
3. What did the doctor RECOMMEND?

Report:
{report_context[:1500]}

Answer concisely."""
        try:
            extracted = llm_analysis.invoke([HumanMessage(content=extract_prompt)])
            report_info = extracted.content
        except:
            report_info = ""
    else:
        report_info = ""
    
    # ── STEP 1: If NO context (no report, no symptoms), ASK for clarification ──────
    if not report_context and not symptoms:
        return {
            "messages": [AIMessage(content="To give you the best remedies, could you please tell me:\n\n• What condition or symptom do you want remedies for?\n• Or you can upload a medical report and I'll give you remedies based on that.")]
        }
    
    # ── STEP 2: Extract full context from conversation history ──────────────────────
    # Don't just use symptoms list — analyze what actually happened
    
    # Build conversation context
    context_parts = []
    for msg in messages[-6:]:  # Last 6 messages for context
        role = "User" if msg.type == "human" else "Assistant"
        content = msg.content[:300] if msg.content else ""  # First 300 chars
        # Skip long report blocks from context
        if "[MEDICAL REPORT CONTEXT]" not in content:
            context_parts.append(f"{role}: {content}")
    
    conversation_context = "\n".join(context_parts)
    
    # ── STEP 3: Ask LLM to analyze the situation (not just template lookup) ────────
    analysis_prompt = f"""Analyze this patient's medical situation:

{f"UPLOADED REPORT INFO: {report_info}" if report_info else ""}

CONVERSATION:
{conversation_context}

Extract and answer:
1. What is the main symptom or condition?
2. What happened in the timeline?
3. What specific remedies/treatment does the patient need?
4. Is this acute or chronic?

Respond in structured format."""

    analysis_result = llm_analysis.invoke([HumanMessage(content=analysis_prompt)])
    situation_analysis = analysis_result.content
    
    # ── STEP 4: Fetch verified medicines from DB ──────────────────────────────
    verified_meds = []
    try:
        # If we have report, extract condition from it to search
        search_symptoms = symptoms
        if report_context and not symptoms:
            condition_extract = f"From this: {report_info[:200]}, what are the key symptoms or conditions? Just list them."
            try:
                cond = llm_analysis.invoke([HumanMessage(content=condition_extract)])
                # Try to extract from result
                search_symptoms = [cond.content[:50]]
            except:
                pass
        
        if search_symptoms:
            verified_meds = find_medicines_for_symptoms(search_symptoms)
    except Exception:
        pass

    # Build medicine reference block
    if verified_meds:
        otc_meds  = [m for m in verified_meds if not m["prescription_required"]]
        prx_meds  = [m for m in verified_meds if m["prescription_required"]]
        med_lines = []
        for m in otc_meds[:5]:   # max 5 OTC suggestions
            med_lines.append(
                f"  • **{m['generic_name']}** ({m['brand_names']}) — {m['dosage_note']}"
                + (f"  \u26a0\ufe0f {m['warning']}" if m['warning'] else "")
            )
        if prx_meds:
            prx_names = ", ".join(m['generic_name'] for m in prx_meds[:3])
            med_lines.append(f"  \U0001f512 *Prescription-only (mention to your doctor):* {prx_names}")
        medicine_block = "\n".join(med_lines)
    else:
        medicine_block = None

    # ── STEP 4: Generate consultant-style response with context awareness ──────────
    system_prompt = (
        "You are an experienced medical consultant, NOT a chatbot. "
        "You provide personalized, context-aware advice based on the patient's SPECIFIC situation. "
        "\n\n"
        "CONSULTANT STYLE RULES:\n"
        "1. ADDRESS THEIR SPECIFIC QUESTIONS first (e.g., if they ask 'why did it come back?' answer that directly)\n"
        "2. Consider context: previous treatment, triggers, timeline, what made it better/worse\n"
        "3. Explain WHY something is happening, not just WHAT to do\n"
        "4. Personalize advice to their situation (don't just list generic tips)\n"
        "5. Reference what they told you (e.g., 'Since you mentioned the cold shower triggered it again...')\n"
        "6. For recurrent issues, explain prevention based on triggers you identified\n"
        "\n"
        "EXPLAINABILITY REQUIREMENTS:\n"
        "1. Include a CONFIDENCE SCORE (0-100%) for your advice based on information provided\n"
        "2. Explain the REASONING behind your recommendations\n"
        "3. Clearly state assumptions you're making\n"
        "\n"
        "ANTI-HALLUCINATION RULES:\n"
        "1. MEDICINES: Use ONLY from the verified list below. No invented drugs.\n"
        "2. DOSAGES: Copy exactly as given. No modifications.\n"
        "3. CONDITIONS: Don't diagnose. Explain general patterns instead.\n"
        "\n"
        "RESPONSE STRUCTURE:\n"
        "- Start by addressing their MAIN QUESTION or concern\n"
        "- Include: **Confidence Level: X%** (How confident given the information)\n"
        "- Explain the pattern/trigger you identified\n"
        "- State your reasoning: 'Based on [specific details you mentioned]...'\n"
        "- Give specific recommendations based on their situation\n"
        "- Then home care, medicines (if applicable), warning signs\n"
        "- End with actionable next steps"
    )

    medicine_section = (
        f"\n\nVerified OTC Medicines (ONLY suggest these):\n{medicine_block}"
        if medicine_block
        else "\n\n(No specific OTC medicines matched — suggest home care instead.)"
    )

    prompt = f"""PATIENT SITUATION ANALYSIS:
{situation_analysis}

USER SYMPTOMS: {symptoms}
{medicine_section}

CONVERSATION SO FAR:
{conversation_context}

Now generate a CONSULTANT-STYLE response. Remember:
- Don't repeat generic advice — be specific to THEIR story
- Answer their questions directly
- Explain WHY things are happening
- Personalize based on what they shared
- Be conversational, not templated

IMPORTANT: Include a **Confidence: X%** score at the start of your response."""

    response = llm_response.invoke([SystemMessage(content=system_prompt), HumanMessage(content=prompt)])
    response_text = response.content
    
    # ── Extract confidence score from response ──────────────────────────────────
    confidence_score = 60  # default
    if "Confidence:" in response_text or "confidence:" in response_text:
        import re
        match = re.search(r'[Cc]onfidence[:\s]*(\d+)', response_text)
        if match:
            confidence_score = int(match.group(1))
    
    # ── Add clarifying questions if confidence is low ─────────────────────────────
    follow_up = ""
    if confidence_score < 50 and len(state.get("messages", [])) < 3:
        # Ask clarifying questions for better info
        clarifying_questions = [
            "❓ Can you tell me: Is this happening **right now** or was it in the **past**?",
            "❓ How long have you been experiencing this? (hours, days, weeks?)",
            "❓ Any recent changes or triggers that started this?",
            "❓ Are you currently taking any medications?",
            "❓ Does this tend to get better/worse at certain times?",
        ]
        # Pick 1 relevant question
        if symptoms:
            if "fever" in str(symptoms).lower():
                follow_up = "\n\n" + "❓ **Follow-up:** Are you currently running a fever right now, or did this happen before?"
            elif "pain" in str(symptoms).lower():
                follow_up = "\n\n" + "❓ **Follow-up:** On a scale of 1-10, how severe is the pain currently?"
            else:
                follow_up = "\n\n" + clarifying_questions[len(symptoms) % len(clarifying_questions)]
    
    # ── Format response into structured sections with severity ───────────────────────────────────
    severity = state.get("severity", "medium")
    formatted_response = _format_medical_response(response_text, confidence_score, severity) + follow_up
    
    return {"messages": [AIMessage(content=formatted_response)]}

def ask_city_node(state: AgentState):
    """Ask user for their city if severity is high and city is unknown"""
    return {
        "messages": [AIMessage(content="Your symptoms sound concerning. To help you find the right specialist nearby, could you please tell me which **city** you are in?")],
        "ask_for_city": True
    }

def check_memory(state: AgentState):
    """Check past history from Mem0 — disabled for performance."""
    # Mem0 initialises SentenceTransformer + ChromaDB on first call (~10-30s cold start).
    # Skip entirely so every message path stays fast.
    return {"memory_context": ""}

def graph_rag_reasoning(state: AgentState):
    """Query Neo4j for diagnosis"""
    kg = get_knowledge_graph()
    symptoms = state["symptoms"]
    city = state.get("city") or "Ahmedabad"
    
    # Try Neo4j
    results = []
    # 1. Try with specific city
    for symptom in symptoms:
        res = kg.symptom_to_specialist(symptom, city)
        results.extend(res)
        
    # 2. Retry without city if no results found
    if not results:
        print(f"⚠️ No doctors found in {city}. Retrying globally...")
        for symptom in symptoms:
             res = kg.symptom_to_specialist(symptom, city=None)
             results.extend(res)

    # 3. SQLite fallback when Neo4j is empty / unavailable
    if not results:
        specialist_hint = state.get("specialist") or (symptoms[0] if symptoms else "General Physician")
        search_city = city if city != "Ahmedabad" else None  # Ahmedabad was a hard-coded default
        db_rows = find_doctors_in_db(specialist_hint, search_city)
        if not db_rows:
            db_rows = find_doctors_in_db(specialist_hint, None)
        if db_rows:
            results = [
                {
                    "doctor_name": r[0],
                    "specialist": r[1],
                    "availability": r[2],
                    "city": r[3],
                    "disease": None,
                    "consultation_fee": 500,
                    "match_confidence": 0.5,
                }
                for r in db_rows
            ]
        
    if results:
        results.sort(key=lambda x: x.get("match_confidence", 0), reverse=True)
        top_result = results[0]
        return {
            "diagnosis": top_result.get("disease"),
            "specialist": top_result.get("specialist"),
            "doctors": results[:5]
        }
    return {"doctors": []}

def generate_response(state: AgentState):
    """Generate final response using LLM with explainability + SEVERITY"""
    if state["is_emergency"]:
        return {"messages": [AIMessage(content="🚨 **EMERGENCY DETECTED**: Please call 911 or visit the nearest emergency room immediately.")]}
    
    llm = get_llm(0.5)
    
    doctors = state["doctors"]
    doc_text = "No specific doctors found nearby."
    if doctors:
        doc_text = "\n".join([f"- Dr. {d['doctor_name']} ({d['specialist']}) in {d['city']}" for d in doctors[:3]])
    
    diagnosis_text = state.get("diagnosis", "Unknown condition")
    specialist_text = state.get("specialist", "General Physician")
    symptoms = state.get("symptoms", [])
    severity = state.get("severity", "medium").lower()  # ← GET SEVERITY
    
    # Map severity to emoji
    severity_map = {"critical": "🔴", "high": "🔴", "urgent": "🔴", "medium": "🟡", "low": "🟢"}
    severity_emoji = severity_map.get(severity, "🟡")
    
    # ── NEW: Add explainability layer ──────────────────────────────────────
    system_prompt = f"""
    You are a medical consultant providing diagnosis WITH EXPLAINABILITY.

    ⚠️ ANTI-HALLUCINATION RULES — STRICTLY FOLLOW:
    - Use ONLY the information provided below. Do NOT invent symptoms, diseases, doctors, hospitals, or medications.
    - If the diagnosis is "Unknown condition", say you are unable to determine a diagnosis and recommend seeing a doctor rather than guessing.
    - Do NOT mention doctor names, specialties, or cities that are not in the Doctors Found list.
    - Do NOT promise a specific diagnosis or treatment outcome.
    - Do NOT make assumptions about past events unless user explicitly stated them.

    Verified Context (use ONLY this):
    - User Symptoms: {symptoms}
    - Potential Condition: {diagnosis_text}
    - Recommended Specialist: {specialist_text}

    FORMAT YOUR RESPONSE EXACTLY LIKE THIS (NO VARIATIONS):

    🩺 **Possible Condition:**
    {diagnosis_text}

    📊 **Confidence: X%**
    (Base on how well symptoms match. Examples: Multiple clear symptoms = 75%, Vague symptom = 45%)

    📌 **Explanation:**
    - List the key symptom points
    - Explain why this condition matches
    - 3-4 clear bullet points

    💊 **Recommended Medication:**
    - Specific medicine (dose and frequency)
    - Format: Medicine Name (XXX mg, XXX times daily)

    ⚠️ **Care Advice:**
    - Practical step 1
    - Practical step 2
    - Practical step 3

    🚨 **When to See a Doctor:**
    - Red flag 1
    - Red flag 2
    - Red flag 3

    ⚠️ **Important Disclaimer:**
    This is AI-assisted analysis only. Please consult a {specialist_text} for final diagnosis and treatment.
    """
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), state["messages"][-1]])
        response_text = response.content
        
        # Extract confidence score
        import re
        confidence_score = 50
        match = re.search(r'[Cc]onfidence[:\s]*(\d+)', response_text)
        if match:
            confidence_score = int(match.group(1))
        
        # ← INSERT SEVERITY after "Possible Condition:" section
        severity_section = f"\n🚨 **Severity:**\n{severity.upper()}\n"
        
        # Find insertion point (right after "Possible Condition" section)
        if "📊 **Confidence:" in response_text:
            insert_pos = response_text.find("📊 **Confidence:")
            formatted_response = response_text[:insert_pos] + severity_section + response_text[insert_pos:]
        else:
            formatted_response = response_text + severity_section
        
        # Add follow-up question if confidence is low
        follow_up = ""
        if confidence_score < 50:
            follow_up = f"\n\n❓ **To give you better advice:**\n- Can you clarify if you're experiencing this **right now** or was it in the **past**?\n- Any other symptoms or triggers you can share?"
        
        # Add doctor booking recommendation
        booking_section = ""
        if doctors and len(doctors) > 0:
            booking_section = f"\n\n✅ **Next Step:** I found {len(doctors)} {specialist_text} nearby:\n{doc_text}\n\nUse the **📅 Book Appointment** form to schedule a consultation."
        
        # Format and return
        final_response = formatted_response + follow_up + booking_section
        return {"messages": [AIMessage(content=final_response)], "booking_requested": True}
    except Exception as e:
        print(f"Response generation error: {e}")
        # Fallback structured response with SEVERITY
        confidence_score = 45 if len(symptoms) < 2 else 60
        msg = f"""🩺 **Possible Condition:**
{diagnosis_text}

🚨 **Severity:**
{severity.upper()}

📊 **Confidence: {confidence_score}%**

📌 **Explanation:**
- Based on symptoms: {', '.join(symptoms) if symptoms else 'symptoms provided'}
- Needs specialist review for confirmation

💊 **Recommended Specialist:**
{specialist_text}

⚠️ **Important Disclaimer:**
This is AI-assisted analysis only. Please consult a doctor for final diagnosis.

❓ **To help better:** Can you share more details about when this started or any triggers?

Doctors Found: {len(doctors)} in your area
{doc_text}"""
        return {"messages": [AIMessage(content=msg)], "booking_requested": True}

# --- GRAPH DEFINITION ---
def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("guardrails", input_guardrails)
    workflow.add_node("router", router_node)
    workflow.add_node("general_chat", general_chat_node)
    workflow.add_node("booking_history", booking_history_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("extract", extract_info)
    workflow.add_node("medical_info", medical_info_node)
    workflow.add_node("remedies", remedy_node)
    workflow.add_node("ask_city", ask_city_node)
    workflow.add_node("booking_inquiry", booking_inquiry_node)
    workflow.add_node("memory", check_memory)
    workflow.add_node("reasoning", graph_rag_reasoning)
    workflow.add_node("response", generate_response)
    
    workflow.set_entry_point("guardrails")
    workflow.add_edge("guardrails", "router")
    
    def route_decision(state):
        if state["input_type"] == "general":
            return "general_chat"
        elif state["input_type"] == "booking_history":
            return "booking_history"
        elif state["input_type"] == "analysis": # NEW ROUTE
            return "analysis"
        return "extract"
        
    workflow.add_conditional_edges(
        "router", 
        route_decision, 
        {
            "general_chat": "general_chat", 
            "booking_history": "booking_history",
            "analysis": "analysis",
            "extract": "extract"
        }
    )
    
    workflow.add_edge("general_chat", END)
    workflow.add_edge("booking_history", END)
    workflow.add_edge("analysis", END) # Analysis ends directly
    
    # TRIAGE ROUTING LOGIC
    def triage_decision(state):
        severity = state.get("severity", "low").lower()
        city = state.get("city")
        booking = state.get("booking_requested", False)
        medical_info_request = state.get("medical_info_request", False)

        if medical_info_request:
            return "medical_info"
        
        # If booking is requested, go to booking_inquiry which handles
        # collecting city/specialist and searching SQLite for real doctors.
        if booking:
            return "booking_inquiry"
        
        # For high/critical symptoms, ask for city if unknown
        if severity in ["high", "critical"]:
            if not city:
                return "ask_city"
            return "memory"
            
        # Low/Medium and no booking request → suggest home remedies
        return "remedies"
        
    workflow.add_conditional_edges(
        "extract", 
        triage_decision, 
        {
            "medical_info": "medical_info",
            "remedies": "remedies",
            "ask_city": "ask_city",
            "booking_inquiry": "booking_inquiry",
            "memory": "memory"
        }
    )
    
    workflow.add_edge("medical_info", END)
    workflow.add_edge("remedies", END)
    workflow.add_edge("ask_city", END)
    workflow.add_edge("booking_inquiry", END) 
    
    workflow.add_edge("memory", "reasoning")
    workflow.add_edge("reasoning", "response")
    workflow.add_edge("response", END)
    
    return workflow.compile()

# Singleton (reset to None ensures graph is rebuilt on every server reload)
_graph_app = None
def get_graph_app():
    global _graph_app
    if _graph_app is None:
        _graph_app = build_graph()
    return _graph_app

def reset_graph():
    """Force rebuild of the graph (call after code changes)."""
    global _graph_app
    _graph_app = None
