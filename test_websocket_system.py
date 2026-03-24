"""
test_websocket_system.py — Test WebSocket Server and Client
Verifies real-time communication between server and clients
"""

import asyncio
import json
import time
import subprocess
import sys
from pathlib import Path

print("\n" + "="*80)
print("🧪 WEBSOCKET SYSTEM TEST")
print("="*80 + "\n")

# ============================================================================
# CHECK SERVER STATUS
# ============================================================================

def check_server_status():
    """Check if WebSocket server is running"""
    
    print("1️⃣  CHECKING SERVER STATUS")
    print("-" * 80)
    
    try:
        import requests
        
        response = requests.get("http://localhost:8000/health", timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is running")
            print(f"   Status: {data['status']}")
            print(f"   Service: {data['service']}")
            return True
        else:
            print(f"⚠️  Server returned status {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at localhost:8000")
        print(f"\n   📍 Make sure WebSocket server is running:")
        print(f"   python -m uvicorn websocket_server:app --host 0.0.0.0 --port 8000")
        return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_server_status():
    """Get detailed server status"""
    
    try:
        import requests
        response = requests.get("http://localhost:8000/api/status", timeout=2)
        data = response.json()
        
        print(f"\n✅ Server Status:")
        print(f"   Online Doctors: {data['online_doctors']}")
        print(f"   Online Patients: {data['online_patients']}")
        print(f"   Active Connections: {data['active_connections']}")
        
        return True
    
    except Exception as e:
        print(f"⚠️  Could not get status: {e}")
        return False

# ============================================================================
# TEST WEBSOCKET CONNECTION
# ============================================================================

async def test_websocket_connection():
    """Test WebSocket connection"""
    
    print("\n2️⃣  TESTING WEBSOCKET CONNECTION")
    print("-" * 80)
    
    try:
        import websockets
        
        # Test doctor connection
        print("Connecting as doctor...")
        
        uri = "ws://localhost:8000/ws/8/doctor"
        
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")
            
            # Send a test message
            test_msg = json.dumps({"action": "ping"})
            await websocket.send(test_msg)
            print(f"   Sent: {test_msg}")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            
            print(f"   Received: {response_data['event_type']}")
            print(f"✅ Ping/Pong successful!\n")
            
            return True
    
    except asyncio.TimeoutError:
        print(f"❌ Timeout waiting for response")
        return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ============================================================================
# TEST MESSAGE SENDING
# ============================================================================

async def test_message_sending():
    """Test sending messages between clients"""
    
    print("\n3️⃣  TESTING MESSAGE SENDING (Doctor → Patient)")
    print("-" * 80)
    
    try:
        import websockets
        
        # Create two connections
        doctor_uri = "ws://localhost:8000/ws/8/doctor"
        patient_uri = "ws://localhost:8000/ws/5/patient"
        
        async with websockets.connect(doctor_uri) as doctor_ws, \
                   websockets.connect(patient_uri) as patient_ws:
            
            print(f"✅ Doctor connected")
            print(f"✅ Patient connected\n")
            
            # Doctor sends chat message
            chat_msg = {
                "action": "chat_message",
                "data": {
                    "recipient_id": 5,
                    "message": "Hello! How are you?",
                    "sender_name": "Dr. Smith"
                }
            }
            
            await doctor_ws.send(json.dumps(chat_msg))
            print(f"Doctor sent: {chat_msg['data']['message']}")
            
            # Patient receives message
            await asyncio.sleep(0.5)
            response = await asyncio.wait_for(patient_ws.recv(), timeout=5)
            response_data = json.loads(response)
            
            if response_data['event_type'] == 'chat_message':
                print(f"Patient received: {response_data['data']['message']}")
                print(f"✅ Message delivery successful!\n")
                return True
            else:
                print(f"⚠️  Unexpected response: {response_data['event_type']}")
                return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ============================================================================
# TEST APPOINTMENT NOTIFICATION
# ============================================================================

async def test_appointment_notification():
    """Test appointment notifications"""
    
    print("\n4️⃣  TESTING APPOINTMENT NOTIFICATIONS")
    print("-" * 80)
    
    try:
        import websockets
        
        doctor_uri = "ws://localhost:8000/ws/8/doctor"
        patient_uri = "ws://localhost:8000/ws/5/patient"
        
        async with websockets.connect(doctor_uri) as doctor_ws, \
                   websockets.connect(patient_uri) as patient_ws:
            
            print("Doctor and Patient connected\n")
            
            # Doctor creates appointment
            apt_msg = {
                "action": "appointment_update",
                "data": {
                    "event_type": "created",
                    "doctor_id": 8,
                    "patient_id": 5,
                    "appointment_date": "2026-03-25",
                    "appointment_time": "14:00",
                    "reason": "Regular checkup"
                }
            }
            
            await doctor_ws.send(json.dumps(apt_msg))
            print(f"Doctor created appointment")
            
            # Both should receive notification
            await asyncio.sleep(0.5)
            
            try:
                doctor_response = await asyncio.wait_for(doctor_ws.recv(), timeout=2)
                doc_data = json.loads(doctor_response)
                print(f"✅ Doctor received: {doc_data['event_type']}")
            except asyncio.TimeoutError:
                pass
            
            try:
                patient_response = await asyncio.wait_for(patient_ws.recv(), timeout=2)
                pat_data = json.loads(patient_response)
                print(f"✅ Patient received: {pat_data['event_type']}")
                print(f"\n✅ Appointment notification successful!\n")
                return True
            except asyncio.TimeoutError:
                print(f"⚠️  Patient did not receive notification")
                return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ============================================================================
# TEST REST API
# ============================================================================

def test_rest_api():
    """Test HTTP API endpoints"""
    
    print("\n5️⃣  TESTING REST API")
    print("-" * 80)
    
    try:
        import requests
        
        # Test notify endpoint
        print("Testing /api/notify/{user_id}...")
        
        response = requests.post(
            "http://localhost:8000/api/notify/8",
            json={
                "type": "test",
                "message": "Test notification",
                "title": "System Test"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ Notification sent")
            print(f"   Response: {response.json()}\n")
        else:
            print(f"⚠️  Status {response.status_code}")
            return False
        
        # Test broadcast endpoint
        print("Testing /api/broadcast...")
        
        response = requests.post(
            "http://localhost:8000/api/broadcast",
            json={
                "user_ids": [5, 8],
                "notification": {
                    "type": "system_test",
                    "message": "System test broadcast"
                }
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Broadcast sent to {data['count']} users")
            print(f"✅ REST API working!\n")
            return True
        else:
            print(f"⚠️  Status {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all tests"""
    
    results = {
        "server_status": False,
        "websocket_connection": False,
        "message_sending": False,
        "appointment_notification": False,
        "rest_api": False
    }
    
    # Check server
    if not check_server_status():
        print("\n❌ Server is not running!")
        print("\nTo start the server, run:")
        print("  python -m uvicorn websocket_server:app --host 0.0.0.0 --port 8000")
        return results
    
    results["server_status"] = True
    get_server_status()
    
    # Run async tests
    results["websocket_connection"] = await test_websocket_connection()
    results["message_sending"] = await test_message_sending()
    results["appointment_notification"] = await test_appointment_notification()
    
    # Run sync tests
    results["rest_api"] = test_rest_api()
    
    return results

def print_summary(results):
    """Print test summary"""
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Results: {passed}/{total} tests passed\n")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name.replace('_', ' ').title()}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nWebSocket system is ready for deployment.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        print("\nPlease check the server logs and try again.")
    
    print("\n" + "="*80 + "\n")

def main():
    """Main entry point"""
    
    try:
        # Run all tests
        results = asyncio.run(run_all_tests())
        
        # Print summary
        print_summary(results)
        
        return 0 if all(results.values()) else 1
    
    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted")
        return 1
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
