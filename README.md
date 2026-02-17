# 🩺 AGENTIC MEDICAL ASSISTANT

**Intelligent, Context-Aware AI System for Patient Triage & Doctor Booking**

## 🎯 What This Does

This is a **production-grade agentic medical assistant** that combines:

✅ **Knowledge Graph Reasoning** - Multi-hop medical intelligence (Symptom → Disease → Specialist → Doctor)  
✅ **Safety Guardrails** - Emergency detection & hallucination prevention  
✅ **Dynamic Doctor Management** - Real-time CRUD operations for doctor data  
✅ **LLM-Powered Analysis** - Understands unstructured patient symptoms  
✅ **Graph RAG Pipeline** - Intelligent reasoning with confidence scoring

## 🚀 Quick Start

### 1. Install & Setup

```bash
cd E:\Project
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python init_graph.py  # Initialize knowledge graph & doctors
```

### 2. Run the App

```bash
streamlit run app.py
```

Open: http://localhost:8501

## 📊 How It Works

```
User: "I have fever and chills in Ahmedabad"
  ↓
[SAFETY CHECK] Emergency? → ✅ Safe to proceed
  ↓
[LLM ANALYSIS] Extract symptoms → Fever, Chills
  ↓
[GRAPH RAG] Multi-hop reasoning:
  Fever + Chills → Malaria/Typhoid →
  Infectious Disease Specialist →
  Dr. Anil Trivedi (4.7⭐) in Ahmedabad
  ↓
[RANKING] Score by (confidence × rating)
  ↓
[RESPONSE] "Found 3 specialists. Book with Dr. X?"
```

## 🏆 Faculty Feedback Integration

| Expectation                         | Before            | After                                | Status |
| ----------------------------------- | ----------------- | ------------------------------------ | ------ |
| **"Does it think or just search?"** | Keyword matching  | Multi-hop graph reasoning            | ✅ A+  |
| **Safety & Guardrails**             | None              | Emergency detection + audit logs     | ✅ A+  |
| **Architecture**                    | Monolithic script | Documented system design             | ✅ A+  |
| **Dynamic Data**                    | Static SQLite     | Graph-based CRUD + real-time updates | ✅ A+  |

## 📁 Project Structure

```
E:\Project/
├── 🩺 Core Modules
│   ├── knowledge_graph.py        # Neo4j GraphRAG engine
│   ├── graph_rag_agent.py        # Intelligent reasoning pipeline
│   ├── doctor_management.py      # Dynamic doctor CRUD
│   ├── safety_layer.py           # Emergency detection & audit
│   └── agent.py                  # Legacy LLM agent
│
├── 🎨 Frontend
│   └── app.py                    # Streamlit web interface
│
├── 💾 Data Layer
│   ├── database.py               # SQLite schema
│   ├── tools.py                  # Doctor lookup tool
│   └── hospital.db               # Auto-created database
│
├── 📚 Documentation
│   ├── ARCHITECTURE.md           # System design & diagrams
│   ├── SETUP.md                  # Detailed setup guide
│   ├── README.md                 # This file
│   └── requirements.txt          # Python dependencies
│
└── 🔧 Utilities
    └── init_graph.py             # Knowledge graph initialization
```

## 🧠 Key Features

### 1. **Graph RAG for Intelligent Reasoning**

```python
from graph_rag_agent import get_graph_rag_agent

agent = get_graph_rag_agent()
result = agent.process_user_input(
    "I have fever and chills",
    user_city="Ahmedabad"
)
print(result["response"])  # Smart recommendations with doctors
```

### 2. **Safety Layer with Emergency Detection**

```python
from safety_layer import get_safety_manager

safety = get_safety_manager()
severity, is_emergency = safety.detect_emergency("I have chest pain")
# Returns: (TriageSeverity.CRITICAL, True)
# Blocks dangerous home remedies
```

### 3. **Dynamic Doctor Management**

