import streamlit as st
import os
import datetime
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from database import init_db, create_session, get_all_sessions, delete_session, load_messages, save_message
from tools import get_doctors_tool
from agent import get_agent_llm, basic_chat_llm

load_dotenv()
init_db()

st.set_page_config(page_title="MediCare AI", page_icon="🩺", layout="wide")

# CSS: Dark Mode Friendly + Hiding Arrows
st.markdown("""
<style>
    [data-testid="stPopover"] > div > button > div > div:nth-child(2) { display: none !important; }
    [data-testid="stPopover"] button svg { display: none !important; }
    .stChatInputContainer { border-radius: 20px; }
    div[data-testid="stExpander"] div[role="button"] p { font-size: 1.1rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- STATE MANAGEMENT ---
if "waiting_for_city" not in st.session_state:
    st.session_state.waiting_for_city = False
if "waiting_for_symptom" not in st.session_state:
    st.session_state.waiting_for_symptom = False
if "pending_specialty" not in st.session_state:
    st.session_state.pending_specialty = None
if "pending_city" not in st.session_state:
    st.session_state.pending_city = None
# FEATURE: Persistent Booking Data (Prevents disappearing UI)
if "doctor_data" not in st.session_state:
    st.session_state.doctor_data = None

# =========================================================
#  FEATURE 1: SMART SESSION LOGIC (Persist on Reload)
# =========================================================
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

current_id = st.session_state["active_session_id"]
if str(url_session_id) != str(current_id):
    st.query_params["session_id"] = str(current_id)

curr_id = st.session_state["active_session_id"]


# --- SIDEBAR ---
with st.sidebar:
    st.header("🗂️ Records")
    if st.button("➕ New Chat", use_container_width=True):
        new_id = create_session("New Chat")
        st.session_state["active_session_id"] = new_id
        if "messages" in st.session_state: del st.session_state["messages"]
        st.session_state.waiting_for_city = False
        st.session_state.waiting_for_symptom = False
        st.session_state.pending_specialty = None
        st.session_state.pending_city = None
        st.session_state.doctor_data = None
        st.query_params["session_id"] = str(new_id)
        st.rerun()
    
    st.divider()
    sessions = get_all_sessions()
    for session_id, title in sessions:
        c1, c2 = st.columns([0.85, 0.15])
        with c1:
            if st.button(f"📄 {title}", key=f"s_{session_id}"):
                st.session_state["active_session_id"] = session_id
                if "messages" in st.session_state: del st.session_state["messages"]
                st.session_state.waiting_for_city = False
                st.session_state.waiting_for_symptom = False
                st.session_state.pending_specialty = None
                st.session_state.pending_city = None
                st.session_state.doctor_data = None
                st.query_params["session_id"] = str(session_id)
                st.rerun()
        with c2:
            with st.popover("⋯"):
                if st.button("🗑️", key=f"d_{session_id}"):
                    delete_session(session_id)
                    if st.session_state["active_session_id"] == session_id:
                        del st.session_state["active_session_id"]
                        st.query_params.clear() 
                    st.rerun()

# --- LOAD MESSAGES ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    db_msgs = load_messages(curr_id)
    for role, content in db_msgs:
        if role == "user": st.session_state.messages.append(HumanMessage(content=content))
        elif role == "assistant": st.session_state.messages.append(AIMessage(content=content))

st.title("🩺 Agentic Medical Assistant")

for msg in st.session_state.messages:
    if isinstance(msg, AIMessage):
        with st.chat_message("assistant", avatar="🤖"):
            st.write(msg.content)
    elif isinstance(msg, HumanMessage):
        with st.chat_message("user", avatar="👤"):
            st.write(msg.content)

# =========================================================
#  FEATURE 2: PERSISTENT BOOKING UI
#  (This runs OUTSIDE the input loop so it never disappears!)
# =========================================================
if st.session_state.doctor_data:
    st.divider()
    st.info("📅 **Please select a date and time to confirm your booking:**")
    
    for doc in st.session_state.doctor_data:
        with st.expander(f"Book with {doc['name']} ({doc['specialty']})", expanded=True):
            st.caption(f"📍 {doc['city']} | 🕒 Usual hours: {doc['time']}")
            
            # DATE & TIME PICKER
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                # Unique key prevents conflicts
                d = st.date_input("Date", datetime.date.today(), key=f"date_{doc['name']}")
            with c2:
                t = st.selectbox("Time", ["10:00 AM", "11:00 AM", "01:00 PM", "04:00 PM", "06:00 PM"], key=f"time_{doc['name']}")
            with c3:
                st.write("") # Spacer
                st.write("") # Spacer
                if st.button("Confirm Booking", key=f"btn_{doc['name']}"):
                    # FEATURE 3: GOOGLE MAPS LINK GENERATION
                    maps_query = f"{doc['name']} {doc['specialty']} {doc['city']}".replace(" ", "+")
                    maps_link = f"https://www.google.com/maps/search/?api=1&query={maps_query}"
                    
                    confirm_text = f"✅ **Booking Confirmed!**\n\nAppointment with **{doc['name']}** on **{d}** at **{t}**.\n\n📍 **Navigate to Clinic:** [Click for Google Maps]({maps_link})"
                    
                    st.session_state.messages.append(AIMessage(content=confirm_text))
                    save_message(curr_id, "assistant", confirm_text)
                    
                    # Clear the Form so it disappears nicely after booking
                    st.session_state.doctor_data = None
                    st.rerun()

# --- CHAT INPUT HANDLING ---
if user_input := st.chat_input("Type here..."):
    
    st.session_state.messages.append(HumanMessage(content=user_input))
    save_message(curr_id, "user", user_input)
    with st.chat_message("user", avatar="👤"):
        st.write(user_input)

    try:
        # FEATURE 4: PASSIVE LISTENER (Silent Memory)
        lower_input = user_input.lower()
        if any(x in lower_input for x in ["fever", "cough", "headache", "pain", "cold", "flu"]):
            st.session_state.pending_specialty = "General Physician"

        # SCENARIO 1: WAITING FOR CITY
        if st.session_state.waiting_for_city:
            city_name = user_input
            specialty = st.session_state.pending_specialty
            
            with st.spinner(f"Searching {specialty} in {city_name}..."):
                found_doctors = get_doctors_tool(specialty, city_name)
                st.session_state.waiting_for_city = False
                st.session_state.pending_city = city_name
                
                if found_doctors:
                    # SAVE TO STATE (This keeps the form alive!)
                    st.session_state.doctor_data = found_doctors
                    
                    reply = f"Found {len(found_doctors)} {specialty}s in **{city_name}**. Please check the booking form below."
                    st.session_state.messages.append(AIMessage(content=reply))
                    save_message(curr_id, "assistant", reply)
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(reply)
                    st.rerun()
                else:
                    reply = f"No {specialty}s found in {city_name}."
                    st.session_state.messages.append(AIMessage(content=reply))
                    save_message(curr_id, "assistant", reply)
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(reply)

        # SCENARIO 2: WAITING FOR SYMPTOMS
        elif st.session_state.waiting_for_symptom:
            with st.spinner("Diagnosing..."):
                agent = get_agent_llm()
                hint_msg = SystemMessage(content="You are a medical triage expert. Map symptoms to the correct specialist. For common flu, fever, cough, or body pain, output 'General Physician'.")
                search_decision = agent.invoke([hint_msg, HumanMessage(content=user_input)])
                
                final_specialty = None
                if search_decision and search_decision.specialty:
                    final_specialty = search_decision.specialty
                
                # Safety Net
                if not final_specialty:
                    if st.session_state.pending_specialty:
                         final_specialty = st.session_state.pending_specialty

                if final_specialty:
                    st.session_state.pending_specialty = final_specialty
                    st.session_state.waiting_for_symptom = False
                    st.session_state.waiting_for_city = True
                    ask_city_msg = f"I suggest a **{final_specialty}**. Which city are you in?"
                    st.session_state.messages.append(AIMessage(content=ask_city_msg))
                    save_message(curr_id, "assistant", ask_city_msg)
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(ask_city_msg)
                else:
                    reply = "I didn't catch that. Could you describe your symptoms clearly?"
                    st.session_state.messages.append(AIMessage(content=reply))
                    save_message(curr_id, "assistant", reply)
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(reply)

        # SCENARIO 3: NEW REQUEST (Book Trigger)
        elif ("appoint" in user_input.lower() or "book" in user_input.lower()) and "yes" not in user_input.lower():
            
            # CASE A: WE KNOW EVERYTHING (Specialty + City)
            if st.session_state.pending_specialty and st.session_state.pending_city:
                city_name = st.session_state.pending_city
                specialty = st.session_state.pending_specialty
                
                with st.spinner(f"Retrieving {specialty}s in {city_name}..."):
                    found_doctors = get_doctors_tool(specialty, city_name)
                    if found_doctors:
                        st.session_state.doctor_data = found_doctors # Trigger UI
                        
                        reply = f"Here are the **{specialty}s** in **{city_name}**. Please select a slot below."
                        st.session_state.messages.append(AIMessage(content=reply))
                        save_message(curr_id, "assistant", reply)
                        with st.chat_message("assistant", avatar="🤖"):
                            st.write(reply)
                        st.rerun()

            # CASE B: WE KNOW SPECIALTY ONLY
            elif st.session_state.pending_specialty:
                 st.session_state.waiting_for_city = True
                 reply = f"Okay, for **{st.session_state.pending_specialty}**. Which city are you in?"
                 st.session_state.messages.append(AIMessage(content=reply))
                 save_message(curr_id, "assistant", reply)
                 with st.chat_message("assistant", avatar="🤖"):
                    st.write(reply)
            
            # CASE C: WE KNOW NOTHING
            else:
                st.session_state.waiting_for_symptom = True
                reply = "Sure. What symptoms are you facing?"
                st.session_state.messages.append(AIMessage(content=reply))
                save_message(curr_id, "assistant", reply)
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(reply)

        # SCENARIO 4: STANDARD CHAT (Agent)
        else:
            with st.spinner("Analyzing..."):
                agent = get_agent_llm()
                search_decision = agent.invoke(st.session_state.messages[-3:])
                
                if search_decision and search_decision.specialty and search_decision.city:
                    found_doctors = get_doctors_tool(search_decision.specialty, search_decision.city)
                    st.session_state.pending_specialty = search_decision.specialty
                    st.session_state.pending_city = search_decision.city
                    
                    reply = f"Searching **{search_decision.specialty}** in **{search_decision.city}**..."
                    st.session_state.messages.append(AIMessage(content=reply))
                    save_message(curr_id, "assistant", reply)
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(reply)
                    
                    if found_doctors:
                        st.session_state.doctor_data = found_doctors # Trigger UI
                        st.rerun()
                
                elif search_decision and search_decision.specialty and not search_decision.city:
                    st.session_state.pending_specialty = search_decision.specialty
                    st.session_state.waiting_for_city = True
                    ask_city_msg = f"Okay, **{search_decision.specialty}**. Which city?"
                    st.session_state.messages.append(AIMessage(content=ask_city_msg))
                    save_message(curr_id, "assistant", ask_city_msg)
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(ask_city_msg)

                else:
                    # Feature 4 (Passive Listener) also runs here
                    lower_input = user_input.lower()
                    if any(x in lower_input for x in ["fever", "cough", "headache", "pain", "cold", "flu"]):
                        st.session_state.pending_specialty = "General Physician"

                    llm = basic_chat_llm()
                    sys_msg = SystemMessage(content="You are a medical assistant. If the user mentions symptoms but does NOT ask to book, provide 3 brief home remedies (bullet points). If they explicitly ask to book, be extremely concise (under 15 words).")
                    resp = llm.invoke([sys_msg] + st.session_state.messages)
                    st.session_state.messages.append(AIMessage(content=resp.content))
                    save_message(curr_id, "assistant", resp.content)
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(resp.content)

    except Exception as e:
        if "429" in str(e):
            st.warning("High Traffic: The AI is busy. Please wait 10 seconds and try again.")
        else:
            st.error(f"An error occurred: {str(e)}")