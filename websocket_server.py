"""
websocket_server.py — Real-Time WebSocket Server for Doctor-Patient Updates
Handles: Live appointments, chat messages, schedule changes, notifications
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "hospital.db"

# Event types
class EventType(str, Enum):
    """Types of real-time events"""
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_UPDATED = "appointment_updated"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    CHAT_MESSAGE = "chat_message"
    SCHEDULE_CHANGE = "schedule_change"
    NOTIFICATION = "notification"
    DOCTOR_ONLINE = "doctor_online"
    DOCTOR_OFFLINE = "doctor_offline"
    PATIENT_ONLINE = "patient_online"
    PATIENT_OFFLINE = "patient_offline"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class RealtimeEvent:
    """Real-time event structure"""
    event_type: EventType
    timestamp: str
    user_id: int
    user_type: str  # "doctor" or "patient"
    data: Dict
    
    def to_json(self) -> str:
        return json.dumps({
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "user_type": self.user_type,
            "data": self.data
        })

# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        # Maps: user_id -> list of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        
        # Track online status
        self.online_doctors: Set[int] = set()
        self.online_patients: Set[int] = set()
        
        # Message queue for missed messages (for offline users)
        self.message_queue: Dict[int, list] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, user_type: str):
        """Register a new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        # Update online status
        if user_type == "doctor":
            self.online_doctors.add(user_id)
        else:
            self.online_patients.add(user_id)
        
        # Deliver any queued messages
        if user_id in self.message_queue:
            for msg in self.message_queue[user_id]:
                await websocket.send_text(msg)
            self.message_queue[user_id] = []
        
        logger.info(f"✅ {user_type} {user_id} connected. Active: {len(self.active_connections[user_id])}")
    
    async def disconnect(self, user_id: int, websocket: WebSocket, user_type: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # If no more connections, mark as offline
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                if user_type == "doctor":
                    self.online_doctors.discard(user_id)
                else:
                    self.online_patients.discard(user_id)
                
                logger.info(f"🔴 {user_type} {user_id} disconnected")
    
    async def broadcast_to_user(self, user_id: int, message: str):
        """Send message to all connections for a user"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
        else:
            # Queue for offline user
            if user_id not in self.message_queue:
                self.message_queue[user_id] = []
            self.message_queue[user_id].append(message)
    
    async def broadcast_to_doctor(self, doctor_id: int, message: str):
        """Send message to a specific doctor"""
        await self.broadcast_to_user(doctor_id, message)
    
    async def broadcast_to_patient(self, patient_id: int, message: str):
        """Send message to a specific patient"""
        await self.broadcast_to_user(patient_id, message)
    
    async def broadcast_to_group(self, user_ids: Set[int], message: str):
        """Send message to multiple users"""
        for user_id in user_ids:
            await self.broadcast_to_user(user_id, message)
    
    def is_online(self, user_id: int) -> bool:
        """Check if user is online"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0
    
    def get_online_doctors(self) -> Set[int]:
        """Get set of online doctors"""
        return self.online_doctors.copy()
    
    def get_online_patients(self) -> Set[int]:
        """Get set of online patients"""
        return self.online_patients.copy()

# ============================================================================
# GLOBAL MANAGER
# ============================================================================

manager = ConnectionManager()

# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle context for app startup/shutdown"""
    logger.info("🚀 WebSocket Server Starting...")
    yield
    logger.info("⛔ WebSocket Server Shutting Down...")

app = FastAPI(title="Medical Appointment WebSocket Server", lifespan=lifespan)

# CORS configuration for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/{user_id}/{user_type}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, user_type: str):
    """
    WebSocket endpoint for real-time updates
    
    URL: ws://localhost:8000/ws/{user_id}/{doctor|patient}
    
    Example:
    - ws://localhost:8000/ws/8/doctor
    - ws://localhost:8000/ws/5/patient
    """
    
    if user_type not in ["doctor", "patient"]:
        await websocket.close(code=1008, reason="Invalid user_type")
        return
    
    await manager.connect(websocket, user_id, user_type)
    
    # Notify others that this user is online
    event = RealtimeEvent(
        event_type=EventType.DOCTOR_ONLINE if user_type == "doctor" else EventType.PATIENT_ONLINE,
        timestamp=datetime.now().isoformat(),
        user_id=user_id,
        user_type=user_type,
        data={"online_doctors": list(manager.get_online_doctors()), 
              "online_patients": list(manager.get_online_patients())}
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info(f"📨 {user_type} {user_id}: {message.get('action')}")
            
            # Handle different message types
            action = message.get("action")
            
            if action == "appointment_update":
                await handle_appointment_update(user_id, user_type, message, manager)
            
            elif action == "chat_message":
                await handle_chat_message(user_id, user_type, message, manager)
            
            elif action == "schedule_change":
                await handle_schedule_change(user_id, user_type, message, manager)
            
            elif action == "typing":
                await handle_typing(user_id, user_type, message, manager)
            
            elif action == "ping":
                # Keep-alive ping
                event = RealtimeEvent(
                    event_type=EventType.NOTIFICATION,
                    timestamp=datetime.now().isoformat(),
                    user_id=user_id,
                    user_type=user_type,
                    data={"type": "pong"}
                )
                await websocket.send_text(event.to_json())
            
    except WebSocketDisconnect:
        await manager.disconnect(user_id, websocket, user_type)
    
    except Exception as e:
        logger.error(f"WebSocket error for {user_type} {user_id}: {e}")
        await manager.disconnect(user_id, websocket, user_type)

# ============================================================================
# EVENT HANDLERS
# ============================================================================

async def handle_appointment_update(user_id: int, user_type: str, message: Dict, mgr: ConnectionManager):
    """Handle appointment creation/update/cancellation"""
    
    action = message.get("action")
    appointment_data = message.get("data", {})
    
    if action == "appointment_update" and appointment_data.get("event_type") == "created":
        event_type = EventType.APPOINTMENT_CREATED
    elif action == "appointment_update" and appointment_data.get("event_type") == "updated":
        event_type = EventType.APPOINTMENT_UPDATED
    elif action == "appointment_update" and appointment_data.get("event_type") == "cancelled":
        event_type = EventType.APPOINTMENT_CANCELLED
    else:
        event_type = EventType.APPOINTMENT_UPDATED
    
    # Get related users (doctor + patient)
    doctor_id = appointment_data.get("doctor_id")
    patient_id = appointment_data.get("patient_id")
    
    event = RealtimeEvent(
        event_type=event_type,
        timestamp=datetime.now().isoformat(),
        user_id=user_id,
        user_type=user_type,
        data=appointment_data
    )
    
    # Broadcast to both doctor and patient
    related_users = {doctor_id, patient_id}
    await mgr.broadcast_to_group(related_users, event.to_json())
    
    logger.info(f"📅 Appointment update: {event_type.value} - Doctor: {doctor_id}, Patient: {patient_id}")

async def handle_chat_message(user_id: int, user_type: str, message: Dict, mgr: ConnectionManager):
    """Handle chat messages"""
    
    recipient_id = message.get("recipient_id")
    chat_text = message.get("message", "")
    
    event = RealtimeEvent(
        event_type=EventType.CHAT_MESSAGE,
        timestamp=datetime.now().isoformat(),
        user_id=user_id,
        user_type=user_type,
        data={
            "message": chat_text,
            "recipient_id": recipient_id,
            "sender_name": message.get("sender_name", "Unknown")
        }
    )
    
    # Save to database
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO chat_messages (sender_id, recipient_id, message, timestamp, is_read)
            VALUES (?, ?, ?, ?, 0)
        """, (user_id, recipient_id, chat_text, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except:
        pass  # Chat messages table might not exist
    
    # Send to recipient
    await mgr.broadcast_to_user(recipient_id, event.to_json())
    
    logger.info(f"💬 Chat: {user_type} {user_id} -> {recipient_id}")

async def handle_schedule_change(user_id: int, user_type: str, message: Dict, mgr: ConnectionManager):
    """Handle doctor schedule changes"""
    
    if user_type != "doctor":
        logger.warning(f"Non-doctor {user_id} tried to update schedule")
        return
    
    schedule_data = message.get("data", {})
    
    event = RealtimeEvent(
        event_type=EventType.SCHEDULE_CHANGE,
        timestamp=datetime.now().isoformat(),
        user_id=user_id,
        user_type=user_type,
        data=schedule_data
    )
    
    # Update database
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        
        working_hours = schedule_data.get("working_hours", {})
        blocked_dates = schedule_data.get("blocked_dates", [])
        
        # Update working hours
        for day, hours in working_hours.items():
            cur.execute("""
                UPDATE doctor_working_hours 
                SET start_time = ?, end_time = ?
                WHERE doctor_id = ? AND day = ?
            """, (hours.get("start"), hours.get("end"), user_id, day))
        
        conn.commit()
        conn.close()
    except:
        pass
    
    # Broadcast to all connected patients (they need to see updated availability)
    online_patients = mgr.get_online_patients()
    await mgr.broadcast_to_group(online_patients, event.to_json())
    
    logger.info(f"📅 Schedule change by doctor {user_id}")

async def handle_typing(user_id: int, user_type: str, message: Dict, mgr: ConnectionManager):
    """Handle typing indicators"""
    
    recipient_id = message.get("recipient_id")
    is_typing = message.get("is_typing", False)
    
    event = RealtimeEvent(
        event_type=EventType.NOTIFICATION,
        timestamp=datetime.now().isoformat(),
        user_id=user_id,
        user_type=user_type,
        data={
            "type": "typing",
            "is_typing": is_typing,
            "sender_id": user_id
        }
    )
    
    await mgr.broadcast_to_user(recipient_id, event.to_json())

# ============================================================================
# REST API ENDPOINTS (for broadcasting without WebSocket)
# ============================================================================

@app.post("/api/notify/{user_id}")
async def notify_user(user_id: int, notification: Dict):
    """Send notification to a user via HTTP"""
    
    event = RealtimeEvent(
        event_type=EventType.NOTIFICATION,
        timestamp=datetime.now().isoformat(),
        user_id=0,  # System notification
        user_type="system",
        data=notification
    )
    
    await manager.broadcast_to_user(user_id, event.to_json())
    
    return {"status": "sent", "user_id": user_id}

@app.post("/api/broadcast")
async def broadcast_notification(data: Dict):
    """Broadcast notification to multiple/all users"""
    
    target_users = data.get("user_ids", list(manager.online_doctors) + list(manager.online_patients))
    
    event = RealtimeEvent(
        event_type=EventType.NOTIFICATION,
        timestamp=datetime.now().isoformat(),
        user_id=0,
        user_type="system",
        data=data.get("notification", {})
    )
    
    await manager.broadcast_to_group(set(target_users), event.to_json())
    
    return {"status": "broadcasted", "count": len(target_users)}

@app.get("/api/status")
async def get_status():
    """Get real-time system status"""
    
    return {
        "online_doctors": len(manager.online_doctors),
        "online_patients": len(manager.online_patients),
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "WebSocket Server"
    }

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*80)
    print("🚀 MEDICAL APPOINTMENT WEBSOCKET SERVER")
    print("="*80)
    print("\n📡 Starting WebSocket server on ws://localhost:8000\n")
    print("Endpoints:")
    print("  WebSocket: ws://localhost:8000/ws/{user_id}/{doctor|patient}")
    print("  Health: http://localhost:8000/health")
    print("  Status: http://localhost:8000/api/status")
    print("  Notify: http://localhost:8000/api/notify/{user_id}")
    print("  Broadcast: http://localhost:8000/api/broadcast")
    print("\n" + "="*80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
