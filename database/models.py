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
MedPharm ERP - SQLAlchemy Database Models
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, Date, DateTime,
    ForeignKey, Enum, Index, UniqueConstraint, Numeric
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


# ── Enums ──────────────────────────────────────────────────────────────────────

class UserRole(enum.Enum):
    DOCTOR = "doctor"
    PSYCHIATRIST = "psychiatrist"
    PHARMACIST = "pharmacist"
    ADMIN = "admin"


class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class BloodType(enum.Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"


class DrugSchedule(enum.Enum):
    NONE = "none"
    II = "II"
    III = "III"
    IV = "IV"
    V = "V"


class DrugForm(enum.Enum):
    TABLET = "tablet"
    CAPSULE = "capsule"
    LIQUID = "liquid"
    INJECTION = "injection"
    TOPICAL = "topical"
    INHALER = "inhaler"
    PATCH = "patch"
    CREAM = "cream"
    DROPS = "drops"
    SUPPOSITORY = "suppository"


class DrugRoute(enum.Enum):
    ORAL = "oral"
    INTRAVENOUS = "intravenous"
    INTRAMUSCULAR = "intramuscular"
    SUBCUTANEOUS = "subcutaneous"
    TOPICAL = "topical"
    INHALATION = "inhalation"
    RECTAL = "rectal"
    OPHTHALMIC = "ophthalmic"
    OTIC = "otic"
    TRANSDERMAL = "transdermal"
    SUBLINGUAL = "sublingual"


class InteractionSeverity(enum.Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"


class AllergySeverity(enum.Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"


class DiagnosisStatus(enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    CHRONIC = "chronic"


class RecordType(enum.Enum):
    VISIT_NOTE = "visit_note"
    LAB_RESULT = "lab_result"
    IMAGING = "imaging"
    PROCEDURE = "procedure"
    REFERRAL = "referral"
    OTHER = "other"


class PrescriptionStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    FILLED = "filled"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class AppointmentType(enum.Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    PROCEDURE = "procedure"
    PSYCHIATRIC_EVAL = "psychiatric_eval"
    MEDICATION_REVIEW = "medication_review"


class AppointmentStatus(enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class InvoiceStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(enum.Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    INSURANCE = "insurance"
    CHECK = "check"
    ONLINE = "online"


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class CoverageType(enum.Enum):
    HMO = "HMO"
    PPO = "PPO"
    EPO = "EPO"
    POS = "POS"
    MEDICAID = "Medicaid"
    MEDICARE = "Medicare"
    OTHER = "Other"


# ── Models ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    phone = Column(String(20))
    license_number = Column(String(50))
    specialization = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    vitals_recorded = relationship("Vital", back_populates="recorded_by")
    diagnoses_made = relationship("Diagnosis", back_populates="diagnosed_by")
    medical_records = relationship("MedicalRecord", back_populates="provider")
    prescriptions_written = relationship("Prescription", back_populates="prescriber")
    appointments = relationship("Appointment", back_populates="provider")
    audit_logs = relationship("AuditLog", back_populates="user")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def display_title(self):
        if self.role in (UserRole.DOCTOR, UserRole.PSYCHIATRIST):
            return f"Dr. {self.last_name}"
        return self.full_name


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=False)
    gender = Column(Enum(Gender))
    ssn_last4 = Column(String(4))
    email = Column(String(200))
    phone = Column(String(20))
    address = Column(String(300))
    city = Column(String(100))
    state = Column(String(2))
    zip_code = Column(String(10))
    emergency_contact_name = Column(String(200))
    emergency_contact_phone = Column(String(20))
    blood_type = Column(Enum(BloodType))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_patients_name", "last_name", "first_name"),
    )

    # Relationships
    portal_account = relationship("PatientPortalAccount", back_populates="patient", uselist=False)
    insurance_records = relationship("Insurance", back_populates="patient")
    allergies = relationship("Allergy", back_populates="patient")
    vitals = relationship("Vital", back_populates="patient", order_by="desc(Vital.recorded_at)")
    diagnoses = relationship("Diagnosis", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")
    invoices = relationship("Invoice", back_populates="patient")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))


class PatientPortalAccount(Base):
    __tablename__ = "patient_portal_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, unique=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    email = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="portal_account")
    payments = relationship("Payment", back_populates="portal_account")


class Insurance(Base):
    __tablename__ = "insurance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_name = Column(String(200), nullable=False)
    policy_number = Column(String(50), nullable=False)
    group_number = Column(String(50))
    subscriber_name = Column(String(200))
    subscriber_dob = Column(Date)
    copay_amount = Column(Numeric(10, 2), default=0)
    coverage_type = Column(Enum(CoverageType))
    effective_date = Column(Date)
    expiry_date = Column(Date)
    is_active = Column(Boolean, default=True)

    patient = relationship("Patient", back_populates="insurance_records")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ndc_code = Column(String(20), unique=True, index=True)
    brand_name = Column(String(200), nullable=False)
    generic_name = Column(String(200), nullable=False, index=True)
    manufacturer = Column(String(200))
    drug_class = Column(String(200), nullable=False, index=True)
    schedule = Column(Enum(DrugSchedule), default=DrugSchedule.NONE)
    route = Column(Enum(DrugRoute), default=DrugRoute.ORAL)
    form = Column(Enum(DrugForm), default=DrugForm.TABLET)
    strength = Column(String(50))
    unit = Column(String(20))
    description = Column(Text)
    indications = Column(Text)
    contraindications = Column(Text)
    side_effects = Column(Text)
    avg_wholesale_price = Column(Numeric(10, 2))
    retail_price = Column(Numeric(10, 2))
    last_price_update = Column(DateTime, default=datetime.utcnow)
    is_controlled = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    interactions_as_a = relationship("MedicationInteraction", foreign_keys="MedicationInteraction.medication_a_id", back_populates="medication_a")
    interactions_as_b = relationship("MedicationInteraction", foreign_keys="MedicationInteraction.medication_b_id", back_populates="medication_b")
    prescription_items = relationship("PrescriptionItem", back_populates="medication")


class MedicationInteraction(Base):
    __tablename__ = "medication_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    medication_a_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    medication_b_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    severity = Column(Enum(InteractionSeverity), nullable=False)
    description = Column(Text)

    medication_a = relationship("Medication", foreign_keys=[medication_a_id], back_populates="interactions_as_a")
    medication_b = relationship("Medication", foreign_keys=[medication_b_id], back_populates="interactions_as_b")

    __table_args__ = (
        UniqueConstraint("medication_a_id", "medication_b_id", name="uq_interaction_pair"),
    )


class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    allergen = Column(String(200), nullable=False)
    reaction = Column(String(300))
    severity = Column(Enum(AllergySeverity), default=AllergySeverity.MILD)
    noted_date = Column(Date, default=date.today)

    patient = relationship("Patient", back_populates="allergies")


class Vital(Base):
    __tablename__ = "vitals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bp_systolic = Column(Integer)
    bp_diastolic = Column(Integer)
    heart_rate = Column(Integer)
    temperature = Column(Numeric(5, 1))
    respiratory_rate = Column(Integer)
    oxygen_saturation = Column(Numeric(5, 1))
    weight = Column(Numeric(6, 1))
    height = Column(Numeric(5, 1))
    bmi = Column(Numeric(5, 1))
    recorded_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="vitals")
    recorded_by = relationship("User", back_populates="vitals_recorded")


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    diagnosed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    icd10_code = Column(String(10), index=True)
    description = Column(String(500), nullable=False)
    diagnosis_date = Column(Date, default=date.today)
    status = Column(Enum(DiagnosisStatus), default=DiagnosisStatus.ACTIVE)
    notes = Column(Text)

    patient = relationship("Patient", back_populates="diagnoses")
    diagnosed_by = relationship("User", back_populates="diagnoses_made")
    prescriptions = relationship("Prescription", back_populates="diagnosis")


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    record_type = Column(Enum(RecordType), nullable=False)
    title = Column(String(300), nullable=False)
    content = Column(Text)
    attachments_json = Column(Text)
    record_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="medical_records")
    provider = relationship("User", back_populates="medical_records")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prescriber_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rx_number = Column(String(20), unique=True, nullable=False, index=True)
    status = Column(Enum(PrescriptionStatus), default=PrescriptionStatus.PENDING)
    diagnosis_id = Column(Integer, ForeignKey("diagnoses.id"), nullable=True)
    notes = Column(Text)
    prescribed_date = Column(Date, default=date.today)
    expiry_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="prescriptions")
    prescriber = relationship("User", back_populates="prescriptions_written")
    diagnosis = relationship("Diagnosis", back_populates="prescriptions")
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    duration = Column(String(100))
    quantity = Column(Integer, default=1)
    refills_allowed = Column(Integer, default=0)
    refills_used = Column(Integer, default=0)
    instructions = Column(Text)
    is_substitution_allowed = Column(Boolean, default=True)
    unit_price = Column(Numeric(10, 2))
    total_price = Column(Numeric(10, 2))

    prescription = relationship("Prescription", back_populates="items")
    medication = relationship("Medication", back_populates="prescription_items")
    invoice_items = relationship("InvoiceItem", back_populates="prescription_item")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_type = Column(Enum(AppointmentType), default=AppointmentType.CONSULTATION)
    scheduled_datetime = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    reason = Column(String(500))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="appointments")
    provider = relationship("User", back_populates="appointments")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    invoice_number = Column(String(20), unique=True, nullable=False, index=True)
    invoice_date = Column(Date, default=date.today)
    due_date = Column(Date)
    subtotal = Column(Numeric(10, 2), default=0)
    tax = Column(Numeric(10, 2), default=0)
    discount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), default=0)
    amount_paid = Column(Numeric(10, 2), default=0)
    balance_due = Column(Numeric(10, 2), default=0)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(String(500), nullable=False)
    service_code = Column(String(20))
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    prescription_item_id = Column(Integer, ForeignKey("prescription_items.id"), nullable=True)

    invoice = relationship("Invoice", back_populates="items")
    prescription_item = relationship("PrescriptionItem", back_populates="invoice_items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    portal_account_id = Column(Integer, ForeignKey("patient_portal_accounts.id"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    transaction_reference = Column(String(100))
    payment_date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    notes = Column(Text)

    invoice = relationship("Invoice", back_populates="payments")
    portal_account = relationship("PatientPortalAccount", back_populates="payments")


class InsuranceClaimStatus(enum.Enum):
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    DENIED = "denied"
    APPEALED = "appealed"
    PAID = "paid"


class SymptomSeverity(enum.Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    insurance_id = Column(Integer, ForeignKey("insurance.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    claim_number = Column(String(30), unique=True, nullable=False, index=True)
    status = Column(Enum(InsuranceClaimStatus), default=InsuranceClaimStatus.SUBMITTED)
    submitted_date = Column(Date, default=date.today)
    response_date = Column(Date, nullable=True)
    claimed_amount = Column(Numeric(10, 2), nullable=False)
    approved_amount = Column(Numeric(10, 2), default=0)
    copay_amount = Column(Numeric(10, 2), default=0)
    deductible_applied = Column(Numeric(10, 2), default=0)
    denial_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", backref="insurance_claims")
    insurance = relationship("Insurance", backref="claims")
    patient = relationship("Patient", backref="insurance_claims")


class Symptom(Base):
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text)
    body_system = Column(String(100), index=True)
    icd10_codes = Column(Text)
    common_conditions = Column(Text)
    is_emergency = Column(Boolean, default=False)


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False, index=True)
    icd10_code = Column(String(10), index=True)
    category = Column(String(100), index=True)
    description = Column(Text)
    common_symptoms = Column(Text)
    typical_medications = Column(Text)
    prevalence = Column(String(50))
    is_chronic = Column(Boolean, default=False)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    details_json = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(300))
    prev_hash = Column(String(64))
    row_hash = Column(String(64), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")


# ── HIPAA: PHI access log (§ 164.312(b)) ──────────────────────────────────────

class PHIAccessLog(Base):
    """
    Dedicated log of every read against PHI. Writes go to AuditLog; this
    captures the addressable "record read" audit requirement with enough
    detail to satisfy audit controls and accounting-of-disclosures queries.
    """
    __tablename__ = "phi_access_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(Integer, nullable=True, index=True)
    actor_type = Column(String(20), nullable=False, default="staff")  # staff|patient|system
    entity_type = Column(String(50), nullable=False, index=True)       # patient, prescription, ...
    entity_id = Column(Integer, index=True)
    reason = Column(String(40), nullable=False, default="treatment")
    endpoint = Column(String(200))
    method = Column(String(10))
    ip_address = Column(String(45))
    user_agent = Column(String(300))
    duration_ms = Column(Integer)
    accessed_at = Column(DateTime, default=datetime.utcnow, index=True)


class FailedLogin(Base):
    """
    Persistent record of failed login attempts for account-lockout history
    and post-incident forensics. Pair with security.lockout.LockoutTracker.
    """
    __tablename__ = "failed_logins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    account_type = Column(String(20), nullable=False, default="staff")  # staff|patient
    ip_address = Column(String(45))
    user_agent = Column(String(300))
    reason = Column(String(60))
    occurred_at = Column(DateTime, default=datetime.utcnow, index=True)


class PasswordHistory(Base):
    """Per-user hash of the last N passwords to enforce reuse policy."""
    __tablename__ = "password_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_type = Column(String(20), nullable=False)  # staff|patient
    account_id = Column(Integer, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)


class MFASecret(Base):
    """TOTP shared secret for users that enrolled in multi-factor auth."""
    __tablename__ = "mfa_secrets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_type = Column(String(20), nullable=False)
    account_id = Column(Integer, nullable=False, index=True)
    secret_encrypted = Column(String(500), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)
    backup_codes_json = Column(Text)  # encrypted list of one-time backup codes


class EmergencyAccessGrantRec(Base):
    """
    "Break-glass" grant — records who opened what PHI under an emergency
    justification, and when the grant expires. Paired with AuditLog.
    """
    __tablename__ = "emergency_access_grants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    justification = Column(Text, nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(300))


# ── HIPAA: patient consent management ─────────────────────────────────────────

class ConsentType(enum.Enum):
    TREATMENT = "treatment"
    PAYMENT = "payment"
    DATA_SHARING = "data_sharing"
    RESEARCH = "research"
    MARKETING = "marketing"
    TELEHEALTH = "telehealth"
    HIE_OPT_IN = "hie_opt_in"           # health information exchange
    RELEASE_OF_INFORMATION = "release_of_information"


class ConsentStatus(enum.Enum):
    GRANTED = "granted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class PatientConsent(Base):
    __tablename__ = "patient_consents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    consent_type = Column(Enum(ConsentType), nullable=False)
    status = Column(Enum(ConsentStatus), nullable=False, default=ConsentStatus.GRANTED)
    scope = Column(Text)                          # free-text scope description
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    witnessed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    signature_hash = Column(String(64))           # sha256 of signed document
    document_ref = Column(String(500))            # path or URL to signed form

    patient = relationship("Patient")
    witness = relationship("User")


# ── Secure provider ↔ patient messaging ──────────────────────────────────────

class MessageThread(Base):
    __tablename__ = "message_threads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    subject = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_closed = Column(Boolean, default=False)

    patient = relationship("Patient")
    provider = relationship("User")
    messages = relationship("SecureMessage", back_populates="thread",
                            cascade="all, delete-orphan",
                            order_by="SecureMessage.sent_at")


class SecureMessage(Base):
    __tablename__ = "secure_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(Integer, ForeignKey("message_threads.id"), nullable=False)
    sender_type = Column(String(20), nullable=False)   # staff|patient|system
    sender_id = Column(Integer, nullable=False)
    body_encrypted = Column(Text, nullable=False)      # Fernet ciphertext
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

    thread = relationship("MessageThread", back_populates="messages")


# ── Private provider notes (author-only visibility) ─────────────────────────
#
# Unlike MedicalRecord, which is shared across providers and surfaced to the
# patient, a ProviderNote is visible only to the staff member who authored
# it. Intended for personal working notes — differentials to chase, soft
# observations, reminders for next visit — that do not belong in the chart.

class ProviderNote(Base):
    __tablename__ = "provider_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    body_encrypted = Column(Text, nullable=False)      # Fernet ciphertext
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient")
    author = relationship("User")


# ── Labs (orders & results) ──────────────────────────────────────────────────

class LabOrderStatus(enum.Enum):
    ORDERED = "ordered"
    COLLECTED = "collected"
    IN_PROCESS = "in_process"
    RESULTED = "resulted"
    CANCELLED = "cancelled"


class LabResultFlag(enum.Enum):
    NORMAL = "normal"
    LOW = "low"
    HIGH = "high"
    CRITICAL_LOW = "critical_low"
    CRITICAL_HIGH = "critical_high"
    ABNORMAL = "abnormal"


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    loinc_code = Column(String(20), index=True)        # panel or analyte
    test_name = Column(String(300), nullable=False)
    status = Column(Enum(LabOrderStatus), default=LabOrderStatus.ORDERED)
    priority = Column(String(20), default="routine")   # routine|stat|asap
    clinical_indication = Column(Text)
    ordered_at = Column(DateTime, default=datetime.utcnow)
    collected_at = Column(DateTime, nullable=True)
    resulted_at = Column(DateTime, nullable=True)

    patient = relationship("Patient")
    provider = relationship("User")
    results = relationship("LabResult", back_populates="order",
                           cascade="all, delete-orphan")


class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("lab_orders.id"), nullable=False)
    analyte = Column(String(200), nullable=False)
    loinc_code = Column(String(20))
    value = Column(String(100))           # stringified — units separate
    unit = Column(String(30))
    reference_range = Column(String(60))
    flag = Column(Enum(LabResultFlag), default=LabResultFlag.NORMAL)
    resulted_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)

    order = relationship("LabOrder", back_populates="results")


