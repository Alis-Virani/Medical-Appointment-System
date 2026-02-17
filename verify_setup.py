
import sys

def check_import(module_name):
    try:
        __import__(module_name)
        print(f"✅ {module_name} installed")
    except ImportError as e:
        print(f"❌ {module_name} MISSING: {e}")

print("--- Verifying Installation ---")
modules = [
    "streamlit",
    "langchain",
    "langgraph",
    "mem0",
    "chromadb",
    "sentence_transformers",
    "pdfplumber",
    "pytesseract",
    "PIL",
    "neo4j",
    "dotenv"
]

for mod in modules:
    check_import(mod)

print("\n--- Python Version ---")
print(sys.version)
