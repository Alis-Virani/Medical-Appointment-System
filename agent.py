# agent.py
import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from typing import Optional

# Fix for pydantic import
try:
    from pydantic import BaseModel, Field
except ImportError:
    from langchain_core.pydantic_v1 import BaseModel, Field

# 1. DEFINE STRUCTURE (City is now Optional)
class DoctorSearch(BaseModel):
    """Call this when the user implies a medical need."""
    specialty: str = Field(description="The medical specialty (e.g., Cardiologist, Dermatologist)")
    # We set default=None so the AI doesn't hallucinate a city if the user didn't say one
    city: Optional[str] = Field(default=None, description="The city, ONLY if explicitly mentioned.")

# 2. AGENT SETUP
def get_agent_llm():
    if not os.getenv("NVIDIA_API_KEY"):
        return None
        
    llm = ChatNVIDIA(
        model="mistralai/mistral-large-3-675b-instruct-2512",
        temperature=0.1
    )
    
    structured_llm = llm.with_structured_output(DoctorSearch)
    return structured_llm

def basic_chat_llm():
    return ChatNVIDIA(
        model="mistralai/mistral-large-3-675b-instruct-2512",
        temperature=0.1
    )