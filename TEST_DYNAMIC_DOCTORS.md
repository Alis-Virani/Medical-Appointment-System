# 🧪 Testing Dynamic Doctor Data System

## Quick Start (5 minutes)

### **Step 1: Start the App**

```bash
streamlit run app.py
```

### **Step 2: Login as Admin**

- Role: `admin` (or `staff`)
- Email: `admin@hospital.com`
- Navigate: Sidebar → ⚙️ **Admin** → 👨‍⚕️ **Doctor Management**

### **Step 3: Bulk Import Sample Doctors**

1. Click **Tab 3: 📥 Bulk Import**
2. Click **"Upload CSV file"**
3. Select: `e:\Project\sample_doctors.csv`
4. Click **"Import Doctors"**
5. ✅ Should show success message: "20 doctors imported successfully"

### **Step 4: Verify Import Success**

1. Click **Tab 1: 📋 View All**
2. Should see table with 20+ doctors
3. Check cities present: Ahmedabad, Surat, Vadodara
4. Export CSV to backup

### **Step 5: Use Dynamic Doctors in Chat**

1. Go to **Chat** page
2. Ask: _"I need a cardiologist in Ahmedabad"_
3. System should return Dr. Rajesh Mehta & others (from database, NOT hardcoded)
4. Click on doctor → can book appointment

---

## 📊 Verification Checklist

### **Database Check:**

```bash
# From terminal, verify database has imported doctors
sqlite3 hospital.db "SELECT COUNT(*) FROM doctors_v2;"
```

Expected output: `20` (or more if you added more)

```bash
# Check doctor details
sqlite3 hospital.db "SELECT name, specialty, city FROM doctors_v2 LIMIT 5;"
```

Expected output:

```
Dr. Rajesh Mehta|Cardiologist|Ahmedabad
Dr. Priya Shah|General Physician|Ahmedabad
Dr. Anil Trivedi|Infectious Disease Specialist|Ahmedabad
...
```

### **Application Check:**

✅ **Admin Panel Test:**

- [ ] Tab 1: Shows all 20 doctors
- [ ] Tab 2: Can add new doctor manually
- [ ] Tab 3: Can see import history
- [ ] Tab 4: Can search & filter doctors

✅ **Chat Integration Test:**

- [ ] Ask for "Cardiologist in Ahmedabad" → Returns Dr. Rajesh Mehta
- [ ] Ask for "General Physician in Surat" → Returns Dr. Sanjay Choksi
- [ ] Ask for "Neurologist" → Returns matches from database
- [ ] Doctor details show correct ratings, fees, experience

✅ **Data Integrity Test:**

- [ ] All 10 columns present: name, specialty, city, rating, fees, contact, address, qualifications, experience, availability
- [ ] No null values in required fields
- [ ] Rating between 1-5
- [ ] Fees > 0

---

## 🔍 Sample Test Queries

Test in chat after importing sample_doctors.csv:

### **Test 1: List Cardiologists in Ahmedabad**

_Query:_ "मुझे अहमदाबाद में कार्डियोलॉजिस्ट चाहिए" (I need cardiologist in Ahmedabad)
_Expected:_ Dr. Rajesh Mehta (₹800, 4.8⭐)

### **Test 2: List General Physicians**

_Query:_ "सामान्य चिकित्सक की सूची" (General physicians list)
_Expected:_ Dr. Priya Shah (Ahmedabad), Dr. Sanjay Choksi (Surat), Dr. Meera Sharma (Vadodara)

### **Test 3: Find Neurologist**

_Query:_ "मुझे न्यूरोलॉजिस्ट चाहिए" (I need neurologist)
_Expected:_ Dr. Mohan Amin (Vadodara, ₹700, 4.8⭐)

### **Test 4: City-based Search**

_Query:_ "सूरत में कौन से डॉक्टर हैं?" (Which doctors in Surat?)
_Expected:_ Dr. Vikram Desai, Dr. Anjali Gupta, Dr. Sanjay Choksi (all from Surat)

