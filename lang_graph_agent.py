
from typing import TypedDict, Annotated, List, Dict, Union
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from knowledge_graph import get_knowledge_graph
from safety_layer import get_safety_manager, TriageSeverity
from vector_store import get_vector_store
from memory_layer import get_patient_memory
import json
import os
from dotenv import load_dotenv

load_dotenv()

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    messages: List[BaseMessage]
    user_id: str
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
    input_type: str # "general" or "medical"
    ask_for_city: bool 
    booking_requested: bool # New flag to override triage

# ... (nodes) ...

# --- NODE FUNCTIONS ---

def input_guardrails(state: AgentState):
    """Check for emergency and safety"""
    last_msg = state["messages"][-1].content
    safety = get_safety_manager()
    severity, is_emergency = safety.detect_emergency(last_msg)
    
    if is_emergency:
        return {
            "severity": severity.value, 
            "is_emergency": True,
            "safe_to_proceed": False
        }
    
    # If not emergency, DO NOT touch severity. 
    # Let existing state persist or let extract_info update it.
    return {
        "is_emergency": False,
        "safe_to_proceed": True
    }

def router_node(state: AgentState):
    """Classify intent: General vs Medical"""
    # 1. If we were waiting for a city, treat this input as medical/extraction info
    if state.get("ask_for_city"):
        return {"input_type": "medical"}

    if state["is_emergency"]:
        return {"input_type": "medical"} 
    
    llm = ChatNVIDIA(model="mistralai/mistral-large-3-675b-instruct-2512", temperature=0)
    last_msg = state["messages"][-1].content
    
    prompt = f"""
    Classify the following user text into one of two categories:
    1. "medical": The user is describing symptoms, asking about a disease, looking for a doctor, or asking a health question.
    2. "general": The user is greeting, saying hello/bye, asking who you are, or making small talk.
    
    Text: "{last_msg}"
    
    Return ONLY the category name (lowercase).
    """
    
    try:
        category = llm.invoke(prompt).content.strip().lower()
        if "medical" in category:
            return {"input_type": "medical"}
        else:
            return {"input_type": "general"}
    except:
        return {"input_type": "general"}

def general_chat_node(state: AgentState):
    """Handle general conversation"""
    llm = ChatNVIDIA(model="mistralai/mistral-large-3-675b-instruct-2512", temperature=0.7)
    system_prompt = "You are MediCare AI. Respond politely to general chitchat."
    response = llm.invoke([SystemMessage(content=system_prompt), state["messages"][-1]])
    return {"messages": [response]}

