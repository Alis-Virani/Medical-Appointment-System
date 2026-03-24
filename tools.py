"""
tools.py - SINGLE SOURCE OF TRUTH FOR ALL TOOL FUNCTIONS
═══════════════════════════════════════════════════════════

This module consolidates ALL tool definitions used by:
- LangGraph Agent (lang_graph_agent.py)
- Chat Interface (pages/chat.py)
- API Endpoints

🔍 Organization:
  ├── Doctor Tools
  │   └── get_doctors_tool()         - Find doctors by specialty + city
  ├── Booking Tools  
  │   ├── get_booking_history_tool() - Retrieve appointment history
  │   └── save_appointment_tool()    - Create new appointment
  └── (Future: Medical tools, Payment tools, etc.)

NOTE: doctor_tools.py is DEPRECATED. All functions consolidated here.
Any new tool functions should be added to THIS FILE ONLY.

⚠️  Do NOT create separate tool files - maintain single source of truth!
"""

from database import find_doctors_in_db, get_user_bookings, get_last_booking, get_upcoming_bookings, get_past_bookings, save_booking

def get_doctors_tool(specialty: str, city: str):
    """
    Retrieves a list of doctors based on specialty and city.
    """
    # If the user didn't specify a city, default to "Jamnagar"
    if not city:
        city = "Jamnagar" 
        
    results = find_doctors_in_db(specialty, city)
    
    if not results:
        return None
    
    doctors_list = []
    for doc in results:
        doctors_list.append({
            "name": doc[0],
            "specialty": doc[1],
            "time": doc[2],
            "city": doc[3]
        })
    return doctors_list

def get_booking_history_tool(user_id: str, query_type: str = "last"):
    """
    Retrieves booking history for a user.
    
    Args:
        user_id: The user's ID
        query_type: "last" (last booking), "upcoming" (future appointments), "all" (all bookings), "past" (previous appointments)
    
    Returns:
        List of bookings or message if none found
    """
    if query_type == "last":
        booking = get_last_booking(user_id)
        if booking:
            booking_id, doctor_name, specialty, city, appt_date, appt_time, status, created_at = booking
            return {
                "last_booking": {
                    "doctor": doctor_name,
                    "specialty": specialty,
                    "city": city,
                    "date": appt_date,
                    "time": appt_time,
                    "status": status
                }
            }
        return {"message": "No booking history found"}
    
    elif query_type == "upcoming":
        bookings = get_upcoming_bookings(user_id)
        if bookings:
            upcoming_list = []
            for booking in bookings:
                booking_id, doctor_name, specialty, city, appt_date, appt_time, status = booking
                upcoming_list.append({
                    "doctor": doctor_name,
                    "specialty": specialty,
                    "city": city,
                    "date": appt_date,
                    "time": appt_time,
                    "status": status
                })
            return {"upcoming_appointments": upcoming_list}
        return {"message": "No upcoming appointments"}
    
    elif query_type == "past":
        bookings = get_past_bookings(user_id)
        if bookings:
            past_list = []
            for booking in bookings:
                booking_id, doctor_name, specialty, city, appt_date, appt_time, status, created_at = booking
                past_list.append({
                    "doctor": doctor_name,
                    "specialty": specialty,
                    "city": city,
                    "date": appt_date,
                    "time": appt_time,
                    "status": status
                })
            return {"past_appointments": past_list}
        return {"message": "No past appointments"}
    
    else:  # "all"
        bookings = get_user_bookings(user_id)
        if bookings:
            all_bookings = []
            for booking in bookings:
                booking_id, doctor_name, specialty, city, appt_date, appt_time, status, created_at = booking
                all_bookings.append({
                    "doctor": doctor_name,
                    "specialty": specialty,
                    "city": city,
                    "date": appt_date,
                    "time": appt_time,
                    "status": status
                })
            return {"all_bookings": all_bookings}
        return {"message": "No bookings found"}

def save_appointment_tool(user_id: str, doctor_name: str, specialty: str, city: str, appointment_date: str, appointment_time: str, notes: str = ""):
    """
    Save a new appointment booking to the database.
    
    Args:
        user_id: The user's ID
        doctor_name: Name of the doctor
        specialty: Doctor's specialty
        city: City where appointment is
        appointment_date: Date in format YYYY-MM-DD
        appointment_time: Time in format HH:MM
        notes: Optional notes for the appointment
    
    Returns:
        Booking confirmation with ID
    """
    try:
        booking_id = save_booking(user_id, None, doctor_name, specialty, city, appointment_date, appointment_time, notes)
        return {
            "status": "success",
            "booking_id": booking_id,
            "message": f"✅ Appointment booked successfully with {doctor_name} on {appointment_date}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save booking: {str(e)}"
        }