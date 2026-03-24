"""
pages/doctor_admin.py — Admin panel for managing doctors and uploads
"""
import streamlit as st
import pandas as pd
import io
import sys
sys.path.insert(0, '.')
from doctor_bulk_import import (
    import_doctors_from_csv,
    export_doctors_to_csv,
    get_doctors_by_city,
    get_doctors_by_specialty,
    get_doctor_statistics,
)
from database import get_db_connection

st.set_page_config(page_title="Doctor Management", layout="wide")

# ── Access Control ───────────────────────────────────────────────────────────
# Check if user is authenticated and is admin
_user = st.session_state.get("current_user", {})
_user_role = _user.get("role", "patient")

if _user_role not in ["admin", "superadmin"]:
    st.error("🔒 Access Denied. Admin access required.")
    st.info("Please login as an administrator.")
    st.stop()

# ── Page Layout ───────────────────────────────────────────────────────────────
st.title("👨‍⚕️ Doctor Management Admin Panel")
st.markdown("---")

# Tabs for different management options
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", 
    "📤 Import Doctors", 
    "👥 View Doctors", 
    "📥 Export Data",
    "🔍 Search"
])

# ── TAB 1: Dashboard ──────────────────────────────────────────────────────────
with tab1:
    st.header("Dashboard Overview")
    
    # Get statistics
    stats = get_doctor_statistics()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Doctors", stats.get("total_doctors", 0))
    
    with col2:
        st.metric("Total Cities", len(stats.get("by_city", {})))
    
    with col3:
        st.metric("Total Specialties", len(stats.get("by_specialty", {})))
    
    with col4:
        st.metric("Avg Rating", f"{stats.get('average_rating', 0):.2f}/5.0")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Doctors by City")
        by_city = stats.get("by_city", {})
        if by_city:
            st.bar_chart(by_city)
        else:
            st.info("No data available")
    
    with col2:
        st.subheader("Doctors by Specialty (Top 10)")
        by_specialty = stats.get("by_specialty", {})
        if by_specialty:
            # Get top 10
            top_10 = dict(sorted(by_specialty.items(), key=lambda x: x[1], reverse=True)[:10])
            st.bar_chart(top_10)
        else:
            st.info("No data available")


# ── TAB 2: Import Doctors from CSV ────────────────────────────────────────────
with tab2:
    st.header("📤 Import Doctors from CSV")
    
    st.markdown("""
    ### Instructions:
    1. Download the template CSV below
    2. Fill in your doctor data
    3. Upload the file to add doctors to the system
    
    ### Required Columns:
    - `name` (Doctor's full name)
    - `specialty` (Medical specialty)
    - `city` (City where doctor practices)
    
    ### Optional Columns:
    - `availability` (e.g., "Mon-Fri 9am-5pm") - Default: "Mon-Sat 9am-5pm"
    - `rating` (1.0-5.0) - Default: 4.5
    - `fees` (consultation fee in rupees) - Default: 500
    - `contact` (phone number)
    - `clinic_address` (full address)
    - `qualifications` (e.g., "MBBS, MD (Medicine)")
    - `years_experience` (integer) - Default: 0
    """)
    
    # Download template
    st.markdown("---")
    st.subheader("📋 Download CSV Template")
    
    template_csv = """name,specialty,city,availability,rating,fees,contact,clinic_address,qualifications,years_experience
Dr. Example Name,General Physician,Ahmedabad,Mon-Fri 10am-6pm,4.5,500,+91-9876543210,Example Clinic Building,MBBS MD,5
Dr. Another Doctor,Cardiologist,Surat,Tue-Sat 2pm-8pm,4.8,800,+91-8765432109,Heart Care Center,MBBS DM Cardiology,12
"""
    
    st.download_button(
        label="📥 Download CSV Template",
        data=template_csv,
        file_name="doctors_template.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    st.subheader("📤 Upload Doctor Data")
    
    # File upload
    uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])
    
    if uploaded_file:
        try:
            # Read CSV content
            csv_content = uploaded_file.read().decode('utf-8')
            
            # Preview data
            df_preview = pd.read_csv(io.StringIO(csv_content))
            
            st.info(f"📊 Preview of {len(df_preview)} rows:")
            st.dataframe(df_preview, use_container_width=True)
            
            # Import button
            if st.button("✅ Import Doctors", key="import_btn"):
                with st.spinner("Importing doctors..."):
                    result = import_doctors_from_csv(csv_content)
                    
                    if result["success"]:
                        st.success(f"✅ Successfully imported {result['imported']} doctors!")
                        
                        if result["errors"]:
                            st.warning(f"⚠️ {len(result['errors'])} errors encountered:")
                            for error in result["errors"][:10]:  # Show first 10 errors
                                st.write(f"  • {error}")
                            if len(result["errors"]) > 10:
                                st.write(f"  ... and {len(result['errors']) - 10} more")
                    else:
                        st.error("❌ Import failed:")
                        for error in result["errors"]:
                            st.write(f"  • {error}")
        
        except Exception as e:
            st.error(f"Error reading file: {e}")


