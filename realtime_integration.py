"""
realtime_integration.py — Streamlit Real-Time Integration Module
Integrates WebSocket updates into the main chat app
"""

import streamlit as st
import time
from datetime import datetime
from websocket_client import (
    init_realtime_session,
    poll_realtime_updates,
    send_realtime_event,
    get_realtime_status
)

def init_realtime_features():
    """Initialize real-time features in Streamlit app"""
    
    # Check if user is logged in
    if "user_id" not in st.session_state or "role" not in st.session_state:
        return False
    
    # Initialize WebSocket if not already done
    if "realtime_initialized" not in st.session_state:
        try:
            init_realtime_session(
                st.session_state.user_id,
                st.session_state.role,
                server_url="ws://localhost:8000"
            )
            st.session_state.realtime_initialized = True
            return True
        except Exception as e:
            st.warning(f"⚠️ Could not connect to real-time server: {e}")
            st.session_state.realtime_initialized = False
            return False
    
    return st.session_state.realtime_initialized

def handle_realtime_updates():
    """
    Detect and handle real-time updates
    Call this in your main chat page polling loop
    """
    
    if not st.session_state.get("realtime_initialized"):
        return []
    
    updates = poll_realtime_updates()
    
    if not updates:
        return []
    
    processed_updates = []
    
    for update in updates:
        event_type = update.get("event_type")
        data = update.get("data", {})
        user_type = update.get("user_type")
        timestamp = update.get("timestamp")
        
        processed_update = {
            "event_type": event_type,
            "data": data,
            "user_type": user_type,
            "timestamp": timestamp
        }
        
        # Handle different event types
        if event_type == "chat_message":
            processed_update["type"] = "chat"
            processed_update["message"] = data.get("message")
            processed_update["sender_name"] = data.get("sender_name")
            
            # Show toast notification
            st.toast(f"💬 New message from {data.get('sender_name', 'Unknown')}", icon="💬")
        
        elif event_type == "appointment_created":
            processed_update["type"] = "appointment_created"
            processed_update["appointment"] = data
            
            # Show notification
            st.toast("📅 New appointment scheduled!", icon="📅")
        
        elif event_type == "appointment_updated":
            processed_update["type"] = "appointment_updated"
            processed_update["appointment"] = data
            
            st.toast("📅 Appointment updated", icon="🔄")
        
        elif event_type == "appointment_cancelled":
            processed_update["type"] = "appointment_cancelled"
            processed_update["appointment"] = data
            
            st.toast("❌ Appointment cancelled", icon="❌")
        
        elif event_type == "schedule_change":
            processed_update["type"] = "schedule_change"
            processed_update["schedule"] = data
            
            st.toast("📅 Doctor schedule updated", icon="📅")
        
        elif event_type == "doctor_online":
            processed_update["type"] = "doctor_online"
            
            # Only show if not current user
            if data.get("online_doctors", []):
                doctor_count = len(data["online_doctors"])
                st.session_state.online_doctors = data["online_doctors"]
        
        elif event_type == "patient_online":
            processed_update["type"] = "patient_online"
            
            if data.get("online_patients", []):
                patient_count = len(data["online_patients"])
                st.session_state.online_patients = data["online_patients"]
        
        elif event_type == "notification":
            processed_update["type"] = "notification"
            notification_type = data.get("type")
            
            if notification_type == "typing":
                processed_update["is_typing"] = data.get("is_typing")
                processed_update["sender_id"] = data.get("sender_id")
            
            elif notification_type == "pong":
                # Keep-alive response
                pass
        
        processed_updates.append(processed_update)
    
    return processed_updates

def show_realtime_status():
    """Display real-time connection status in sidebar"""
    
    try:
        status = get_realtime_status()
        
        with st.sidebar:
            st.divider()
            st.subheader("🔗 Real-Time Status")
            
            # Connection status
            if status["connected"]:
                st.success(f"✅ **Connected**")
            else:
                st.error(f"🔴 **Disconnected** ({status['state']})")
            
            # Details
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Messages", status.get("messages_queued", 0))
            with col2:
                st.metric("Attempts", status.get("reconnect_attempts", 0))
            
            # User info
            if status["user_id"]:
                st.caption(f"User: {status['user_type']} #{status['user_id']}")
    
    except Exception as e:
        st.sidebar.warning(f"⚠️ Status unavailable: {e}")

def send_chat_message(recipient_id: int, message: str, sender_name: str) -> bool:
    """
    Send a chat message via real-time
    
    Args:
        recipient_id: Target user ID
        message: Message text
        sender_name: Name of sender
        
    Returns:
        True if sent successfully
    """
    
    if not st.session_state.get("realtime_initialized"):
        st.warning("⚠️ Real-time not connected")
        return False
    
    try:
        success = send_realtime_event("chat_message", {
            "recipient_id": recipient_id,
            "message": message,
            "sender_name": sender_name
        })
        
        if success:
            st.toast("💬 Message sent via real-time!", icon="✅")
        
        return success
    
    except Exception as e:
        st.error(f"Error sending message: {e}")
        return False

