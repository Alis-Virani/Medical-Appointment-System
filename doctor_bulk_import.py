"""
Bulk Doctor Data Management
Allows importing doctors from CSV and managing doctor database
"""
import csv
import io
import pandas as pd
from doctor_management import add_doctor
from database import get_db_connection


def import_doctors_from_csv(csv_file_content: str) -> dict:
    """
    Import doctors from CSV content
    Expected CSV columns: name, specialty, city, availability, rating, fees, contact, clinic_address, qualifications, years_experience
    """
    try:
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_file_content))
        
        imported = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (after header)
            try:
                # Validate required fields
                required_fields = ['name', 'specialty', 'city']
                for field in required_fields:
                    if not row.get(field, '').strip():
                        errors.append(f"Row {row_num}: Missing required field '{field}'")
                        continue
                
                # Optional fields with defaults
                availability = row.get('availability', 'Mon-Sat 9am-5pm')
                rating = float(row.get('rating', 4.5))
                fees = int(row.get('fees', 500))
                contact = row.get('contact', '')
                clinic_address = row.get('clinic_address', '')
                qualifications = row.get('qualifications', '')
                years_experience = int(row.get('years_experience', 0))
                
                # Add doctor to database
                doctor_id = add_doctor(
                    name=row['name'].strip(),
                    specialty=row['specialty'].strip(),
                    city=row['city'].strip(),
                    availability=availability,
                    rating=min(5.0, max(1.0, rating)),  # Clamp 1-5
                    fees=max(100, fees),  # Min 100
                    contact=contact,
                    clinic_address=clinic_address,
                    qualifications=qualifications,
                    years_experience=years_experience,
                )
                imported += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return {
            "success": True,
            "imported": imported,
            "errors": errors,
            "total_errors": len(errors)
        }
        
    except Exception as e:
        return {
            "success": False,
            "imported": 0,
            "errors": [f"CSV parsing error: {str(e)}"],
            "total_errors": 1
        }


def export_doctors_to_csv() -> str:
    """Export all doctors to CSV format"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            id,
            name,
            specialty,
            city,
            availability,
            rating,
            fees,
            contact,
            clinic_address,
            qualifications,
            years_experience,
            created_at
        FROM doctors_v2
        WHERE deleted_at IS NULL
        ORDER BY city, specialty, name
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'id', 'name', 'specialty', 'city', 'availability', 'rating', 
            'fees', 'contact', 'clinic_address', 'qualifications', 
            'years_experience', 'created_at'
        ])
        
        # Write data
        for row in rows:
            writer.writerow(row)
        
        conn.close()
        return output.getvalue()
        
    except Exception as e:
        return f"Error exporting doctors: {str(e)}"


def get_doctors_by_city(city: str) -> list:
    """Get all doctors in a specific city"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            id, name, specialty, city, availability, rating, fees, contact,
            clinic_address, qualifications, years_experience
        FROM doctors_v2
        WHERE city = ? AND deleted_at IS NULL
        ORDER BY rating DESC, name
        """
        
        cursor.execute(query, (city,))
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'name': row[1],
            'specialty': row[2],
            'city': row[3],
            'availability': row[4],
            'rating': row[5],
            'fees': row[6],
            'contact': row[7],
            'clinic_address': row[8],
            'qualifications': row[9],
            'years_experience': row[10],
        } for row in rows]
        
    except Exception as e:
        print(f"Error fetching doctors: {e}")
        return []


def get_doctors_by_specialty(specialty: str) -> list:
    """Get all doctors with a specific specialty"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            id, name, specialty, city, availability, rating, fees, contact,
            clinic_address, qualifications, years_experience
        FROM doctors_v2
        WHERE specialty = ? AND deleted_at IS NULL
        ORDER BY rating DESC, city
        """
        
        cursor.execute(query, (specialty,))
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'name': row[1],
            'specialty': row[2],
            'city': row[3],
            'availability': row[4],
            'rating': row[5],
            'fees': row[6],
            'contact': row[7],
            'clinic_address': row[8],
            'qualifications': row[9],
            'years_experience': row[10],
        } for row in rows]
        
    except Exception as e:
        print(f"Error fetching doctors: {e}")
        return []


def get_doctor_statistics() -> dict:
    """Get statistics about doctors in the system"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total doctors
        cursor.execute("SELECT COUNT(*) FROM doctors_v2 WHERE deleted_at IS NULL")
        total = cursor.fetchone()[0]
        
        # By city
        cursor.execute("""
            SELECT city, COUNT(*) as count 
            FROM doctors_v2 
            WHERE deleted_at IS NULL 
            GROUP BY city 
            ORDER BY count DESC
        """)
        by_city = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By specialty
        cursor.execute("""
            SELECT specialty, COUNT(*) as count 
            FROM doctors_v2 
            WHERE deleted_at IS NULL 
            GROUP BY specialty 
            ORDER BY count DESC
        """)
        by_specialty = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Average rating
        cursor.execute("SELECT AVG(rating) FROM doctors_v2 WHERE deleted_at IS NULL")
        avg_rating = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_doctors": total,
            "by_city": by_city,
            "by_specialty": by_specialty,
            "average_rating": round(avg_rating, 2)
        }
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {}