```python
from doctor_management import add_doctor, update_doctor, book_appointment

# Add new doctor
doc_id = add_doctor(
    name="Dr. X",
    specialty="Cardiologist",
    city="Mumbai",
    rating=4.9
)

# Update availability
update_doctor(doc_id, availability="Mon-Fri 10am-5pm")

# Book appointment
appt_id = book_appointment(doc_id, "Patient Name", "+91-98765", "2026-02-10", "2:00 PM")
```

### 4. **Knowledge Graph Relationships**

```
Symptom: "Fever"
  ├→ Disease: "Malaria" (90% confidence)
  │   └→ Specialist: "Infectious Disease Specialist"
  │       └→ Doctors in Ahmedabad
  │
  └→ Disease: "Typhoid" (80% confidence)
      └→ Specialist: "General Physician"
          └→ Doctors in Ahmedabad
```

## 🔒 Safety & Compliance

✅ **Emergency Detection** - CRITICAL/URGENT/HIGH severity levels  
✅ **Home Remedy Prevention** - Blocks dangerous self-treatment  
✅ **Hallucination Prevention** - Confidence-based responses  
✅ **Audit Logging** - All emergencies logged (HIPAA-ready)  
✅ **Soft Deletes** - Removed doctors marked inactive, not deleted

### Emergency Examples

```
User: "I have chest pain" → 🚨 CRITICAL ALERT: "Call 911 immediately"
User: "How to treat chest pain at home?" → ❌ BLOCKED: "Go to ER"
User: "I have mild fever" → ✅ "See a doctor, here are recommendations"
```

## 🔧 Configuration

### Nvidia API (Required for LLM)

```env
# .env file
NVIDIA_API_KEY=your_api_key_here
```

### Neo4j (Optional - Fallback to In-Memory)

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

## 📈 Sample Data

Initialization script populates:

- **15 Medical Conditions** (Malaria, Pneumonia, Appendicitis, etc.)
- **11 Specialist Types** (Cardiologist, Pulmonologist, etc.)
- **75 Medical Relationships** (Symptom→Disease→Specialist)
- **9 Sample Doctors** across Ahmedabad, Surat, Vadodara

### Cities Covered

- Ahmedabad (4 doctors)
- Surat (3 doctors)
- Vadodara (2 doctors)

## 📊 Database Schema

### Neo4j Nodes

```
Symptom {name, severity, description}
Disease {name, severity, description}
Specialist {type, description}
Doctor {id, name, specialty, rating, city}
City {name}
```

### Neo4j Relationships

```
Symptom -[CAUSES]-> Disease (confidence: 0-1)
Disease -[TREATED_BY]-> Specialist (confidence: 0-1)
Doctor -[HAS_SPECIALTY]-> Specialist
Doctor -[LOCATED_IN]-> City
```

### SQLite Tables

```
doctors_v2        (name, specialty, city, rating, availability...)
appointments      (doctor_id, patient_name, date, time, status)
doctor_reviews    (doctor_id, rating, review_text)
sessions          (session chat history)
messages          (chat messages)
```

## 🧪 Testing

### Run Tests

```bash
python knowledge_graph.py   # Test graph reasoning
python safety_layer.py      # Test emergency detection
python doctor_management.py # Test CRUD operations
python graph_rag_agent.py   # Test full pipeline
```

### Manual Testing

1. Start app: `streamlit run app.py`
2. Test scenarios:
   - **Normal case**: "I have fever in Ahmedabad"
   - **Emergency case**: "I have chest pain"
   - **Booking**: Click "Book Now" after selecting doctor

## 🚀 Deployment

### Development

```bash
streamlit run app.py --logger.level=debug
```

### Production (Docker)

```bash
docker build -t medical-assistant .
docker run -p 8501:8501 \
  -e NVIDIA_API_KEY=xxx \
  -e NEO4J_URI=bolt://neo4j:7687 \
  medical-assistant
```

### Streamlit Cloud

```bash
git push origin main
# Visit streamlit.io/cloud → Deploy from GitHub
```

## 📚 API Examples

### Example 1: Symptom-Based Doctor Recommendation