---

## 🎯 What This Proves

✅ **Hardcoded doctors REPLACED** - Using database instead
✅ **Add unlimited doctors** - Not limited to 9 anymore
✅ **CSV bulk import works** - Sample data successfully loaded
✅ **Dynamic routing** - Chat queries search database
✅ **Scalable system** - Can add 100/1000 doctors

---

## 📝 Sample Data Statistics

**20 sample doctors included:**

- **Ahmedabad:** Dr. Rajesh Mehta, Dr. Priya Shah, Dr. Anil Trivedi, Dr. Neha Patel
- **Surat:** Dr. Vikram Desai, Dr. Anjali Gupta, Dr. Sanjay Choksi
- **Vadodara:** Dr. Mohan Amin, Dr. Meera Sharma
- Plus 11 more across Jamnagar, Rajkot, Bhavnagar

**Specialties covered:**
Cardiologist, General Physician, Infectious Disease, Pulmonologist, Gastroenterologist, Neurologist, Orthopedic, Pediatrician, Dermatologist, Psychiatrist, Physiotherapist, Dentist, Surgeon, Pathologist, Oncologist

**Key metrics:**

- Avg Rating: 4.6/5.0 ⭐
- Fee Range: ₹400-₹1500
- Experience Range: 7-20 years

---

## 🚀 Next Steps

After verifying system works:

1. **Add Your Real Doctors**
   - Create CSV with actual hospital doctors
   - Upload via Admin → Import

2. **Customize Specialties** (if needed)
   - Edit specialty list in `pages/admin_doctors.py` (line ~80)
   - Add/remove specialties based on your hospital

3. **Enable Payment Integration**
   - Uncomment Razorpay code in `payment_service.py`
   - Add Razorpay API key to `.env`
   - Test booking → payment flow

4. **Add Email Notifications**
   - Configure Sendgrid API key in `.env`
   - Uncomment notification code
   - Verify booking confirmation emails sent

---

## ❌ Troubleshooting

### **Issue: "No doctors found" in chat**

```
Solution:
1. Verify import succeeded (check admin panel Tab 1)
2. Check database: sqlite3 hospital.db "SELECT * FROM doctors_v2 LIMIT 1;"
3. Ensure specialty matches (e.g., "Cardiologist" not "Cardiologist " with space)
```

### **Issue: CSV import fails**

```
Solution:
1. Verify required columns: name, specialty, city, rating, fees
2. Check no duplicate names (doctor_id must be unique)
3. Ensure encoding is UTF-8 (not Excel UTF-16 LE)
4. Try importing sample_doctors.csv first to verify system works
```

### **Issue: Chat still shows old hardcoded doctors**

```
Solution:
1. Restart app: Press Ctrl+C then streamlit run app.py
2. Clear cache: Delete __pycache__ folder
3. Check lang_graph_agent.py is calling get_all_doctors()
4. Verify database query returns doctors
```

### **Issue: Rating shows as 0 or wrong value**

```
Solution:
1. CSV must have numeric rating 1-5
2. Check database: sqlite3 hospital.db "SELECT name, rating FROM doctors_v2;"
3. If corrupted, delete doctors_v2 table and reimport
```

---

## 📞 Success Metrics

✅ All tests below should pass:

- [ ] Admin panel accessible with admin/staff role
- [ ] CSV import completes without errors
- [ ] 20 doctors visible in Tab 1
- [ ] Each doctor has name, specialty, city, rating, fees
- [ ] Chat returns doctors from database (not hardcoded list)
- [ ] Doctor search filters by specialty and city
- [ ] Doctor ratings and fees display correctly
- [ ] Can add new doctor via Tab 2 form
- [ ] Can export doctors to CSV

**When all above pass: ✅ DYNAMIC DOCTOR DATA SYSTEM READY**