def extract_info(state: AgentState):
    """Extract symptoms, city, SEVERITY, and BOOKING INTENT"""
    existing_symptoms = state.get("symptoms", [])
    existing_city = state.get("city")
    existing_booking = state.get("booking_requested", False)
    
    if state.get("input_type") == "general":
        return {"symptoms": existing_symptoms, "city": existing_city}
        
    llm = ChatNVIDIA(model="mistralai/mistral-large-3-675b-instruct-2512", temperature=0)
    last_msg = state["messages"][-1].content
    
    # Get conversation context (last 3 messages for symptom recall)
    recent_messages = state["messages"][-4:-1] if len(state["messages"]) > 1 else []
    context = "\n".join([f"{msg.type}: {msg.content}" for msg in recent_messages])
    
    prompt = f"""
    Extract the following from the user text, considering the conversation context:
    - Symptoms (list detected symptoms from current OR previous messages if user is requesting booking)
    - City (if mentioned, else null)
    - Severity (low, medium, high, critical) based on the user's tone and description.
    - Booking (true/false): Does the user explicitly ask to "book", "appointment", "see doctor", or "schedule"?
    
    Conversation Context:
    {context}
    
    Current User Text: "{last_msg}"
    
    IMPORTANT: If the user is requesting a booking/appointment but doesn't mention symptoms in the current message,
    look for symptoms in the conversation context above.
    
    Return ONLY JSON: {{ "symptoms": [], "city": "...", "severity": "...", "booking": true/false }}
    """
    try:
        response = llm.invoke(prompt).content
        text = response
        if "```json" in text: text = text.split("```json")[1].split("```")[0]
        elif "```" in text: text = text.split("```")[1].split("```")[0]
            
        data = json.loads(text.strip())
        
        new_symptoms = data.get("symptoms", [])
        new_booking = data.get("booking", False)
        
        # CRITICAL FIX: If user is requesting booking but no symptoms in current message,
        # preserve existing symptoms (don't let them get lost!)
        if new_booking and not new_symptoms and existing_symptoms:
            print(f"DEBUG: Booking requested, preserving existing symptoms: {existing_symptoms}")
            merged_symptoms = existing_symptoms
        else:
            merged_symptoms = list(set(existing_symptoms + new_symptoms))
        
        print(f"DEBUG: Extracted symptoms - New: {new_symptoms}, Existing: {existing_symptoms}, Merged: {merged_symptoms}")
        
        new_city = data.get("city")
        final_city = new_city if new_city else existing_city
        
        # Merge booking: if it was true before, keep it true. Or if new input requests it.
        final_booking = existing_booking or new_booking
        
        # Merge Severity: logic to prevent accidental downgrade
        new_severity = data.get("severity", "low").lower()
        existing_severity = state.get("severity", "low").lower()
        
        # LOGIC FIX: If we specifically asked for city, IGNORE new severity (it's likely just a city name)
        # and forcefully keep the existing severity that triggered the question.
        was_asking_for_city = state.get("ask_for_city", False)
        
        if was_asking_for_city:
             print(f"DEBUG: Was asking for city, forcing severity: {existing_severity}")
             final_severity = existing_severity
        elif existing_severity in ["high", "critical"]:
             # Standard downgrade protection
            if new_severity in ["low", "medium"]:
                final_severity = existing_severity
            else:
                final_severity = new_severity
        else:
            final_severity = new_severity

        print(f"DEBUG: EXTRACT Returning Severity: {final_severity}")
        
        # Only reset ask_for_city if we actually got a city response
        new_city = data.get("city")
        should_reset_city_flag = was_asking_for_city and new_city

        return {
            "symptoms": merged_symptoms,
            "city": final_city,
            "severity": final_severity,
            "booking_requested": final_booking,
            "ask_for_city": False if should_reset_city_flag else was_asking_for_city
        }
    except Exception as e:
        print(f"Extraction Error: {e}")
        # CRITICAL FIX: Return existing severity on error, don't lose it!
        return {
            "symptoms": existing_symptoms, 
            "city": existing_city, 
            "severity": state.get("severity", "low"),
            "booking_requested": state.get("booking_requested", False)
        }

def remedy_node(state: AgentState):
    """Suggest Home Remedies for low/medium severity"""
    llm = ChatNVIDIA(model="mistralai/mistral-large-3-675b-instruct-2512", temperature=0.5)
    symptoms = state.get("symptoms", [])
    
    prompt = f"""
    The user has mild symptoms: {symptoms}.
    Suggest 3 safe, effective home remedies.
    Also advise them to see a doctor if symptoms worsen.
    Keep it concise.
    """
    response = llm.invoke([SystemMessage(content="You are a helpful medical assistant."), HumanMessage(content=prompt)])
    return {"messages": [response]}

def ask_city_node(state: AgentState):
    """Ask user for their city if severity is high and city is unknown"""
    return {
        "messages": [AIMessage(content="Your symptoms sound concerning. To help you find the right specialist nearby, could you please tell me which **city** you are in?")],
        "ask_for_city": True
    }

def check_memory(state: AgentState):
    """Check past history from Mem0"""
    mem = get_patient_memory()
    query = " ".join(state["symptoms"]) if state["symptoms"] else "medical history"
    memories = mem.search_memories(user_id=state["user_id"], query=query)
    context = ""
    if memories:
        context = "\n".join([m["memory"] for m in memories[:3]])
    return {"memory_context": context}

