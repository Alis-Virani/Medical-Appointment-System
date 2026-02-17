# 🏗️ AGENTIC MEDICAL ASSISTANT - SYSTEM ARCHITECTURE

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        🩺 AGENTIC MEDICAL ASSISTANT                         │
└─────────────────────────────────────────────────────────────────────────────┘

                                  USER LAYER
                                      │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
              👤 Patients          🎤 Voice Input        📱 Mobile
            (Web/Mobile)           (Whisper)           (Responsive)


                                FRONTEND LAYER
                                      │
                        ┌──────────────┴──────────────┐
                        │   Streamlit Web Interface    │
                        │  - Chat Interface           │
                        │  - Appointment Booking      │
                        │  - Report Upload            │
                        │  - Session Management       │
                        └──────────────┬──────────────┘
                                      │


                          SAFETY & GUARDRAILS LAYER
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
            🚨 Emergency Detection          ⚠️ Hallucination
              - Critical Triage               Prevention
              - Safety Interrupts            - Confidence
              - Audit Logging                  Thresholds


                        INTELLIGENT REASONING LAYER
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
            📊 Graph RAG Agent            🧠 LLM Analysis
         (Multi-hop Reasoning)        (Symptom Extraction)
          Symptom → Disease →            - Structured
            Specialist → Doctor            Output
                                        - Context Aware


                            DATA & KNOWLEDGE LAYER
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
            🌐 Neo4j Knowledge Graph           💾 SQLite Database
          (Medical Relationships)           (Fast Lookup)

          Nodes:                          Tables:
          - Symptoms                      - doctors_v2
          - Diseases                      - appointments
          - Specialists                   - doctor_reviews
          - Doctors                       - sessions
          - Cities                        - messages

          Relationships:
          - CAUSES (Symptom → Disease)
          - TREATED_BY (Disease → Specialist)
          - HAS_SPECIALTY (Doctor → Specialist)
          - LOCATED_IN (Doctor → City)


                            EXTERNAL INTEGRATIONS
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
              🌐 Google Maps      🎵 Whisper OCR      📧 Email
            (Clinic Location)    (Speech-to-Text)   (Notifications)


                            DYNAMIC DOCTOR MANAGEMENT
                                      │
          ┌──────────────────────────────┴──────────────────────────────┐
          │                                                              │
    📋 CRUD Operations                                   👨‍⚕️ Admin Dashboard
    - add_doctor()                                    - Doctor Login
    - update_doctor()                                 - Manage Schedule
    - delete_doctor()                                 - View Appointments
    - list_doctors()                                  - Update Fees
                                                      - View Reviews


                              BOOKING FLOW
                                      │
    ┌───────────────────────────────┬───────────────────────────────┐
    │                               │                               │
User Input                    Graph RAG Analysis              Doctor Selection
  (Symptoms)                  (Multi-hop Reasoning)              (Ranked)
    │                               │                               │
    ▼                               ▼                               ▼
  "Fever"           "Fever → Malaria →              "Dr. Mehta"
  "Chills"          Infectious Disease              (4.8⭐, Available)
  "Ahmedabad"       Specialist → Nearby Doctor"

                                                Booking Confirmation
                                                    │
                                                    ▼
                                                📅 Appointment
                                                📍 Google Maps Link
                                                ✅ Notification


                              DATA FLOW DIAGRAM

    ┌──────────────────────────────────────────────────────────┐
    │  1. USER INPUT                                           │
    │     - Text message                                       │
    │     - Voice (Whisper)                                    │
    │     - Medical Report (OCR)                               │
    └──────────────────┬───────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────┐
    │  2. SAFETY CHECK                                         │
    │     - Emergency Detection                                │
    │     - Hallucination Prevention                           │
    │     - Audit Logging                                      │
    └──────────────────┬───────────────────────────────────────┘
                       │
                 ▼─────┴─────▼
            SAFE        NOT SAFE
             │              │
             │        Return Emergency
             │        Message to User
             │
             ▼
    ┌──────────────────────────────────────────────────────────┐
    │  3. LLM SYMPTOM ANALYSIS                                 │
    │     - Extract symptoms                                   │
    │     - Identify severity                                  │
    │     - Suggest specialist                                 │
    │     - Confidence score                                   │
    └──────────────────┬───────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────┐
    │  4. NEO4J GRAPH REASONING                                │
    │     Multi-hop path:                                      │
    │     Symptom → Disease → Specialist → Doctor              │
    │     (With confidence scoring at each hop)                │
    └──────────────────┬───────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────┐
    │  5. RANKING & FILTERING                                  │
    │     - Score: 60% Match Confidence + 40% Doctor Rating   │
    │     - Remove duplicates                                  │
    │     - Top 5 recommendations                              │
    └──────────────────┬───────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────┐
    │  6. FORMATTED RESPONSE                                   │
    │     - Symptoms Summary                                   │
    │     - Likely Conditions                                  │
    │     - Recommended Specialist                             │
    │     - Top Doctors with Details                           │
    └──────────────────┬───────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────┐
    │  7. USER DECISION                                        │
    │     - Book Appointment                                   │
    │     - Ask More Questions                                 │
    │     - View Doctor Details                                │
    └──────────────────┬───────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────┐
    │  8. APPOINTMENT BOOKING                                  │
    │     - Select Date/Time                                   │
    │     - Confirmation                                       │
    │     - Google Maps Link to Clinic                         │
    │     - Appointment Saved to Database                      │
    └──────────────────────────────────────────────────────────┘


