"""
Doctor API Client - Fetches real-time doctor data from external sources
Includes mock API for testing and fallback mechanism
"""

import os
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class DoctorAPIClient:
    """Client for fetching doctor data from external healthcare APIs"""
    
    def __init__(self):
        self.enabled = os.getenv("DOCTOR_API_ENABLED", "true").lower() == "true"
        self.base_url = os.getenv("DOCTOR_API_BASE_URL", "mock")
        self.api_key = os.getenv("DOCTOR_API_KEY", "")
        self.cache = {}
        self.cache_ttl = int(os.getenv("DOCTOR_API_CACHE_TTL", "3600"))
        
    def search_doctors(self, specialty: str, city: str, limit: int = 10) -> List[Dict]:
        """
        Search for doctors by specialty and city
        
        Args:
            specialty: Medical specialty (e.g., "Cardiologist", "Neurologist")
            city: City name (e.g., "Mumbai", "Delhi")
            limit: Maximum number of results
            
        Returns:
            List of doctor dictionaries with profile information
        """
        if not self.enabled:
            return []
            
        # Check cache
        cache_key = f"{specialty}_{city}_{limit}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                print(f"✅ Using cached data for {specialty} in {city}")
                return cached_data
        
        # Fetch from API (mock for now)
        try:
            doctors = self._fetch_mock_doctors(specialty, city, limit)
            
            # Cache results
            self.cache[cache_key] = (doctors, datetime.now())
            
            print(f"✅ Fetched {len(doctors)} doctors from API for {specialty} in {city}")
            return doctors
            
        except Exception as e:
            print(f"⚠️ API Error: {e}")
            return []
    
    def _fetch_mock_doctors(self, specialty: str, city: str, limit: int) -> List[Dict]:
        """
        Mock API that generates realistic doctor data
        In production, replace this with actual API calls
        """
        
        # Realistic Indian doctor names
        first_names = [
            "Rajesh", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Arjun", "Kavya",
            "Rahul", "Deepika", "Sanjay", "Meera", "Karthik", "Pooja", "Aditya", "Nisha",
            "Rohan", "Divya", "Suresh", "Lakshmi", "Varun", "Shreya", "Nikhil", "Riya"
        ]
        
        last_names = [
            "Sharma", "Patel", "Kumar", "Singh", "Reddy", "Nair", "Iyer", "Gupta",
            "Mehta", "Joshi", "Rao", "Desai", "Agarwal", "Verma", "Shah", "Malhotra"
        ]
        
        # Medical qualifications
        qualifications = [
            "MBBS, MD", "MBBS, MS", "MBBS, DNB", "MBBS, MD, DM",
            "MBBS, MS, MCh", "MBBS, MD, MRCP", "MBBS, MS, FRCS"
        ]
        
        # Hospitals/Clinics by city
        hospitals = {
            "Mumbai": ["Lilavati Hospital", "Breach Candy Hospital", "Kokilaben Hospital", "Nanavati Hospital"],
            "Delhi": ["AIIMS Delhi", "Max Hospital", "Fortis Hospital", "Apollo Hospital"],
            "Bangalore": ["Manipal Hospital", "Apollo Hospital", "Fortis Hospital", "Columbia Asia"],
            "Chennai": ["Apollo Hospital", "MIOT Hospital", "Fortis Malar", "Kauvery Hospital"],
            "Pune": ["Ruby Hall Clinic", "Sahyadri Hospital", "Jupiter Hospital", "Deenanath Mangeshkar"],
            "Hyderabad": ["Apollo Hospital", "KIMS Hospital", "Yashoda Hospital", "Care Hospital"],
            "Ahmedabad": ["Sterling Hospital", "Apollo Hospital", "Shalby Hospital", "Civil Hospital"],
            "Jamnagar": ["GG Hospital", "Shreeji Hospital", "Ayushman Hospital", "City Hospital"],
            "Kolkata": ["AMRI Hospital", "Apollo Gleneagles", "Fortis Hospital", "Medica Superspecialty"],
            "Surat": ["KIMS Hospital", "Mahavir Hospital", "New Civil Hospital", "Sunshine Hospital"]
        }
        
        # Get hospitals for city or use generic
        city_hospitals = hospitals.get(city, ["City Hospital", "General Hospital", "Medical Center"])
        
        doctors = []
        for i in range(min(limit, 15)):
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            # Generate realistic data
            experience = random.randint(5, 30)
            rating = round(random.uniform(3.8, 4.9), 1)
            reviews = random.randint(50, 500)
            consultation_fee = random.choice([500, 600, 700, 800, 1000, 1200, 1500])
            
            # Availability (some doctors available today, some tomorrow)
            available_today = random.choice([True, False])
            next_slot = datetime.now() + timedelta(hours=random.randint(2, 48))
            
            doctor = {
                "doctor_id": f"DOC_{city[:3].upper()}_{i+1:03d}",
                "doctor_name": name,
                "specialist": specialty,
                "qualification": random.choice(qualifications),
                "experience_years": experience,
                "hospital": random.choice(city_hospitals),
                "city": city,
                "doctor_rating": rating,
                "total_reviews": reviews,
                "consultation_fee": consultation_fee,
                "available_today": available_today,
                "next_available_slot": next_slot.strftime("%Y-%m-%d %I:%M %p"),
                "languages": random.sample(["English", "Hindi", "Gujarati", "Marathi", "Tamil", "Telugu"], k=random.randint(2, 3)),
                "phone": f"+91 {random.randint(70000, 99999)}{random.randint(10000, 99999)}",
                "match_confidence": round(random.uniform(0.75, 0.98), 2)
            }
            
            doctors.append(doctor)
        
        # Sort by rating and availability
        doctors.sort(key=lambda x: (x["available_today"], x["doctor_rating"]), reverse=True)
        
        return doctors
    
    def get_doctor_details(self, doctor_id: str) -> Optional[Dict]:
        """Get detailed information about a specific doctor"""
        # In production, this would fetch from API
        # For now, return None (not implemented)
        return None
    
    def check_availability(self, doctor_id: str, date: str) -> List[str]:
        """
        Check available appointment slots for a doctor on a specific date
        
        Returns:
            List of available time slots (e.g., ["10:00 AM", "2:30 PM"])
        """
        # Mock availability
        slots = [
            "09:00 AM", "10:00 AM", "11:00 AM", 
            "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"
        ]
        
        # Randomly return some available slots
        available = random.sample(slots, k=random.randint(2, 5))
        available.sort()
        
        return available


# Singleton instance
_api_client = None

def get_api_client() -> DoctorAPIClient:
    """Get singleton instance of API client"""
    global _api_client
    if _api_client is None:
        _api_client = DoctorAPIClient()
    return _api_client