def graph_rag_reasoning(state: AgentState):
    """Query Neo4j for diagnosis"""
    kg = get_knowledge_graph()
    symptoms = state["symptoms"]
    city = state.get("city") or "Ahmedabad" # fallback only if we really have to
    
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
    """Generate final response using LLM"""
    if state["is_emergency"]:
        return {"messages": [AIMessage(content="🚨 **EMERGENCY DETECTED**: Please call 911 or visit the nearest emergency room immediately.")]}
    
    llm = ChatNVIDIA(model="mistralai/mistral-large-3-675b-instruct-2512", temperature=0.5)
    
    doctors = state["doctors"]
    doc_text = "No specific doctors found nearby."
    if doctors:
        doc_text = "\n".join([f"- Dr. {d['doctor_name']} ({d['specialist']}) in {d['city']} | Rating: {d.get('doctor_rating')}⭐" for d in doctors[:3]])
    
    diagnosis_text = state.get("diagnosis", "Unknown condition")
    specialist_text = state.get("specialist", "General Physician")
    memory_text = state.get("memory_context", "No previous history.")
    
    system_prompt = f"""
    You are an empathetic medical assistant.
    
    Context:
    - User Symptoms: {state['symptoms']}
    - Potential Condition: {diagnosis_text}
    - Recommended Specialist: {specialist_text}
    - Doctors Found: {len(doctors)}
    
    Task:
    1. Briefly explain the potential condition.
    2. Strongly recommend seeing the specialist: {specialist_text}.
    3. List the available doctors below.
    4. Mention that a booking form is available in the sidebar.
    """
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), state["messages"][-1]])
        return {"messages": [response]}
    except:
        msg = f"Based on your symptoms, it might be {diagnosis_text}. I recommend a {specialist_text}.\n\nDoctors:\n{doc_text}"
        return {"messages": [AIMessage(content=msg)]}

# --- GRAPH DEFINITION ---
def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("guardrails", input_guardrails)
    workflow.add_node("router", router_node)
    workflow.add_node("general_chat", general_chat_node)
    workflow.add_node("extract", extract_info)
    workflow.add_node("remedies", remedy_node)
    workflow.add_node("ask_city", ask_city_node)
    workflow.add_node("memory", check_memory)
    workflow.add_node("reasoning", graph_rag_reasoning)
    workflow.add_node("response", generate_response)
    
    workflow.set_entry_point("guardrails")
    workflow.add_edge("guardrails", "router")
    
    def route_decision(state):
        if state["input_type"] == "general":
            return "general_chat"
        return "extract"
        
    workflow.add_conditional_edges("router", route_decision, {"general_chat": "general_chat", "extract": "extract"})
    workflow.add_edge("general_chat", END)
    
    # TRIAGE ROUTING LOGIC
    def triage_decision(state):
        severity = state.get("severity", "low").lower()
        city = state.get("city")
        booking = state.get("booking_requested", False)
        
        # Override: If user wants to book, treat as High severity (find doctor)
        if booking or severity in ["high", "critical"]:
            if not city:
                return "ask_city" # Need city for doctors
            return "memory" # Have city, find doctor
            
        # If Low/Medium AND no booking request, give remedies
        return "remedies"
        
    workflow.add_conditional_edges(
        "extract", 
        triage_decision, 
        {
            "remedies": "remedies",
            "ask_city": "ask_city",
            "memory": "memory"
        }
    )
    
    workflow.add_edge("remedies", END)
    workflow.add_edge("ask_city", END) 
    
    workflow.add_edge("memory", "reasoning")
    workflow.add_edge("reasoning", "response")
    workflow.add_edge("response", END)
    
    return workflow.compile()

# Singleton
_graph_app = None
def get_graph_app():
    global _graph_app
    if _graph_app is None:
        _graph_app = build_graph()
    return _graph_app
