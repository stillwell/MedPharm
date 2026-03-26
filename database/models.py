# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
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


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    details_json = Column(Text)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")