# ── TAB 3: View Doctors ───────────────────────────────────────────────────────
with tab3:
    st.header("👥 View All Doctors")
    
    # Get all doctors
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            id, name, specialty, city, availability, rating, fees, contact,
            clinic_address, qualifications, years_experience
        FROM doctors_v2
        WHERE deleted_at IS NULL
        ORDER BY city, specialty, name
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=[
                'ID', 'Name', 'Specialty', 'City', 'Availability', 
                'Rating', 'Fees', 'Contact', 'Clinic Address', 
                'Qualifications', 'Experience (Years)'
            ])
            
            st.metric("Total Doctors", len(df))
            
            # Display table
            st.dataframe(df, use_container_width=True, height=400)
            
            # Export to CSV
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv_data,
                file_name="doctors_export.csv",
                mime="text/csv"
            )
        else:
            st.info("No doctors found in the system.")
    
    except Exception as e:
        st.error(f"Error fetching doctors: {e}")


# ── TAB 4: Export Data ────────────────────────────────────────────────────────
with tab4:
    st.header("📥 Export Doctor Data")
    
    st.markdown("Download all doctor data in various formats:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export as CSV"):
            try:
                csv_data = export_doctors_to_csv()
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="all_doctors.csv",
                    mime="text/csv"
                )
                st.success("✅ CSV exported successfully!")
            except Exception as e:
                st.error(f"Error exporting: {e}")
    
    with col2:
        if st.button("📊 Export as Excel"):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM doctors_v2 WHERE deleted_at IS NULL
                    ORDER BY city, specialty, name
                """)
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                conn.close()
                
                df = pd.DataFrame(rows, columns=columns)
                
                # Create Excel file
                excel_buffer = io.BytesIO()
                df.to_excel(excel_buffer, sheet_name="Doctors", index=False)
                excel_buffer.seek(0)
                
                st.download_button(
                    label="Download Excel",
                    data=excel_buffer.getvalue(),
                    file_name="all_doctors.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.success("✅ Excel exported successfully!")
            except Exception as e:
                st.error(f"Error exporting: {e}")


# ── TAB 5: Search Doctors ─────────────────────────────────────────────────────
with tab5:
    st.header("🔍 Search Doctors")
    
    search_type = st.radio("Search by:", ["City", "Specialty"])
    
    if search_type == "City":
        # Get unique cities
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT city FROM doctors_v2 
                WHERE deleted_at IS NULL 
                ORDER BY city
            """)
            cities = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            selected_city = st.selectbox("Select City", cities)
            
            if selected_city:
                doctors = get_doctors_by_city(selected_city)
                
                if doctors:
                    st.success(f"✅ Found {len(doctors)} doctor(s) in {selected_city}")
                    
                    for doctor in doctors:
                        with st.expander(f"Dr. {doctor['name']} - {doctor['specialty']}"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"**Rating:** ⭐ {doctor['rating']}/5.0")
                                st.write(f"**Fees:** ₹{doctor['fees']}")
                                st.write(f"**Experience:** {doctor['years_experience']} years")
                            
                            with col2:
                                st.write(f"**Availability:** {doctor['availability']}")
                                st.write(f"**Contact:** {doctor['contact'] or 'N/A'}")
                            
                            with col3:
                                st.write(f"**Clinic:** {doctor['clinic_address'] or 'N/A'}")
                                st.write(f"**Qualifications:** {doctor['qualifications'] or 'N/A'}")
                else:
                    st.info(f"No doctors found in {selected_city}")
        
        except Exception as e:
            st.error(f"Error: {e}")
    
    else:  # Search by Specialty
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT specialty FROM doctors_v2 
                WHERE deleted_at IS NULL 
                ORDER BY specialty
            """)
            specialties = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            selected_specialty = st.selectbox("Select Specialty", specialties)
            
            if selected_specialty:
                doctors = get_doctors_by_specialty(selected_specialty)
                
                if doctors:
                    st.success(f"✅ Found {len(doctors)} {selected_specialty}(s)")
                    
                    for doctor in doctors:
                        with st.expander(f"Dr. {doctor['name']} - {doctor['city']}"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"**Rating:** ⭐ {doctor['rating']}/5.0")
                                st.write(f"**Fees:** ₹{doctor['fees']}")
                                st.write(f"**Experience:** {doctor['years_experience']} years")
                            
                            with col2:
                                st.write(f"**City:** {doctor['city']}")
                                st.write(f"**Availability:** {doctor['availability']}")
                                st.write(f"**Contact:** {doctor['contact'] or 'N/A'}")
                            
                            with col3:
                                st.write(f"**Clinic:** {doctor['clinic_address'] or 'N/A'}")
                                st.write(f"**Qualifications:** {doctor['qualifications'] or 'N/A'}")
                else:
                    st.info(f"No {selected_specialty}s found")
        
        except Exception as e:
            st.error(f"Error: {e}")
