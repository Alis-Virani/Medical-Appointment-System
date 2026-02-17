"""
Knowledge Graph Initialization Script
======================================
Populates Neo4j with medical relationships for intelligent reasoning
Run once to set up the knowledge graph
"""

from knowledge_graph import get_knowledge_graph
from doctor_management import add_doctor, init_database

def initialize_medical_knowledge():
    """Initialize medical knowledge graph with relationships"""
    kg = get_knowledge_graph()
    
    print("\n" + "="*80)
    print("🏥 INITIALIZING MEDICAL KNOWLEDGE GRAPH")
    print("="*80 + "\n")
    
    # ========== SYMPTOMS ==========
    print("📝 Adding symptoms...")
    symptoms = [
        ("fever", "high", "High body temperature"),
        ("cough", "high", "Persistent coughing"),
        ("chest pain", "critical", "Pain in the chest area"),
        ("headache", "medium", "Head pain"),
        ("rash", "medium", "Skin eruption"),
        ("abdominal pain", "high", "Stomach or belly pain"),
        ("shortness of breath", "critical", "Difficulty breathing"),
        ("chills", "medium", "Shivering sensation"),
        ("joint pain", "medium", "Pain in joints"),
        ("sore throat", "low", "Throat irritation"),
    ]
    
    for symptom_name, severity, description in symptoms:
        kg.add_symptom(symptom_name, severity, description)
    
    print(f"✅ Added {len(symptoms)} symptoms\n")
    
    # ========== DISEASES ==========
    print("🦠 Adding diseases...")
    diseases = [
        ("Malaria", "high", "Parasitic infection transmitted by mosquitoes"),
        ("Typhoid", "high", "Bacterial infection from contaminated water"),
        ("Pneumonia", "high", "Lung infection causing inflammation"),
        ("Tuberculosis", "high", "Serious respiratory infection"),
        ("Heart Attack", "critical", "Acute myocardial infarction"),
        ("Angina", "high", "Chest pain from reduced heart blood flow"),
        ("Common Cold", "low", "Viral upper respiratory infection"),
        ("Flu", "medium", "Influenza viral infection"),
        ("Appendicitis", "high", "Inflammation of the appendix"),
        ("Gastritis", "medium", "Stomach inflammation"),
        ("Asthma", "high", "Chronic respiratory disease"),
        ("Dermatitis", "low", "Skin inflammation"),
        ("Migraine", "medium", "Severe headache disorder"),
        ("Arthritis", "medium", "Joint inflammation"),
        ("Strep Throat", "medium", "Bacterial throat infection"),
    ]
    
    for disease_name, severity, description in diseases:
        kg.add_disease(disease_name, severity, description)
    
    print(f"✅ Added {len(diseases)} diseases\n")
    
    # ========== SPECIALISTS ==========
    print("👨‍⚕️ Adding medical specialists...")
    specialists = [
        ("General Physician", "Primary care doctor"),
        ("Cardiologist", "Heart and cardiovascular specialist"),
        ("Pulmonologist", "Lung and respiratory specialist"),
        ("Gastroenterologist", "Digestive system specialist"),
        ("Dermatologist", "Skin specialist"),
        ("Neurologist", "Nervous system specialist"),
        ("Orthopedic Surgeon", "Bone and joint specialist"),
        ("Infectious Disease Specialist", "Infection and disease specialist"),
        ("Emergency Medicine Specialist", "Critical care specialist"),
        ("Rheumatologist", "Autoimmune and joint specialist"),
        ("ENT Specialist", "Ear, Nose, Throat specialist"),
    ]
    
    for specialist_type, description in specialists:
        kg.add_specialist(specialist_type, description)
    
    print(f"✅ Added {len(specialists)} specialists\n")
    
    # ========== SYMPTOM → DISEASE RELATIONSHIPS ==========
    print("🔗 Creating Symptom → Disease relationships...")
    symptom_disease_relations = [
        # Fever relationships
        ("fever", "Malaria", 0.9),
        ("fever", "Typhoid", 0.8),
        ("fever", "Flu", 0.85),
        ("fever", "Pneumonia", 0.75),
        ("chills", "Malaria", 0.85),
        ("chills", "Typhoid", 0.8),
        
        # Cough relationships
        ("cough", "Pneumonia", 0.9),
        ("cough", "Tuberculosis", 0.8),
        ("cough", "Common Cold", 0.7),
        ("cough", "Asthma", 0.75),
        ("cough", "Flu", 0.7),
        
        # Chest pain relationships
        ("chest pain", "Heart Attack", 0.95),
        ("chest pain", "Angina", 0.85),
        ("chest pain", "Pneumonia", 0.6),
        ("chest pain", "Asthma", 0.5),
        
        # Abdominal pain relationships
        ("abdominal pain", "Appendicitis", 0.9),
        ("abdominal pain", "Gastritis", 0.75),
        
        # Other relationships
        ("headache", "Migraine", 0.8),
        ("headache", "Flu", 0.6),
        ("rash", "Dermatitis", 0.85),
        ("joint pain", "Arthritis", 0.8),
        ("sore throat", "Strep Throat", 0.8),
        ("sore throat", "Common Cold", 0.6),
        ("shortness of breath", "Asthma", 0.9),
        ("shortness of breath", "Heart Attack", 0.7),
    ]
    
    for symptom, disease, confidence in symptom_disease_relations:
        kg.add_relationship("Symptom", symptom, "CAUSES", "Disease", disease, confidence)
    
    print(f"✅ Added {len(symptom_disease_relations)} symptom-disease relationships\n")
    
    # ========== DISEASE → SPECIALIST RELATIONSHIPS ==========
    print("🔗 Creating Disease → Specialist relationships...")
    disease_specialist_relations = [
        # Malaria/Typhoid
        ("Malaria", "Infectious Disease Specialist", 0.95),
        ("Malaria", "General Physician", 0.8),
        ("Typhoid", "Infectious Disease Specialist", 0.95),
        ("Typhoid", "General Physician", 0.8),
        
        # Respiratory
        ("Pneumonia", "Pulmonologist", 0.95),
        ("Pneumonia", "General Physician", 0.7),
        ("Tuberculosis", "Pulmonologist", 0.98),
        ("Asthma", "Pulmonologist", 0.95),
        ("Common Cold", "General Physician", 0.8),
        ("Flu", "General Physician", 0.85),
        
        # Cardiac
        ("Heart Attack", "Cardiologist", 0.98),
        ("Heart Attack", "Emergency Medicine Specialist", 0.95),
        ("Angina", "Cardiologist", 0.95),
        
        # Gastrointestinal
        ("Appendicitis", "General Surgeon", 0.95),
        ("Appendicitis", "Gastroenterologist", 0.85),
        ("Gastritis", "Gastroenterologist", 0.9),
        ("Gastritis", "General Physician", 0.75),
        
        # Dermatological
        ("Dermatitis", "Dermatologist", 0.95),
        
        # Neurological
        ("Migraine", "Neurologist", 0.9),
        ("Migraine", "General Physician", 0.6),
        
        # Rheumatological
        ("Arthritis", "Rheumatologist", 0.95),
        ("Arthritis", "Orthopedic Surgeon", 0.85),
        
        # Throat
        ("Strep Throat", "ENT Specialist", 0.9),
        ("Strep Throat", "General Physician", 0.75),
    ]
    
    for disease, specialist, confidence in disease_specialist_relations:
        kg.add_relationship("Disease", disease, "TREATED_BY", "Specialist", specialist, confidence)
    
    print(f"✅ Added {len(disease_specialist_relations)} disease-specialist relationships\n")
    
    print("="*80)
    print("✅ KNOWLEDGE GRAPH INITIALIZATION COMPLETE!")
    print("="*80 + "\n")


