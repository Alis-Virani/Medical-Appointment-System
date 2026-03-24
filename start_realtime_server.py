"""
start_realtime_server.py — Start WebSocket Server for Real-Time Updates
Run this script to enable real-time appointment and chat features
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"   {text}")
    print("="*80 + "\n")

def check_dependencies():
    """Check if required packages are installed"""
    
    print_header("CHECKING DEPENDENCIES")
    
    required_packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "websockets": "WebSockets",
    }
    
    missing = []
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {name:<20} installed")
        except ImportError:
            print(f"❌ {name:<20} MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Installing missing packages: {', '.join(missing)}\n")
        
        for package in missing:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        print(f"\n✅ All dependencies installed!")
    
    return len(missing) == 0

def start_websocket_server():
    """Start the WebSocket server"""
    
    print_header("STARTING WEBSOCKET SERVER")
    
    try:
        # Run uvicorn with websocket_server.py
        print("🚀 Starting uvicorn server...\n")
        print("   Host: 0.0.0.0")
        print("   Port: 8000")
        print("   WebSocket: ws://localhost:8000/ws/{user_id}/{doctor|patient}")
        print("\n   Press Ctrl+C to stop\n")
        print("="*80 + "\n")
        
        subprocess.run(
            [sys.executable, "-m", "uvicorn", 
             "websocket_server:app", 
             "--host", "0.0.0.0",
             "--port", "8000",
             "--reload"],
            cwd=Path(__file__).parent
        )
    
    except KeyboardInterrupt:
        print("\n\n✋ Server shutdown requested")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")

def start_streamlit_app():
    """Start Streamlit app (optional - can be run separately)"""
    
    print_header("STARTING STREAMLIT APP")
    
    try:
        print("🎨 Starting Streamlit app...\n")
        
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app.py"],
            cwd=Path(__file__).parent
        )
    
    except KeyboardInterrupt:
        print("\n\n✋ Streamlit shutdown requested")
    except Exception as e:
        print(f"\n❌ Error starting Streamlit: {e}")

def main():
    """Main entry point"""
    
    print("\n" + "="*80)
    print("   MEDICAL APPOINTMENT SYSTEM - REAL-TIME SERVER")
    print("="*80)
    
    print("""
┌─────────────────────────────────────────────────────────────┐
│  This script starts the WebSocket server for real-time      │
│  appointment and chat updates.                              │
│                                                              │
│  Features enabled:                                           │
│    ✓ Live chat messages                                      │
│    ✓ Instant appointment notifications                       │
│    ✓ Real-time schedule updates                             │
│    ✓ Doctor/Patient online status                           │
│    ✓ Typing indicators                                       │
└─────────────────────────────────────────────────────────────┘
""")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot start: missing dependencies")
        sys.exit(1)
    
    # Show options
    print("\n📋 OPTIONS:\n")
    print("   1. Start WebSocket server only")
    print("   2. Start Streamlit app only")
    print("   3. Start both (in separate terminals)")
    print("   4. Show usage examples")
    print("   0. Exit\n")
    
    choice = input("Enter choice (0-4): ").strip()
    
    if choice == "1":
        start_websocket_server()
    
    elif choice == "2":
        start_streamlit_app()
    
    elif choice == "3":
        print("\n⚠️  Starting both in background...")
        print("   Note: You must run each in a separate terminal")
        print("\n   Terminal 1: python start_realtime_server.py")
        print("   Terminal 2: python -m streamlit run app.py\n")
        
        input("Press Enter when you're ready to start...")
        
        try:
            print("🚀 Starting WebSocket server...")
            subprocess.Popen([sys.executable, "-m", "uvicorn",
                            "websocket_server:app",
                            "--host", "0.0.0.0",
                            "--port", "8000",
                            "--reload"])
            
            time.sleep(2)
            
            print("🎨 Starting Streamlit app...")
            subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py"])
            
            print("\n✅ Both services started!")
            print("   WebSocket: ws://localhost:8000")
            print("   Streamlit: http://localhost:8501")
            print("\n   Press Ctrl+C to close...\n")
            
            # Keep running
            while True:
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\n✋ Shutting down all services...")
    
    elif choice == "4":
        show_usage_examples()
    
    else:
        print("\n👋 Goodbye!")

def show_usage_examples():
    """Show usage examples"""
    
    print_header("USAGE EXAMPLES")
    
    print("""
1️⃣  PYTHON CLIENT (Direct)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from websocket_client import RealtimeWebSocketClient

# Create client
client = RealtimeWebSocketClient(server_url="ws://localhost:8000")