# ── Care plans / problem list ────────────────────────────────────────────────

class CarePlanStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CarePlan(Base):
    __tablename__ = "care_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    status = Column(Enum(CarePlanStatus), default=CarePlanStatus.ACTIVE)
    goals_json = Column(Text)             # [{goal, target_date, progress}]
    interventions_json = Column(Text)     # [{intervention, frequency}]
    started_on = Column(Date, default=date.today)
    review_on = Column(Date)
    closed_on = Column(Date, nullable=True)

    patient = relationship("Patient")
    author = relationship("User")


# ── Immunizations ────────────────────────────────────────────────────────────

class Immunization(Base):
    __tablename__ = "immunizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    administered_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    vaccine_name = Column(String(200), nullable=False)
    cvx_code = Column(String(10))         # CDC CVX vaccine code
    lot_number = Column(String(50))
    manufacturer = Column(String(200))
    administered_at = Column(DateTime, default=datetime.utcnow)
    dose_number = Column(Integer)
    route = Column(String(50))
    site = Column(String(50))             # e.g., left deltoid
    notes = Column(Text)

    patient = relationship("Patient")
    administered_by = relationship("User")


# ── Referrals ────────────────────────────────────────────────────────────────

class ReferralStatus(enum.Enum):
    REQUESTED = "requested"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    referring_provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_specialist_name = Column(String(200), nullable=False)
    to_specialty = Column(String(100))
    to_organization = Column(String(200))
    reason = Column(Text, nullable=False)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.REQUESTED)
    requested_at = Column(DateTime, default=datetime.utcnow)
    scheduled_for = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text)

    patient = relationship("Patient")
    referring_provider = relationship("User")


# ── Document vault ───────────────────────────────────────────────────────────

class PatientDocument(Base):
    """
    Patient-uploaded or provider-attached documents. Bytes are stored
    outside the DB; this row keeps metadata + Fernet-encrypted filename
    and SHA-256 integrity hash of the ciphertext-at-rest file.
    """
    __tablename__ = "patient_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    uploaded_by_id = Column(Integer, nullable=True)
    uploader_type = Column(String(20), default="staff")   # staff|patient
    category = Column(String(50), default="other")         # lab|consent|imaging|...
    filename_encrypted = Column(String(500), nullable=False)
    content_type = Column(String(100))
    size_bytes = Column(Integer)
    storage_ref = Column(String(500), nullable=False)      # path on disk or S3 key
    sha256_ciphertext = Column(String(64), nullable=False) # integrity check
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
