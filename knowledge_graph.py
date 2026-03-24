"""
Knowledge Graph Module (Neo4j Integration)
==========================================
This module manages:
1. Medical knowledge relationships (Symptoms -> Diseases -> Specialists)
2. Dynamic doctor profiles and their relationships
3. Graph-based queries for intelligent reasoning
"""

from neo4j import GraphDatabase
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class MedicalKnowledgeGraph:
    """Manages Neo4j knowledge graph for medical relationships"""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        Initialize Neo4j connection
        Default: Local Neo4j instance (bolt://localhost:7687)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        
        # Initialize medical knowledge caches
        self.medical_conditions = {}
        self.herb_remedies = {}
        self.drug_interactions = []
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            print("✅ Connected to Neo4j")
        except Exception as e:
            print(f"⚠️ Neo4j connection failed: {e}")
            print("   Using In-Memory Graph Mode (fallback)")
            self.driver = None
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
    
    # ============================================================================
    # SCHEMA INITIALIZATION
    # ============================================================================
    
    def initialize_medical_graph(self):
        """Create indexes and constraints for medical knowledge"""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            # Create constraints for unique identifiers
            constraints = [
                "CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
                "CREATE CONSTRAINT disease_name IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE",
                "CREATE CONSTRAINT specialist_type IF NOT EXISTS FOR (s:Specialist) REQUIRE s.type IS UNIQUE",
                "CREATE CONSTRAINT doctor_id IF NOT EXISTS FOR (d:Doctor) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT city_name IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except:
                    pass  # Constraint might already exist
            
            # Create indexes for faster queries
            indexes = [
                "CREATE INDEX symptom_severity IF NOT EXISTS FOR (s:Symptom) ON (s.severity)",
                "CREATE INDEX disease_severity IF NOT EXISTS FOR (d:Disease) ON (d.severity)",
                "CREATE INDEX doctor_rating IF NOT EXISTS FOR (d:Doctor) ON (d.rating)",
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except:
                    pass
    
    # ============================================================================
    # ADD MEDICAL RELATIONSHIPS
    # ============================================================================
    
    def add_symptom(self, name: str, severity: str = "medium", description: str = ""):
        """
        Add a symptom node
        severity: 'critical', 'high', 'medium', 'low'
        """
        if not self.driver:
            return
        
        with self.driver.session() as session:
            query = """
            MERGE (s:Symptom {name: $name})
            SET s.severity = $severity, s.description = $description
            RETURN s
            """
            session.run(query, name=name, severity=severity, description=description)
    
    def add_disease(self, name: str, severity: str = "medium", description: str = ""):
        """
        Add a disease node
        severity: 'critical', 'high', 'medium', 'low'
        """
        if not self.driver:
            return
        
        with self.driver.session() as session:
            query = """
            MERGE (d:Disease {name: $name})
            SET d.severity = $severity, d.description = $description
            RETURN d
            """
            session.run(query, name=name, severity=severity, description=description)
    
    def add_specialist(self, type_name: str, description: str = ""):
        """Add a specialist type (e.g., Cardiologist, Dermatologist)"""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            query = """
            MERGE (s:Specialist {type: $type})
            SET s.description = $description
            RETURN s
            """
            session.run(query, type=type_name, description=description)
    
    def add_relationship(self, from_label: str, from_name: str, 
                        rel_type: str, to_label: str, to_name: str, 
                        confidence: float = 0.8):
        """
        Add relationship between nodes
        Examples:
        - Symptom "Fever" -> Disease "Malaria"
        - Disease "Malaria" -> Specialist "Infectious Disease Specialist"
        """
        if not self.driver:
            return
        
        with self.driver.session() as session:
            query = f"""
            MATCH (a:{from_label} {{name: $from_name}})
            MATCH (b:{to_label} {{name: $to_name}})
            MERGE (a)-[r:{rel_type}]->(b)
            SET r.confidence = $confidence
            RETURN r
            """
            session.run(query, from_name=from_name, to_name=to_name, confidence=confidence)
    
    # ============================================================================
    # DOCTOR & CLINIC MANAGEMENT
    # ============================================================================
    
    def add_doctor(self, doctor_id: str, name: str, specialty: str, 
                   city: str, rating: float = 4.5, availability: str = ""):
        """
        Add a doctor node dynamically
        This enables real-time doctor updates
        """
        if not self.driver:
            return
        
        with self.driver.session() as session:
            # First ensure specialist exists
            self._ensure_specialist(specialty)
            
            query = """
            MATCH (s:Specialist {type: $specialty})
            MERGE (d:Doctor {id: $doctor_id})
            SET d.name = $name, d.specialty = $specialty, d.rating = $rating, 
                d.availability = $availability, d.city = $city
            MERGE (d)-[:HAS_SPECIALTY]->(s)
            MERGE (c:City {name: $city})
            MERGE (d)-[:LOCATED_IN]->(c)
            RETURN d
            """
            session.run(query, doctor_id=doctor_id, name=name, specialty=specialty, 
                       city=city, rating=rating, availability=availability)
    
    def update_doctor(self, doctor_id: str, **kwargs):
        """
        Update doctor information dynamically
        kwargs: name, rating, availability, contact, fees, etc.
        """
        if not self.driver:
            return
        
        with self.driver.session() as session:
            set_clause = ", ".join([f"d.{key} = ${key}" for key in kwargs.keys()])
            query = f"""
            MATCH (d:Doctor {{id: $doctor_id}})
            SET {set_clause}
            RETURN d
            """
            session.run(query, doctor_id=doctor_id, **kwargs)
    
    def remove_doctor(self, doctor_id: str):
        """Remove a doctor from the graph"""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            query = """
            MATCH (d:Doctor {id: $doctor_id})
            DETACH DELETE d
            """
            session.run(query, doctor_id=doctor_id)
    
    # ============================================================================
    # LOAD MEDICAL DATA FROM SQLITE
    # ============================================================================
    
    def load_medical_conditions_from_db(self) -> Dict:
        """Load all medical conditions from SQLite into memory cache"""
        import sqlite3
        try:
            conn = sqlite3.connect("hospital.db", timeout=10)
            cur = conn.cursor()
            
            # Fetch all conditions
            cur.execute("SELECT condition_name, symptoms, causes, severity FROM medical_conditions")
            conditions = {}
            count = 0
            
            for row in cur.fetchall():
                condition_name = row[0]
                conditions[condition_name] = {
                    "symptoms": row[1].split(", ") if row[1] else [],
                    "causes": row[2].split(", ") if row[2] else [],
                    "severity": row[3] or "medium"
                }
                count += 1
            
            conn.close()
            print(f"   ✅ Loaded {count} medical conditions from SQLite")
            return conditions
        except Exception as e:
            print(f"   ⚠️  Could not load conditions from SQLite: {e}")
            return {}
    
    def load_herb_remedies_from_db(self) -> Dict:
        """Load all herb remedies from SQLite into memory cache"""
        import sqlite3
        try:
            conn = sqlite3.connect("hospital.db", timeout=10)
            cur = conn.cursor()
            
            # Fetch all herbs
            cur.execute("SELECT herb_name, conditions_treat, dosage, benefits FROM herb_remedies")
            herbs = {}
            count = 0
            
            for row in cur.fetchall():
                herb_name = row[0]
                herbs[herb_name] = {
                    "conditions": row[1].split(", ") if row[1] else [],
                    "dosage": row[2] or "As directed",
                    "benefits": row[3] or ""
                }
                count += 1
            
            conn.close()
            print(f"   ✅ Loaded {count} herb remedies from SQLite")
            return herbs
        except Exception as e:
            print(f"   ⚠️  Could not load herbs from SQLite: {e}")
            return {}
    
    def load_drug_interactions_from_db(self) -> List[Dict]:
        """Load all drug interactions from SQLite into memory cache"""
        import sqlite3
        try:
            conn = sqlite3.connect("hospital.db", timeout=10)
            cur = conn.cursor()
            
            # Fetch all interactions
            cur.execute("SELECT drug1, drug2, severity, effect FROM drug_interactions")
            interactions = []
            count = 0
            
            for row in cur.fetchall():
                interactions.append({
                    "drug1": row[0],
                    "drug2": row[1],
                    "severity": row[2],
                    "effect": row[3]
                })
                count += 1
            
            conn.close()
            print(f"   ✅ Loaded {count} drug interactions from SQLite")
            return interactions
        except Exception as e:
            print(f"   ⚠️  Could not load interactions from SQLite: {e}")
            return []
    
    def cache_medical_knowledge(self):
        """Cache medical data in memory for fast access"""
        print("📚 Caching Medical Knowledge...")
        self.medical_conditions = self.load_medical_conditions_from_db()
        self.herb_remedies = self.load_herb_remedies_from_db()
        self.drug_interactions = self.load_drug_interactions_from_db()
        print("   ✅ Medical knowledge cached in memory\n")
    
    def get_condition_details(self, condition: str) -> Dict:
        """Get detailed information about a condition"""
        if not hasattr(self, 'medical_conditions'):
            self.cache_medical_knowledge()
        
        condition_lower = condition.lower()
        for cond_name, details in self.medical_conditions.items():
            if cond_name.lower() == condition_lower:
                return details
        return None
    
    def get_herb_for_condition(self, condition: str) -> List[str]:
        """Find herbs that can treat a given condition"""
        if not hasattr(self, 'herb_remedies'):
            self.cache_medical_knowledge()
        
        matching_herbs = []
        condition_lower = condition.lower()
        
        for herb_name, details in self.herb_remedies.items():
            for cond in details.get("conditions", []):
                if condition_lower in cond.lower() or cond.lower() in condition_lower:
                    matching_herbs.append({
                        "herb": herb_name,
                        "dosage": details.get("dosage"),
                        "benefits": details.get("benefits")
                    })
                    break
        
        return matching_herbs
    
    def check_drug_interaction(self, drug1: str, drug2: str) -> Optional[Dict]:
        """Check if two drugs have dangerous interactions"""
        if not hasattr(self, 'drug_interactions'):
            self.cache_medical_knowledge()
        
        drug1_lower = drug1.lower()
        drug2_lower = drug2.lower()
        
        for interaction in self.drug_interactions:
            d1 = interaction["drug1"].lower()
            d2 = interaction["drug2"].lower()
            
            if (d1 == drug1_lower and d2 == drug2_lower) or \
               (d1 == drug2_lower and d2 == drug1_lower):
                return interaction
        
        return None
    
    # ============================================================================
    # INTELLIGENT SYMPTOM-BASED REASONING (GraphRAG)
    # ============================================================================
    
    def infer_diseases_from_symptom(self, symptom: str, limit: int = 5) -> List[Dict]:
        """
        Multi-hop reasoning: Symptom -> Disease
        Returns diseases associated with the given symptom
        """
        if not self.driver:
            return self._fallback_infer_diseases(symptom)
        
        with self.driver.session() as session:
            query = """
            MATCH (sym:Symptom {name: $symptom})-[rel:CAUSES]->(disease:Disease)
            RETURN disease.name as name, disease.severity as severity, 
                   disease.description as description, rel.confidence as confidence
            ORDER BY rel.confidence DESC, disease.severity DESC
            LIMIT $limit
            """
            result = session.run(query, symptom=symptom, limit=limit)
            return [dict(record) for record in result]
    
    def recommend_specialists(self, disease: str, limit: int = 5) -> List[Dict]:
        """
        Multi-hop reasoning: Disease -> Specialist
        Returns specialists recommended for treating the disease
        """
        if not self.driver:
            return self._fallback_recommend_specialists(disease)
        
        with self.driver.session() as session:
            query = """
            MATCH (disease:Disease {name: $disease})-[rel:TREATED_BY]->(spec:Specialist)
            RETURN spec.type as type, spec.description as description, 
                   rel.confidence as confidence
            ORDER BY rel.confidence DESC
            LIMIT $limit
            """
            result = session.run(query, disease=disease, limit=limit)
            return [dict(record) for record in result]
    
    def recommend_doctors(self, specialty: str, city: str = None, 
                         limit: int = 5) -> List[Dict]:
        """
        Find best doctors by specialty and optionally by city
        Ordered by rating
        """
        if not self.driver:
            return self._fallback_recommend_doctors(specialty, city)
        
        with self.driver.session() as session:
            if city:
                query = """
                MATCH (d:Doctor)-[:HAS_SPECIALTY]->(s:Specialist {type: $specialty})
                MATCH (d)-[:LOCATED_IN]->(c:City {name: $city})
                RETURN d.id as id, d.name as name, d.specialty as specialty,
                       d.rating as rating, d.availability as availability, 
                       d.city as city
                ORDER BY d.rating DESC
                LIMIT $limit
                """
                result = session.run(query, specialty=specialty, city=city, limit=limit)
            else:
                query = """
                MATCH (d:Doctor)-[:HAS_SPECIALTY]->(s:Specialist {type: $specialty})
                RETURN d.id as id, d.name as name, d.specialty as specialty,
                       d.rating as rating, d.availability as availability, 
                       d.city as city
                ORDER BY d.rating DESC
                LIMIT $limit
                """
                result = session.run(query, specialty=specialty, limit=limit)
            
            return [dict(record) for record in result]
    
    def symptom_to_specialist(self, symptom: str, city: str = None) -> List[Dict]:
        """
        FULL GRAPH RAG: Symptom -> Disease -> Specialist -> Doctor
        Now with Real-Time API Integration!
        
        Flow:
        1. Try external API for real-time doctor data
        2. Fall back to Neo4j graph if API fails
        3. Fall back to in-memory if Neo4j unavailable
        """
        # STEP 1: Try fetching from external API first
        try:
            from api_client import get_api_client
            api_client = get_api_client()
            
            # Map symptom to specialty (simple heuristic for now)
            specialty = self._infer_specialty_from_symptom(symptom)
            
            if specialty and city:
                api_results = api_client.search_doctors(specialty, city, limit=10)
                
                if api_results:
                    print(f"✅ Using API data: Found {len(api_results)} doctors")
                    # Add disease info to API results
                    for doc in api_results:
                        doc['disease'] = self._infer_disease_from_symptom(symptom)
                    return api_results
        except Exception as e:
            print(f"⚠️ API fetch failed: {e}, falling back to graph/in-memory")
        
        # STEP 2: Fall back to Neo4j graph
        if not self.driver:
            return self._fallback_symptom_to_specialist(symptom, city)
        
        with self.driver.session() as session:
            if city:
                query = """
                MATCH (sym:Symptom {name: $symptom})-[r1:CAUSES]->(disease:Disease)
                MATCH (disease)-[r2:TREATED_BY]->(spec:Specialist)
                MATCH (doc:Doctor)-[:HAS_SPECIALTY]->(spec)
                MATCH (doc)-[:LOCATED_IN]->(c:City {name: $city})
                RETURN 
                    disease.name as disease,
                    disease.severity as disease_severity,
                    spec.type as specialist,
                    doc.id as doctor_id,
                    doc.name as doctor_name,
                    doc.rating as doctor_rating,
                    doc.availability as availability,
                    (r1.confidence * r2.confidence) as match_confidence
                ORDER BY match_confidence DESC, doc.rating DESC
                LIMIT 10
                """
                result = session.run(query, symptom=symptom, city=city)
            else:
                query = """
                MATCH (sym:Symptom {name: $symptom})-[r1:CAUSES]->(disease:Disease)
                MATCH (disease)-[r2:TREATED_BY]->(spec:Specialist)
                MATCH (doc:Doctor)-[:HAS_SPECIALTY]->(spec)
                RETURN 
                    disease.name as disease,
                    disease.severity as disease_severity,
                    spec.type as specialist,
                    doc.id as doctor_id,
                    doc.name as doctor_name,
                    doc.rating as doctor_rating,
                    doc.availability as availability,
                    doc.city as city,
                    (r1.confidence * r2.confidence) as match_confidence
                ORDER BY match_confidence DESC, doc.rating DESC
                LIMIT 10
                """
                result = session.run(query, symptom=symptom)
            
            return [dict(record) for record in result]
    
    # ============================================================================
    # FALLBACK: IN-MEMORY GRAPH (For local testing without Neo4j)
    # ============================================================================
    
    def _ensure_specialist(self, specialty: str):
        """Ensure specialist node exists"""
        self.add_specialist(specialty)
    
    def _fallback_infer_diseases(self, symptom: str) -> List[Dict]:
        """Fallback: In-memory mapping for testing"""
        symptom_disease_map = {
            "fever": [{"name": "Malaria", "severity": "high", "confidence": 0.9},
                     {"name": "Typhoid", "severity": "high", "confidence": 0.8},
                     {"name": "Flu", "severity": "medium", "confidence": 0.7}],
            "cough": [{"name": "Pneumonia", "severity": "high", "confidence": 0.85},
                     {"name": "Tuberculosis", "severity": "high", "confidence": 0.8},
                     {"name": "Common Cold", "severity": "low", "confidence": 0.6}],
            "chest pain": [{"name": "Heart Attack", "severity": "critical", "confidence": 0.95},
                          {"name": "Angina", "severity": "high", "confidence": 0.85},
                          {"name": "Asthma", "severity": "high", "confidence": 0.7}],
            "abdominal pain": [{"name": "Appendicitis", "severity": "high", "confidence": 0.9},
                              {"name": "Gastritis", "severity": "medium", "confidence": 0.75},
                              {"name": "IBS", "severity": "low", "confidence": 0.6}],
            "headache": [{"name": "Migraine", "severity": "medium", "confidence": 0.85},
                        {"name": "Tension Headache", "severity": "low", "confidence": 0.8},
                        {"name": "Hypertension", "severity": "high", "confidence": 0.7}],
            "skin rash": [{"name": "Dermatitis", "severity": "low", "confidence": 0.9},
                         {"name": "Eczema", "severity": "low", "confidence": 0.8},
                         {"name": "Allergies", "severity": "medium", "confidence": 0.8}],
            "joint pain": [{"name": "Arthritis", "severity": "medium", "confidence": 0.9},
                          {"name": "Gout", "severity": "high", "confidence": 0.8},
                          {"name": "Injury", "severity": "medium", "confidence": 0.7}],
        }
        return symptom_disease_map.get(symptom.lower(), [])
    
    def _fallback_recommend_specialists(self, disease: str) -> List[Dict]:
        """Fallback: In-memory mapping for testing"""
        disease_specialist_map = {
            "malaria": [{"type": "Infectious Disease Specialist", "confidence": 0.95},
                       {"type": "General Physician", "confidence": 0.8}],
            "heart attack": [{"type": "Cardiologist", "confidence": 0.98},
                            {"type": "Emergency Medicine Specialist", "confidence": 0.95}],
            "appendicitis": [{"type": "General Surgeon", "confidence": 0.95},
                            {"type": "Gastroenterologist", "confidence": 0.85}],
            "pneumonia": [{"type": "Pulmonologist", "confidence": 0.9},
                         {"type": "General Physician", "confidence": 0.75}],
            "migraine": [{"type": "Neurologist", "confidence": 0.9},
                        {"type": "General Physician", "confidence": 0.8}],
            "tension headache": [{"type": "General Physician", "confidence": 0.9}],
            "dermatitis": [{"type": "Dermatologist", "confidence": 0.95}],
            "eczema": [{"type": "Dermatologist", "confidence": 0.95}],
            "arthritis": [{"type": "Orthopedic", "confidence": 0.95},
                         {"type": "Rheumatologist", "confidence": 0.9}],
        }
        return disease_specialist_map.get(disease.lower(), [])
    
    def _infer_specialty_from_symptom(self, symptom: str) -> Optional[str]:
        """Map symptom directly to specialty for API calls"""
        symptom_specialty_map = {
            "headache": "Neurologist",
            "severe headache": "Neurologist",
            "migraine": "Neurologist",
            "chest pain": "Cardiologist",
            "heart pain": "Cardiologist",
            "breathing problem": "Pulmonologist",
            "cough": "Pulmonologist",
            "fever": "General Physician",
            "skin rash": "Dermatologist",
            "rash": "Dermatologist",
            "joint pain": "Orthopedic",
            "back pain": "Orthopedic",
            "stomach pain": "Gastroenterologist",
            "abdominal pain": "Gastroenterologist",
            "anxiety": "Psychiatrist",
            "depression": "Psychiatrist",
            "eye problem": "Ophthalmologist",
            "vision problem": "Ophthalmologist",
            "ear pain": "ENT Specialist",
            "throat pain": "ENT Specialist"
        }
        return symptom_specialty_map.get(symptom.lower())
    
    def _infer_disease_from_symptom(self, symptom: str) -> str:
        """Simple symptom-to-disease mapping for API results"""
        diseases = self._fallback_infer_diseases(symptom)
        if diseases:
            return diseases[0]["name"]
        return "General Condition"
    
    def _fallback_recommend_doctors(self, specialty: str, city: str = None) -> List[Dict]:
        """Fallback: Query SQLite doctor database"""
        from database import find_doctors_in_db
        doctors = find_doctors_in_db(specialty, city)
        result = []
        for doc in doctors:
            result.append({
                "id": str(hash(doc[0])),
                "name": doc[0],
                "specialty": doc[1],
                "availability": doc[2],
                "city": doc[3],
                "rating": 4.5
            })
        return result
    
    def _fallback_symptom_to_specialist(self, symptom: str, city: str = None) -> List[Dict]:
        """Fallback: Multi-hop reasoning using fallback maps"""
        diseases = self._fallback_infer_diseases(symptom)
        if not diseases:
            return []
        
        result = []
        for disease in diseases[:2]:  # Take top 2 diseases
            specialists = self._fallback_recommend_specialists(disease["name"])
            for spec in specialists[:1]:  # Take top specialist
                doctors = self._fallback_recommend_doctors(spec["type"], city)
                for doc in doctors[:2]:  # Take top 2 doctors
                    result.append({
                        "disease": disease["name"],
                        "disease_severity": disease["severity"],
                        "specialist": spec["type"],
                        "doctor_id": doc["id"],
                        "doctor_name": doc["name"],
                        "doctor_rating": doc.get("rating", 4.5),
                        "availability": doc["availability"],
                        "city": doc["city"],
                        "match_confidence": disease["confidence"] * spec["confidence"]
                    })
        
        return sorted(result, key=lambda x: x["match_confidence"], reverse=True)


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_kg_instance = None

def get_knowledge_graph() -> MedicalKnowledgeGraph:
    """Get or create the knowledge graph singleton"""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = MedicalKnowledgeGraph()
        _kg_instance.initialize_medical_graph()
        _kg_instance.cache_medical_knowledge()  # Load medical data on startup
    return _kg_instance


if __name__ == "__main__":
    kg = get_knowledge_graph()
    
    # Example: Test fallback reasoning
    print("\n📊 Symptom-to-Specialist Reasoning:")
    results = kg.symptom_to_specialist("fever", city="Ahmedabad")
    for r in results[:3]:
        print(f"  • {r['disease']} -> {r['specialist']} -> Dr. {r['doctor_name']} ({r['doctor_rating']}⭐)")
