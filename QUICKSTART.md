# ⚡ QUICK START GUIDE

## 30-Second Setup

```bash
# 1. Enter project directory
cd E:\Project

# 2. Activate environment
.venv\Scripts\Activate.ps1

# 3. Install dependencies (skip if already done)
pip install -r requirements.txt

# 4. Initialize knowledge graph (skip if already done)
python init_graph.py

# 5. Start the app
streamlit run app.py
```

**Result**: Opens http://localhost:8501 🚀

---

## What You Can Do NOW

### 👤 As a Patient

1. **Ask about symptoms**

   ```
   "I have fever and chills in Ahmedabad"
   ```

   → System recommends specialists and doctors

2. **Book an appointment**
   - Select from recommended doctors
   - Choose date/time
   - Get Google Maps link to clinic

3. **Get emergency help**
   ```
   "I have chest pain"
   ```
   → System: 🚨 "CALL 911 IMMEDIATELY"

### 🏥 As a Developer

1. **Add new doctors**

   ```python
   from doctor_management import add_doctor
   doc_id = add_doctor("Dr. X", "Cardiologist", "Mumbai", 4.9)
   ```

2. **Update doctor info**

   ```python
   from doctor_management import update_doctor
   update_doctor(doc_id, availability="Mon-Fri 10am-5pm")
   ```

3. **Query the knowledge graph**

   ```python
   from knowledge_graph import get_knowledge_graph
   kg = get_knowledge_graph()
   results = kg.symptom_to_specialist("fever", city="Ahmedabad")
   ```

4. **Test safety features**
   ```python
   from safety_layer import get_safety_manager
   safety = get_safety_manager()
   severity, is_emergency = safety.detect_emergency("chest pain")
   ```

---

## 📁 File Quick Reference

| Want To...                | See File                                    |
| ------------------------- | ------------------------------------------- |
| Run the app               | `app.py`                                    |
| Understand architecture   | `ARCHITECTURE.md`                           |
| Setup guide               | `SETUP.md`                                  |
| Add/update doctors        | `doctor_management.py`                      |
| Emergency detection       | `safety_layer.py`                           |
| Graph reasoning           | `knowledge_graph.py` + `graph_rag_agent.py` |
| Initialize data           | `init_graph.py`                             |
| Faculty feedback response | `FACULTY_REVIEW.md`                         |

---

## 🧪 Test It

### Test 1: Normal Query

```
User: "I have fever"
Expected: Recommendations for General Physician or Infectious Disease Specialist
```

### Test 2: Emergency

```
User: "I have chest pain"
Expected: 🚨 ALERT: "CALL 911 IMMEDIATELY"
```

### Test 3: Home Remedy Prevention

```
User: "How to treat chest pain at home?"
Expected: ❌ "This is unsafe. Go to hospital immediately"
```

### Test 4: Booking

```
1. Type symptom → Get doctor list
2. Click "Book Now" on any doctor
3. Select date/time
4. Get confirmation with Google Maps link
```

---

## 🔧 Configuration

### If You Have Neo4j (Optional)

```env
# .env file
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### Required: Nvidia API Key

```env
# .env file
NVIDIA_API_KEY=your_api_key_here
```

---

## 🆘 Troubleshooting

| Problem                   | Fix                                                   |
| ------------------------- | ----------------------------------------------------- |
| "ModuleNotFoundError"     | `pip install -r requirements.txt`                     |
| "NVIDIA_API_KEY not set"  | Add to `.env` file                                    |
| "Neo4j connection failed" | Don't worry! System falls back to in-memory reasoning |
| "No doctors showing"      | Run `python init_graph.py` to populate data           |
| "Streamlit not found"     | `pip install streamlit`                               |

---

## 📚 Documentation

- **README.md** - Overview & features
- **ARCHITECTURE.md** - System design with diagrams
- **SETUP.md** - Detailed setup guide
- **FACULTY_REVIEW.md** - How we addressed feedback
- **This file** - Quick start

---

## 🎯 Next (Phase 2)

Want to add medical report OCR?

```python
# Will be in Phase 2
from ocr_engine import extract_medical_report
values = extract_medical_report("blood_test.pdf")
# {"hemoglobin": 8.0, "interpretation": "Anemia"}
# → Auto-recommend Hematologist
```

---

## 💡 Key Insight

This system uses **Graph RAG** instead of keyword search:

```
OLD WAY (Keyword Search):
  "chest pain" → Search database → [Orthopedic, Physiotherapy]

NEW WAY (Graph RAG):
  "chest pain" → LLM: "Could be Heart Issue" →
  Graph: Disease(Heart) → Specialist(Cardiologist) →
  Doctors: [Cardiologist A, Cardiologist B]
```

---

**Questions?** Check SETUP.md or ARCHITECTURE.md  
**Ready to deploy?** See SETUP.md → Deployment section  
**Want to understand the tech?** Check ARCHITECTURE.md

**Enjoy!** 🚀
