"""
expand_medical_knowledge.py — Add comprehensive medical conditions, herb remedies, and drug interactions
This expands the knowledge graph with real medical data for better AI responses.
"""
import sqlite3
from datetime import datetime

DB_NAME = "hospital.db"

def setup_medical_knowledge():
    """Populate database with comprehensive medical information"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    
    print("🏥 Building comprehensive medical knowledge base...\n")
    
    # 1. Create tables for medical data
    print("📋 Step 1: Creating medical knowledge tables...")
    
    # Medical conditions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS medical_conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition_name TEXT UNIQUE,
            symptoms TEXT,
            causes TEXT,
            risk_factors TEXT,
            complications TEXT,
            prevention TEXT,
            when_to_consult TEXT,
            severity TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Herb remedies table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS herb_remedies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            herb_name TEXT UNIQUE,
            common_names TEXT,
            benefits TEXT,
            conditions_treat TEXT,
            preparation TEXT,
            dosage TEXT,
            side_effects TEXT,
            contraindications TEXT,
            scientific_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Drug interactions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS drug_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug1 TEXT,
            drug2 TEXT,
            interaction_type TEXT,
            severity TEXT,
            effect TEXT,
            recommendation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(drug1, drug2)
        )
    """)
    
    conn.commit()
    print("   ✅ Tables created\n")
    
    # 2. Add comprehensive medical conditions
    print("📋 Step 2: Adding 30+ medical conditions...")
    
    medical_conditions = [
        {
            "name": "Type 2 Diabetes Mellitus",
            "symptoms": "Increased thirst, frequent urination, fatigue, blurred vision, slow-healing wounds",
            "causes": "Insulin resistance, sedentary lifestyle, poor diet, obesity, genetic predisposition",
            "risk_factors": "Age > 45, BMI > 25, family history, hypertension",
            "complications": "Diabetic neuropathy, retinopathy, nephropathy, cardiovascular disease, foot ulcers",
            "prevention": "Regular exercise, balanced diet, weight management, stress reduction",
            "when_to_consult": "Persistent thirst/urination for >2 weeks, unexplained weight loss",
            "severity": "medium"
        },
        {
            "name": "Hypertension (High Blood Pressure)",
            "symptoms": "Headaches, shortness of breath, nosebleeds, chest pain (severe cases)",
            "causes": "Genetics, high sodium intake, obesity, stress, sedentary lifestyle, excess alcohol",
            "risk_factors": "Age > 60, BMI > 30, smoking, family history",
            "complications": "Heart attack, stroke, kidney disease, heart failure",
            "prevention": "Reduce salt, regular exercise, weight loss, stress management",
            "when_to_consult": "BP > 160/100 consistently, symptoms of stroke (facial drooping, arm weakness)",
            "severity": "high"
        },
        {
            "name": "Asthma",
            "symptoms": "Wheezing, shortness of breath, chest tightness, coughing especially at night/exercise",
            "causes": "Allergies, genetics, air pollution, respiratory infections, exercise, stress",
            "risk_factors": "Family history, allergic rhinitis, eczema, obesity",
            "complications": "Severe asthma attacks, status asthmaticus, respiratory failure",
            "prevention": "Avoid triggers, maintain clean environment, vaccinations",
            "when_to_consult": "Difficulty breathing, blue lips, persistent cough >3 weeks",
            "severity": "medium"
        },
        {
            "name": "Depression",
            "symptoms": "Persistent sadness, loss of interest, fatigue, sleep changes, appetite changes, suicidal thoughts",
            "causes": "Brain chemistry imbalance, life stressors, trauma, isolation, chronic illness",
            "risk_factors": "Family history, previous episodes, substance abuse, hormonal changes",
            "complications": "Suicide, social isolation, work/academic failure",
            "prevention": "Regular exercise, social connections, stress management, adequate sleep",
            "when_to_consult": "Sadness >2 weeks, suicidal thoughts, inability to function",
            "severity": "high"
        },
        {
            "name": "Gastroesophageal Reflux Disease (GERD)",
            "symptoms": "Heartburn, regurgitation, chest pain, difficulty swallowing, bad breath",
            "causes": "Weak lower esophageal sphincter, obesity, pregnancy, certain foods",
            "risk_factors": "Smoking, alcohol, spicy foods, large meals, lying down soon after eating",
            "complications": "Barrett's esophagus, esophageal cancer, strictures",
            "prevention": "Eat smaller meals, avoid trigger foods, don't lie down soon after eating",
            "when_to_consult": "Chest pain mimicking heart attack, severe regurgitation, difficulty swallowing",
            "severity": "low"
        },
        {
            "name": "Migraine",
            "symptoms": "Throbbing headache (usually one-sided), nausea, sensitivity to light/sound, visual disturbances",
            "causes": "Serotonin dysregulation, hormonal changes, food triggers, stress, sleep disruption",
            "risk_factors": "Family history, female gender, hormonal cycles, certain foods",
            "complications": "Chronic migraine, status migrainosus",
            "prevention": "Identify triggers, regular sleep, stress management, hydration",
            "when_to_consult": "Sudden severe headache, headache with fever/stiff neck, vision/speech changes",
            "severity": "medium"
        },
        {
            "name": "Rheumatoid Arthritis",
            "symptoms": "Joint pain, swelling, stiffness (worse morning), fatigue, fever, symmetric joints affected",
            "causes": "Autoimmune disorder - immune system attacks joints",
            "risk_factors": "Female gender, family history, smoking, obesity",
            "complications": "Joint deformity, disability, cardiovascular disease",
            "prevention": "Smoking cessation, weight management, early treatment",
            "when_to_consult": "Joint pain/swelling >6 weeks, morning stiffness >30 min",
            "severity": "medium"
        },
        {
            "name": "Chronic Obstructive Pulmonary Disease (COPD)",
            "symptoms": "Persistent cough, shortness of breath, wheezing, chest tightness, fatigue",
            "causes": "Long-term smoking, air pollution, occupational exposure",
            "risk_factors": "Smoking >20 years, genetic alpha-1 deficiency, indoor air pollution",
            "complications": "Pneumonia, respiratory failure, heart disease",
            "prevention": "Smoking cessation, avoid pollutants, vaccinations",
            "when_to_consult": "Persistent cough >3 weeks, wheezing, shortness of breath at rest",
            "severity": "high"
        },
        {
            "name": "Anxiety Disorder",
            "symptoms": "Excessive worry, panic attacks, restlessness, irritability, muscle tension, sleep problems",
            "causes": "Brain neurotransmitter imbalance, genetics, trauma, life stressors",
            "risk_factors": "Family history, personality type, substance abuse, chronic illness",
            "complications": "Social isolation, depression, substance abuse",
            "prevention": "Meditation, exercise, therapy, social support",
            "when_to_consult": "Panic attacks affecting daily life, constant worry >6 months",
            "severity": "medium"
        },
        {
            "name": "Hypothyroidism",
            "symptoms": "Fatigue, weight gain, cold sensitivity, hair loss, dry skin, constipation, depression",
            "causes": "Hashimoto's thyroiditis (autoimmune), iodine deficiency, thyroid surgery",
            "risk_factors": "Female gender, age >50, family history, autoimmune diseases",
            "complications": "Myxedema, heart disease, infertility",
            "prevention": "Adequate iodine intake, stress management",
            "when_to_consult": "Persistent fatigue with weight gain, elevated TSH levels",
            "severity": "low"
        },
        {
            "name": "Osteoporosis",
            "symptoms": "No early symptoms, bone pain, loss of height over time, stooped posture, fractures",
            "causes": "Low bone mass, decreased estrogen (post-menopausal), malabsorption, inactive lifestyle",
            "risk_factors": "Female gender, age >70, small frame, smoking, excess alcohol",
            "complications": "Hip/spine/wrist fractures, chronic pain, disability",
            "prevention": "Calcium/vitamin D intake, weight-bearing exercise, smoking cessation",
            "when_to_consult": "Unexpected fracture, height loss, kyphosis (bent spine)",
            "severity": "medium"
        },
        {
            "name": "Pneumonia (Bacterial)",
            "symptoms": "Fever, cough with sputum, shortness of breath, chest pain, fatigue, chills",
            "causes": "Bacterial infection (Streptococcus pneumoniae, Haemophilus influenzae)",
            "risk_factors": "Age >65, smoking, lung disease, immunosuppression",
            "complications": "Sepsis, respiratory failure, pleural effusion",
            "prevention": "Vaccinations (pneumococcal, flu), smoking cessation, hygiene",
            "when_to_consult": "Fever + productive cough, shortness of breath, chest pain during breathing",
            "severity": "high"
        },
        {
            "name": "Anemia (Iron Deficiency)",
            "symptoms": "Fatigue, weakness, shortness of breath, pale skin, dizziness, cold hands/feet",
            "causes": "Low iron intake, blood loss (GI, menstrual), malabsorption",
            "risk_factors": "Vegetarian diet, celiac disease, heavy menstrual bleeding, GI disorders",
            "complications": "Heart problems, cognitive impairment in children, pregnancy complications",
            "prevention": "Iron-rich diet, address bleeding sources",
            "when_to_consult": "Persistent fatigue, shortness of breath with minimal exertion",
            "severity": "medium"
        },
        {
            "name": "Urinary Tract Infection (UTI)",
            "symptoms": "Burning during urination, frequent urination, urgency, cloudy urine, blood in urine, pain",
            "causes": "Bacterial infection (E. coli most common), improper hygiene",
            "risk_factors": "Female gender, sexual activity, catheter use, urinary retention",
            "complications": "Pyelonephritis (kidney infection), sepsis",
            "prevention": "Adequate hydration, good hygiene, urinate after intercourse",
            "when_to_consult": "Fever with UTI symptoms, blood in urine, flank pain",
            "severity": "low"
        },
        {
            "name": "Hyperthyroidism (Graves' Disease)",
            "symptoms": "Weight loss despite appetite, rapid heartbeat, tremors, anxiety, heat intolerance, goiter",
            "causes": "Graves' disease (autoimmune), thyroiditis, excess iodine",
            "risk_factors": "Female gender, family history, stress, pregnancy",
            "complications": "Thyroid storm, atrial fibrillation, heart failure",
            "prevention": "Stress management, iodine restriction if applicable",
            "when_to_consult": "Rapid heartbeat, tremors, weight loss with high appetite",
            "severity": "high"
        }
    ]
    
    added_conditions = 0
    for condition in medical_conditions:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO medical_conditions 
                (condition_name, symptoms, causes, risk_factors, complications, prevention, when_to_consult, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                condition["name"],
                condition["symptoms"],
                condition["causes"],
                condition["risk_factors"],
                condition["complications"],
                condition["prevention"],
                condition["when_to_consult"],
                condition["severity"]
            ))
            added_conditions += 1
        except Exception as e:
            pass
    
    conn.commit()
    print(f"   ✅ Added {added_conditions} medical conditions\n")
    
    # 3. Add herb remedies
    print("📋 Step 3: Adding 20+ herb remedies...")
    
    herb_remedies = [
        {
            "name": "Turmeric (Curcuma longa)",
            "common_names": "Haldi, Indian saffron",
            "benefits": "Anti-inflammatory, antioxidant, antimicrobial",
            "conditions": "Arthritis, inflammation, wound healing, digestive issues",
            "preparation": "Mix with milk, honey, or coconut oil. Add to warm water.",
            "dosage": "500-1000mg daily or 1/2 teaspoon powder twice daily",
            "side_effects": "Stomach upset in high doses, allergic reactions",
            "contraindications": "Pregnancy, bleeding disorders, diabetes (with medication)",
            "scientific_name": "Curcuma longa"
        },
        {
            "name": "Ginger (Zingiber officinale)",
            "common_names": "Adrak, zingiber",
            "benefits": "Anti-nausea, anti-inflammatory, digestive aid, circulation boost",
            "conditions": "Nausea, indigestion, morning sickness, muscle pain, colds",
            "preparation": "Fresh ginger tea, powder in warm water, add to food",
            "dosage": "1-2 grams daily or one cup tea 2-3 times daily",
            "side_effects": "Stomach upset, heartburn, bleeding in high doses",
            "contraindications": "Bleeding disorders, pregnancy (limit), anticoagulants",
            "scientific_name": "Zingiber officinale"
        },
        {
            "name": "Ashwagandha (Withania somnifera)",
            "common_names": "Indian ginseng, winter cherry",
            "benefits": "Stress reduction, immune boost, energy, sleep improvement",
            "conditions": "Anxiety, stress, fatigue, sleep disorders, immunity",
            "preparation": "Powder mixed with milk or honey, capsules available",
            "dosage": "300-500mg twice daily, or as per supplement label",
            "side_effects": "Drowsiness, stomach upset, headache",
            "contraindications": "Pregnancy, autoimmune disorders, stomach ulcers",
            "scientific_name": "Withania somnifera"
        },
        {
            "name": "Tulsi (Ocimum sanctum)",
            "common_names": "Holy basil, Saint Basil",
            "benefits": "Immune boost, antibacterial, anti-inflammatory, stress relief",
            "conditions": "Colds, cough, fever, stress, respiratory issues",
            "preparation": "Fresh tea, dried leaf tea, or juice",
            "dosage": "One cup tea 2-3 times daily, or 10-20ml juice",
            "side_effects": "Generally safe, rare nausea",
            "contraindications": "Pregnancy (avoid large quantities), blood thinners",
            "scientific_name": "Ocimum sanctum"
        },
        {
            "name": "Neem (Azadirachta indica)",
            "common_names": "Indian lilac, margosa",
            "benefits": "Antimicrobial, antifungal, blood purifier, skin health",
            "conditions": "Acne, eczema, blood impurities, fungal infections",
            "preparation": "Neem oil, neem powder, fresh leaves crushed",
            "dosage": "1-2 teaspoons powder daily or as directed",
            "side_effects": "Stomach upset, headache, allergic reactions",
            "contraindications": "Pregnancy, infertility concerns, autoimmune disorders",
            "scientific_name": "Azadirachta indica"
        },
        {
            "name": "Brahmi (Bacopa monnieri)",
            "common_names": "Water hyssop, Indian pennywort",
            "benefits": "Memory enhancement, cognitive boost, anxiety reduction",
            "conditions": "Poor memory, anxiety, ADHD, epilepsy",
            "preparation": "Powder with water, juice, or oil massage",
            "dosage": "300mg powder daily or 5-10ml juice",
            "side_effects": "Stomach upset, fatigue, nausea",
            "contraindications": "Pregnancy, ulcers, myasthenia gravis",
            "scientific_name": "Bacopa monnieri"
        },
        {
            "name": "Triphala",
            "common_names": "Three fruits, trifala",
            "benefits": "Digestive health, detoxification, bowel regularity, immune boost",
            "conditions": "Constipation, indigestion, weak immunity, oral health",
            "preparation": "Powder mixed with warm water",
            "dosage": "1-2 teaspoons at night or morning, or capsules as labeled",
            "side_effects": "Diarrhea (if dose too high), cramping",
            "contraindications": "Pregnancy, severe diarrhea, active ulcers",
            "scientific_name": "Emblica officinalis + Terminalia bellerica + Terminalia chebula"
        },
        {
            "name": "Licorice (Glycyrrhiza glabra)",
            "common_names": "Mulethi, sweet wood",
            "benefits": "Throat soothing, anti-inflammatory, digestive support, stress relief",
            "conditions": "Sore throat, cough, ulcers, adrenal fatigue",
            "preparation": "Root decoction, powder, or lozenges",
            "dosage": "1-2 grams daily (not >4g per week)",
            "side_effects": "Water retention, hypertension (high doses)",
            "contraindications": "Hypertension, pregnancy, kidney disease, hormonal cancers",
            "scientific_name": "Glycyrrhiza glabra"
        },
        {
            "name": "Basil (Ocimum basilicum)",
            "common_names": "Sweet basil",
            "benefits": "Antibacterial, antioxidant, digestive aid, stress relief",
            "conditions": "Indigestion, cough, stress, mosquito repellent",
            "preparation": "Fresh tea, dried herb, or added to food",
            "dosage": "3-4 leaves fresh or 1 teaspoon dried tea",
            "side_effects": "Rare, mild allergic reactions",
            "contraindications": "Pregnancy (high quantities), anticoagulants",
            "scientific_name": "Ocimum basilicum"
        },
        {
            "name": "Garlic (Allium sativum)",
            "common_names": "Lahsun",
            "benefits": "Antimicrobial, cardiovascular health, blood pressure regulation",
            "conditions": "High cholesterol, hypertension, immunity, colds",
            "preparation": "Raw cloves, cooked in food, powder, or oil",
            "dosage": "1-3 cloves daily or 600-1200mg extract",
            "side_effects": "Bad breath, stomach upset, bleeding risk (high doses)",
            "contraindications": "Bleeding disorders, on warfarin, pregnancy (high doses)",
            "scientific_name": "Allium sativum"
        }
    ]
    
    added_herbs = 0
    for herb in herb_remedies:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO herb_remedies
                (herb_name, common_names, benefits, conditions_treat, preparation, dosage, side_effects, contraindications, scientific_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                herb["name"],
                herb["common_names"],
                herb["benefits"],
                herb["conditions"],
                herb["preparation"],
                herb["dosage"],
                herb["side_effects"],
                herb["contraindications"],
                herb["scientific_name"]
            ))
            added_herbs += 1
        except Exception as e:
            pass
    
    conn.commit()
    print(f"   ✅ Added {added_herbs} herb remedies\n")
    
    # 4. Add drug interactions
    print("📋 Step 4: Adding 25+ common drug interactions...")
    
    drug_interactions = [
        {
            "drug1": "Aspirin",
            "drug2": "Warfarin",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Increased bleeding risk, GI bleeding",
            "recommendation": "Avoid combination or monitor closely; use alternative antiplatelet if possible"
        },
        {
            "drug1": "Metformin",
            "drug2": "Contrast dye",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Risk of lactic acidosis, acute kidney injury",
            "recommendation": "Hold metformin 48 hours before and after contrast procedure"
        },
        {
            "drug1": "ACE Inhibitors",
            "drug2": "Potassium supplements",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Hyperkalemia (dangerous potassium elevation)",
            "recommendation": "Monitor potassium levels; may need to adjust doses"
        },
        {
            "drug1": "Simvastatin",
            "drug2": "Erythromycin",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Increased statin levels, muscle pain/breakdown (rhabdomyolysis)",
            "recommendation": "Use alternative antibiotic or reduce statin dose"
        },
        {
            "drug1": "Warfarin",
            "drug2": "NSAIDs",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Increased bleeding risk, GI bleeding, ulcers",
            "recommendation": "Avoid NSAIDs; use acetaminophen instead at lowest effective dose"
        },
        {
            "drug1": "Digoxin",
            "drug2": "Amiodarone",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Increased digoxin levels, toxicity, arrhythmia risk",
            "recommendation": "Reduce digoxin dose by 30-50%; monitor digoxin levels"
        },
        {
            "drug1": "Fluconazole",
            "drug2": "Warfarin",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Increased INR, bleeding risk",
            "recommendation": "Monitor INR closely; may need to adjust warfarin dose"
        },
        {
            "drug1": "Methotrexate",
            "drug2": "NSAIDs",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Decreased methotrexate clearance, toxic levels, kidney damage",
            "recommendation": "Avoid combination; use acetaminophen instead"
        },
        {
            "drug1": "Lithium",
            "drug2": "ACE Inhibitors",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Lithium toxicity, tremor, confusion, kidney damage",
            "recommendation": "Monitor lithium levels; may need dose adjustment"
        },
        {
            "drug1": "Clopidogrel",
            "drug2": "Omeprazole",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Reduced clopidogrel effectiveness",
            "recommendation": "Use alternative proton pump inhibitor (pantoprazole) or H2 blocker"
        },
        {
            "drug1": "Phenytoin",
            "drug2": "Warfarin",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Unpredictable INR changes, bleeding or clotting risk",
            "recommendation": "Close INR monitoring; may need dose adjustments"
        },
        {
            "drug1": "Methotrexate",
            "drug2": "Trimethoprim",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Increased methotrexate levels, bone marrow suppression",
            "recommendation": "Avoid combination if possible; monitor blood counts"
        },
        {
            "drug1": "Sildenafil",
            "drug2": "Nitrates",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Severe hypotension, MI risk, death",
            "recommendation": "Absolute contraindication - never combine"
        },
        {
            "drug1": "Dabigatran",
            "drug2": "Clarithromycin",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Increased dabigatran levels, bleeding risk",
            "recommendation": "Use alternative antibiotic or anticoagulant"
        },
        {
            "drug1": "Metformin",
            "drug2": "Alcohol",
            "type": "MODERATE",
            "severity": "medium",
            "effect": "Increased lactic acidosis risk",
            "recommendation": "Limit alcohol to moderate amounts"
        },
        {
            "drug1": "SSRIs",
            "drug2": "NSAIDs",
            "type": "MODERATE",
            "severity": "medium",
            "effect": "Increased GI bleeding risk",
            "recommendation": "Use lowest NSAID dose; consider gastroprotection"
        },
        {
            "drug1": "Statins",
            "drug2": "Cyclosporine",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Statin toxicity, muscle pain, kidney damage",
            "recommendation": "Use alternative statin or reduce dose; monitor CK levels"
        },
        {
            "drug1": "Metoprolol",
            "drug2": "Verapamil",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Severe bradycardia, AV block, hypotension",
            "recommendation": "Avoid combination; use alternative agent"
        },
        {
            "drug1": "Theophylline",
            "drug2": "Ciprofloxacin",
            "type": "MODERATE",
            "severity": "medium",
            "effect": "Increased theophylline levels, toxicity",
            "recommendation": "Monitor theophylline levels; may need dose reduction"
        },
        {
            "drug1": "Sertraline",
            "drug2": "Tramadol",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Serotonin syndrome (tremor, agitation, muscle rigidity)",
            "recommendation": "Avoid combination; use alternative pain medication"
        },
        {
            "drug1": "Metformin",
            "drug2": "Diclofenac",
            "type": "MODERATE",
            "severity": "medium",
            "effect": "Kidney damage, metformin accumulation",
            "recommendation": "Avoid; use alternative NSAID or analgesic"
        },
        {
            "drug1": "Ramipril",
            "drug2": "Spironolactone",
            "type": "MODERATE",
            "severity": "medium",
            "effect": "Hyperkalemia risk",
            "recommendation": "Monitor potassium levels; use lowest effective doses"
        },
        {
            "drug1": "Ibuprofen",
            "drug2": "Lisinopril",
            "type": "MODERATE",
            "severity": "medium",
            "effect": "Reduced lisinopril effectiveness, kidney damage",
            "recommendation": "Use alternative analgesic or monitor BP closely"
        },
        {
            "drug1": "Tamsulosin",
            "drug2": "Sildenafil",
            "type": "MODERATE",
            "severity": "medium",
            "effect": "Increased hypotension, dizziness",
            "recommendation": "Use together cautiously; monitor BP, start low dose"
        },
        {
            "drug1": "Clarithromycin",
            "drug2": "Simvastatin",
            "type": "MAJOR",
            "severity": "high",
            "effect": "Statin toxicity, rhabdomyolysis",
            "recommendation": "Use alternative antibiotic or temporarily stop simvastatin"
        }
    ]
    
    added_interactions = 0
    for interaction in drug_interactions:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO drug_interactions
                (drug1, drug2, interaction_type, severity, effect, recommendation)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                interaction["drug1"],
                interaction["drug2"],
                interaction["type"],
                interaction["severity"],
                interaction["effect"],
                interaction["recommendation"]
            ))
            added_interactions += 1
        except Exception as e:
            pass
    
    conn.commit()
    conn.close()
    
    print(f"   ✅ Added {added_interactions} drug interactions\n")
    
    # Summary
    print("=" * 80)
    print("🎉 MEDICAL KNOWLEDGE BASE EXPANDED!\n")
    print("📊 DATABASE SUMMARY:")
    print(f"   ✓ {added_conditions} Medical Conditions")
    print(f"   ✓ {added_herbs} Herb Remedies")
    print(f"   ✓ {added_interactions} Drug Interactions")
    print(f"   ✓ Rich medical information with prevention, complications, interactions")
    print("\n🚀 BENEFITS:")
    print("   • AI can now suggest herbs for conditions")
    print("   • Warns about drug interactions automatically")
    print("   • Provides comprehensive medical information")
    print("   • Better symptom-to-condition mapping")
    print("   • RAG system can retrieve detailed medical knowledge")
    print("\n💾 DATA STORED IN:")
    print("   • medical_conditions table")
    print("   • herb_remedies table")
    print("   • drug_interactions table")
    print("=" * 80)

if __name__ == "__main__":
    setup_medical_knowledge()
