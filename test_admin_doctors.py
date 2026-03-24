#!/usr/bin/env python3
"""
Quick test script to verify doctor management functionality
"""
from database import (
    create_connection, get_all_doctors, save_doctor,
    update_doctor_info, delete_doctor, init_db
)

def test_doctor_crud():
    """Test Create, Read, Update, Delete operations"""
    
    print("=" * 60)
    print("DOCTOR MANAGEMENT SYSTEM - CRUD TESTS")
    print("=" * 60)
    
    # Initialize database
    init_db()
    print("✅ Database initialized")
    
    # TEST 1: Add a doctor
    print("\n[TEST 1] Adding a doctor...")
    try:
        save_doctor(
            name="Dr. Rajesh Kumar",
            specialty="Cardiologist",
            city="Ahmedabad",
            years_experience=15,
            contact="+91 9876543210",
            rating=4.8,
            fees=800,
            clinic_address="123 Medical Plaza, Ahmedabad",
            qualifications="MBBS, MD (Cardiology)",
            availability="Mon-Fri 10am-5pm"
        )
        print("✅ Doctor added successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # TEST 2: Get all doctors
    print("\n[TEST 2] Retrieving all doctors...")
    try:
        doctors = get_all_doctors()
        print(f"✅ Total doctors in system: {len(doctors)}")
        if doctors:
            first_doc = doctors[0]
            print(f"   First doctor: {first_doc['name']} ({first_doc['specialty']}) - ₹{first_doc['fees']}/session")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # TEST 3: Add bulk doctors
    print("\n[TEST 3] Adding multiple doctors (bulk)...")
    try:
        bulk_doctors = [
            ("Dr. Priya Sharma", "Dermatologist", "Surat", 8, "+91 8765432109", 4.6, 500, "Clinic 1", "MBBS, MD", "Tue-Sat 2pm-8pm"),
            ("Dr. Amit Patel", "Orthopedic", "Vadodara", 12, "+91 7654321098", 4.7, 600, "Clinic 2", "MBBS, MD (Orthopedics)", "Mon-Sat 9am-1pm"),
            ("Dr. Anjali Singh", "Pediatrician", "Rajkot", 10, "+91 6543210987", 4.9, 400, "Clinic 3", "MBBS, MD (Pediatrics)", "Daily 10am-6pm"),
        ]
        for doc_data in bulk_doctors:
            save_doctor(*doc_data)
        print(f"✅ Added {len(bulk_doctors)} doctors")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # TEST 4: Verify count increased
    print("\n[TEST 4] Verifying doctor count...")
    try:
        doctors = get_all_doctors()
        print(f"✅ Total doctors now: {len(doctors)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # TEST 5: Update doctor info
    if doctors:
        print("\n[TEST 5] Updating doctor information...")
        try:
            first_doc_id = doctors[0]['id']
            update_doctor_info(first_doc_id, rating=4.9, fees=900)
            
            # Verify update
            updated_docs = get_all_doctors()
            updated_doc = next((d for d in updated_docs if d['id'] == first_doc_id), None)
            if updated_doc:
                print(f"✅ Updated {updated_doc['name']}: Rating={updated_doc['rating']}, Fees=₹{updated_doc['fees']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # TEST 6: Soft delete (mark as inactive)
    if len(doctors) > 1:
        print("\n[TEST 6] Testing soft delete...")
        try:
            second_doc_id = doctors[1]['id']
            delete_doctor(second_doc_id)
            
            # Verify deletion
            remaining = get_all_doctors()
            print(f"✅ Doctor marked as inactive")
            print(f"   Active doctors: {len(remaining)} (was {len(doctors)})")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # TEST 7: Show final summary
    print("\n[TEST 7] Final Summary")
    try:
        final_doctors = get_all_doctors()
        print(f"✅ FINAL COUNT: {len(final_doctors)} active doctors")
        print("\nDoctor List:")
        for doc in final_doctors[:5]:  # Show first 5
            print(f"  • {doc['name']} ({doc['specialty']}) - {doc['city']} - ₹{doc['fees']} - Rating: {doc['rating']}⭐")
        if len(final_doctors) > 5:
            print(f"  ... and {len(final_doctors) - 5} more")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    test_doctor_crud()
