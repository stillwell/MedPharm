# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# Email: Andrew.Stillwell@enlightec.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
MedPharm ERP - Seed Data
Populates the database with realistic sample data including 50+ medications.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
import random

from database.db_manager import DatabaseManager
from database.models import (
    User, Patient, PatientPortalAccount, Insurance, Medication,
    MedicationInteraction, Allergy, Vital, Diagnosis, MedicalRecord,
    Prescription, PrescriptionItem, Appointment, Invoice, InvoiceItem,
    Payment, AuditLog, UserRole, Gender, BloodType, DrugSchedule,
    DrugForm, DrugRoute, InteractionSeverity, AllergySeverity,
    DiagnosisStatus, RecordType, PrescriptionStatus, AppointmentType,
    AppointmentStatus, InvoiceStatus, PaymentMethod, PaymentStatus,
    CoverageType
)
from werkzeug.security import generate_password_hash


def seed_database(db_manager: DatabaseManager):
    if not db_manager.is_database_empty():
        return

    with db_manager.get_session() as session:
        # ── Users ──────────────────────────────────────────────────────
        users = [
            User(username="dr.carter", password_hash=generate_password_hash("doctor123"),
                 role=UserRole.DOCTOR, first_name="James", last_name="Carter",
                 email="james.carter@medpharm.com", phone="555-0101",
                 license_number="MD-12345", specialization="Internal Medicine"),
            User(username="dr.chen", password_hash=generate_password_hash("doctor123"),
                 role=UserRole.DOCTOR, first_name="Lisa", last_name="Chen",
                 email="lisa.chen@medpharm.com", phone="555-0102",
                 license_number="MD-12346", specialization="Family Medicine"),
            User(username="dr.brooks", password_hash=generate_password_hash("doctor123"),
                 role=UserRole.PSYCHIATRIST, first_name="Michael", last_name="Brooks",
                 email="michael.brooks@medpharm.com", phone="555-0103",
                 license_number="MD-12347", specialization="Psychiatry"),
            User(username="pharm.davis", password_hash=generate_password_hash("pharm123"),
                 role=UserRole.PHARMACIST, first_name="Sarah", last_name="Davis",
                 email="sarah.davis@medpharm.com", phone="555-0104",
                 license_number="RPH-56789", specialization="Clinical Pharmacy"),
            User(username="admin", password_hash=generate_password_hash("admin123"),
                 role=UserRole.ADMIN, first_name="Robert", last_name="Admin",
                 email="admin@medpharm.com", phone="555-0100"),
        ]
        session.add_all(users)
        session.flush()

        # ── Patients ───────────────────────────────────────────────────
        patients_data = [
            ("John", "Smith", date(1985, 3, 15), Gender.MALE, "1234", "jsmith@email.com", "555-1001", "123 Oak St", "Springfield", "IL", "62701", "Mary Smith", "555-1002", BloodType.A_POS),
            ("Maria", "Johnson", date(1990, 7, 22), Gender.FEMALE, "2345", "mjohnson@email.com", "555-1003", "456 Elm Ave", "Springfield", "IL", "62702", "Carlos Johnson", "555-1004", BloodType.O_POS),
            ("Emily", "Williams", date(1978, 11, 8), Gender.FEMALE, "3456", "ewilliams@email.com", "555-1005", "789 Pine Rd", "Chicago", "IL", "60601", "Tom Williams", "555-1006", BloodType.B_NEG),
            ("Robert", "Brown", date(1965, 1, 30), Gender.MALE, "4567", "rbrown@email.com", "555-1007", "321 Maple Dr", "Chicago", "IL", "60602", "Linda Brown", "555-1008", BloodType.AB_POS),
            ("Sarah", "Davis", date(1995, 5, 12), Gender.FEMALE, "5678", "sdavis@email.com", "555-1009", "654 Birch Ln", "Aurora", "IL", "60503", "Mike Davis", "555-1010", BloodType.O_NEG),
            ("James", "Wilson", date(1972, 9, 3), Gender.MALE, "6789", "jwilson@email.com", "555-1011", "987 Cedar Ct", "Naperville", "IL", "60540", "Nancy Wilson", "555-1012", BloodType.A_NEG),
            ("Linda", "Martinez", date(1988, 12, 19), Gender.FEMALE, "7890", "lmartinez@email.com", "555-1013", "147 Walnut St", "Evanston", "IL", "60201", "Pedro Martinez", "555-1014", BloodType.B_POS),
            ("Michael", "Anderson", date(1955, 6, 25), Gender.MALE, "8901", "manderson@email.com", "555-1015", "258 Spruce Ave", "Joliet", "IL", "60431", "Susan Anderson", "555-1016", BloodType.O_POS),
            ("Jennifer", "Thomas", date(1992, 2, 14), Gender.FEMALE, "9012", "jthomas@email.com", "555-1017", "369 Ash Blvd", "Rockford", "IL", "61101", "David Thomas", "555-1018", BloodType.AB_NEG),
            ("David", "Garcia", date(1980, 8, 7), Gender.MALE, "0123", "dgarcia@email.com", "555-1019", "741 Oak Park", "Peoria", "IL", "61602", "Rosa Garcia", "555-1020", BloodType.A_POS),
            ("Jessica", "Moore", date(1998, 4, 28), Gender.FEMALE, "1122", "jmoore@email.com", "555-1021", "852 Lake Dr", "Champaign", "IL", "61820", "Ann Moore", "555-1022", BloodType.O_POS),
            ("William", "Taylor", date(1970, 10, 16), Gender.MALE, "2233", "wtaylor@email.com", "555-1023", "963 River Rd", "Decatur", "IL", "62521", "Karen Taylor", "555-1024", BloodType.B_POS),
            ("Amanda", "Jackson", date(1983, 7, 1), Gender.FEMALE, "3344", "ajackson@email.com", "555-1025", "159 Hill St", "Bloomington", "IL", "61701", "Tom Jackson", "555-1026", BloodType.A_NEG),
            ("Christopher", "White", date(1960, 3, 9), Gender.MALE, "4455", "cwhite@email.com", "555-1027", "267 Valley Ave", "Normal", "IL", "61761", "Diane White", "555-1028", BloodType.O_NEG),
            ("Stephanie", "Harris", date(1993, 11, 23), Gender.FEMALE, "5566", "sharris@email.com", "555-1029", "378 Creek Ln", "Urbana", "IL", "61801", "Paul Harris", "555-1030", BloodType.AB_POS),
        ]
        patients = []
        for pd in patients_data:
            p = Patient(
                first_name=pd[0], last_name=pd[1], dob=pd[2], gender=pd[3],
                ssn_last4=pd[4], email=pd[5], phone=pd[6], address=pd[7],
                city=pd[8], state=pd[9], zip_code=pd[10],
                emergency_contact_name=pd[11], emergency_contact_phone=pd[12],
                blood_type=pd[13]
            )
            patients.append(p)
        session.add_all(patients)
        session.flush()

        # ── Portal Accounts ────────────────────────────────────────────
        portal_accounts = [
            PatientPortalAccount(patient_id=patients[0].id, username="jsmith_portal",
                password_hash=generate_password_hash("patient123"), email="jsmith@email.com"),
            PatientPortalAccount(patient_id=patients[1].id, username="mjohnson_portal",
                password_hash=generate_password_hash("patient123"), email="mjohnson@email.com"),
            PatientPortalAccount(patient_id=patients[2].id, username="ewilliams_portal",
                password_hash=generate_password_hash("patient123"), email="ewilliams@email.com"),
            PatientPortalAccount(patient_id=patients[4].id, username="sdavis_portal",
                password_hash=generate_password_hash("patient123"), email="sdavis@email.com"),
            PatientPortalAccount(patient_id=patients[6].id, username="lmartinez_portal",
                password_hash=generate_password_hash("patient123"), email="lmartinez@email.com"),
        ]
        session.add_all(portal_accounts)
        session.flush()

        # ── Insurance ──────────────────────────────────────────────────
        insurance_data = [
            (patients[0].id, "Blue Cross Blue Shield", "BCB-001234", "GRP-500", CoverageType.PPO, 30),
            (patients[1].id, "Aetna", "AET-005678", "GRP-501", CoverageType.HMO, 25),
            (patients[2].id, "UnitedHealthcare", "UHC-009012", "GRP-502", CoverageType.PPO, 35),
            (patients[3].id, "Medicare", "MCR-003456", None, CoverageType.MEDICARE, 0),
            (patients[4].id, "Cigna", "CIG-007890", "GRP-503", CoverageType.EPO, 20),
            (patients[5].id, "Humana", "HUM-001122", "GRP-504", CoverageType.PPO, 40),
            (patients[6].id, "Kaiser Permanente", "KP-003344", "GRP-505", CoverageType.HMO, 15),
            (patients[7].id, "Medicare", "MCR-005566", None, CoverageType.MEDICARE, 0),
            (patients[8].id, "Anthem", "ANT-007788", "GRP-506", CoverageType.PPO, 30),
            (patients[9].id, "Molina Healthcare", "MOL-009900", "GRP-507", CoverageType.MEDICAID, 5),
        ]
        for ins in insurance_data:
            session.add(Insurance(
                patient_id=ins[0], provider_name=ins[1], policy_number=ins[2],
                group_number=ins[3], subscriber_name=None,
                copay_amount=ins[5], coverage_type=ins[4],
                effective_date=date(2025, 1, 1), expiry_date=date(2026, 12, 31),
                is_active=True
            ))
        session.flush()

        # ── Medications (50+) ──────────────────────────────────────────
        meds_data = [
            # Antibiotics
            ("0069-3150-83", "Amoxicillin", "Amoxicillin", "Teva Pharmaceuticals", "Antibiotic - Penicillin", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.CAPSULE, "500mg", "mg", "Penicillin-type antibiotic", "Bacterial infections including ear, nose, throat, urinary tract, and skin infections", "Penicillin allergy, mononucleosis", "Nausea, diarrhea, rash, vomiting", 4.50, 12.99),
            ("0093-3109-01", "Azithromycin", "Azithromycin", "Pfizer", "Antibiotic - Macrolide", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "250mg", "mg", "Macrolide antibiotic (Z-Pack)", "Respiratory infections, skin infections, ear infections, STIs", "Hepatic impairment, QT prolongation", "Nausea, diarrhea, abdominal pain, headache", 8.00, 24.99),
            ("0093-2270-01", "Ciprofloxacin", "Ciprofloxacin", "Bayer", "Antibiotic - Fluoroquinolone", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "500mg", "mg", "Fluoroquinolone antibiotic", "UTIs, respiratory infections, bone/joint infections, anthrax", "Tendon disorders, myasthenia gravis, children under 18", "Tendinitis, nausea, diarrhea, dizziness", 6.00, 18.99),
            ("0781-2150-01", "Doxycycline", "Doxycycline Hyclate", "Mylan", "Antibiotic - Tetracycline", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.CAPSULE, "100mg", "mg", "Tetracycline antibiotic", "Acne, Lyme disease, respiratory infections, STIs, malaria prophylaxis", "Pregnancy, children under 8, severe hepatic impairment", "Photosensitivity, nausea, esophageal irritation", 5.00, 15.99),
            ("0143-9928-01", "Cephalexin", "Cephalexin", "Ascend Laboratories", "Antibiotic - Cephalosporin", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.CAPSULE, "500mg", "mg", "First-generation cephalosporin", "Skin infections, bone infections, respiratory infections, UTIs", "Cephalosporin allergy, severe penicillin allergy", "Diarrhea, nausea, gastritis, headache", 4.00, 11.99),

            # Antidepressants
            ("0049-4960-66", "Zoloft", "Sertraline", "Pfizer", "Antidepressant - SSRI", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "50mg", "mg", "Selective serotonin reuptake inhibitor", "Major depression, OCD, panic disorder, PTSD, social anxiety, PMDD", "MAOIs within 14 days, pimozide, disulfiram (liquid form)", "Nausea, diarrhea, insomnia, sexual dysfunction, tremor", 3.00, 14.99),
            ("0002-4220-30", "Prozac", "Fluoxetine", "Eli Lilly", "Antidepressant - SSRI", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.CAPSULE, "20mg", "mg", "Selective serotonin reuptake inhibitor", "Major depression, OCD, bulimia nervosa, panic disorder", "MAOIs within 14 days, thioridazine, pimozide", "Nausea, headache, insomnia, anxiety, sexual dysfunction", 3.50, 15.99),
            ("0456-2010-01", "Lexapro", "Escitalopram", "Forest Laboratories", "Antidepressant - SSRI", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "10mg", "mg", "Selective serotonin reuptake inhibitor", "Major depression, generalized anxiety disorder", "MAOIs within 14 days, pimozide, IV methylene blue", "Nausea, insomnia, ejaculation disorder, somnolence", 4.00, 19.99),
            ("0008-1090-01", "Effexor XR", "Venlafaxine", "Wyeth", "Antidepressant - SNRI", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.CAPSULE, "75mg", "mg", "Serotonin-norepinephrine reuptake inhibitor", "Major depression, generalized anxiety, social anxiety, panic disorder", "MAOIs within 14 days, uncontrolled hypertension", "Nausea, dizziness, insomnia, sweating, constipation, increased BP", 6.00, 22.99),
            ("0597-0048-68", "Wellbutrin XL", "Bupropion", "GlaxoSmithKline", "Antidepressant - NDRI", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "150mg", "mg", "Norepinephrine-dopamine reuptake inhibitor", "Major depression, seasonal affective disorder, smoking cessation aid", "Seizure disorder, eating disorders, MAOIs, abrupt alcohol discontinuation", "Dry mouth, insomnia, headache, nausea, weight loss", 5.00, 28.99),

            # Antipsychotics
            ("0002-4210-60", "Zyprexa", "Olanzapine", "Eli Lilly", "Antipsychotic - Atypical", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "10mg", "mg", "Second-generation atypical antipsychotic", "Schizophrenia, bipolar disorder (manic/mixed episodes), treatment-resistant depression (with fluoxetine)", "Dementia-related psychosis in elderly", "Weight gain, somnolence, dizziness, metabolic syndrome, hyperglycemia", 12.00, 45.99),
            ("4088-0001-10", "Risperdal", "Risperidone", "Janssen", "Antipsychotic - Atypical", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "2mg", "mg", "Second-generation atypical antipsychotic", "Schizophrenia, bipolar mania, irritability in autism", "Dementia-related psychosis in elderly", "Weight gain, EPS, prolactin elevation, somnolence, metabolic effects", 8.00, 32.99),
            ("0003-0852-11", "Seroquel", "Quetiapine", "AstraZeneca", "Antipsychotic - Atypical", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "100mg", "mg", "Second-generation atypical antipsychotic", "Schizophrenia, bipolar disorder, major depression (adjunct)", "Dementia-related psychosis in elderly", "Somnolence, weight gain, dizziness, dry mouth, metabolic changes", 10.00, 38.99),

            # Anxiolytics / Benzodiazepines
            ("0009-0029-02", "Xanax", "Alprazolam", "Pfizer", "Anxiolytic - Benzodiazepine", DrugSchedule.IV, DrugRoute.ORAL, DrugForm.TABLET, "0.5mg", "mg", "Short-acting benzodiazepine", "Anxiety disorders, panic disorder with or without agoraphobia", "Acute narrow-angle glaucoma, ketoconazole/itraconazole use", "Drowsiness, fatigue, memory impairment, dependence, withdrawal", 5.00, 16.99),
            ("0004-0094-01", "Klonopin", "Clonazepam", "Roche", "Anxiolytic - Benzodiazepine", DrugSchedule.IV, DrugRoute.ORAL, DrugForm.TABLET, "1mg", "mg", "Long-acting benzodiazepine", "Seizure disorders, panic disorder, anxiety", "Severe hepatic impairment, acute narrow-angle glaucoma", "Drowsiness, ataxia, depression, dependence, cognitive impairment", 4.50, 14.99),
            ("0140-0005-01", "Ativan", "Lorazepam", "Wyeth", "Anxiolytic - Benzodiazepine", DrugSchedule.IV, DrugRoute.ORAL, DrugForm.TABLET, "1mg", "mg", "Intermediate-acting benzodiazepine", "Anxiety disorders, insomnia, seizure emergencies, procedural sedation", "Severe respiratory insufficiency, sleep apnea, acute narrow-angle glaucoma", "Sedation, dizziness, weakness, unsteadiness, dependence", 3.50, 12.99),

            # Mood Stabilizers
            ("0054-0011-25", "Lithium", "Lithium Carbonate", "Roxane Laboratories", "Mood Stabilizer", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.CAPSULE, "300mg", "mg", "Mood stabilizing agent", "Bipolar disorder (manic episodes), maintenance therapy for bipolar", "Severe renal impairment, severe cardiovascular disease, dehydration", "Tremor, polyuria, polydipsia, weight gain, thyroid dysfunction, nausea", 2.50, 9.99),
            ("0074-6214-13", "Depakote", "Divalproex Sodium", "AbbVie", "Anticonvulsant / Mood Stabilizer", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "500mg", "mg", "Valproic acid derivative", "Epilepsy, bipolar mania, migraine prophylaxis", "Hepatic disease, urea cycle disorders, pregnancy", "Nausea, tremor, weight gain, hair loss, hepatotoxicity, pancreatitis", 7.00, 25.99),
            ("0078-0510-05", "Lamictal", "Lamotrigine", "GlaxoSmithKline", "Anticonvulsant / Mood Stabilizer", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "100mg", "mg", "Phenyltriazine anticonvulsant", "Epilepsy, bipolar disorder maintenance", "Known hypersensitivity to lamotrigine", "Stevens-Johnson syndrome (rare), headache, dizziness, nausea, rash", 5.00, 22.99),

            # Stimulants (ADHD)
            ("0555-0767-02", "Adderall XR", "Amphetamine/Dextroamphetamine", "Shire", "CNS Stimulant", DrugSchedule.II, DrugRoute.ORAL, DrugForm.CAPSULE, "20mg", "mg", "Mixed amphetamine salts extended-release", "ADHD, narcolepsy", "Advanced arteriosclerosis, cardiovascular disease, MAOIs within 14 days, glaucoma, agitated states, substance abuse history", "Insomnia, decreased appetite, dry mouth, anxiety, tachycardia, weight loss", 25.00, 89.99),
            ("0078-0368-05", "Ritalin", "Methylphenidate", "Novartis", "CNS Stimulant", DrugSchedule.II, DrugRoute.ORAL, DrugForm.TABLET, "10mg", "mg", "Methylphenidate hydrochloride", "ADHD, narcolepsy", "Marked anxiety/tension/agitation, glaucoma, tics, MAOIs within 14 days", "Insomnia, decreased appetite, nervousness, headache, tachycardia", 15.00, 49.99),
            ("0058-0180-10", "Vyvanse", "Lisdexamfetamine", "Shire", "CNS Stimulant", DrugSchedule.II, DrugRoute.ORAL, DrugForm.CAPSULE, "30mg", "mg", "Prodrug of dextroamphetamine", "ADHD, binge eating disorder", "Advanced arteriosclerosis, cardiovascular disease, MAOIs within 14 days", "Insomnia, decreased appetite, dry mouth, irritability, anxiety", 30.00, 110.00),

            # Antihypertensives
            ("0071-0155-23", "Lisinopril", "Lisinopril", "Merck", "Antihypertensive - ACE Inhibitor", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "10mg", "mg", "Angiotensin-converting enzyme inhibitor", "Hypertension, heart failure, post-MI, diabetic nephropathy", "Pregnancy, angioedema history, bilateral renal artery stenosis", "Dry cough, dizziness, headache, hyperkalemia, angioedema (rare)", 2.00, 8.99),
            ("0006-0951-54", "Losartan", "Losartan", "Merck", "Antihypertensive - ARB", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "50mg", "mg", "Angiotensin II receptor blocker", "Hypertension, diabetic nephropathy, stroke prevention", "Pregnancy, bilateral renal artery stenosis", "Dizziness, hyperkalemia, hypotension, back pain", 3.00, 11.99),
            ("0069-2770-68", "Amlodipine", "Amlodipine", "Pfizer", "Antihypertensive - CCB", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "5mg", "mg", "Calcium channel blocker (dihydropyridine)", "Hypertension, coronary artery disease, angina", "Severe aortic stenosis, cardiogenic shock", "Peripheral edema, dizziness, flushing, headache, fatigue", 2.00, 7.99),
            ("0591-0152-01", "Metoprolol", "Metoprolol Tartrate", "AstraZeneca", "Antihypertensive - Beta Blocker", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "50mg", "mg", "Selective beta-1 adrenergic blocker", "Hypertension, angina, heart failure, post-MI, rate control", "Severe bradycardia, heart block, cardiogenic shock, decompensated HF", "Fatigue, bradycardia, dizziness, depression, cold extremities", 2.50, 9.99),
            ("0781-1506-10", "Hydrochlorothiazide", "Hydrochlorothiazide", "Mylan", "Antihypertensive - Diuretic", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "25mg", "mg", "Thiazide diuretic", "Hypertension, edema, calcium nephrolithiasis prevention", "Anuria, sulfonamide allergy", "Hypokalemia, hyperuricemia, hyperglycemia, dizziness, photosensitivity", 1.50, 5.99),

            # Statins (Cholesterol)
            ("0071-0156-40", "Lipitor", "Atorvastatin", "Pfizer", "Antilipemic - Statin", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "20mg", "mg", "HMG-CoA reductase inhibitor", "Hyperlipidemia, cardiovascular risk reduction, familial hypercholesterolemia", "Active liver disease, pregnancy, nursing", "Myalgia, arthralgia, diarrhea, nasopharyngitis, elevated transaminases", 4.00, 16.99),
            ("0006-0726-61", "Crestor", "Rosuvastatin", "AstraZeneca", "Antilipemic - Statin", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "10mg", "mg", "HMG-CoA reductase inhibitor", "Hyperlipidemia, atherosclerosis slowing, cardiovascular prevention", "Active liver disease, pregnancy, nursing", "Myalgia, headache, abdominal pain, nausea, elevated CK", 5.00, 19.99),

            # Diabetes
            ("0087-6060-05", "Glucophage", "Metformin", "Bristol-Myers Squibb", "Antidiabetic - Biguanide", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "500mg", "mg", "Biguanide antihyperglycemic", "Type 2 diabetes, insulin resistance, PCOS (off-label)", "Renal impairment (eGFR <30), metabolic acidosis, radiologic contrast", "GI upset, diarrhea, nausea, lactic acidosis (rare), B12 deficiency", 2.00, 6.99),
            ("0169-3060-12", "Januvia", "Sitagliptin", "Merck", "Antidiabetic - DPP-4 Inhibitor", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "100mg", "mg", "Dipeptidyl peptidase-4 inhibitor", "Type 2 diabetes (adjunct to diet and exercise)", "Type 1 diabetes, diabetic ketoacidosis", "Nasopharyngitis, headache, pancreatitis (rare), joint pain", 15.00, 55.99),
            ("0310-6205-30", "Jardiance", "Empagliflozin", "Boehringer Ingelheim", "Antidiabetic - SGLT2 Inhibitor", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "10mg", "mg", "Sodium-glucose co-transporter 2 inhibitor", "Type 2 diabetes, heart failure risk reduction, cardiovascular death reduction", "Severe renal impairment, dialysis, type 1 diabetes", "UTI, genital mycotic infections, dehydration, ketoacidosis (rare)", 18.00, 65.99),

            # PPIs (Acid Reflux)
            ("0186-5040-31", "Nexium", "Esomeprazole", "AstraZeneca", "PPI - Proton Pump Inhibitor", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.CAPSULE, "40mg", "mg", "Proton pump inhibitor", "GERD, erosive esophagitis, H. pylori eradication, Zollinger-Ellison syndrome", "Rilpivirine, nelfinavir combination", "Headache, diarrhea, nausea, abdominal pain, B12/Mg deficiency (long-term)", 5.00, 22.99),
            ("0300-3023-13", "Prilosec", "Omeprazole", "AstraZeneca", "PPI - Proton Pump Inhibitor", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.CAPSULE, "20mg", "mg", "Proton pump inhibitor", "GERD, duodenal/gastric ulcers, H. pylori eradication, Zollinger-Ellison", "Rilpivirine combination", "Headache, abdominal pain, diarrhea, nausea, C. diff risk (long-term)", 3.00, 12.99),

            # Pain Management
            ("0406-0123-01", "Tylenol #3", "Acetaminophen/Codeine", "Janssen", "Analgesic - Opioid Combination", DrugSchedule.III, DrugRoute.ORAL, DrugForm.TABLET, "300mg/30mg", "mg", "Acetaminophen with codeine", "Mild to moderate pain", "Respiratory depression, acute/severe asthma, GI obstruction, MAOIs within 14 days", "Drowsiness, constipation, nausea, dizziness, respiratory depression", 6.00, 19.99),
            ("0591-0385-01", "Tramadol", "Tramadol HCl", "Mylan", "Analgesic - Opioid-like", DrugSchedule.IV, DrugRoute.ORAL, DrugForm.TABLET, "50mg", "mg", "Centrally acting synthetic opioid analgesic", "Moderate to moderately severe pain", "Seizure disorders, concurrent MAOIs, acute intoxication, suicidal patients", "Nausea, dizziness, constipation, headache, somnolence, seizure risk", 3.00, 10.99),
            ("0093-0058-01", "Naproxen", "Naproxen", "Bayer", "NSAID", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "500mg", "mg", "Non-steroidal anti-inflammatory drug", "Pain, inflammation, arthritis, dysmenorrhea, gout, tendinitis", "CABG surgery, active GI bleeding, severe renal impairment", "GI upset, nausea, heartburn, edema, increased CV risk", 2.00, 7.99),
            ("0054-8528-25", "Gabapentin", "Gabapentin", "Pfizer", "Anticonvulsant / Neuropathic Pain", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.CAPSULE, "300mg", "mg", "GABA analog anticonvulsant", "Epilepsy (adjunct), postherpetic neuralgia, neuropathic pain, restless legs (off-label)", "Known hypersensitivity", "Dizziness, somnolence, ataxia, fatigue, peripheral edema", 3.00, 11.99),
            ("0591-5502-01", "Pregabalin", "Pregabalin", "Pfizer", "Anticonvulsant / Neuropathic Pain", DrugSchedule.V, DrugRoute.ORAL, DrugForm.CAPSULE, "75mg", "mg", "GABA analog (Lyrica)", "Neuropathic pain, fibromyalgia, epilepsy (adjunct), generalized anxiety (EU)", "Known hypersensitivity", "Dizziness, somnolence, dry mouth, edema, weight gain, blurred vision", 8.00, 35.99),

            # Bronchodilators / Respiratory
            ("0173-0682-20", "Ventolin HFA", "Albuterol", "GlaxoSmithKline", "Bronchodilator - Beta-2 Agonist", DrugSchedule.NONE, DrugRoute.INHALATION, DrugForm.INHALER, "90mcg/actuation", "mcg", "Short-acting beta-2 adrenergic agonist inhaler", "Asthma (rescue), exercise-induced bronchospasm, COPD exacerbation", "Tachyarrhythmia, severe hypertrophic cardiomyopathy", "Tachycardia, tremor, nervousness, headache, throat irritation", 8.00, 35.99),
            ("0085-1336-01", "Symbicort", "Budesonide/Formoterol", "AstraZeneca", "Bronchodilator - ICS/LABA Combination", DrugSchedule.NONE, DrugRoute.INHALATION, DrugForm.INHALER, "160/4.5mcg", "mcg", "Inhaled corticosteroid + long-acting beta agonist", "Asthma maintenance, COPD maintenance", "Status asthmaticus, acute bronchospasm", "Oral candidiasis, headache, nasopharyngitis, URI, dysphonia", 25.00, 95.99),

            # Anticoagulants
            ("0003-0169-21", "Eliquis", "Apixaban", "Bristol-Myers Squibb", "Anticoagulant - Factor Xa Inhibitor", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "5mg", "mg", "Direct factor Xa inhibitor", "DVT/PE treatment and prevention, stroke prevention in atrial fibrillation", "Active pathological bleeding, prosthetic heart valves", "Bleeding, bruising, anemia, nausea, hypersensitivity", 15.00, 55.99),
            ("0597-0136-90", "Xarelto", "Rivaroxaban", "Janssen", "Anticoagulant - Factor Xa Inhibitor", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "20mg", "mg", "Direct factor Xa inhibitor", "DVT/PE treatment, stroke prevention in AFib, ACS, CAD/PAD", "Active pathological bleeding, severe hepatic impairment", "Bleeding, bruising, anemia, back pain, pruritus", 16.00, 58.99),
            ("0056-0173-70", "Warfarin", "Warfarin Sodium", "Bristol-Myers Squibb", "Anticoagulant - Vitamin K Antagonist", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "5mg", "mg", "Vitamin K antagonist anticoagulant", "DVT/PE treatment, stroke prevention in AFib, mechanical valve prophylaxis", "Pregnancy, hemorrhagic tendencies, recent surgery, unsupervised patients", "Bleeding, bruising, purple toes syndrome, skin necrosis (rare)", 2.00, 8.99),

            # Thyroid
            ("0074-6624-90", "Synthroid", "Levothyroxine", "AbbVie", "Thyroid Hormone", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "50mcg", "mcg", "Synthetic thyroid hormone (T4)", "Hypothyroidism, TSH suppression in thyroid cancer, myxedema coma", "Untreated adrenal insufficiency, acute MI (uncorrected thyrotoxicosis)", "Palpitations, weight loss, tremor, anxiety, insomnia, heat intolerance", 3.00, 13.99),

            # Muscle Relaxants
            ("0228-2057-10", "Flexeril", "Cyclobenzaprine", "McNeil", "Muscle Relaxant", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "10mg", "mg", "Centrally acting muscle relaxant", "Acute musculoskeletal pain and spasm (short-term, 2-3 weeks)", "MAOIs within 14 days, hyperthyroidism, CHF, arrhythmias, acute recovery post-MI", "Drowsiness, dry mouth, dizziness, constipation, fatigue", 3.00, 11.99),

            # Antiemetics
            ("0173-0442-00", "Zofran", "Ondansetron", "GlaxoSmithKline", "Antiemetic - 5-HT3 Antagonist", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "4mg", "mg", "Serotonin 5-HT3 receptor antagonist", "Nausea and vomiting (chemotherapy, radiation, post-operative)", "Concomitant apomorphine, congenital long QT syndrome", "Headache, constipation, fatigue, QT prolongation (high doses)", 4.00, 15.99),

            # Sleep Aids
            ("0310-0540-10", "Ambien", "Zolpidem", "Sanofi", "Sedative-Hypnotic", DrugSchedule.IV, DrugRoute.ORAL, DrugForm.TABLET, "10mg", "mg", "Non-benzodiazepine hypnotic (Z-drug)", "Insomnia (short-term treatment)", "Severe hepatic impairment, sleep apnea, myasthenia gravis", "Somnolence, dizziness, diarrhea, complex sleep behaviors, amnesia", 4.00, 14.99),

            # Corticosteroids
            ("0054-4740-25", "Prednisone", "Prednisone", "Roxane Laboratories", "Corticosteroid", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "10mg", "mg", "Systemic corticosteroid", "Inflammatory conditions, autoimmune diseases, asthma exacerbation, allergic reactions, organ transplant", "Systemic fungal infections, live vaccines during high-dose therapy", "Weight gain, insomnia, mood changes, hyperglycemia, osteoporosis, adrenal suppression", 2.00, 6.99),

            # Allergy
            ("0573-0157-20", "Zyrtec", "Cetirizine", "Johnson & Johnson", "Antihistamine - 2nd Generation", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "10mg", "mg", "Second-generation antihistamine", "Seasonal and perennial allergic rhinitis, chronic urticaria", "Severe renal impairment (dose adjustment), hydroxyzine allergy", "Drowsiness, headache, fatigue, dry mouth, pharyngitis", 1.50, 5.99),
            ("0085-1330-01", "Singulair", "Montelukast", "Merck", "Leukotriene Receptor Antagonist", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "10mg", "mg", "Leukotriene receptor antagonist", "Asthma maintenance, allergic rhinitis, exercise-induced bronchoconstriction", "Phenylketonuria (chewable tablets)", "Headache, URI, neuropsychiatric events (boxed warning), abdominal pain", 5.00, 22.99),

            # Erectile Dysfunction
            ("0069-4200-30", "Viagra", "Sildenafil", "Pfizer", "PDE5 Inhibitor", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "50mg", "mg", "Phosphodiesterase type 5 inhibitor", "Erectile dysfunction, pulmonary arterial hypertension (Revatio)", "Nitrate use, riociguat, severe hepatic/cardiovascular disease", "Headache, flushing, dyspepsia, visual disturbance, nasal congestion", 20.00, 70.99),

            # Osteoporosis
            ("0006-0270-31", "Fosamax", "Alendronate", "Merck", "Bisphosphonate", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "70mg", "mg", "Bisphosphonate (weekly dosing)", "Osteoporosis treatment and prevention, Paget's disease", "Esophageal abnormalities, inability to stand/sit upright 30min, hypocalcemia", "Abdominal pain, nausea, esophageal irritation, musculoskeletal pain, osteonecrosis of jaw (rare)", 4.00, 16.99),

            # Antifungal
            ("0093-7171-56", "Diflucan", "Fluconazole", "Pfizer", "Antifungal - Azole", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "150mg", "mg", "Triazole antifungal", "Candidiasis (vaginal, oropharyngeal, esophageal), cryptococcal meningitis, fungal prophylaxis", "Terfenadine, cisapride (QT prolongation risk)", "Nausea, headache, abdominal pain, diarrhea, hepatotoxicity (rare)", 5.00, 18.99),

            # Migraine
            ("0173-0540-00", "Imitrex", "Sumatriptan", "GlaxoSmithKline", "Antimigraine - Triptan", DrugSchedule.NONE, DrugRoute.ORAL, DrugForm.TABLET, "50mg", "mg", "Selective 5-HT1B/1D receptor agonist", "Acute migraine treatment (with or without aura), cluster headache", "Ischemic heart disease, uncontrolled HTN, MAOIs within 14 days, basilar/hemiplegic migraine", "Tingling, flushing, chest tightness, dizziness, drowsiness, injection site reactions", 12.00, 42.99),
        ]

        medications = []
        for md in meds_data:
            is_controlled = md[5] not in (DrugSchedule.NONE,)
            m = Medication(
                ndc_code=md[0], brand_name=md[1], generic_name=md[2],
                manufacturer=md[3], drug_class=md[4], schedule=md[5],
                route=md[6], form=md[7], strength=md[8], unit=md[9],
                description=md[10], indications=md[11],
                contraindications=md[12], side_effects=md[13],
                avg_wholesale_price=md[14], retail_price=md[15],
                is_controlled=is_controlled
            )
            medications.append(m)
        session.add_all(medications)
        session.flush()

        # ── Drug Interactions ──────────────────────────────────────────
        # Build a lookup by brand name for easier reference
        med_by_name = {m.brand_name: m for m in medications}

        interactions_data = [
            ("Xanax", "Ambien", InteractionSeverity.MAJOR, "Combined CNS depression: increased risk of profound sedation, respiratory depression, coma, and death"),
            ("Xanax", "Tramadol", InteractionSeverity.MAJOR, "Combined CNS/respiratory depression risk; may cause fatal respiratory arrest"),
            ("Zoloft", "Tramadol", InteractionSeverity.MAJOR, "Serotonin syndrome risk: agitation, hyperthermia, tachycardia, muscle rigidity"),
            ("Prozac", "Zyprexa", InteractionSeverity.MODERATE, "Fluoxetine inhibits CYP2D6, increasing olanzapine levels and sedation risk"),
            ("Warfarin", "Naproxen", InteractionSeverity.MAJOR, "Greatly increased bleeding risk; NSAIDs impair platelet function and may cause GI bleeding"),
            ("Warfarin", "Diflucan", InteractionSeverity.MAJOR, "Fluconazole inhibits CYP2C9, significantly increasing warfarin levels and bleeding risk"),
            ("Lisinopril", "Losartan", InteractionSeverity.MAJOR, "Dual RAAS blockade: hyperkalemia, hypotension, and renal failure risk"),
            ("Metoprolol", "Amlodipine", InteractionSeverity.MODERATE, "Additive hypotension and bradycardia; monitor heart rate and blood pressure closely"),
            ("Lexapro", "Imitrex", InteractionSeverity.MODERATE, "Potential serotonin syndrome risk with combined serotonergic agents"),
            ("Effexor XR", "Tramadol", InteractionSeverity.MAJOR, "Serotonin syndrome risk; both drugs increase serotonin. Seizure threshold also lowered"),
            ("Lithium", "Lisinopril", InteractionSeverity.MAJOR, "ACE inhibitors reduce lithium clearance, causing potentially toxic lithium levels"),
            ("Lithium", "Naproxen", InteractionSeverity.MAJOR, "NSAIDs reduce lithium clearance by 20-30%, risk of lithium toxicity"),
            ("Eliquis", "Naproxen", InteractionSeverity.MAJOR, "Increased bleeding risk; avoid concurrent NSAID use with anticoagulants"),
            ("Xarelto", "Naproxen", InteractionSeverity.MAJOR, "Increased bleeding risk; NSAIDs potentiate anticoagulant-related hemorrhage"),
            ("Prozac", "Adderall XR", InteractionSeverity.MODERATE, "Fluoxetine inhibits CYP2D6, may increase amphetamine levels; serotonin syndrome risk"),
            ("Klonopin", "Ambien", InteractionSeverity.MAJOR, "Excessive CNS depression; combined use may cause profound sedation and respiratory failure"),
            ("Adderall XR", "Xanax", InteractionSeverity.MODERATE, "Pharmacologic antagonism; stimulants and benzodiazepines have opposing effects, masking impairment"),
            ("Viagra", "Amlodipine", InteractionSeverity.MODERATE, "Additive hypotensive effects; may cause symptomatic blood pressure drops"),
            ("Wellbutrin XL", "Adderall XR", InteractionSeverity.MODERATE, "Bupropion lowers seizure threshold; combined stimulant effect may increase seizure and cardiovascular risk"),
            ("Depakote", "Lamictal", InteractionSeverity.MAJOR, "Valproate doubles lamotrigine levels; greatly increased risk of serious rash including Stevens-Johnson syndrome"),
            ("Synthroid", "Prilosec", InteractionSeverity.MODERATE, "PPIs may reduce levothyroxine absorption, requiring dose adjustment and TSH monitoring"),
            ("Seroquel", "Klonopin", InteractionSeverity.MODERATE, "Additive CNS depression; enhanced sedation, dizziness, and psychomotor impairment"),
            ("Zoloft", "Xanax", InteractionSeverity.MODERATE, "Sertraline inhibits CYP3A4, may increase alprazolam levels; enhanced sedation"),
            ("Lipitor", "Diflucan", InteractionSeverity.MAJOR, "Fluconazole inhibits CYP3A4, significantly increasing statin levels and rhabdomyolysis risk"),
        ]
        for ia_name, ib_name, sev, desc in interactions_data:
            ma = med_by_name.get(ia_name)
            mb = med_by_name.get(ib_name)
            if ma and mb:
                session.add(MedicationInteraction(
                    medication_a_id=ma.id, medication_b_id=mb.id,
                    severity=sev, description=desc
                ))
        session.flush()

        # ── Allergies ──────────────────────────────────────────────────
        allergies_data = [
            (patients[0].id, "Penicillin", "Hives, rash", AllergySeverity.MODERATE),
            (patients[0].id, "Sulfa drugs", "Difficulty breathing", AllergySeverity.SEVERE),
            (patients[2].id, "Aspirin", "GI bleeding", AllergySeverity.SEVERE),
            (patients[3].id, "Codeine", "Nausea, vomiting", AllergySeverity.MILD),
            (patients[4].id, "Latex", "Contact dermatitis", AllergySeverity.MODERATE),
            (patients[5].id, "Iodine contrast", "Anaphylaxis", AllergySeverity.LIFE_THREATENING),
            (patients[7].id, "NSAIDs", "Bronchospasm", AllergySeverity.SEVERE),
            (patients[8].id, "Morphine", "Itching, hives", AllergySeverity.MODERATE),
            (patients[10].id, "Erythromycin", "Rash", AllergySeverity.MILD),
            (patients[12].id, "Tetracycline", "Photosensitivity", AllergySeverity.MILD),
        ]
        for al in allergies_data:
            session.add(Allergy(patient_id=al[0], allergen=al[1], reaction=al[2], severity=al[3]))
        session.flush()

        # ── Vitals ─────────────────────────────────────────────────────
        for i, p in enumerate(patients[:10]):
            for days_ago in [0, 7, 30, 90]:
                session.add(Vital(
                    patient_id=p.id, recorded_by_id=users[0].id,
                    bp_systolic=random.randint(110, 145),
                    bp_diastolic=random.randint(65, 95),
                    heart_rate=random.randint(60, 100),
                    temperature=round(random.uniform(97.0, 99.5), 1),
                    respiratory_rate=random.randint(12, 20),
                    oxygen_saturation=round(random.uniform(95.0, 100.0), 1),
                    weight=round(random.uniform(120, 220), 1),
                    height=round(random.uniform(155, 190), 1),
                    recorded_at=datetime.utcnow() - timedelta(days=days_ago)
                ))
        session.flush()

        # ── Diagnoses ──────────────────────────────────────────────────
        diagnoses_data = [
            (patients[0].id, users[0].id, "J06.9", "Acute upper respiratory infection", DiagnosisStatus.RESOLVED),
            (patients[0].id, users[0].id, "I10", "Essential hypertension", DiagnosisStatus.CHRONIC),
            (patients[1].id, users[2].id, "F32.1", "Major depressive disorder, single episode, moderate", DiagnosisStatus.ACTIVE),
            (patients[1].id, users[0].id, "K21.0", "GERD with esophagitis", DiagnosisStatus.ACTIVE),
            (patients[2].id, users[2].id, "F41.1", "Generalized anxiety disorder", DiagnosisStatus.ACTIVE),
            (patients[2].id, users[0].id, "M54.5", "Low back pain", DiagnosisStatus.ACTIVE),
            (patients[3].id, users[0].id, "E11.9", "Type 2 diabetes mellitus without complications", DiagnosisStatus.CHRONIC),
            (patients[3].id, users[0].id, "E78.5", "Hyperlipidemia, unspecified", DiagnosisStatus.CHRONIC),
            (patients[4].id, users[2].id, "F90.0", "ADHD, predominantly inattentive type", DiagnosisStatus.ACTIVE),
            (patients[5].id, users[0].id, "J45.20", "Mild intermittent asthma, uncomplicated", DiagnosisStatus.CHRONIC),
            (patients[5].id, users[0].id, "I10", "Essential hypertension", DiagnosisStatus.CHRONIC),
            (patients[6].id, users[2].id, "F31.9", "Bipolar disorder, unspecified", DiagnosisStatus.CHRONIC),
            (patients[7].id, users[0].id, "I48.91", "Atrial fibrillation, unspecified", DiagnosisStatus.CHRONIC),
            (patients[7].id, users[0].id, "E03.9", "Hypothyroidism, unspecified", DiagnosisStatus.CHRONIC),
            (patients[8].id, users[0].id, "M79.3", "Panniculitis / fibromyalgia", DiagnosisStatus.CHRONIC),
            (patients[9].id, users[0].id, "G43.909", "Migraine, unspecified", DiagnosisStatus.ACTIVE),
        ]
        diagnoses = []
        for dd in diagnoses_data:
            dx = Diagnosis(
                patient_id=dd[0], diagnosed_by_id=dd[1], icd10_code=dd[2],
                description=dd[3], status=dd[4],
                diagnosis_date=date.today() - timedelta(days=random.randint(30, 365))
            )
            diagnoses.append(dx)
            session.add(dx)
        session.flush()

        # ── Prescriptions ─────────────────────────────────────────────
        lisinopril = med_by_name["Lisinopril"]
        zoloft = med_by_name["Zoloft"]
        nexium = med_by_name["Nexium"]
        lexapro = med_by_name["Lexapro"]
        gabapentin = med_by_name["Gabapentin"]
        metformin = med_by_name["Glucophage"]
        lipitor = med_by_name["Lipitor"]
        adderall = med_by_name["Adderall XR"]
        ventolin = med_by_name["Ventolin HFA"]
        lamictal = med_by_name["Lamictal"]
        eliquis = med_by_name["Eliquis"]
        synthroid = med_by_name["Synthroid"]
        pregabalin = med_by_name["Pregabalin"]
        imitrex = med_by_name["Imitrex"]
        metoprolol = med_by_name["Metoprolol"]

        prescriptions_data = [
            # Patient 0 - Hypertension
            (patients[0].id, users[0].id, "RX-00000001", PrescriptionStatus.ACTIVE, diagnoses[1].id,
             [(lisinopril.id, "10mg", "Once daily", "Ongoing", 90, 3, "Take in the morning with water")]),
            # Patient 1 - Depression + GERD
            (patients[1].id, users[2].id, "RX-00000002", PrescriptionStatus.ACTIVE, diagnoses[2].id,
             [(zoloft.id, "50mg", "Once daily", "6 months", 30, 5, "Take in the morning with food")]),
            (patients[1].id, users[0].id, "RX-00000003", PrescriptionStatus.ACTIVE, diagnoses[3].id,
             [(nexium.id, "40mg", "Once daily", "3 months", 30, 2, "Take 30 minutes before breakfast")]),
            # Patient 2 - Anxiety + Back pain
            (patients[2].id, users[2].id, "RX-00000004", PrescriptionStatus.ACTIVE, diagnoses[4].id,
             [(lexapro.id, "10mg", "Once daily", "6 months", 30, 5, "Take at the same time each day")]),
            (patients[2].id, users[0].id, "RX-00000005", PrescriptionStatus.ACTIVE, diagnoses[5].id,
             [(gabapentin.id, "300mg", "Three times daily", "3 months", 90, 2, "Take with or without food; do not stop abruptly")]),
            # Patient 3 - Diabetes + Hyperlipidemia
            (patients[3].id, users[0].id, "RX-00000006", PrescriptionStatus.ACTIVE, diagnoses[6].id,
             [(metformin.id, "500mg", "Twice daily", "Ongoing", 60, 5, "Take with meals to reduce GI side effects"),
              (lipitor.id, "20mg", "Once daily at bedtime", "Ongoing", 30, 5, "Take in the evening; avoid grapefruit")]),
            # Patient 4 - ADHD
            (patients[4].id, users[2].id, "RX-00000007", PrescriptionStatus.ACTIVE, diagnoses[8].id,
             [(adderall.id, "20mg", "Once daily in the morning", "Ongoing", 30, 0, "Take early in the morning; avoid afternoon dosing to prevent insomnia")]),
            # Patient 5 - Asthma + HTN
            (patients[5].id, users[0].id, "RX-00000008", PrescriptionStatus.ACTIVE, diagnoses[9].id,
             [(ventolin.id, "90mcg", "2 puffs every 4-6 hours PRN", "Ongoing", 1, 5, "Shake well before use; rinse mouth after"),
              (metoprolol.id, "50mg", "Twice daily", "Ongoing", 60, 5, "Do not stop abruptly; take with food")]),
            # Patient 6 - Bipolar
            (patients[6].id, users[2].id, "RX-00000009", PrescriptionStatus.ACTIVE, diagnoses[11].id,
             [(lamictal.id, "100mg", "Once daily", "Ongoing", 30, 5, "Report any rash immediately; titrate per schedule")]),
            # Patient 7 - AFib + Hypothyroid
            (patients[7].id, users[0].id, "RX-00000010", PrescriptionStatus.ACTIVE, diagnoses[12].id,
             [(eliquis.id, "5mg", "Twice daily", "Ongoing", 60, 5, "Take at the same times each day; do not skip doses"),
              (synthroid.id, "50mcg", "Once daily on empty stomach", "Ongoing", 30, 5, "Take 30-60 min before breakfast; avoid calcium/iron within 4 hours")]),
            # Patient 8 - Fibromyalgia
            (patients[8].id, users[0].id, "RX-00000011", PrescriptionStatus.ACTIVE, diagnoses[14].id,
             [(pregabalin.id, "75mg", "Twice daily", "3 months", 60, 3, "May cause dizziness; avoid driving until effects are known")]),
            # Patient 9 - Migraine
            (patients[9].id, users[0].id, "RX-00000012", PrescriptionStatus.ACTIVE, diagnoses[15].id,
             [(imitrex.id, "50mg", "As needed at onset of migraine", "6 months", 9, 2, "Take at first sign of migraine; max 2 doses in 24 hours")]),
        ]

        for rx_data in prescriptions_data:
            rx = Prescription(
                patient_id=rx_data[0], prescriber_id=rx_data[1],
                rx_number=rx_data[2], status=rx_data[3],
                diagnosis_id=rx_data[4], prescribed_date=date.today() - timedelta(days=random.randint(5, 60)),
                expiry_date=date.today() + timedelta(days=300)
            )
            session.add(rx)
            session.flush()
            for item in rx_data[5]:
                med = session.get(Medication, item[0])
                unit_price = float(med.retail_price) if med else 0
                pi = PrescriptionItem(
                    prescription_id=rx.id, medication_id=item[0],
                    dosage=item[1], frequency=item[2], duration=item[3],
                    quantity=item[4], refills_allowed=item[5],
                    instructions=item[6], unit_price=unit_price,
                    total_price=unit_price * item[4]
                )
                session.add(pi)
        session.flush()

        # ── Medical Records ────────────────────────────────────────────
        records_data = [
            (patients[0].id, users[0].id, RecordType.VISIT_NOTE, "Annual Physical Exam",
             "Patient presents for annual physical. BP 138/88, slightly elevated. Started on Lisinopril 10mg daily. Labs ordered: CBC, CMP, Lipid panel, HbA1c. Follow up in 3 months."),
            (patients[0].id, users[0].id, RecordType.LAB_RESULT, "Comprehensive Metabolic Panel",
             "Glucose: 95 mg/dL (normal)\nBUN: 18 mg/dL (normal)\nCreatinine: 1.0 mg/dL (normal)\neGFR: >60\nSodium: 140 mEq/L\nPotassium: 4.2 mEq/L\nChloride: 101 mEq/L\nCO2: 25 mEq/L\nCalcium: 9.5 mg/dL\nTotal Protein: 7.2 g/dL\nAlbumin: 4.1 g/dL\nBilirubin: 0.8 mg/dL\nAlk Phos: 72 U/L\nAST: 25 U/L\nALT: 30 U/L"),
            (patients[1].id, users[2].id, RecordType.VISIT_NOTE, "Psychiatric Evaluation",
             "Patient reports persistent low mood, decreased interest in activities, difficulty concentrating, and disrupted sleep for the past 3 months. PHQ-9 score: 14 (moderate depression). No suicidal ideation. Started Sertraline 50mg daily. Therapy referral provided. Follow up in 4 weeks."),
            (patients[2].id, users[2].id, RecordType.VISIT_NOTE, "Anxiety Follow-up",
             "Patient reports ongoing generalized anxiety with physical symptoms (muscle tension, restlessness, difficulty sleeping). GAD-7 score: 12 (moderate). Current Escitalopram 10mg providing some relief. Will continue current medication. CBT recommended."),
            (patients[3].id, users[0].id, RecordType.LAB_RESULT, "HbA1c and Lipid Panel",
             "HbA1c: 7.2% (target <7%)\nTotal Cholesterol: 245 mg/dL (high)\nLDL: 158 mg/dL (high)\nHDL: 42 mg/dL (low)\nTriglycerides: 225 mg/dL (high)\nStarting Atorvastatin 20mg. Reinforcing dietary modifications."),
            (patients[4].id, users[2].id, RecordType.VISIT_NOTE, "ADHD Assessment",
             "Adult ADHD comprehensive evaluation completed. Connors Adult ADHD Rating Scale indicates clinically significant inattention (T-score 72). Minimal hyperactivity. Started Adderall XR 20mg daily. Monitor BP and weight. Follow up in 2 weeks."),
            (patients[7].id, users[0].id, RecordType.IMAGING, "Echocardiogram Report",
             "Findings: Left atrial enlargement (mild). Normal LV size and function. LVEF 55-60%. No valvular abnormalities. No pericardial effusion. Mild tricuspid regurgitation. Consistent with atrial fibrillation."),
            (patients[8].id, users[0].id, RecordType.REFERRAL, "Rheumatology Referral",
             "Referring patient for rheumatology evaluation for persistent widespread pain consistent with fibromyalgia. Current management: Pregabalin 75mg BID. Request evaluation for additional treatment options."),
        ]
        for rd in records_data:
            session.add(MedicalRecord(
                patient_id=rd[0], provider_id=rd[1], record_type=rd[2],
                title=rd[3], content=rd[4],
                record_date=date.today() - timedelta(days=random.randint(5, 90))
            ))
        session.flush()

        # ── Appointments ───────────────────────────────────────────────
        now = datetime.utcnow()
        today = date.today()
        appts_data = [
            (patients[0].id, users[0].id, AppointmentType.FOLLOW_UP, now.replace(hour=9, minute=0) + timedelta(days=1), 30, AppointmentStatus.SCHEDULED, "BP follow-up"),
            (patients[1].id, users[2].id, AppointmentType.FOLLOW_UP, now.replace(hour=10, minute=0) + timedelta(days=1), 45, AppointmentStatus.SCHEDULED, "Depression follow-up"),
            (patients[2].id, users[2].id, AppointmentType.PSYCHIATRIC_EVAL, now.replace(hour=14, minute=0) + timedelta(days=2), 60, AppointmentStatus.SCHEDULED, "Anxiety assessment"),
            (patients[3].id, users[0].id, AppointmentType.MEDICATION_REVIEW, now.replace(hour=11, minute=0) + timedelta(days=3), 30, AppointmentStatus.SCHEDULED, "Diabetes medication review"),
            (patients[4].id, users[2].id, AppointmentType.FOLLOW_UP, now.replace(hour=9, minute=30) + timedelta(days=4), 30, AppointmentStatus.SCHEDULED, "ADHD medication check"),
            (patients[5].id, users[0].id, AppointmentType.CONSULTATION, now.replace(hour=15, minute=0) + timedelta(days=5), 30, AppointmentStatus.SCHEDULED, "Asthma management"),
            (patients[6].id, users[2].id, AppointmentType.MEDICATION_REVIEW, now.replace(hour=13, minute=0) + timedelta(days=6), 45, AppointmentStatus.SCHEDULED, "Bipolar medication review"),
            # Past appointments
            (patients[0].id, users[0].id, AppointmentType.CONSULTATION, now.replace(hour=9, minute=0) - timedelta(days=30), 30, AppointmentStatus.COMPLETED, "Initial consultation"),
            (patients[1].id, users[2].id, AppointmentType.PSYCHIATRIC_EVAL, now.replace(hour=10, minute=0) - timedelta(days=25), 60, AppointmentStatus.COMPLETED, "Initial psychiatric evaluation"),
            (patients[3].id, users[0].id, AppointmentType.CONSULTATION, now.replace(hour=14, minute=0) - timedelta(days=60), 30, AppointmentStatus.COMPLETED, "Diabetes diagnosis"),
            (patients[7].id, users[0].id, AppointmentType.FOLLOW_UP, now.replace(hour=11, minute=0) - timedelta(days=14), 30, AppointmentStatus.COMPLETED, "AFib follow-up"),
            (patients[9].id, users[0].id, AppointmentType.CONSULTATION, now.replace(hour=16, minute=0) - timedelta(days=7), 30, AppointmentStatus.COMPLETED, "Migraine evaluation"),
        ]
        for ad in appts_data:
            session.add(Appointment(
                patient_id=ad[0], provider_id=ad[1], appointment_type=ad[2],
                scheduled_datetime=ad[3], duration_minutes=ad[4],
                status=ad[5], reason=ad[6]
            ))
        session.flush()

        # ── Invoices & Payments ────────────────────────────────────────
        invoices_data = [
            (patients[0].id, "INV-00000001", 150.00 + 8.99, InvoiceStatus.PAID, 158.99,
             [("Medical Consultation - Follow-up", "99213", 150.00), ("Lisinopril 10mg (90ct)", "RX", 8.99)]),
            (patients[1].id, "INV-00000002", 200.00 + 14.99 + 22.99, InvoiceStatus.SENT, 0,
             [("Psychiatric Evaluation", "99214", 200.00), ("Sertraline 50mg (30ct)", "RX", 14.99), ("Esomeprazole 40mg (30ct)", "RX", 22.99)]),
            (patients[2].id, "INV-00000003", 200.00 + 19.99, InvoiceStatus.PARTIAL, 100.00,
             [("Psychiatric Consultation", "99214", 200.00), ("Escitalopram 10mg (30ct)", "RX", 19.99)]),
            (patients[3].id, "INV-00000004", 150.00 + 6.99 + 16.99, InvoiceStatus.PAID, 173.98,
             [("Medical Consultation", "99213", 150.00), ("Metformin 500mg (60ct)", "RX", 6.99), ("Atorvastatin 20mg (30ct)", "RX", 16.99)]),
            (patients[4].id, "INV-00000005", 250.00 + 89.99, InvoiceStatus.OVERDUE, 0,
             [("Psychiatric Evaluation - ADHD", "99215", 250.00), ("Adderall XR 20mg (30ct)", "RX", 89.99)]),
            (patients[5].id, "INV-00000006", 150.00 + 35.99 + 9.99, InvoiceStatus.SENT, 0,
             [("Medical Consultation", "99213", 150.00), ("Albuterol Inhaler", "RX", 35.99), ("Metoprolol 50mg (60ct)", "RX", 9.99)]),
            (patients[6].id, "INV-00000007", 200.00 + 22.99, InvoiceStatus.PAID, 222.99,
             [("Psychiatric Evaluation", "99214", 200.00), ("Lamotrigine 100mg (30ct)", "RX", 22.99)]),
            (patients[7].id, "INV-00000008", 150.00 + 55.99 + 13.99, InvoiceStatus.PARTIAL, 100.00,
             [("Medical Consultation", "99213", 150.00), ("Apixaban 5mg (60ct)", "RX", 55.99), ("Levothyroxine 50mcg (30ct)", "RX", 13.99)]),
        ]

        for inv_data in invoices_data:
            subtotal = sum(item[2] for item in inv_data[5])
            inv = Invoice(
                patient_id=inv_data[0], invoice_number=inv_data[1],
                invoice_date=date.today() - timedelta(days=random.randint(10, 45)),
                due_date=date.today() + timedelta(days=random.randint(-10, 20)),
                subtotal=subtotal, tax=0, total_amount=subtotal,
                amount_paid=inv_data[4],
                balance_due=subtotal - inv_data[4],
                status=inv_data[3]
            )
            session.add(inv)
            session.flush()
            for item in inv_data[5]:
                session.add(InvoiceItem(
                    invoice_id=inv.id, description=item[0],
                    service_code=item[1], quantity=1,
                    unit_price=item[2], total_price=item[2]
                ))

            if inv_data[4] > 0:
                session.add(Payment(
                    invoice_id=inv.id, amount=inv_data[4],
                    payment_method=PaymentMethod.CREDIT_CARD,
                    transaction_reference=f"TXN-{inv_data[1][-8:]}",
                    status=PaymentStatus.COMPLETED
                ))
        session.flush()

        # ── Audit Log ──────────────────────────────────────────────────
        audit_entries = [
            (users[0].id, "Patient Created", "Patient", patients[0].id),
            (users[0].id, "Prescription Created", "Prescription", 1),
            (users[2].id, "Psychiatric Evaluation", "MedicalRecord", 3),
            (users[0].id, "Invoice Generated", "Invoice", 1),
            (users[0].id, "Payment Recorded", "Payment", 1),
            (users[2].id, "Prescription Created", "Prescription", 2),
            (users[0].id, "Vitals Recorded", "Vital", 1),
            (users[0].id, "Diagnosis Added", "Diagnosis", 1),
        ]
        for ae in audit_entries:
            session.add(AuditLog(
                user_id=ae[0], action=ae[1], entity_type=ae[2], entity_id=ae[3],
                timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 720))
            ))
        session.flush()

    print("Database seeded successfully with sample data.")
