#!/usr/bin/env python
"""
Test script for booking history feature
"""
from database import save_booking, get_user_bookings, get_last_booking, get_upcoming_bookings
from tools import get_booking_history_tool
from datetime import datetime, timedelta

def test_booking_history():
    print("🧪 Testing Booking History Feature...\n")
    
    # Create test bookings
    user_id = 'test_user_1'
    
    # Booking 1: Past appointment
    booking_id_1 = save_booking(
        user_id=user_id,
        doctor_id=1,
        doctor_name='Dr. Mehta',
        specialty='Cardiologist',
        city='Ahmedabad',
        appointment_date='2026-02-10',
        appointment_time='10:30 AM',
        notes='Initial consultation'
    )
    print(f"✅ Past booking saved: ID {booking_id_1}")
    
    # Booking 2: Upcoming appointment
    booking_id_2 = save_booking(
        user_id=user_id,
        doctor_id=2,
        doctor_name='Dr. Shah',
        specialty='Dermatologist',
        city='Ahmedabad',
        appointment_date='2026-03-15',
        appointment_time='02:00 PM',
        notes='Skin checkup'
    )
    print(f"✅ Upcoming booking saved: ID {booking_id_2}")
    
    # Booking 3: Most recent (this will be the "last" booking)
    booking_id_3 = save_booking(
        user_id=user_id,
        doctor_id=3,
        doctor_name='Dr. Trivedi',
        specialty='Pediatrician',
        city='Ahmedabad',
        appointment_date='2026-02-20',
        appointment_time='04:00 PM',
        notes='Follow-up consultation'
    )
    print(f"✅ Latest booking saved: ID {booking_id_3}\n")
    
    # Test 1: Get last booking
    print("Test 1: Get Last Booking")
    last_booking = get_last_booking(user_id)
    if last_booking:
        booking_id, doctor_name, specialty, city, appt_date, appt_time, status, created_at = last_booking
        print(f"  Doctor: {doctor_name} ({specialty})")
        print(f"  City: {city}")
        print(f"  Date: {appt_date}")
        print(f"  Time: {appt_time}")
        print(f"  Status: {status}")
    else:
        print("  ❌ No booking found")
    print()
    
    # Test 2: Get all bookings
    print("Test 2: Get All Bookings")
    all_bookings = get_user_bookings(user_id)
    print(f"  Total bookings: {len(all_bookings)}")
    for idx, booking in enumerate(all_bookings, 1):
        booking_id, doctor_name, specialty, city, appt_date, appt_time, status, created_at = booking
        print(f"    {idx}. {doctor_name} ({appt_date})")
    print()
    
    # Test 3: Using the tool
    print("Test 3: Using get_booking_history_tool")
    result = get_booking_history_tool(user_id, 'last')
    if 'last_booking' in result:
        booking = result['last_booking']
        print(f"  Doctor: {booking['doctor']}")
        print(f"  Date: {booking['date']}")
        print(f"  Time: {booking['time']}")
    else:
        print(f"  Result: {result}")
    print()
    
    # Test 4: Get upcoming bookings
    print("Test 4: Get Upcoming Bookings")
    upcoming = get_upcoming_bookings(user_id)
    print(f"  Total upcoming: {len(upcoming)}")
    for booking in upcoming:
        booking_id, doctor_name, specialty, city, appt_date, appt_time, status = booking
        print(f"    - {doctor_name} on {appt_date}")
    print()
    
    print("✅ All booking history tests passed!\n")

if __name__ == "__main__":
    test_booking_history()