```python
from graph_rag_agent import get_graph_rag_agent

agent = get_graph_rag_agent()
result = agent.process_user_input(
    "I have high fever for 3 days with chills",
    user_city="Ahmedabad"
)

# Returns:
# {
#   "response": "Found 3 specialists...",
#   "doctors": [
#     {
#       "disease": "Malaria",
#       "specialist": "Infectious Disease Specialist",
#       "doctor_name": "Dr. Anil Trivedi",
#       "doctor_rating": 4.7,
#       "availability": "Mon-Sat 9am-5pm",
#       "city": "Ahmedabad"
#     },
#     ...
#   ]
# }
```

### Example 2: Emergency Detection

```python
from safety_layer import get_safety_manager

safety = get_safety_manager()

# Test various inputs
inputs = [
    "I have chest pain",           # CRITICAL
    "I have fever",               # LOW
    "How to treat at home?",      # Safety check
]

for text in inputs:
    severity, is_emergency = safety.detect_emergency(text)
    print(f"{text} → {severity.value}")
```

### Example 3: Doctor Management

```python
from doctor_management import add_doctor, list_doctors, update_doctor

# Add
doc_id = add_doctor(
    name="Dr. New",
    specialty="Neurologist",
    city="Mumbai",
    rating=4.8
)

# List
doctors = list_doctors(specialty="Neurologist", city="Mumbai")

# Update
update_doctor(doc_id, availability="Mon-Fri 3pm-7pm", fees=1000)
```

## 🐛 Troubleshooting

| Issue                      | Solution                                    |
| -------------------------- | ------------------------------------------- |
| ModuleNotFoundError: neo4j | `pip install neo4j`                         |
| NVIDIA_API_KEY not found   | Add to `.env` file                          |
| Neo4j connection failed    | Optional. Falls back to in-memory reasoning |
| No doctors showing         | Run `python init_graph.py` to populate data |
| Unicode errors             | Already fixed in latest version             |

## 🔄 Data Flow Diagram

```
┌─────────────────────┐
│   User Input        │ (Text/Voice/Report)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Safety Check       │ (Emergency detection)
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
  SAFE      EMERGENCY → Return alert
     │
     ▼
┌─────────────────────┐
│  LLM Analysis       │ (Extract symptoms)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Graph RAG Query    │ (Multi-hop reasoning)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Ranking            │ (Score + filter)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Format Response    │ (Top 5 doctors)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Show Doctors       │ (Book appointment)
└─────────────────────┘
```

## 📞 Next Steps (Roadmap)

### Phase 2: Multimodal OCR

- Upload blood test PDFs
- Extract values: "Hemoglobin: 8.0 → Anemia"
- Auto-recommend specialists

### Phase 3: Voice Interface

- Whisper API for speech-to-text
- Multi-language: Hindi, Gujarati, English
- Accessibility for elderly patients

### Phase 4: Doctor Admin Dashboard

- Doctor login & profile management
- View/manage appointments
- Update availability & fees

### Phase 5: Long-term Memory

- Remember patient history
- Proactive follow-ups: "3 days since fever - still there?"
- Health monitoring

## 📄 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design, diagrams, scaling
- [SETUP.md](SETUP.md) - Detailed setup, API usage, troubleshooting
- [README.md](README.md) - This file (overview)

## 🏆 Awards-Ready Features

✅ Addresses "B-grade to A+ product" transformation  
✅ Graph-based reasoning (not just keyword matching)  
✅ Medical safety & guardrails  
✅ Dynamic data management  
✅ Production-ready architecture  
✅ Compliance-ready audit logging

## 📜 License

Built as a faculty-mentored academic project for "Agentic AI in Healthcare."

---

**Built with ❤️ using**:

- Streamlit (UI)
- Neo4j (Knowledge Graph)
- Nvidia Mistral API (LLM)
- Python 3.11+

**Last Updated**: February 2, 2026  
**Status**: 🟢 Production Ready (Phase 1 Complete)
