

import os
from dotenv import load_dotenv
from mem0 import Memory

load_dotenv()

class PatientMemory:
    def __init__(self):
        """Initialize Mem0 for patient history"""
        # Configure Mem0 to use NVIDIA API (via OpenAI-compatible endpoint)
        config = {
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "patient_history",
                    "path": "./chroma_db"
                }
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": "all-MiniLM-L6-v2"
                }
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "mistralai/mistral-large-3-675b-instruct-2512",
                    "api_key": os.getenv("NVIDIA_API_KEY"),
                    "base_url": "https://integrate.api.nvidia.com/v1"
                }
            }
        }
        
        try:
             # Check for NVIDIA Key (Primary for this setup)
            if not os.getenv("NVIDIA_API_KEY"):
                 print("⚠️ No NVIDIA API Key found. Memory features will be disabled.")
                 self.memory = None
                 return

            self.memory = Memory.from_config(config)
            print("✅ Patient Memory Layer Initialized (using NVIDIA API)")
        except Exception as e:
            print(f"⚠️ Memory Layer Initialization Failed: {e}")
            print("   Continuing without persistent memory features.")
            self.memory = None

    def add_memory(self, user_id: str, text: str):
        """Add a memory for a user"""
        if self.memory:
            try:
                self.memory.add(text, user_id=user_id)
            except Exception as e:
                print(f"⚠️ Failed to add memory: {e}")

    def get_memories(self, user_id: str):
        """Retrieve memories for a user"""
        if self.memory:
            return self.memory.get_all(user_id=user_id)
        return []

    def search_memories(self, user_id: str, query: str):
        """Search related memories"""
        if self.memory:
            return self.memory.search(query, user_id=user_id)
        return []

# Singleton
_memory_instance = None
def get_patient_memory():
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = PatientMemory()
    return _memory_instance