# Register event handlers
def on_chat_message(data):
    print(f"New message: {data['data']['message']}")

client.register_handler("chat_message", on_chat_message)

# Connect
client.connect_async(user_id=8, user_type="doctor")

# Send message
client.send_message_sync("chat_message", {
    "recipient_id": 5,
    "message": "Hello, patient!",
    "sender_name": "Dr. Smith"
})


2️⃣  STREAMLIT INTEGRATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import streamlit as st
from realtime_integration import (
    init_realtime_features,
    handle_realtime_updates,
    show_realtime_status
)

# Initialize
init_realtime_features()

# Show status
show_realtime_status()

# Handle updates
updates = handle_realtime_updates()

for update in updates:
    if update["type"] == "chat":
        st.chat_message(update["sender_name"])
        st.write(update["message"])


3️⃣  HTTP API (For External Integration)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Send notification to specific user
POST http://localhost:8000/api/notify/8
{
    "type": "appointment_reminder",
    "title": "Your appointment in 30 minutes",
    "doctor": "Dr. Smith"
}

# Broadcast notification to all users
POST http://localhost:8000/api/broadcast
{
    "user_ids": [1, 2, 3, 4, 5],
    "notification": {
        "type": "system_maintenance",
        "message": "System maintenance scheduled for 2AM"
    }
}

# Get system status
GET http://localhost:8000/api/status

Response:
{
    "online_doctors": 3,
    "online_patients": 7,
    "active_connections": 10,
    "timestamp": "2026-03-22T10:30:00"
}


4️⃣  WEBSOCKET EVENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Available event types:

Client sends:
  • appointment_update → {"event_type": "created|updated|cancelled", ...}
  • chat_message       → {"recipient_id": 5, "message": "Hello"}
  • schedule_change    → {"working_hours": {...}, "blocked_dates": [...]}
  • typing            → {"recipient_id": 5, "is_typing": true}

Server broadcasts:
  • appointment_created     → New appointment notification
  • appointment_updated     → Appointment time/details changed
  • appointment_cancelled   → Appointment cancelled
  • chat_message           → New chat message from other user
  • schedule_change        → Doctor schedule updated
  • doctor_online          → Doctor came online
  • doctor_offline         → Doctor went offline
  • patient_online         → Patient came online
  • patient_offline        → Patient went offline
  • notification           → General system notification


5️⃣  TESTING WITH CURL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Health check
curl http://localhost:8000/health

# Get status
curl http://localhost:8000/api/status

# Send notification
curl -X POST http://localhost:8000/api/notify/8 \\
  -H "Content-Type: application/json" \\
  -d '{"type": "test", "message": "Test notification"}'


6️⃣  TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Port 8000 already in use:
  $ lsof -i :8000        (Linux/Mac)
  $ netstat -ano | findstr :8000  (Windows)

Connection refused:
  • Make sure WebSocket server is running
  • Check firewall settings
  • Verify server URL in client config

Messages not received:
  • Check WebSocket connection status
  • Verify event handlers are registered
  • Check server logs for errors
  • Ensure recipient_id is correct

Performance issues:
  • Load test with multiple connections
  • Monitor server CPU/memory
  • Check database query performance
  • Consider Redis message queue for scaling


7️⃣  STARTING MULTIPLE SERVERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Terminal 1: WebSocket Server (Port 8000)
python -m uvicorn websocket_server:app --host 0.0.0.0 --port 8000

# Terminal 2: Backup WebSocket Server (Port 8001)
python -m uvicorn websocket_server:app --host 0.0.0.0 --port 8001

# Terminal 3: Streamlit App (Port 8501)
streamlit run app.py

# Client connects to primary, fails over to backup if needed


ENABLED FEATURES
════════════════════════════════════════════════════════════════

✅ REAL-TIME CHAT
   • Instant message delivery
   • Typing indicators
   • Message history
   • Offline message queue

✅ APPOINTMENT UPDATES
   • Create appointment notification
   • Update/reschedule alerts
   • Cancellation notices
   • Confirmation status

✅ SCHEDULE MANAGEMENT
   • Doctor schedule changes broadcast
   • Automatic patient notification
   • Slot availability updates
   • Blocked dates management

✅ PRESENCE TRACKING
   • Online/offline status
   • Doctor availability indicator
   • Patient availability indicator
   • Real-time user count

✅ SYSTEM MONITORING
   • Connection status dashboard
   • Active connection count
   • Message queue monitoring
   • Reconnection tracking

✅ SCALABILITY
   • Connection pooling
   • Message buffering
   • Automatic reconnection
   • Graceful degradation

════════════════════════════════════════════════════════════════
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
