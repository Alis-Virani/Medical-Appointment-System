"""
websocket_client.py — WebSocket Client for Streamlit Real-Time Integration
Handles: Connecting to server, receiving updates, managing connection state
"""

import asyncio
import json
import threading
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import queue

import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class ConnectionState(Enum):
    """Connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

# ============================================================================
# WEBSOCKET CLIENT
# ============================================================================

class RealtimeWebSocketClient:
    """WebSocket client for Streamlit-based real-time updates"""
    
    def __init__(self, server_url: str = "ws://localhost:8000", debug: bool = False):
        """
        Initialize WebSocket client
        
        Args:
            server_url: Base URL of WebSocket server (without /ws path)
            debug: Enable debug logging
        """
        self.server_url = server_url
        self.debug = debug
        
        # Connection state
        self.state = ConnectionState.DISCONNECTED
        self.user_id: Optional[int] = None
        self.user_type: Optional[str] = None
        self.websocket = None
        
        # Event handlers
        self.event_handlers: Dict[str, list] = {}
        
        # Message queue for Streamlit (thread-safe)
        self.message_queue = queue.Queue()
        
        # Background thread
        self.bg_thread: Optional[threading.Thread] = None
        self.should_stop = False
        
        # Reconnection
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2
    
    def connect_async(self, user_id: int, user_type: str):
        """Start connection in background thread"""
        self.user_id = user_id
        self.user_type = user_type
        
        # Start background thread
        self.bg_thread = threading.Thread(target=self._run_connection, daemon=True)
        self.bg_thread.start()
        
        logger.info(f"🔄 WebSocket connection started for {user_type} {user_id}")
    
    def _run_connection(self):
        """Run the WebSocket connection (blocking - runs in background thread)"""
        async def main():
            await self._connect_and_listen()
        
        # Run async loop in thread
        asyncio.run(main())
    
    async def _connect_and_listen(self):
        """Establish WebSocket connection and listen for messages"""
        
        uri = f"{self.server_url}/ws/{self.user_id}/{self.user_type}"
        
        while not self.should_stop and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.state = ConnectionState.CONNECTING
                logger.info(f"🔗 Connecting to {uri}")
                
                async with websockets.connect(uri) as websocket:
                    self.websocket = websocket
                    self.state = ConnectionState.CONNECTED
                    self.reconnect_attempts = 0
                    
                    logger.info(f"✅ Connected: {self.user_type} {self.user_id}")
                    
                    # Start keep-alive ping
                    ping_task = asyncio.create_task(self._send_ping())
                    
                    try:
                        # Listen for messages
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                self.message_queue.put(data)
                                
                                # Call event handlers
                                await self._call_handlers(data)
                                
                                if self.debug:
                                    logger.info(f"📨 Received: {data.get('event_type')}")
                            
                            except json.JSONDecodeError:
                                logger.error(f"Invalid JSON: {message}")
                    
                    finally:
                        ping_task.cancel()
            
            except websockets.exceptions.WebSocketException as e:
                self.state = ConnectionState.ERROR
                logger.error(f"❌ WebSocket error: {e}")
                self.reconnect_attempts += 1
                
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    wait_time = self.reconnect_delay * (2 ** self.reconnect_attempts)
                    logger.info(f"🔄 Reconnecting in {wait_time}s (attempt {self.reconnect_attempts})")
                    await asyncio.sleep(wait_time)
            
            except Exception as e:
                self.state = ConnectionState.ERROR
                logger.error(f"❌ Unexpected error: {e}")
                self.reconnect_attempts += 1
                await asyncio.sleep(self.reconnect_delay)
        
        self.state = ConnectionState.DISCONNECTED
        logger.warning(f"🔴 WebSocket connection closed ({self.user_type} {self.user_id})")
    
    async def _send_ping(self):
        """Send periodic ping to keep connection alive"""
        while not self.should_stop and self.websocket:
            try:
                await asyncio.sleep(30)  # Ping every 30 seconds
                
                if self.websocket and not self.websocket.closed:
                    message = json.dumps({"action": "ping"})
                    await self.websocket.send(message)
                    
                    if self.debug:
                        logger.info("🏓 Ping sent")
            
            except Exception as e:
                logger.error(f"Ping error: {e}")
    
    async def send_message(self, action: str, data: Dict[str, Any]):
        """Send message to server"""
        
        if self.state != ConnectionState.CONNECTED or not self.websocket:
            logger.warning(f"Cannot send: not connected (state={self.state})")
            return False
        
        try:
            message = json.dumps({"action": action, "data": data})
            await self.websocket.send(message)
            
            if self.debug:
                logger.info(f"📤 Sent: {action}")
            
            return True
        
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False
    
    def send_message_sync(self, action: str, data: Dict[str, Any]):
        """Synchronous wrapper for send_message (for Streamlit)"""
        try:
            # Create new event loop if needed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_message(action, data))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Sync send error: {e}")
            return False
    
    async def _call_handlers(self, event_data: Dict):
        """Call registered event handlers"""
        event_type = event_data.get("event_type")
        
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(event_data)
                except Exception as e:
                    logger.error(f"Handler error: {e}")
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register a callback handler for an event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.info(f"✅ Handler registered for {event_type}")
    
    def get_messages(self, timeout: float = 0.1) -> list:
        """Get all queued messages (non-blocking)"""
        messages = []
        
        while True:
            try:
                msg = self.message_queue.get(timeout=timeout)
                messages.append(msg)
            except queue.Empty:
                break
        
        return messages
    
    def is_connected(self) -> bool:
        """Check if currently connected"""
        return self.state == ConnectionState.CONNECTED
    
    def get_status(self) -> Dict:
        """Get connection status"""
        return {
            "state": self.state.value,
            "connected": self.is_connected(),
            "user_id": self.user_id,
            "user_type": self.user_type,
            "messages_queued": self.message_queue.qsize(),
            "reconnect_attempts": self.reconnect_attempts
        }
    
    def disconnect(self):
        """Disconnect and clean up"""
        self.should_stop = True
        
        if self.websocket:
            try:
                asyncio.run(self.websocket.close())
            except:
                pass
        
        self.state = ConnectionState.DISCONNECTED
        logger.info(f"🔴 Disconnected: {self.user_type} {self.user_id}")

# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_client_instance: Optional[RealtimeWebSocketClient] = None

def get_realtime_client(server_url: str = "ws://localhost:8000", debug: bool = False) -> RealtimeWebSocketClient:
    """Get or create WebSocket client singleton"""
    global _client_instance
    
    if _client_instance is None:
        _client_instance = RealtimeWebSocketClient(server_url=server_url, debug=debug)
    
    return _client_instance

def disconnect_realtime_client():
    """Disconnect and destroy the client"""
    global _client_instance
    
    if _client_instance:
        _client_instance.disconnect()
        _client_instance = None

# ============================================================================
# STREAMLIT INTEGRATION HELPERS
# ============================================================================

def init_realtime_session(user_id: int, user_type: str, server_url: str = "ws://localhost:8000"):
    """
    Initialize real-time connection in Streamlit session
    
    Usage in Streamlit:
    ```python
    import streamlit as st
    from websocket_client import init_realtime_session
    
    if "realtime_initialized" not in st.session_state:
        init_realtime_session(st.session_state.user_id, st.session_state.role)
        st.session_state.realtime_initialized = True
    ```
    """
    client = get_realtime_client(server_url=server_url)
    client.connect_async(user_id, user_type)
    logger.info(f"✅ Streamlit session initialized with real-time updates")

def poll_realtime_updates():
    """
    Poll for new updates from WebSocket (call periodically in Streamlit)
    
    Usage:
    ```python
    updates = poll_realtime_updates()
    for update in updates:
        st.toast(f"New {update['event_type']}")
    ```
    """
    client = get_realtime_client()
    return client.get_messages()

def send_realtime_event(action: str, data: Dict[str, Any]):
    """
    Send a real-time event
    
    Usage:
    ```python
    send_realtime_event("chat_message", {
        "recipient_id": 5,
        "message": "Hello!",
        "sender_name": "Dr. Smith"
    })
    ```
    """
    client = get_realtime_client()
    return client.send_message_sync(action, data)

def get_realtime_status() -> Dict:
    """Get current real-time connection status"""
    client = get_realtime_client()
    return client.get_status()

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 WebSocket Client Test")
    print("="*80 + "\n")
    
    # Create client
    client = RealtimeWebSocketClient(debug=True)
    
    # Register handlers
    def on_chat_message(data):
        print(f"💬 Chat: {data.get('data', {}).get('message')}")
    
    def on_appointment(data):
        print(f"📅 Appointment: {data.get('event_type')}")
    
    client.register_handler("chat_message", on_chat_message)
    client.register_handler("appointment_created", on_appointment)
    
    # Connect
    print("Connecting to WebSocket server...\n")
    client.connect_async(8, "doctor")
    
    # Keep running
    try:
        import time
        while True:
            time.sleep(5)
            status = client.get_status()
            print(f"\nStatus: {status['state']} | Messages: {status['messages_queued']}")
    
    except KeyboardInterrupt:
        print("\n\nDisconnecting...")
        client.disconnect()
        print("✅ Tests complete\n")