def populate_sample_doctors():
    """Populate database with sample doctors"""
    print("="*80)
    print("👨‍⚕️ POPULATING SAMPLE DOCTORS")
    print("="*80 + "\n")
    
    sample_doctors = [
        # Ahmedabad
        {
            "name": "Dr. Rajesh Mehta",
            "specialty": "Cardiologist",
            "city": "Ahmedabad",
            "availability": "Mon-Fri 11am-5pm",
            "rating": 4.8,
            "fees": 800,
            "contact": "+91-9876543210",
            "clinic_address": "Heart Care Center, C.G. Road, Ahmedabad",
            "qualifications": "MBBS, MD (Cardiology), FESC",
            "years_experience": 15,
        },
        {
            "name": "Dr. Priya Shah",
            "specialty": "General Physician",
            "city": "Ahmedabad",
            "availability": "Daily 10am-6pm",
            "rating": 4.6,
            "fees": 500,
            "contact": "+91-8765432109",
            "clinic_address": "Health Plus Clinic, Satellite, Ahmedabad",
            "qualifications": "MBBS, MD (General Medicine)",
            "years_experience": 10,
        },
        {
            "name": "Dr. Anil Trivedi",
            "specialty": "Infectious Disease Specialist",
            "city": "Ahmedabad",
            "availability": "Mon-Sat 9am-5pm",
            "rating": 4.7,
            "fees": 700,
            "contact": "+91-7654321098",
            "clinic_address": "Apollo Hospital, Ahmedabad",
            "qualifications": "MBBS, MD (Microbiology), FICP",
            "years_experience": 12,
        },
        {
            "name": "Dr. Neha Patel",
            "specialty": "Pulmonologist",
            "city": "Ahmedabad",
            "availability": "Tue-Sat 2pm-8pm",
            "rating": 4.9,
            "fees": 600,
            "contact": "+91-6543210987",
            "clinic_address": "Respiratory Care Center, Navrangpura, Ahmedabad",
            "qualifications": "MBBS, MD (Pulmonary Medicine), FCCP",
            "years_experience": 11,
        },
        
        # Surat
        {
            "name": "Dr. Vikram Desai",
            "specialty": "Cardiologist",
            "city": "Surat",
            "availability": "Tue-Sat 10am-4pm",
            "rating": 4.7,
            "fees": 750,
            "contact": "+91-9876543211",
            "clinic_address": "Heart Institute, Vesu, Surat",
            "qualifications": "MBBS, DM (Cardiology)",
            "years_experience": 14,
        },
        {
            "name": "Dr. Anjali Gupta",
            "specialty": "Gastroenterologist",
            "city": "Surat",
            "availability": "Mon-Fri 3pm-7pm",
            "rating": 4.5,
            "fees": 650,
            "contact": "+91-8765432110",
            "clinic_address": "Gastro Care, Kabilwadi, Surat",
            "qualifications": "MBBS, MD (Medicine), DM (Gastroenterology)",
            "years_experience": 9,
        },
        {
            "name": "Dr. Sanjay Choksi",
            "specialty": "General Physician",
            "city": "Surat",
            "availability": "Mon-Sat 9am-9pm",
            "rating": 4.4,
            "fees": 400,
            "contact": "+91-7654321099",
            "clinic_address": "City Care Clinic, Vesu, Surat",
            "qualifications": "MBBS, MD (Medicine)",
            "years_experience": 8,
        },
        
        # Vadodara
        {
            "name": "Dr. Mohan Amin",
            "specialty": "Neurologist",
            "city": "Vadodara",
            "availability": "Mon-Thu 11am-3pm",
            "rating": 4.8,
            "fees": 700,
            "contact": "+91-9876543212",
            "clinic_address": "Neuro Clinic, Alkapuri, Vadodara",
            "qualifications": "MBBS, MD (Neurology), DM",
            "years_experience": 13,
        },
        {
            "name": "Dr. Meera Sharma",
            "specialty": "General Physician",
            "city": "Vadodara",
            "availability": "Daily 8am-6pm",
            "rating": 4.3,
            "fees": 450,
            "contact": "+91-8765432111",
            "clinic_address": "Wellness Center, Vadodara",
            "qualifications": "MBBS, MD (Medicine)",
            "years_experience": 7,
        },
    ]
    
    print("Adding doctors...\n")
    for doctor in sample_doctors:
        doctor_id = add_doctor(
            name=doctor["name"],
            specialty=doctor["specialty"],
            city=doctor["city"],
            availability=doctor["availability"],
            rating=doctor["rating"],
            fees=doctor["fees"],
            contact=doctor["contact"],
            clinic_address=doctor["clinic_address"],
            qualifications=doctor["qualifications"],
            years_experience=doctor["years_experience"],
        )
        print(f"✅ {doctor['name']} ({doctor['specialty']}) in {doctor['city']}")
    
    print(f"\n✅ Added {len(sample_doctors)} doctors\n")
    print("="*80 + "\n")