def create_appointment_notification(doctor_id: int, patient_id: int, appointment_data: dict):
    """
    Notify both doctor and patient about appointment
    
    Args:
        doctor_id: Doctor user ID
        patient_id: Patient user ID
        appointment_data: Dict with appointment details
    """
    
    try:
        event_type = appointment_data.get("event_type", "created")
        
        send_realtime_event("appointment_update", {
            "event_type": event_type,
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "appointment": appointment_data,
            "timestamp": datetime.now().isoformat()
        })
        
        st.toast("📅 Appointment notification sent!", icon="✅")
    
    except Exception as e:
        st.error(f"Error sending notification: {e}")

def update_doctor_schedule(doctor_id: int, working_hours: dict, blocked_dates: list):
    """
    Notify about doctor schedule changes
    
    Args:
        doctor_id: Doctor user ID
        working_hours: Dict of day -> {start, end}
        blocked_dates: List of blocked dates
    """
    
    try:
        send_realtime_event("schedule_change", {
            "doctor_id": doctor_id,
            "working_hours": working_hours,
            "blocked_dates": blocked_dates,
            "timestamp": datetime.now().isoformat()
        })
        
        st.toast("📅 Schedule update sent!", icon="✅")
    
    except Exception as e:
        st.error(f"Error updating schedule: {e}")

# ============================================================================
# STREAMLIT COMPONENTS
# ============================================================================

def show_real_time_chat_updates():
    """
    Display real-time chat message updates
    Call this in your chat page
    """
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        pass  # Reserved for messages
    
    with col2:
        if st.session_state.get("realtime_initialized"):
            st.success("🟢 Live", help="Connected to real-time updates")
        else:
            st.warning("🟡 Offline", help="Not connected to real-time updates")
    
    with col3:
        if st.button("🔄 Refresh", help="Check for new messages"):
            st.rerun()

def show_typing_indicator(sender_name: str):
    """Show typing indicator"""
    st.info(f"✍️ {sender_name} is typing...")

def show_appointment_notification(event_type: str, appointment: dict):
    """Show appointment notification"""
    
    doctor = appointment.get("doctor_name", "Unknown")
    patient = appointment.get("patient_name", "Unknown")
    date = appointment.get("appointment_date", "")
    time = appointment.get("appointment_time", "")
    
    if event_type == "appointment_created":
        st.success(f"📅 New appointment: {doctor} ↔ {patient} on {date} at {time}")
    
    elif event_type == "appointment_updated":
        st.info(f"🔄 Appointment updated: {doctor} ↔ {patient}")
    
    elif event_type == "appointment_cancelled":
        st.error(f"❌ Appointment cancelled: {doctor} ↔ {patient}")

def show_online_status():
    """Show online doctors and patients"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        online_doctors = st.session_state.get("online_doctors", [])
        if online_doctors:
            st.success(f"👨‍⚕️ {len(online_doctors)} doctors online")
        else:
            st.info("👨‍⚕️ No doctors online")
    
    with col2:
        online_patients = st.session_state.get("online_patients", [])
        if online_patients:
            st.success(f"👤 {len(online_patients)} patients online")
        else:
            st.info("👤 No patients online")

# ============================================================================
# EXAMPLE: HOW TO USE IN MAIN CHAT PAGE
# ============================================================================

"""
# Example integration in pages/chat.py:

import streamlit as st
from realtime_integration import (
    init_realtime_features,
    handle_realtime_updates,
    show_realtime_status,
    show_real_time_chat_updates,
    show_online_status
)

# Initialize real-time features
if not init_realtime_features():
    st.warning("Real-time updates not available. Install websocket server.")

# Show status in sidebar
show_realtime_status()

# Main content
st.title("Chat - Live Updates")

# Show connection status
show_real_time_chat_updates()
show_online_status()

# Display messages
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Messages")
    
    # Polling loop
    placeholder = st.empty()
    
    while True:
        # Check for new updates
        updates = handle_realtime_updates()
        
        # Process updates
        for update in updates:
            if update["type"] == "chat":
                with placeholder.container():
                    st.chat_message(update["sender_name"])
                    st.write(update["message"])
        
        # Sleep before next poll
        time.sleep(1)
        
        # Optional: refresh less frequently to avoid flickering
        # time.sleep(5)

with col2:
    st.subheader("Send Message")
    
    recipient_id = st.number_input("Recipient ID", value=5)
    message = st.text_area("Message")
    
    if st.button("Send"):
        from realtime_integration import send_chat_message
        
        success = send_chat_message(
            recipient_id,
            message,
            st.session_state.get("full_name", "Unknown")
        )
        
        if success:
            st.success("Message sent!")
"""