## Knowledge Graph Schema

### Nodes
```

┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Symptom │ │ Disease │ │ Specialist │ │ Doctor │
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
│ name (PK) │ │ name (PK) │ │ type (PK) │ │ id (PK) │
│ severity │ │ severity │ │ description │ │ name │
│ description │ │ description │ │ │ │ specialty │
│ │ │ │ │ │ │ rating │
│ │ │ │ │ │ │ availability │
│ │ │ │ │ │ │ city │
│ │ │ │ │ │ │ fees │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

```

### Relationships
```

Symptom ──CAUSES──> Disease (confidence: 0.0-1.0)
│
│
Disease ──TREATED_BY──> Specialist (confidence: 0.0-1.0)
│
│
Specialist <──HAS_SPECIALTY──┐
│
Doctor
│
│
──LOCATED_IN──> City

```


## Key Components

### 1. **Knowledge Graph (Neo4j)**
   - Stores medical relationships
   - Enables multi-hop reasoning
   - Dynamic updates (add/remove doctors)
   - Confidence scoring

### 2. **Safety Layer**
   - Emergency detection (CRITICAL/URGENT/HIGH)
   - Home remedy prevention
   - Hallucination prevention
   - Audit logging for compliance

### 3. **Graph RAG Agent**
   - LLM-based symptom analysis
   - Multi-hop graph reasoning
   - Doctor ranking & filtering
   - Confidence-based responses

### 4. **Dynamic Doctor Management**
   - CRUD operations for doctors
   - Real-time availability updates
   - Appointment booking system
   - Review & rating system

### 5. **SQLite Database**
   - Fast lookup queries
   - Appointment history
   - Session persistence
   - Review management

### 6. **Frontend (Streamlit)**
   - Chat interface
   - Appointment booking UI
   - Session management
   - Doctor dashboard (Phase 5)


## API Integration Points

```

┌─────────────────────────────────────────────────────────┐
│ Patient-Facing APIs │
├─────────────────────────────────────────────────────────┤
│ POST /api/chat │
│ POST /api/appointments │
│ GET /api/doctors?specialty=X&city=Y │
│ POST /api/reviews │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Admin APIs (Doctor Dashboard - Phase 5) │
├─────────────────────────────────────────────────────────┤
│ GET /api/admin/appointments │
│ POST /api/admin/availability │
│ PUT /api/admin/profile │
│ GET /api/admin/reviews │
└─────────────────────────────────────────────────────────┘

```


## Scaling Considerations

### Horizontal Scaling
- Streamlit can be load-balanced with Gunicorn
- Neo4j can be clustered for high availability
- SQLite → PostgreSQL for production

### Performance
- Graph query caching
- Doctor list pagination
- Session-based context (not re-querying)
- Fallback to SQLite if Neo4j unavailable

### Security
- API authentication (JWT)
- Audit logging for compliance
- HIPAA-compliant data encryption
- PII anonymization in logs


## Deployment Architecture (Production)

```

                    Load Balancer (Nginx)
                            │
                ┌───────────┼───────────┐
                │           │           │
            Instance 1   Instance 2   Instance 3
          (Streamlit)   (Streamlit)   (Streamlit)
                │           │           │
                └───────────┼───────────┘
                            │
                    ┌───────┼───────┐
                    │               │
            PostgreSQL          Neo4j Cluster
            (Production DB)     (HA Graph DB)
                    │               │
                    └───────┬───────┘
                            │
                    AWS S3 (Backups)
                    Redis (Cache)

```

## Next Steps

1. ✅ **Phase 1**: Knowledge Graph + Safety Layer (DONE)
2. ⏳ **Phase 2**: Integrate into Streamlit app
3. ⏳ **Phase 3**: Multimodal OCR for medical reports
4. ⏳ **Phase 4**: Voice interface with Whisper
5. ⏳ **Phase 5**: Doctor admin dashboard
6. ⏳ **Phase 6**: Long-term memory & proactive monitoring
```
