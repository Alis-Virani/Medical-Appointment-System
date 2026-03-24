"""
medical_knowledge_integration.py — Integration helpers for using medical knowledge in agent responses
This module provides utilities to enrich agent responses with medical data
"""

from knowledge_graph import get_knowledge_graph
from vector_store import get_vector_store
from typing import List, Dict, Optional

def get_condition_information(condition_name: str) -> Optional[Dict]:
    """Get detailed information about a medical condition"""
    kg = get_knowledge_graph()
    condition_info = kg.get_condition_details(condition_name)
    
    if condition_info:
        return {
            "condition": condition_name,
            "severity": condition_info.get("severity", "unknown"),
            "symptoms": condition_info.get("symptoms", []),
            "causes": condition_info.get("causes", [])
        }
    return None


def get_herb_recommendations(condition: str) -> List[Dict]:
    """Get recommended herbs for a condition"""
    kg = get_knowledge_graph()
    herbs = kg.get_herb_for_condition(condition)
    
    return [
        {
            "herb": h["herb"],
            "dosage": h["dosage"],
            "benefits": h["benefits"]
        }
        for h in herbs
    ]


def check_medication_safety(drug1: str, drug2: str) -> Optional[Dict]:
    """Check if two medications have dangerous interactions"""
    kg = get_knowledge_graph()
    interaction = kg.check_drug_interaction(drug1, drug2)
    
    if interaction:
        return {
            "safe": False,
            "drugs": f"{interaction['drug1']} + {interaction['drug2']}",
            "severity": interaction["severity"],
            "effect": interaction["effect"],
            "warning": f"⚠️ {interaction['severity'].upper()} SEVERITY: {interaction['effect']}"
        }
    return {"safe": True, "drugs": f"{drug1} + {drug2}"}


def search_medical_knowledge(query: str, n_results: int = 3) -> Dict:
    """Semantic search across medical knowledge base"""
    store = get_vector_store("medical_knowledge")
    results = store.search(query, n_results=n_results)
    
    formatted_results = []
    if results.get("documents") and results["documents"][0]:
        for doc, meta, score in zip(
            results["documents"][0],
            results.get("metadatas", [[]])[0],
            results.get("distances", [[]])[0]
        ):
            formatted_results.append({
                "type": meta.get("type", "unknown"),
                "content": doc,
                "relevance": f"{score:.1%}",
                "metadata": meta
            })
    
    return {
        "query": query,
        "results_found": len(formatted_results),
        "results": formatted_results
    }


def format_medical_response(condition: str, include_herbs: bool = True, include_severity: bool = True) -> str:
    """Format medical information for agent response"""
    kg = get_knowledge_graph()
    
    condition_info = kg.get_condition_details(condition)
    if not condition_info:
        return f"I don't have detailed information about {condition} in my knowledge base."
    
    response = f"\n**{condition}**"
    
    if include_severity:
        severity = condition_info.get("severity", "unknown").upper()
        response += f"\n• Severity: {severity}"
    
    symptoms = condition_info.get("symptoms", [])
    if symptoms:
        response += f"\n• Common Symptoms: {', '.join(symptoms[:3])}"
    
    if include_herbs:
        herbs = kg.get_herb_for_condition(condition)
        if herbs:
            response += "\n• Natural Remedies:"
            for herb in herbs[:2]:
                response += f"\n  - {herb['herb']}: {herb['dosage']}"
    
    return response


def analyze_drug_interaction_risk(medications: List[str]) -> Dict:
    """Analyze interaction risk for multiple medications"""
    kg = get_knowledge_graph()
    
    interactions = []
    warnings = []
    safe_pairs = []
    
    for i, drug1 in enumerate(medications):
        for drug2 in medications[i+1:]:
            interaction = kg.check_drug_interaction(drug1, drug2)
            if interaction:
                interactions.append(interaction)
                if interaction["severity"] == "high":
                    warnings.append(f"{drug1} + {drug2}: {interaction['effect']}")
            else:
                safe_pairs.append(f"{drug1} + {drug2}")
    
    return {
        "total_combinations": len(medications) * (len(medications) - 1) // 2,
        "interactions_found": len(interactions),
        "high_severity_count": len(warnings),
        "warnings": warnings,
        "safe_pairs": safe_pairs,
        "all_safe": len(interactions) == 0
    }


# ============================================================================
# AGENT INTEGRATION EXAMPLES
# ============================================================================

def create_medical_context_prompt(user_query: str) -> str:
    """Create enriched prompt context for medical queries"""
    
    # Search medical knowledge base
    search_results = search_medical_knowledge(user_query, n_results=2)
    
    context = "Medical Knowledge Base Lookup:\n"
    if search_results["results_found"] > 0:
        for result in search_results["results"]:
            context += f"\n- [{result['type']}] {result['content'][:100]}..."
    else:
        context += "\nNo directly matching medical data found."
    
    return context


def enrich_agent_response_with_medical_data(agent_response: str, medical_keywords: List[str]) -> str:
    """Add medical knowledge to agent response"""
    
    enriched = agent_response
    
    for keyword in medical_keywords:
        # Try to append herb recommendations if it's a condition
        herbs = get_herb_recommendations(keyword)
        if herbs:
            enriched += f"\n\n💚 **Natural Remedies for {keyword}:**"
            for herb in herbs[:2]:
                enriched += f"\n- {herb['herb']}: {herb['dosage']}"
    
    return enriched


# ============================================================================
# USAGE IN LANG_GRAPH AGENT
# ============================================================================
"""
Example integration in lang_graph_agent.py nodes:

def medical_info_node(state: AgentState):
    # Get medical context
    symptoms = state.get("symptoms", [])
    context = create_medical_context_prompt(" ".join(symptoms))
    
    # Build prompt
    system_msg = SystemMessage(content=f\"\"\"
    You are a medical information assistant. Use the following medical knowledge base data:
    
    {context}
    
    Answer the user's medical question based on this information.
    Suggest natural remedies where appropriate.
    Always warn about potential drug interactions.
    \"\"\")
    
    messages = [system_msg] + state["messages"]
    
    llm = get_llm(temperature=0.3)
    response = llm.invoke(messages)
    
    # Enrich response with medical data
    medical_keywords = extract_keywords_from_messages(state["messages"])
    enriched_response = enrich_agent_response_with_medical_data(
        response.content,
        medical_keywords
    )
    
    return {
        "messages": state["messages"] + [AIMessage(content=enriched_response)]
    }


def drug_interaction_check_node(state: AgentState):
    # Extract medications mentioned
    medications = extract_medications_from_messages(state["messages"])
    
    if len(medications) >= 2:
        risk_analysis = analyze_drug_interaction_risk(medications)
        
        if risk_analysis["high_severity_count"] > 0:
            warning_msg = f\"\"\"
            ⚠️ DRUG INTERACTION WARNING:
            {chr(10).join(risk_analysis['warnings'])}
            
            Please consult with a healthcare provider before taking these combinations.
            \"\"\"
            
            return {
                "messages": state["messages"] + [AIMessage(content=warning_msg)]
            }
    
    return state
"""