def test_graph_rag():
    """Test the Graph RAG reasoning"""
    from graph_rag_agent import get_graph_rag_agent
    
    print("="*80)
    print("🧪 TESTING GRAPH RAG REASONING")
    print("="*80 + "\n")
    
    agent = get_graph_rag_agent()
    
    test_cases = [
        ("I have high fever for 3 days with chills", "Ahmedabad"),
        ("I have a persistent cough and chest pain", "Surat"),
        ("Sharp pain in my lower right abdomen", "Vadodara"),
    ]
    
    for user_input, city in test_cases:
        print(f"👤 Patient: {user_input}")
        print(f"📍 City: {city}\n")
        
        result = agent.process_user_input(user_input, user_city=city)
        
        print(f"📋 Response Preview:\n{result['response'][:300]}...\n")
        
        if result["doctors"]:
            print(f"✅ Found {len(result['doctors'])} matching doctors")
            for doc in result["doctors"][:2]:
                print(f"  • Dr. {doc.get('doctor_name', doc.get('name'))} - {doc.get('specialist', doc.get('specialty'))}")
        else:
            print("⚠️ No doctors found (normal if no Neo4j connection)")
        
        print("\n" + "-"*80 + "\n")


if __name__ == "__main__":
    print("\n\n")
    print("=" * 80)
    print("AGENTIC MEDICAL ASSISTANT - INITIALIZATION")
    print("=" * 80)
    
    # Initialize database
    print("\n1️⃣  Initializing database schema...")
    init_database()
    print("✅ Database schema ready\n")
    
    # Initialize knowledge graph
    print("\n2️⃣  Setting up medical knowledge graph...")
    initialize_medical_knowledge()
    
    # Populate sample doctors
    print("\n3️⃣  Adding sample doctors...")
    populate_sample_doctors()
    
    # Test Graph RAG
    print("\n4️⃣  Testing Graph RAG reasoning...")
    test_graph_rag()
    
    print("\n")
    print("=" * 80)
    print("INITIALIZATION COMPLETE - READY TO RUN!")
    print("Next: streamlit run app.py")
    print("=" * 80)
    print("\n")
