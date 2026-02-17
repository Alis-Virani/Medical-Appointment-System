import streamlit as st
import os
import datetime
import random
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


try:
    from audio_recorder_streamlit import audio_recorder
except ImportError:
    st.error("Please run: pip install audio-recorder-streamlit")

from database import init_db, create_session, get_all_sessions, delete_session, load_messages, save_message
from tools import get_doctors_tool
from agent import get_agent_llm, basic_chat_llm
from lang_graph_agent import get_graph_app
from doctor_management import init_database
from safety_layer import get_safety_manager, get_audit_log
import pdfplumber
from PIL import Image
import pytesseract
import io

load_dotenv()
init_db()
init_database()  # Initialize doctor management system

st.set_page_config(page_title="MediCare AI", page_icon="🩺", layout="wide")

# --- CSS FOR UI ---
st.markdown("""
<style>
    .stChatInputContainer { border-radius: 20px; }
    .stApp { background-color: #131314; }
    div[data-testid="stExpander"] div[role="button"] p { font-size: 1.1rem; font-weight: bold; }
    
    /* Specific adjustment for Sidebar Buttons to align vertically */
    section[data-testid="stSidebar"] div[data-testid="column"] {
        display: flex;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# --- STATE MANAGEMENT ---
if "waiting_for_city" not in st.session_state:
    st.session_state.waiting_for_city = False
if "waiting_for_details" not in st.session_state:
    st.session_state.waiting_for_details = False
if "pending_specialty" not in st.session_state:
    st.session_state.pending_specialty = None
if "pending_city" not in st.session_state:
    st.session_state.pending_city = None
if "doctor_data" not in st.session_state:
    st.session_state.doctor_data = None
if "current_symptom" not in st.session_state:
    st.session_state.current_symptom = None

# --- SESSION LOGIC ---
query_params = st.query_params
url_session_id = query_params.get("session_id")

if "active_session_id" not in st.session_state:
    if url_session_id:
        try:
            st.session_state["active_session_id"] = int(url_session_id)
        except:
            new_id = create_session("New Chat")
            st.session_state["active_session_id"] = new_id
            st.query_params["session_id"] = str(new_id)
    else:
        new_id = create_session("New Chat")
        st.session_state["active_session_id"] = new_id
        st.query_params["session_id"] = str(new_id)

curr_id = st.session_state["active_session_id"]

# --- DELETE MODAL ---
@st.dialog("Delete chat?")
def show_delete_modal(session_id):
    st.write("This will delete prompts, responses and feedback.")
    c1, c2 = st.columns(2)
    if c1.button("Cancel", use_container_width=True): st.rerun()
    if c2.button("Delete", type="primary", use_container_width=True):
        delete_session(session_id)
        if st.session_state["active_session_id"] == session_id:
            st.session_state["active_session_id"] = None
            st.query_params.clear()
        st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Records")
    if st.button("+ New Chat", use_container_width=True):
        new_id = create_session("New Chat")
        st.session_state["active_session_id"] = new_id
        if "messages" in st.session_state: del st.session_state["messages"]
        st.session_state.waiting_for_city = False
        st.session_state.waiting_for_details = False
        st.session_state.pending_specialty = None
        st.session_state.pending_city = None
        st.session_state.doctor_data = None
        st.session_state.current_symptom = None
        st.query_params["session_id"] = str(new_id)
        st.rerun()
    
    st.divider()
    st.subheader("Voice Command")
    audio_bytes = audio_recorder(text="", icon_size="2x", neutral_color="#ffffff", recording_color="#ff4b4b")
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        st.success("Audio captured!")

    st.divider()
    st.subheader("Upload Report")
    uploaded_file = st.file_uploader("Upload PDF/Image", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file:
        with st.spinner("Analyzing report..."):
            try:
                text = ""
                if uploaded_file.name.lower().endswith('.pdf'):
                    with pdfplumber.open(uploaded_file) as pdf:
                        for page in pdf.pages:
                            text += page.extract_text() + "\n"
                else:
                    # For images
                    image = Image.open(uploaded_file)
                    text = pytesseract.image_to_string(image)
                
                if text.strip():
                    st.session_state.file_context = text
                    st.success("Report analyzed! You can now ask questions about it.")
                    with st.expander("View Extracted Text"):
                        st.text(text[:500] + "...")
                else:
                    st.warning("Could not extract text. Try a clearer image.")
            except Exception as e:
                st.error(f"Error analyzing file: {e}")

    st.divider()
    st.caption("Recent Chats")
    sessions = get_all_sessions()
    if sessions:
        for session_id, title in sessions:
            c1, c2 = st.columns([0.8, 0.2]) # Adjusted ratio for better alignment
            if c1.button(f"{title}", key=f"s_{session_id}", use_container_width=True):
                st.session_state["active_session_id"] = session_id
                if "messages" in st.session_state: del st.session_state["messages"]
                st.session_state.waiting_for_city = False
                st.session_state.waiting_for_details = False
                st.session_state.pending_specialty = None
                st.session_state.pending_city = None
                st.session_state.doctor_data = None
                st.session_state.current_symptom = None
                st.query_params["session_id"] = str(session_id)
                st.rerun()
            # Changed to 'x', added help text, and CRITICALLY added use_container_width=True
            if c2.button("x", key=f"d_{session_id}", help="Delete Chat", use_container_width=True):
                show_delete_modal(session_id)
    else:
        st.caption("No chats yet.")

# --- MAIN CHAT AREA ---

# Initialize messages if not present
if "messages" not in st.session_state:
    st.session_state.messages = load_messages(curr_id)

# Display Chat History
for msg in st.session_state.messages:
    # Handle different message types (LangChain Objects vs Dicts from DB)
    if isinstance(msg, (HumanMessage, AIMessage, SystemMessage)):
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        content = msg.content
    else:
        # Fallback for dicts
        role = msg.get("role", "user")
        content = msg.get("content", "")
    
    with st.chat_message(role):
        st.markdown(content)

# --- Main Chat Interface ---
user_input = st.chat_input("Type your symptoms or questions...")

# --- PROCESS INPUT ---
# Handle File Context
if "file_context" in st.session_state and st.session_state.file_context:
    if not user_input:
        user_input = "Please analyze the uploaded report."
    else:
        user_input += f"\n\n[Context from uploaded report]:\n{st.session_state.file_context}"
    
    # Clear context after use so it doesn't repeat
    st.session_state.file_context = None

if user_input:
    # 2. Add to UI
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append(HumanMessage(content=user_input))
    save_message(curr_id, "user", user_input)

    # 3. Invoke LangGraph Agent
    try:
        with st.spinner("Thinking..."):
            graph_app = get_graph_app()
            
            # Prepare initial state - SYNC FROM SESSION STATE
            initial_state = {
                "messages": st.session_state.messages,
                "user_id": str(curr_id),
                "symptoms": st.session_state.get("current_symptoms", []),
                "city": st.session_state.get("current_city"),
                "severity": st.session_state.get("current_severity", "low"),
                "doctors": st.session_state.get("suggested_doctors", []),
                "diagnosis": "",
                "specialist": "",
                "is_emergency": False,
                "safe_to_proceed": True,
                "needs_more_info": False,
                "memory_context": "",
                "input_type": "medical",
                "ask_for_city": st.session_state.get("ask_for_city", False),
                "booking_requested": st.session_state.get("booking_requested", False)
            }
            
            # Run graph
            final_state = graph_app.invoke(initial_state)
            
            # Extract response
            agent_response = final_state["messages"][-1].content
            
            # SYNC BACK TO SESSION STATE
            st.session_state.current_symptoms = final_state.get("symptoms", [])
            st.session_state.current_city = final_state.get("city")
            st.session_state.current_severity = final_state.get("severity", "low")
            st.session_state.suggested_doctors = final_state.get("doctors", [])
            st.session_state.ask_for_city = final_state.get("ask_for_city", False)
            st.session_state.booking_requested = final_state.get("booking_requested", False)
            
            # Display and Save
            st.chat_message("assistant").markdown(agent_response)
            st.session_state.messages.append(AIMessage(content=agent_response))
            save_message(curr_id, "assistant", agent_response)
            
            # Force rerun to update sidebar if doctors found
            if final_state.get("doctors"):
                st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
        # ... error handling ...

# --- SIDEBAR BOOKING UI ---
with st.sidebar:
    st.divider()
    # Show if doctors found OR if user explicitly wanted to book
    if st.session_state.get("suggested_doctors") or st.session_state.get("booking_requested"):
        st.subheader("📅 Book Appointment")
        with st.form("booking_form"):
            doctors = st.session_state.get("suggested_doctors", [])
            
            if doctors:
                st.write("Doctors found for your query:")
                doctor_options = [f"{d['doctor_name']} ({d['specialist']})" for d in doctors]
            else:
                st.warning("No specific doctors matched, but you can request a general appointment.")
                doctor_options = ["General Physician (Assign Next Available)"]
                
            selected_doc = st.selectbox("Select Doctor", doctor_options)
            
            # Show consultation fee
            consultation_fee = 500  # Default fee
            if doctors:
                # Try to get fee from doctor data (if available)
                selected_index = doctor_options.index(selected_doc)
                consultation_fee = doctors[selected_index].get('consultation_fee', 500)
            
            st.info(f"💰 Consultation Fee: ₹{consultation_fee}")
            
            name = st.text_input("Patient Name", placeholder="Enter your full name")
            phone = st.text_input("Phone Number", placeholder="+91XXXXXXXXXX")
            email = st.text_input("Email (Optional)", placeholder="your@email.com")
            
            # Only allow future dates (from today onwards)
            import datetime
            today = datetime.date.today()
            date = st.date_input(
                "Preferred Date",
                min_value=today,  # Cannot book past dates
                value=today  # Default to today
            )
            time = st.time_input("Preferred Time")
            
            submit_button = st.form_submit_button("💳 Proceed to Payment", use_container_width=True)
            
            if submit_button:
                # Validation
                if not name or not phone:
                    st.error("Please fill in all required fields!")
                else:
                    # Store booking details in session state to process after form
                    st.session_state.pending_booking = {
                        "doctor": selected_doc,
                        "name": name,
                        "phone": phone,
                        "email": email,
                        "date": date,
                        "time": time,
                        "consultation_fee": consultation_fee
                    }
                    st.success(f"✅ Proceeding to payment...")
                    st.balloons()
    
    # Process pending booking OUTSIDE the form context
    if "pending_booking" in st.session_state and st.session_state.pending_booking:
        booking = st.session_state.pending_booking
        
        # Show payment section
        st.sidebar.markdown("---")
        st.sidebar.subheader("💳 Payment")
        
        # Import payment service
        try:
            from payment_service import create_booking_payment, create_mock_payment_order, rupees_to_paise
            from notification_service import send_booking_confirmation
            
            # Create payment order
            booking_id = f"{curr_id}_{len(st.session_state.messages)}"
            
            # Try to create real payment order, fallback to mock
            payment_order = create_booking_payment(
                doctor_name=booking['doctor'],
                patient_name=booking['name'],
                consultation_fee=booking['consultation_fee'],
                booking_id=booking_id
            )
            
            if not payment_order:
                # Fallback to mock payment
                payment_order = create_mock_payment_order(
                    amount=rupees_to_paise(booking['consultation_fee']),
                    receipt_id=f"booking_{booking_id}"
                )
            
            # Display payment info
            amount_display = payment_order.get('amount_display', f"₹{booking['consultation_fee']}")
            st.sidebar.info(f"**Amount:** {amount_display}")
            
            # Payment button
            if payment_order.get('mock'):
                # Mock payment - just confirm
                if st.sidebar.button("✅ Confirm Payment (Test Mode)", use_container_width=True):
                    payment_status = "success"
                    payment_id = "pay_mock_" + booking_id
                else:
                    payment_status = None
            else:
                # Real Razorpay integration would go here
                # For now, show a button to simulate payment
                st.sidebar.warning("🔧 Razorpay integration: Add your API keys to .env")
                if st.sidebar.button("💳 Pay with Razorpay (Demo)", use_container_width=True):
                    payment_status = "success"
                    payment_id = "pay_demo_" + booking_id
                else:
                    payment_status = None
            
            # If payment successful, send notifications and show receipt
            if payment_status == "success":
                # Send notifications
                notification_results = send_booking_confirmation({
                    'patient_name': booking['name'],
                    'patient_phone': booking['phone'],
                    'patient_email': booking.get('email'),
                    'doctor_name': booking['doctor'],
                    'date': booking['date'].strftime('%B %d, %Y'),
                    'time': booking['time'].strftime('%I:%M %p'),
                    'booking_id': booking_id
                })
                
                # Create receipt message
                receipt = f"""
📋 **Appointment Confirmation**

✅ Your appointment has been booked and paid!

**Patient Details:**
- Name: {booking['name']}
- Phone: {booking['phone']}
{f"- Email: {booking['email']}" if booking.get('email') else ""}

**Appointment Details:**
- Doctor: {booking['doctor']}
- Date: {booking['date'].strftime('%B %d, %Y')}
- Time: {booking['time'].strftime('%I:%M %p')}

**Payment Details:**
- Consultation Fee: ₹{booking['consultation_fee']}
- Payment ID: {payment_id}
- Status: ✅ Paid

**Notifications Sent:**
- SMS: {'✅ Sent' if notification_results.get('sms') else '⚠️ Not configured'}
- Email: {'✅ Sent' if notification_results.get('email') else '⚠️ Not configured'}

**Next Steps:**
- You will receive a confirmation call/SMS shortly
- Please arrive 10 minutes early
- Bring any relevant medical reports

*Booking Reference: #{booking_id}*
                """
                
                # Add to chat history
                st.session_state.messages.append({"role": "assistant", "content": receipt})
                
                # Save to database
                save_message(curr_id, "assistant", receipt)
                
                # Clear the pending booking
                st.session_state.pending_booking = None
                
                # Show success message
                st.sidebar.success("✅ Payment successful!")
                
                # Rerun to show the receipt
                st.rerun()
                
        except Exception as e:
            st.sidebar.error(f"Payment service error: {e}")
            st.sidebar.info("Payment services not configured. See setup guide.")
    else:
        st.info("Start a chat to find doctors.")

    # --- DEBUG SECTION (Visible for diagnosis) ---
    with st.expander("🛠️ Debug State"):
        st.write("Severity:", st.session_state.get("current_severity"))
        st.write("City:", st.session_state.get("current_city"))
        st.write("Symptoms:", st.session_state.get("current_symptoms"))
        st.write("Ask City:", st.session_state.get("ask_for_city"))
        st.write("Booking:", st.session_state.get("booking_requested"))
