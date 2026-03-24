"""
Admin page for managing doctors - Add, Edit, Delete, Import CSV
"""
import streamlit as st
import pandas as pd
import sys
sys.path.insert(0, '.')
from database import (
    create_connection, get_all_doctors, save_doctor,
    delete_doctor, update_doctor_info
)
from datetime import datetime
import io

st.set_page_config(page_title="Admin - Doctor Management", layout="wide")

# Check admin access (simple check - in production use proper auth)
if "current_user" not in st.session_state or st.session_state.get("current_user", {}).get("role") != "admin":
    st.error("❌ Admin access required")
    st.stop()

st.title("👨‍⚕️ Doctor Management System")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 View All", "➕ Add Doctor", "📥 Bulk Import", "⚙️ Edit/Delete"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: View All Doctors
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("All Doctors in System")
    
    try:
        doctors = get_all_doctors()
        if doctors:
            df = pd.DataFrame(doctors)
            # Format columns for display
            display_df = df[['id', 'name', 'specialty', 'city', 'years_experience', 'rating', 'fees']].copy()
            display_df.columns = ['ID', 'Name', 'Specialty', 'City', 'Experience (yrs)', 'Rating ⭐', 'Fee (₹)']
            
            st.dataframe(display_df, use_container_width=True)
            st.info(f"📊 Total doctors: {len(doctors)}")
            
            # Export to CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name=f"doctors_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ No doctors found in database")
    except Exception as e:
        st.error(f"Error loading doctors: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: Add Single Doctor
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Add New Doctor")
    
    with st.form("add_doctor_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            doctor_name = st.text_input("Doctor Name *", placeholder="Dr. John Doe")
            specialty = st.selectbox("Specialty *", [
                "General Physician",
                "Cardiologist",
                "Orthopedic",
                "Pediatrician",
                "Dermatologist",
                "Gynecologist",
                "ENT",
                "Psychiatrist",
                "Neurologist",
                "Urologist",
                "Ophthalmologist",
                "Other"
            ])
            experience = st.number_input("Experience (years)", min_value=0, max_value=60, value=5)
        
        with col2:
            city = st.selectbox("City *", [
                "Ahmedabad",
                "Surat",
                "Vadodara",
                "Rajkot",
                "Jamnagar",
                "Bhavnagar",
                "Mumbai",
                "Delhi",
                "Bangalore",
                "Other"
            ])
            contact = st.text_input("Phone Number", placeholder="+91 98765 43210")
            clinic_address = st.text_area("Clinic Address", placeholder="Address line 1, Address line 2")
        
        col3, col4 = st.columns(2)
        with col3:
            rating = st.slider("Rating", 1.0, 5.0, 4.5, 0.1)
            fee = st.number_input("Consultation Fee (₹)", min_value=100, value=500, step=50)
        
        with col4:
            qualifications = st.text_area("Qualifications", placeholder="MBBS, MD, etc.")
            availability = st.text_input("Availability (e.g., Mon-Fri 10am-5pm)", placeholder="Mon-Fri 10am-5pm")
        
        submit = st.form_submit_button("✅ Add Doctor", use_container_width=True)
        
        if submit:
            if not doctor_name or not specialty or not city:
                st.error("❌ Name, Specialty, and City are required!")
            else:
                try:
                    conn = create_connection()
                    cursor = conn.cursor()
                    
                    # Generate unique doctor_id
                    import uuid
                    doctor_id = f"dr_{uuid.uuid4().hex[:8]}"
                    
                    cursor.execute("""
                        INSERT INTO doctors_v2 
                        (doctor_id, name, specialty, city, years_experience, contact, rating, fees, 
                         clinic_address, qualifications, availability, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        doctor_id, doctor_name, specialty, city, experience, contact, 
                        rating, fee, clinic_address, qualifications, availability,
                        1, datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ Doctor '{doctor_name}' added successfully!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error adding doctor: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: Bulk Import CSV
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Bulk Import Doctors from CSV")
    
    # Show template
    with st.expander("📋 View CSV Template"):
        template_data = {
            "name": ["Dr. John Doe", "Dr. Jane Smith"],
            "specialty": ["Cardiologist", "Dermatologist"],
            "city": ["Ahmedabad", "Surat"],
            "years_experience": [10, 8],
            "contact": ["+91 9876543210", "+91 9765432109"],
            "rating": [4.8, 4.6],
            "fees": [600, 400],
            "clinic_address": ["Clinic Address 1", "Clinic Address 2"],
            "qualifications": ["MBBS, MD", "MBBS"],
            "availability": ["Mon-Fri 10am-5pm", "Tue-Sat 2pm-8pm"]
        }
        template_df = pd.DataFrame(template_data)
        st.write(template_df)
        
        # Download template
        csv_template = template_df.to_csv(index=False)
        st.download_button(
            label="Download CSV Template",
            data=csv_template,
            file_name="doctors_template.csv",
            mime="text/csv"
        )
    
    # Upload CSV
    uploaded_file = st.file_uploader("Upload CSV file", type="csv")
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Validate columns
            required_cols = ["name", "specialty", "city", "years_experience", "rating", "fees"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
            else:
                st.info(f"📊 Preview ({len(df)} doctors):")
                st.dataframe(df, use_container_width=True)
                
                if st.button("✅ Import All Doctors", use_container_width=True):
                    try:
                        conn = create_connection()
                        cursor = conn.cursor()
                        
                        success_count = 0
                        error_count = 0
                        
                        for _, row in df.iterrows():
                            try:
                                import uuid
                                doctor_id = f"dr_{uuid.uuid4().hex[:8]}"
                                
                                # Fill missing optional fields
                                contact = row.get("contact", row.get("phone", ""))
                                clinic_address = row.get("clinic_address", "")
                                qualifications = row.get("qualifications", "")
                                availability = row.get("availability", "")
                                
                                cursor.execute("""
                                    INSERT INTO doctors_v2 
                                    (doctor_id, name, specialty, city, years_experience, contact, 
                                     rating, fees, clinic_address, qualifications, availability,
                                     is_active, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    doctor_id, row["name"], row["specialty"], row["city"], 
                                    int(row["years_experience"]), contact,
                                    float(row["rating"]), float(row["fees"]),
                                    clinic_address, qualifications, availability,
                                    1, datetime.now().isoformat()
                                ))
                                success_count += 1
                            except Exception as row_error:
                                error_count += 1
                                st.warning(f"⚠️ Error importing {row.get('name', 'Unknown')}: {row_error}")
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ Imported {success_count} doctors")
                        if error_count > 0:
                            st.warning(f"⚠️ {error_count} rows had errors")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Import failed: {e}")
        except Exception as e:
            st.error(f"❌ Error reading CSV: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: Edit/Delete Doctors
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Edit or Delete Doctors")
    
    try:
        doctors = get_all_doctors()
        if doctors:
            # Select doctor to edit
            doctor_options = {f"{doc['name']} ({doc['city']})" : doc['id'] for doc in doctors}
            selected_doctor_name = st.selectbox("Select Doctor", list(doctor_options.keys()))
            selected_doctor_id = doctor_options[selected_doctor_name]
            
            # Find the selected doctor's data
            selected_doctor = next((d for d in doctors if d['id'] == selected_doctor_id), None)
            
            if selected_doctor:
                st.write("**Current Details:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Specialty", selected_doctor['specialty'])
                with col2:
                    st.metric("City", selected_doctor['city'])
                with col3:
                    st.metric("Rating", f"{selected_doctor['rating']}⭐")
                
                # Edit form
                st.write("**Update Details:**")
                with st.form(f"edit_doctor_{selected_doctor_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_rating = st.slider("Rating", 1.0, 5.0, float(selected_doctor['rating']), 0.1)
                        new_fees = st.number_input("Fee (₹)", value=int(selected_doctor['fees']), step=50)
                    
                    with col2:
                        new_experience = st.number_input("Experience (years)", value=int(selected_doctor.get('years_experience', 0)), min_value=0)
                        new_contact = st.text_input("Phone", value=selected_doctor.get('contact', ''))
                    
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        submit_edit = st.form_submit_button("✅ Update", use_container_width=True)
                    
                    with col4:
                        submit_delete = st.form_submit_button("🗑️ Delete", use_container_width=True)
                    
                    if submit_edit:
                        try:
                            conn = create_connection()
                            cursor = conn.cursor()
                            
                            cursor.execute("""
                                UPDATE doctors_v2 
                                SET rating = ?, fees = ?, years_experience = ?, contact = ?, updated_at = ?
                                WHERE id = ?
                            """, (new_rating, new_fees, new_experience, new_contact, datetime.now().isoformat(), selected_doctor_id))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success("✅ Doctor updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error updating: {e}")
                    
                    if submit_delete:
                        try:
                            conn = create_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM doctors_v2 WHERE id = ?", (selected_doctor_id,))
                            conn.commit()
                            conn.close()
                            
                            st.success(f"✅ Doctor deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting: {e}")
        else:
            st.warning("⚠️ No doctors to edit")
    except Exception as e:
        st.error(f"❌ Error: {e}")
