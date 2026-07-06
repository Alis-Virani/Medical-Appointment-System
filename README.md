# MediCare AI — Intelligent Medical Appointment & Health Advisory System

> A comprehensive healthcare platform combining AI-powered medical consultation, intelligent doctor matching, real-time appointment booking, and clinical report analysis.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Component Breakdown](#component-breakdown)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [LangGraph Architecture](#langgraph-architecture)
- [Vector Store & Embeddings](#vector-store--embeddings)
- [Memory Layer](#memory-layer)
- [Real-Time Features](#real-time-features)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [Key Features](#key-features)
- [File Structure](#file-structure)

---

## 🏥 Overview

**MediCare AI** is an intelligent medical appointment system that leverages:

- **AI-Powered Consultation**: LangGraph-based multi-node reasoning for medical queries
- **Smart Doctor Matching**: Dynamic doctor discovery with NEO4J knowledge graphs
- **Real-Time Updates**: WebSocket-based live appointment and notification system
- **Multi-Channel Support**: Web (React), Mobile (React Native), and CLI (Streamlit)
- **Safety & Compliance**: Emergency detection, triage severity classification, and clinical validation
- **Multi-Language**: Support for medical translation and localization
- **Voice Integration**: Speech-to-text and text-to-speech via Sarvam AI

---

## 🛠️ Tech Stack

### Backend

- **Framework**: FastAPI 0.100.0+
- **ASGI Server**: Uvicorn
- **LLM & AI**:
  - LangChain (orchestration)
  - LangGraph (agentic workflows)
  - LangChain-Groq (LLM integration)
  - LangChain-NVIDIA (alternative LLM provider)
- **Database**:
  - SQLite 3 (primary relational DB)
  - Neo4j (knowledge graph & medical relationships)
  - Qdrant (vector search in-memory)
  - ChromaDB (persistent embeddings)
- **Memory & Context**:
  - Mem0AI (persistent memory layer)
  - Sentence-Transformers (embeddings)
- **External Integrations**:
  - Twilio (SMS/Call notifications)
  - SendGrid (Email)
  - Razorpay (Payment processing)
  - Sarvam AI (Speech services)
- **Document Processing**:
  - PDFPlumber (PDF extraction)
  - PyTesseract + EasyOCR (OCR)
  - Pillow (image processing)
- **Utilities**: Pandas, Plotly, Requests, Python-dotenv

### Frontend

- **Framework**: React 19.2.4
- **Build Tool**: Vite 8.0.1
- **Styling**: CSS3 with animations (Framer Motion, GSAP)
- **HTTP Client**: Axios
- **Routing**: React Router DOM 7.13.2
- **Animations**: Framer Motion 12.38.0, GSAP 3.14.2, Lenis 1.3.20
- **Build**: ESLint, Vite plugins

### Mobile

- **Framework**: React Native 0.72.0
- **State Management**: Zustand 4.4.0
- **Navigation**: React Navigation 6.1.0
- **Push Notifications**: Firebase Messaging
- **Real-Time**: WebSocket 1.0.34
- **UI Components**: React Native Vector Icons, React Native Picker Select
- **HTTP**: Axios 1.6.0
- **Date/Time**: Dayjs 1.11.0

### Real-Time Communication

- **WebSockets**: Python `websockets` library + FastAPI WebSocket support
- **Event-Driven**: Custom EventType enum for appointment, chat, schedule, notification events

---

## 📁 Project Structure

```
e:\Project/
├── 📄 README.md (this file)
├── 📄 requirements.txt (Python dependencies)
├── 📄 START.txt (Quick start guide)
│
├── 🐍 Core Backend Scripts
│   ├── app.py (Streamlit main navigation shell)
│   ├── app_v1_stable.py (Stable version backup)
│   ├── backend/
│   │   ├── main.py (FastAPI entry point)
│   │   ├── models.py (Pydantic request/response models)
│   │   ├── auth_utils.py (JWT & authentication)
│   │   └── routers/ (9 API endpoint modules)
│   │       ├── auth.py (Login, register, token refresh)
│   │       ├── chat.py (Chat sessions, messaging)
│   │       ├── appointments.py (Booking management)
│   │       ├── doctors.py (Doctor search & profiles)
│   │       ├── health.py (Health history & reports)
│   │       ├── notes.py (Patient notes)
│   │       ├── schedule.py (Doctor schedules)
│   │       ├── admin.py (Admin dashboard & stats)
│   │       └── sarvam_ai.py (Voice TTS/STT)
│   │
│   ├── 🤖 AI & Language Processing
│   │   ├── lang_graph_agent.py (15-node LangGraph agentic workflow)
│   │   ├── graph_rag_agent.py (Graph-RAG reasoning)
│   │   ├── knowledge_graph.py (Neo4j medical knowledge graph)
│   │   ├── vector_store.py (Qdrant vector embeddings store)
│   │   ├── memory_layer.py (Mem0AI persistent memory)
│   │   ├── safety_layer.py (Emergency detection & triage)
│   │   ├── translator.py (Multi-language support)
│   │   ├── tools.py (Tool definitions for agents)
│   │   ├── agent.py (Agent configuration)
│   │   └── tools/ (specialized tool modules)
│   │
│   ├── 🗄️ Database & Data
│   │   ├── database.py (SQLite schema & queries)
│   │   ├── doctor_management.py (Doctor CRUD & dynamic profiles)
│   │   ├── doctor_bulk_import.py (Bulk doctor import utility)
│   │   ├── medical_knowledge_integration.py (Medical data setup)
│   │   ├── expand_medical_knowledge.py (Knowledge base expansion)
│   │   ├── demo_data.py (Sample data generator)
│   │   ├── fix_demo_data.py (Data cleanup utility)
│   │   ├── sample_doctors.csv (Doctor seed data)
│   │   └── chroma_db/ (ChromaDB vector storage)
│   │
│   ├── 📱 Real-Time & Services
│   │   ├── websocket_server.py (WebSocket real-time updates)
│   │   ├── websocket_client.py (WebSocket client)
│   │   ├── notification_service.py (Twilio/SendGrid integration)
│   │   ├── payment_service.py (Razorpay integration)
│   │   ├── voice_service.py (Sarvam AI voice services)
│   │   ├── report_analyzer.py (Clinical report analysis)
│   │   └── realtime_integration.py (Real-time event handling)
│   │
│   ├── 🔧 Utilities & Setup
│   │   ├── config.py (Configuration management)
│   │   ├── api_client.py (HTTP client utilities)
│   │   ├── auth.py (Streamlit auth UI)
│   │   ├── setup_demo.py (Demo environment setup)
│   │   ├── setup_doctor_pages_demo.py (Doctor page demo)
│   │   ├── verify_setup.py (Verification script)
│   │   ├── check_qdrant_api.py (Vector store health check)
│   │   ├── check_user.py (User lookup utility)
│   │   ├── find_random_user.py (Debug utility)
│   │   ├── scrape_real_doctors.py (Doctor data scraper)
│   │   └── init_graph.py (Knowledge graph initialization)
│   │
│   ├── 📊 Visualization
│   │   ├── graph_viz.py (Graph visualization)
│   │   └── demo_medical_integration.py (Medical integration demo)
│   │
│   └── ✅ Testing & Validation
│       ├── tests/
│       │   └── verify_emergency_logic.py (Emergency detection tests)
│       ├── test_admin_doctors.py
│       ├── test_booking_history.py
│       ├── test_medical_comprehensive.py
│       ├── test_medical_integration.py
│       ├── test_otp_flow.py
│       ├── test_vector_search.py
│       ├── test_websocket_system.py
│       └── eval_metrics.py (Performance metrics)
│
├── 🖥️ Frontend (React + Vite)
│   ├── package.json
│   ├── vite.config.js
│   ├── eslint.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.jsx (React entry)
│   │   ├── App.jsx (Main app component)
│   │   ├── App.css
│   │   ├── index.css
│   │   ├── api/
│   │   │   └── client.js (API client configuration)
│   │   ├── components/ (13 components)
│   │   │   ├── ConfirmationModal.jsx
│   │   │   ├── Layout.jsx
│   │   │   └── ... (UI components)
│   │   ├── context/
│   │   │   └── AuthContext.jsx (Auth state management)
│   │   ├── pages/ (13 pages)
│   │   │   ├── AdminPage.jsx
│   │   │   ├── AppointmentBookingPage.jsx
│   │   │   ├── AuthPage.jsx
│   │   │   ├── ChatPage.jsx
│   │   │   ├── DoctorDashboardPage.jsx
│   │   │   ├── HealthHistoryPage.jsx
│   │   │   ├── LandingPage.jsx
│   │   │   ├── PatientNotesPage.jsx
│   │   │   ├── SchedulePage.jsx
│   │   │   └── ... (other pages)
│   │   └── assets/ (images, icons)
│   └── public/
│
├── 📱 Mobile App (React Native)
│   ├── package.json
│   ├── App.js
│   ├── setup.js
│   ├── src/
│   │   ├── services/ (API & WebSocket services)
│   │   └── stores/ (Zustand state management)
│   ├── android/ (Android build files)
│   └── ios/ (iOS build files)
│
├── 📄 Streamlit Pages
│   ├── pages/
│   │   ├── chat.py (Streamlit chat interface)
│   │   ├── health_history.py (Health records)
│   │   ├── patient_notes.py (Patient notes)
│   │   ├── doctor_dashboard.py (Doctor dashboard)
│   │   ├── doctor_admin.py (Doctor admin panel)
│   │   ├── admin_doctors.py (Doctor management)
│   │   ├── doctor_schedule.py (Schedule management)
│   │   └── eval_metrics.py (Analytics)
│
└── 📦 Other
    ├── hospital.db (SQLite database file)
    └── chroma_db/ (Vector store persistence)
```

---

## 🔌 Component Breakdown

### 1. **LangGraph Agentic Workflow** (`lang_graph_agent.py`)

**15 Nodes in the workflow**:

1. **`guardrails`** - Input validation & emergency detection
2. **`router`** - Route user input to appropriate handler
3. **`general_chat`** - General conversational responses
4. **`booking_history`** - Retrieve appointment history
5. **`analysis`** - Clinical report analysis
6. **`extract`** - Information extraction from medical text
7. **`medical_info`** - Medical knowledge retrieval
8. **`remedies`** - Home remedies & natural solutions
9. **`ask_city`** - Collect location for doctor search
10. **`booking_inquiry`** - Handle booking requests
11. **`memory`** - Check patient memory & context
12. **`reasoning`** - Graph-RAG reasoning engine
13. **`response`** - Generate final response

**State Management**:

- `AgentState` TypedDict with 21 fields including:
  - `messages` (conversation history)
  - `user_id`, `session_id`, `user_role`
  - `symptoms`, `severity`, `diagnosis`
  - `specialist`, `city`, `doctors` (matched doctors)
  - `is_emergency`, `safe_to_proceed`
  - `memory_context`, `input_type`

**LLM Models**:

- `meta-llama/llama-4-scout-17b-16e-instruct` (via Groq)
- 3 temperature buckets: 0 (classification), 0.3 (analysis), 0.5 (chat)

---

### 2. **Backend API Endpoints** (`backend/routers/` - 9 routers)

#### **Auth Router** (`auth.py`)

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `GET /api/auth/profile` - User profile

#### **Chat Router** (`chat.py`)

- `GET /api/chat/sessions` - List sessions
- `POST /api/chat/sessions` - Create session
- `POST /api/chat/message` - Send message
- `GET /api/chat/history/{session_id}` - Message history

#### **Appointments Router** (`appointments.py`)

- `GET /api/appointments/` - List bookings
- `GET /api/appointments/upcoming` - Upcoming appointments
- `GET /api/appointments/past` - Past appointments
- `GET /api/appointments/slots` - Available time slots
- `POST /api/appointments/` - Create booking

#### **Doctors Router** (`doctors.py`)

- `GET /api/doctors` - Search doctors
- `GET /api/doctors/{id}` - Doctor details
- `POST /api/doctors` - Create doctor profile
- `PUT /api/doctors/{id}` - Update doctor

#### **Health Router** (`health.py`)

- `GET /api/health/history` - Health records
- `POST /api/health/report` - Upload health report

#### **Notes Router** (`notes.py`)

- `GET /api/notes/` - List patient notes
- `POST /api/notes/` - Create note
- `PUT /api/notes/{id}` - Update note
- `DELETE /api/notes/{id}` - Delete note

#### **Schedule Router** (`schedule.py`)

- `GET /api/schedule/` - Doctor schedule
- `GET /api/schedule/today` - Today's appointments
- `POST /api/schedule/` - Create schedule

#### **Admin Router** (`admin.py`)

- `GET /api/admin/doctors` - List all doctors
- `POST /api/admin/doctors` - Add doctor
- `GET /api/admin/users` - List users
- `GET /api/admin/stats` - System statistics

#### **Sarvam AI Router** (`sarvam_ai.py`)

- `POST /api/sarvam/tts` - Text-to-speech
- `POST /api/sarvam/tts/audio` - Audio TTS
- `POST /api/sarvam/stt` - Speech-to-text

---

### 3. **Database Schema** (`database.py` - 10+ tables)

#### **Core Tables**

| Table                    | Purpose                | Key Fields                                                                                                       |
| ------------------------ | ---------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `users`                  | User accounts & auth   | id, username, email, password_hash, role (patient/doctor), phone, full_name                                      |
| `sessions`               | Chat sessions          | id, title, user_id, created_at                                                                                   |
| `messages`               | Chat messages          | id, session_id, role, content                                                                                    |
| `doctors`                | Doctor profiles        | id, name, specialty, availability, city, years_experience, contact, rating, fees, clinic_address, qualifications |
| `bookings`               | Appointment history    | id, user_id, doctor_id, appointment_date, appointment_time, status (confirmed/cancelled)                         |
| `health_history`         | Patient health records | id, user_id, medical_condition, medication, allergy, date_recorded                                               |
| `notes`                  | Clinical notes         | id, user_id, doctor_id, note_text, created_at                                                                    |
| `payments`               | Payment transactions   | id, booking_id, amount, razorpay_order_id, razorpay_payment_id, status (pending/completed)                       |
| `notifications`          | Sent notifications     | id, user_id, type, recipient, subject, message, status, sent_at                                                  |
| `session_report_context` | Report caching         | id, session_id, user_id, report_text, updated_at                                                                 |

---

### 4. **Vector Store & Embeddings** (`vector_store.py`)

**Configuration**:

- **Database**: Qdrant (in-memory mode)
- **Embedding Model**: `all-MiniLM-L6-v2` (384-dim)
- **Chunk Size**: 600 characters with 100-char overlap
- **Similarity Threshold**: 0.6 (0-1 scale)

**Collection**:

- `medical_knowledge` - Main vector collection

**Key Functions**:

- `add_documents()` - Index medical documents
- `search()` - Semantic search with threshold
- `_chunk_text()` - Smart text chunking
- `_text_to_hash_id()` - Deterministic ID generation

---

### 5. **Memory Layer** (`memory_layer.py`)

**Provider**: Mem0AI with NVIDIA API backend

**Configuration**:

- **Vector Store**: ChromaDB (`./chroma_db`)
- **Embedder**: HuggingFace (`all-MiniLM-L6-v2`)
- **LLM**: NVIDIA API with Mistral Large 3 model
- **Collection**: `patient_history`

**Features**:

- Persistent patient history
- Cross-session context
- Long-term memory management

---

### 6. **Knowledge Graph** (`knowledge_graph.py` - Neo4j)

**Neo4j Schema**:

**Node Types**:

- `Symptom` (unique name)
- `Disease` (unique name)
- `Specialist` (unique name)
- `Treatment` (unique name)
- `Doctor` (unique id)
- `Patient` (unique id)
- `Medicine` (unique name)
- `Herb` (unique name)

**Relationship Types**:

- `PRESENTS_AS` (Symptom → Disease)
- `REQUIRES_SPECIALIST` (Disease → Specialist)
- `TREATS` (Doctor → Disease)
- `PRESCRIBES` (Doctor → Medicine)
- `RECOMMENDS` (Specialist → Treatment)
- `HAS_ALLERGY` (Patient → Medicine)
- `INTERACTS_WITH` (Medicine → Medicine)

---

### 7. **Real-Time WebSocket System** (`websocket_server.py`)

**Event Types** (10 total):

- `APPOINTMENT_CREATED`
- `APPOINTMENT_UPDATED`
- `APPOINTMENT_CANCELLED`
- `APPOINTMENT_CONFIRMED`
- `CHAT_MESSAGE`
- `SCHEDULE_CHANGE`
- `NOTIFICATION`
- `DOCTOR_ONLINE`
- `DOCTOR_OFFLINE`
- `PATIENT_ONLINE`

**Features**:

- Real-time connection management
- User & doctor status tracking
- Event broadcasting to subscribed clients
- Async event queue processing

---

### 8. **Safety Layer & Emergency Detection** (`safety_layer.py`)

**Severity Levels** (5 tiers):

- `CRITICAL` - Life-threatening, call 911
- `URGENT` - Serious, go to hospital
- `HIGH` - Important, see doctor today
- `MEDIUM` - Can wait 1-2 days
- `LOW` - Can wait a week+

**Emergency Keywords Tracked**:

- Cardiac: chest pain, heart attack, cardiac arrest
- Neurological: unconscious, seizure, facial drooping
- Respiratory: difficulty breathing, shortness of breath
- Severe: severe bleeding, severe burns, anaphylaxis
- Etc. (100+ keywords categorized)

---

### 9. **Frontend Pages** (`frontend/src/pages/` - 13 pages)

| Page                         | Purpose                 |
| ---------------------------- | ----------------------- |
| `LandingPage.jsx`            | Welcome & intro         |
| `AuthPage.jsx`               | Login & registration    |
| `ChatPage.jsx`               | AI medical consultation |
| `AppointmentBookingPage.jsx` | Book appointments       |
| `DoctorDashboardPage.jsx`    | Doctor view             |
| `HealthHistoryPage.jsx`      | Medical records         |
| `PatientNotesPage.jsx`       | Clinical notes          |
| `SchedulePage.jsx`           | Schedule management     |
| `AdminPage.jsx`              | System admin panel      |
| Others                       | Additional features     |

---

### 10. **Streamlit Pages** (`pages/` - 9 pages)

| Page                  | Purpose                  |
| --------------------- | ------------------------ |
| `chat.py`             | Streamlit chat interface |
| `health_history.py`   | Health records viewer    |
| `patient_notes.py`    | Patient note management  |
| `doctor_dashboard.py` | Doctor dashboard         |
| `doctor_admin.py`     | Doctor administration    |
| `admin_doctors.py`    | Doctor roster management |
| `doctor_schedule.py`  | Schedule editor          |
| `eval_metrics.py`     | Performance analytics    |
| Others                | Utilities                |

---

## 📊 API Endpoints Summary

**Total Endpoints**: 40+

```
Auth (4)
├── POST /api/auth/register
├── POST /api/auth/login
├── POST /api/auth/refresh
└── GET /api/auth/profile

Chat (4)
├── GET /api/chat/sessions
├── POST /api/chat/sessions
├── POST /api/chat/message
└── GET /api/chat/history/{session_id}

Appointments (5)
├── GET /api/appointments/
├── GET /api/appointments/upcoming
├── GET /api/appointments/past
├── GET /api/appointments/slots
└── POST /api/appointments/

Doctors (4)
├── GET /api/doctors
├── GET /api/doctors/{id}
├── POST /api/doctors
└── PUT /api/doctors/{id}

Health (2)
├── GET /api/health/history
└── POST /api/health/report

Notes (4)
├── GET /api/notes/
├── POST /api/notes/
├── PUT /api/notes/{id}
└── DELETE /api/notes/{id}

Schedule (3)
├── GET /api/schedule/
├── GET /api/schedule/today
└── POST /api/schedule/

Admin (3)
├── GET /api/admin/doctors
├── POST /api/admin/doctors
├── GET /api/admin/users
└── GET /api/admin/stats

Sarvam AI (3)
├── POST /api/sarvam/tts
├── POST /api/sarvam/tts/audio
└── POST /api/sarvam/stt

Health Check
└── GET /api/ping
```

---

## 💾 Database Schema

### SQLite Tables (hospital.db)

```
┌─ AUTHENTICATION ─────────────────────────────────────┐
│ users                                                │
│  ├─ id (PRIMARY KEY)                                 │
│  ├─ username (UNIQUE)                                │
│  ├─ password_hash                                    │
│  ├─ salt                                             │
│  ├─ full_name                                        │
│  ├─ email                                            │
│  ├─ phone                                            │
│  ├─ role (patient | doctor)                          │
│  ├─ created_at (TIMESTAMP)                           │
│  └─ last_login (TIMESTAMP)                           │
└──────────────────────────────────────────────────────┘

┌─ CHAT & CONVERSATION ────────────────────────────────┐
│ sessions                                             │
│  ├─ id (PRIMARY KEY)                                 │
│  ├─ title                                            │
│  ├─ user_id (FOREIGN KEY → users)                    │
│  └─ created_at (TIMESTAMP)                           │
│                                                      │
│ messages                                             │
│  ├─ id (PRIMARY KEY)                                 │
│  ├─ session_id (FOREIGN KEY → sessions)              │
│  ├─ role (user | assistant)                          │
│  └─ content (TEXT)                                   │
│                                                      │
│ session_report_context                              │
│  ├─ id (PRIMARY KEY)                                 │
│  ├─ session_id (UNIQUE with user_id)                 │
│  ├─ user_id                                          │
│  ├─ report_text                                      │
│  └─ updated_at (TIMESTAMP)                           │
└──────────────────────────────────────────────────────┘

┌─ DOCTORS & APPOINTMENTS ─────────────────────────────┐
│ doctors                                              │
│  ├─ id (PRIMARY KEY)                                 │
│  ├─ doctor_id (UNIQUE, dynamic profile)              │
│  ├─ name                                             │
│  ├─ specialty                                        │
│  ├─ city                                             │
│  ├─ years_experience                                 │
│  ├─ contact                                          │
│  ├─ rating                                           │
│  ├─ fees                                             │
│  ├─ clinic_address                                   │
│  ├─ qualifications                                   │
│  └─ availability (JSON)                              │
│                                                      │
│ bookings (appointments)                              │
│  ├─ id (PRIMARY KEY)                                 │
│  ├─ user_id (FOREIGN KEY)                            │
│  ├─ doctor_id (FOREIGN KEY)                          │
│  ├─ doctor_name                                      │
│  ├─ specialty                                        │
│  ├─ city                                             │
│  ├─ appointment_date                                 │
│  ├─ appointment_time                                 │
│  ├─ status (confirmed | cancelled)                   │
│  ├─ created_at (TIMESTAMP)                           │
│  └─ notes                                            │
└──────────────────────────────────────────────────────┘

┌─ HEALTH RECORDS ─────────────────────────────────────┐
│ health_history                                       │
│  ├─ id (PRIMARY KEY)                                 │
│  ├─ user_id (FOREIGN KEY)                            │
│  ├─ medical_condition                                │
│  ├─ medication                                       │
│  ├─ allergy                                          │
│  ├─ date_recorded (TIMESTAMP)                        │
│  └─ notes                                            │
│                                                      │
│ notes (clinical notes)                               │
│  ├─ id (PRIMARY KEY)                                 │
│  ├─ user_id (FOREIGN KEY)                            │
│  ├─ doctor_id (FOREIGN KEY)                          │
│  ├─ note_text                                        │
│  ├─ created_at (TIMESTAMP)                           │
│  └─ updated_at (TIMESTAMP)                           │
└──────────────────────────────────────────────────────┘

┌─ PAYMENTS ───────────────────────────────────────────┐
│ payments                                             │
│  ├─ id (PRIMARY KEY)                                 │
│  ├─ booking_id (FOREIGN KEY)                         │
│  ├─ amount (INTEGER, in paise)                       │
│  ├─ currency (default: INR)                          │
│  ├─ razorpay_order_id                                │
│  ├─ razorpay_payment_id                              │
│  ├─ razorpay_signature                               │
│  ├─ status (pending | completed | failed)            │
│  ├─ created_at (TIMESTAMP)                           │
│  └─ updated_at (TIMESTAMP)                           │
└──────────────────────────────────────────────────────┘

┌─ NOTIFICATIONS ──────────────────────────────────────┐
│ notifications                                        │
│  ├─ id (PRIMARY KEY)                                 │
│  ├─ user_id                                          │
│  ├─ type (sms | email | push)                        │
│  ├─ recipient (phone | email)                        │
│  ├─ subject                                          │
│  ├─ message                                          │
│  ├─ status (pending | sent | failed)                 │
│  ├─ sent_at (TIMESTAMP)                              │
│  └─ created_at (TIMESTAMP)                           │
└──────────────────────────────────────────────────────┘
```

---

## 🤖 LangGraph Architecture

### State Flow Diagram

```
                   ┌─────────────────┐
                   │   User Input    │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │   GUARDRAILS    │
                   │ • Emergency?    │
                   │ • Safe proceed? │
                   │ • Triage        │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
         ┌────────▶│    ROUTER       │◀────────┐
         │         │ Route to handler│         │
         │         └────────┬────────┘         │
         │                  │                  │
    General Chat      Specialized Nodes    Emergency
         │          ┌──────────────────────────│
         │          │                          │
    ┌────▼──┐  ┌────▼────┐  ┌──────┐  ┌────────▼────┐
    │GENERAL│  │MEDICAL  │  │BOOKING  │ MEMORY
    │ CHAT  │  │  INFO   │  │INQUIRY  │ CHECK
    └────┬──┘  └────┬────┘  └──┬─────┘  └──────┬─────┘
         │          │          │               │
    ┌────▼──┴──────────────────┴───────────────┴─────┐
    │          REASONING ENGINE                       │
    │  • Graph-RAG (knowledge graph queries)          │
    │  • Vector search (semantic similarity)          │
    │  • LLM reasoning (context synthesis)            │
    └────┬───────────────────────────────────────────┘
         │
    ┌────▼──────────────┐
    │ RESPONSE          │
    │ Generation        │
    └────┬──────────────┘
         │
    ┌────▼──────────────────┐
    │ User Response + Actions│
    │ (navigate, book, etc) │
    └───────────────────────┘
```

### Node Execution Logic

```
1. guardrails()
   ├─ Safety detection
   ├─ Emergency classification
   └─ Route to appropriate handler

2. router()
   ├─ Classify input type
   ├─ Determine specialized path
   └─ Pass context to specialized node

3. [Specialized Nodes]
   ├─ general_chat → Conversational response
   ├─ medical_info → Knowledge retrieval
   ├─ booking_inquiry → Appointment booking logic
   ├─ booking_history → History retrieval
   ├─ analysis → Report analysis
   ├─ extract → Information extraction
   ├─ remedies → Home remedy suggestions
   ├─ ask_city → Location confirmation
   └─ memory → Patient context retrieval

4. reasoning()
   ├─ Query knowledge graph
   ├─ Vector search for similar cases
   ├─ LLM synthesis
   └─ Prepare response

5. response()
   ├─ Generate natural language
   ├─ Format action data (if booking)
   └─ Return complete response
```

---

## 🔍 Vector Store & Embeddings

### Qdrant Collection: `medical_knowledge`

**Configuration**:

```
- Backend: Qdrant (in-memory)
- Embedding Dimension: 384
- Embedding Model: all-MiniLM-L6-v2 (HuggingFace)
- Chunk Size: 600 characters
- Chunk Overlap: 100 characters
- Similarity Threshold: 0.6 (60% match required)
```

**Chunking Strategy**:

```
Document
  │
  ├─ Split into 600-char chunks
  ├─ 100-char overlap between chunks
  ├─ Hash-based deduplication
  │
  ├─ Chunk 1: "Fever is a common..."
  ├─ Chunk 2: "...symptom of various conditions..."
  └─ Chunk 3: "...infections and inflammations..."
```

**Search Process**:

1. User query → Embedding (384-dim vector)
2. Qdrant similarity search → Candidate chunks
3. Filter by threshold (0.6)
4. Return top-k most similar documents

---

## 🧠 Memory Layer

### Mem0AI Integration

**Architecture**:

```
User Query
    │
    ├─► ChromaDB (Persistent Storage)
    │   └─ Collection: patient_history
    │
    ├─► Embedder (HuggingFace)
    │   └─ Model: all-MiniLM-L6-v2
    │
    ├─► LLM Backend (NVIDIA)
    │   └─ Model: Mistral Large 3 (675B parameters)
    │
    └─► Memory Operations
        ├─ Add (store new facts)
        ├─ Update (modify existing memory)
        └─ Retrieve (fetch relevant context)
```

**Memory Categories**:

- Patient demographics
- Medical history
- Medication history
- Allergy information
- Previous appointments
- Preferred doctors/specialists
- Health concerns timeline

---

## 📡 Real-Time Features

### WebSocket Event System

**Event Flow**:

```
Doctor/Patient Action
    │
    ├─► Trigger Event Creation
    │
    ├─► WebSocket Broadcast
    │   ├─ Appointment Events
    │   ├─ Chat Messages
    │   ├─ Schedule Changes
    │   ├─ Status Updates
    │   └─ Notifications
    │
    └─► Connected Clients Receive
        ├─ Doctors (real-time schedule updates)
        └─ Patients (appointment status updates)
```

**Event Types** (10):

1. `APPOINTMENT_CREATED` - New booking
2. `APPOINTMENT_UPDATED` - Rescheduled
3. `APPOINTMENT_CANCELLED` - Cancelled
4. `APPOINTMENT_CONFIRMED` - Confirmed
5. `CHAT_MESSAGE` - New chat
6. `SCHEDULE_CHANGE` - Doctor availability
7. `NOTIFICATION` - System alerts
8. `DOCTOR_ONLINE` - Doctor goes online
9. `DOCTOR_OFFLINE` - Doctor goes offline
10. `PATIENT_ONLINE` - Patient session starts

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.9+
- Node.js 16+
- React Native CLI (for mobile)
- Neo4j (local or cloud)
- Qdrant (runs in-memory)

### Step 1: Clone & Navigate

```bash
cd e:\Project
```

### Step 2: Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Environment Variables

Create `.env` file in project root:

```env
# API Keys
GROQ_API_KEY=your_groq_key
NVIDIA_API_KEY=your_nvidia_key
OPENAI_API_KEY=your_openai_key (optional)

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# External Services
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number

SENDGRID_API_KEY=your_sendgrid_key

RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret

SARVAM_API_KEY=your_sarvam_key

# JWT
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
```

### Step 5: Database Setup

```bash
# Initialize SQLite
python database.py

# Initialize Neo4j knowledge graph
python init_graph.py

# Load demo data
python setup_demo.py
```

### Step 6: Frontend Setup

```bash
cd frontend
npm install
```

### Step 7: Mobile Setup (Optional)

```bash
cd mobile-app
npm install
```

---

## 🚀 Running the Application

### Terminal 1: FastAPI Backend

```bash
# From project root
python -m uvicorn backend.main:app --reload --port 8000
```

**API Documentation**:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Terminal 2: React Frontend

```bash
cd frontend
npm run dev
```

**Frontend URL**: http://localhost:5173

### Terminal 3: Streamlit (Optional)

```bash
streamlit run app.py
```

**Streamlit URL**: http://localhost:8501

### Mobile App (Optional)

```bash
cd mobile-app

# iOS
npm run ios

# Android
npm run android
```

---

## ✨ Key Features

### 1. **AI-Powered Medical Consultation**

- Multi-node LangGraph workflow (15 nodes)
- Emergency triage detection
- Personalized health advice
- Clinical report analysis

### 2. **Intelligent Doctor Matching**

- Neo4j knowledge graph integration
- Specialty-based filtering
- Location-aware search
- Rating and experience filters
- Dynamic doctor profiles

### 3. **Smart Appointment Booking**

- Real-time availability slots
- Multi-step booking workflow
- Appointment history tracking
- Schedule notifications

### 4. **Real-Time Collaboration**

- WebSocket-based live updates
- Doctor-patient real-time messaging
- Live schedule synchronization
- Status notifications

### 5. **Multi-Channel Support**

- Web (React)
- Mobile (React Native)
- CLI (Streamlit)
- Voice (Sarvam AI)

### 6. **Secure Authentication**

- JWT tokens
- Password hashing with salt
- Role-based access (patient/doctor/admin)
- Session management

### 7. **Payment Integration**

- Razorpay payment processing
- Order creation & verification
- Payment status tracking

### 8. **Notification System**

- SMS via Twilio
- Email via SendGrid
- In-app notifications
- Push notifications (mobile)

### 9. **Voice Services**

- Text-to-Speech (TTS) - Sarvam AI
- Speech-to-Text (STT) - Sarvam AI
- Multi-language support

### 10. **Multi-Language Support**

- Translation via deep-translator
- Language detection
- Localized responses

### 11. **Persistent Memory**

- Patient history with Mem0AI
- Context-aware responses
- Cross-session continuity

### 12. **Vector Search**

- Semantic document search
- Similar case retrieval
- Medical knowledge base queries

---

## 📊 Technology Metrics

| Category                    | Count | Details                                  |
| --------------------------- | ----- | ---------------------------------------- |
| **LangGraph Nodes**         | 15    | Agentic workflow stages                  |
| **API Endpoints**           | 40+   | RESTful API routes                       |
| **Database Tables**         | 10+   | SQLite schema                            |
| **Frontend Pages**          | 13    | React components                         |
| **Streamlit Pages**         | 9     | Data science interfaces                  |
| **WebSocket Events**        | 10    | Real-time event types                    |
| **API Routers**             | 9     | FastAPI routers                          |
| **External Integrations**   | 8     | Twilio, SendGrid, Razorpay, Sarvam, etc. |
| **Embedding Dimension**     | 384   | Vector size (all-MiniLM-L6-v2)           |
| **LLM Temperature Buckets** | 3     | Classification, Analysis, Chat           |

---

## 🔐 Security Features

- ✅ JWT-based authentication
- ✅ Password hashing with salt
- ✅ Role-based access control (RBAC)
- ✅ SQL injection prevention (parameterized queries)
- ✅ CORS middleware
- ✅ Emergency detection & safety guardrails
- ✅ Hallucination prevention in AI responses
- ✅ PII masking in logs

---

## 📝 Configuration

### Key Configuration Files

**`.env`** - Environment variables (required)
**`config.py`** - Application configuration
**`backend/main.py`** - FastAPI setup & routing

### Important Settings

```python
# Vector Store
SIMILARITY_THRESHOLD = 0.6
CHUNK_SIZE = 600
EMBEDDING_DIM = 384

# LLM
LLM_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
LLM_TEMPERATURES = [0, 0.3, 0.5]

# Database
DB_NAME = "hospital.db"
NEO4J_URI = "bolt://localhost:7687"

# CORS
ALLOWED_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Neo4j Connection Failed**

```
Solution: Ensure Neo4j service is running
Windows: Services > Neo4j
Linux: sudo systemctl start neo4j
```

**2. Qdrant Not Initializing**

```
Solution: In-memory Qdrant requires ~1GB RAM
Check: Free up RAM or restart application
```

**3. API Endpoints Return 403**

```
Solution: Check JWT token in Authorization header
Format: Authorization: Bearer <token>
```

**4. Frontend Can't Connect to Backend**

```
Solution: Check CORS configuration
Ensure port 8000 backend is running
Check http://localhost:8000/api/ping
```

---

## 📚 Documentation

- **[API Docs](http://localhost:8000/docs)** - Auto-generated Swagger
- **[Database Schema](./DATABASE_SCHEMA.md)** - Detailed table definitions
- **[LangGraph Guide](./LANGGRAPH_GUIDE.md)** - Node workflow documentation
- **[Deployment Guide](./DEPLOYMENT.md)** - Production setup

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👥 Support

For issues, questions, or suggestions:

- 📧 Email: support@medicare-ai.com
- 🐛 GitHub Issues: [Report Bug](../../issues)
- 💬 Discussions: [Start Discussion](../../discussions)

---

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **LangChain & LangGraph** - AI orchestration
- **React** - Frontend UI library
- **Neo4j** - Knowledge graph database
- **Qdrant** - Vector database
- **Groq** - LLM API provider
- **NVIDIA** - AI acceleration

---

**Last Updated**: May 14, 2026

**Version**: 2.0.0

**Status**: ✅ Active Development
