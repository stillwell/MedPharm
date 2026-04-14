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
MedPharm ERP - Database Manager
Provides all CRUD operations and business logic for the database layer.
"""

import json
import uuid
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine, func, or_, and_, desc
from sqlalchemy.orm import sessionmaker, Session

from werkzeug.security import generate_password_hash, check_password_hash

from database.models import (
    Base, User, Patient, PatientPortalAccount, Insurance, Medication,
    MedicationInteraction, Allergy, Vital, Diagnosis, MedicalRecord,
    Prescription, PrescriptionItem, Appointment, Invoice, InvoiceItem,
    Payment, AuditLog, InsuranceClaim, Symptom, Condition,
    UserRole, PrescriptionStatus, AppointmentStatus,
    InvoiceStatus, PaymentStatus, PaymentMethod, InteractionSeverity,
    InsuranceClaimStatus
)


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engine = None
        self._session_factory = None

    def init_db(self):
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,
            connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(self.engine)
        self._session_factory = sessionmaker(bind=self.engine)

    @contextmanager
    def get_session(self):
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ── Authentication ─────────────────────────────────────────────────────

    @staticmethod
    def hash_password(password: str) -> str:
        return generate_password_hash(password)

    @staticmethod
    def verify_password(password_hash: str, password: str) -> bool:
        return check_password_hash(password_hash, password)

    def authenticate_user(self, username: str, password: str) -> User | None:
        with self.get_session() as session:
            user = session.query(User).filter_by(username=username, is_active=True).first()
            if user and self.verify_password(user.password_hash, password):
                session.expunge(user)
                return user
        return None

    def authenticate_portal(self, username: str, password: str) -> dict | None:
        with self.get_session() as session:
            account = session.query(PatientPortalAccount).filter_by(
                username=username, is_active=True
            ).first()
            if account and self.verify_password(account.password_hash, password):
                account.last_login = datetime.utcnow()
                result = {
                    "id": account.id,
                    "patient_id": account.patient_id,
                    "username": account.username,
                    "email": account.email,
                }
                session.commit()
                return result
        return None

    # ── User CRUD ──────────────────────────────────────────────────────────

    def create_user(self, **kwargs) -> int:
        kwargs["password_hash"] = self.hash_password(kwargs.pop("password"))
        with self.get_session() as session:
            user = User(**kwargs)
            session.add(user)
            session.flush()
            return user.id

    def get_user(self, user_id: int) -> dict | None:
        with self.get_session() as session:
            user = session.get(User, user_id)
            if user:
                return self._user_to_dict(user)
        return None

    def get_all_users(self) -> list[dict]:
        with self.get_session() as session:
            users = session.query(User).filter_by(is_active=True).all()
            return [self._user_to_dict(u) for u in users]

    def get_providers(self) -> list[dict]:
        with self.get_session() as session:
            users = session.query(User).filter(
                User.role.in_([UserRole.DOCTOR, UserRole.PSYCHIATRIST]),
                User.is_active == True
            ).all()
            return [self._user_to_dict(u) for u in users]

    @staticmethod
    def _user_to_dict(user: User) -> dict:
        return {
            "id": user.id, "username": user.username, "role": user.role.value,
            "first_name": user.first_name, "last_name": user.last_name,
            "full_name": user.full_name, "display_title": user.display_title,
            "email": user.email, "phone": user.phone,
            "license_number": user.license_number,
            "specialization": user.specialization,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }

    # ── Patient CRUD ───────────────────────────────────────────────────────

    def create_patient(self, **kwargs) -> int:
        with self.get_session() as session:
            patient = Patient(**kwargs)
            session.add(patient)
            session.flush()
            return patient.id

    def get_patient(self, patient_id: int) -> dict | None:
        with self.get_session() as session:
            patient = session.get(Patient, patient_id)
            if patient:
                return self._patient_to_dict(patient)
        return None

    def get_patient_full(self, patient_id: int) -> dict | None:
        with self.get_session() as session:
            patient = session.get(Patient, patient_id)
            if not patient:
                return None
            d = self._patient_to_dict(patient)
            d["allergies"] = [
                {"id": a.id, "allergen": a.allergen, "reaction": a.reaction,
                 "severity": a.severity.value if a.severity else None,
                 "noted_date": a.noted_date.isoformat() if a.noted_date else None}
                for a in patient.allergies
            ]
            d["insurance_records"] = [
                {"id": i.id, "provider_name": i.provider_name,
                 "policy_number": i.policy_number, "group_number": i.group_number,
                 "copay_amount": float(i.copay_amount) if i.copay_amount else 0,
                 "coverage_type": i.coverage_type.value if i.coverage_type else None,
                 "is_active": i.is_active}
                for i in patient.insurance_records
            ]
            d["diagnoses"] = [
                {"id": dx.id, "icd10_code": dx.icd10_code,
                 "description": dx.description, "status": dx.status.value,
                 "diagnosis_date": dx.diagnosis_date.isoformat() if dx.diagnosis_date else None,
                 "diagnosed_by": dx.diagnosed_by.display_title if dx.diagnosed_by else None}
                for dx in patient.diagnoses
            ]
            return d

    def search_patients(self, query: str) -> list[dict]:
        with self.get_session() as session:
            q = session.query(Patient).filter(Patient.is_active == True)
            if query:
                like = f"%{query}%"
                q = q.filter(or_(
                    Patient.first_name.ilike(like),
                    Patient.last_name.ilike(like),
                    Patient.email.ilike(like),
                    Patient.phone.ilike(like)
                ))
            patients = q.order_by(Patient.last_name, Patient.first_name).limit(100).all()
            return [self._patient_to_dict(p) for p in patients]

    def get_all_patients(self, page: int = 1, per_page: int = 50) -> tuple[list[dict], int]:
        with self.get_session() as session:
            total = session.query(func.count(Patient.id)).filter_by(is_active=True).scalar()
            patients = session.query(Patient).filter_by(is_active=True)\
                .order_by(Patient.last_name, Patient.first_name)\
                .offset((page - 1) * per_page).limit(per_page).all()
            return [self._patient_to_dict(p) for p in patients], total

    def update_patient(self, patient_id: int, **kwargs) -> bool:
        with self.get_session() as session:
            patient = session.get(Patient, patient_id)
            if not patient:
                return False
            for k, v in kwargs.items():
                if hasattr(patient, k):
                    setattr(patient, k, v)
            return True

    def deactivate_patient(self, patient_id: int) -> bool:
        return self.update_patient(patient_id, is_active=False)

    @staticmethod
    def _patient_to_dict(patient: Patient) -> dict:
        return {
            "id": patient.id, "first_name": patient.first_name,
            "last_name": patient.last_name, "full_name": patient.full_name,
            "dob": patient.dob.isoformat() if patient.dob else None,
            "age": patient.age, "gender": patient.gender.value if patient.gender else None,
            "ssn_last4": patient.ssn_last4, "email": patient.email, "phone": patient.phone,
            "address": patient.address, "city": patient.city, "state": patient.state,
            "zip_code": patient.zip_code,
            "emergency_contact_name": patient.emergency_contact_name,
            "emergency_contact_phone": patient.emergency_contact_phone,
            "blood_type": patient.blood_type.value if patient.blood_type else None,
            "is_active": patient.is_active,
            "created_at": patient.created_at.isoformat() if patient.created_at else None
        }

    # ── Portal Account ─────────────────────────────────────────────────────

    def create_portal_account(self, patient_id: int, username: str, password: str, email: str) -> int:
        with self.get_session() as session:
            account = PatientPortalAccount(
                patient_id=patient_id, username=username,
                password_hash=self.hash_password(password), email=email
            )
            session.add(account)
            session.flush()
            return account.id

    def get_portal_patient(self, account_id: int) -> dict | None:
        with self.get_session() as session:
            account = session.get(PatientPortalAccount, account_id)
            if account and account.patient:
                return self._patient_to_dict(account.patient)
        return None

    def verify_patient_identity(self, first_name: str, last_name: str, dob: date, ssn_last4: str) -> int | None:
        with self.get_session() as session:
            patient = session.query(Patient).filter(
                func.lower(Patient.first_name) == first_name.lower(),
                func.lower(Patient.last_name) == last_name.lower(),
                Patient.dob == dob,
                Patient.ssn_last4 == ssn_last4,
                Patient.is_active == True
            ).first()
            if patient and not patient.portal_account:
                return patient.id
        return None

    # ── Medication CRUD ────────────────────────────────────────────────────

    def get_medication(self, med_id: int) -> dict | None:
        with self.get_session() as session:
            med = session.get(Medication, med_id)
            if med:
                return self._medication_to_dict(med)
        return None

    def search_medications(self, query: str = "", drug_class: str = "",
                           schedule: str = "", form: str = "") -> list[dict]:
        with self.get_session() as session:
            q = session.query(Medication).filter(Medication.is_active == True)
            if query:
                like = f"%{query}%"
                q = q.filter(or_(
                    Medication.brand_name.ilike(like),
                    Medication.generic_name.ilike(like),
                    Medication.ndc_code.ilike(like)
                ))
            if drug_class:
                q = q.filter(Medication.drug_class.ilike(f"%{drug_class}%"))
            if schedule:
                from database.models import DrugSchedule
                try:
                    q = q.filter(Medication.schedule == DrugSchedule(schedule))
                except ValueError:
                    pass
            if form:
                from database.models import DrugForm
                try:
                    q = q.filter(Medication.form == DrugForm(form))
                except ValueError:
                    pass
            meds = q.order_by(Medication.brand_name).all()
            return [self._medication_to_dict(m) for m in meds]

    def get_all_medications(self) -> list[dict]:
        return self.search_medications()

    def get_medication_interactions(self, med_id: int) -> list[dict]:
        with self.get_session() as session:
            interactions = session.query(MedicationInteraction).filter(
                or_(
                    MedicationInteraction.medication_a_id == med_id,
                    MedicationInteraction.medication_b_id == med_id
                )
            ).all()
            result = []
            for inter in interactions:
                other_id = inter.medication_b_id if inter.medication_a_id == med_id else inter.medication_a_id
                other_med = session.get(Medication, other_id)
                result.append({
                    "id": inter.id,
                    "other_medication": other_med.brand_name if other_med else "Unknown",
                    "other_medication_id": other_id,
                    "severity": inter.severity.value,
                    "description": inter.description
                })
            return result

    def check_interactions(self, medication_ids: list[int]) -> list[dict]:
        with self.get_session() as session:
            results = []
            for i, mid_a in enumerate(medication_ids):
                for mid_b in medication_ids[i + 1:]:
                    inter = session.query(MedicationInteraction).filter(
                        or_(
                            and_(MedicationInteraction.medication_a_id == mid_a,
                                 MedicationInteraction.medication_b_id == mid_b),
                            and_(MedicationInteraction.medication_a_id == mid_b,
                                 MedicationInteraction.medication_b_id == mid_a)
                        )
                    ).first()
                    if inter:
                        med_a = session.get(Medication, mid_a)
                        med_b = session.get(Medication, mid_b)
                        results.append({
                            "medication_a": med_a.brand_name if med_a else "?",
                            "medication_b": med_b.brand_name if med_b else "?",
                            "severity": inter.severity.value,
                            "description": inter.description
                        })
            return results

    def update_medication_prices(self, med_id: int, awp: float, retail: float):
        with self.get_session() as session:
            med = session.get(Medication, med_id)
            if med:
                med.avg_wholesale_price = awp
                med.retail_price = retail
                med.last_price_update = datetime.utcnow()

    @staticmethod
    def _medication_to_dict(med: Medication) -> dict:
        return {
            "id": med.id, "ndc_code": med.ndc_code,
            "brand_name": med.brand_name, "generic_name": med.generic_name,
            "manufacturer": med.manufacturer, "drug_class": med.drug_class,
            "schedule": med.schedule.value if med.schedule else "none",
            "route": med.route.value if med.route else None,
            "form": med.form.value if med.form else None,
            "strength": med.strength, "unit": med.unit,
            "description": med.description, "indications": med.indications,
            "contraindications": med.contraindications,
            "side_effects": med.side_effects,
            "avg_wholesale_price": float(med.avg_wholesale_price) if med.avg_wholesale_price else 0,
            "retail_price": float(med.retail_price) if med.retail_price else 0,
            "last_price_update": med.last_price_update.isoformat() if med.last_price_update else None,
            "is_controlled": med.is_controlled, "is_active": med.is_active
        }

    # ── Prescription CRUD ──────────────────────────────────────────────────

    def create_prescription(self, patient_id: int, prescriber_id: int,
                            items: list[dict], diagnosis_id: int = None,
                            notes: str = "") -> int:
        with self.get_session() as session:
            rx_number = f"RX-{uuid.uuid4().hex[:8].upper()}"
            rx = Prescription(
                patient_id=patient_id, prescriber_id=prescriber_id,
                rx_number=rx_number, status=PrescriptionStatus.ACTIVE,
                diagnosis_id=diagnosis_id, notes=notes,
                prescribed_date=date.today(),
                expiry_date=date.today() + timedelta(days=365)
            )
            session.add(rx)
            session.flush()
            for item_data in items:
                med = session.get(Medication, item_data["medication_id"])
                unit_price = float(med.retail_price) if med and med.retail_price else 0
                qty = item_data.get("quantity", 1)
                pi = PrescriptionItem(
                    prescription_id=rx.id,
                    medication_id=item_data["medication_id"],
                    dosage=item_data.get("dosage", ""),
                    frequency=item_data.get("frequency", ""),
                    duration=item_data.get("duration", ""),
                    quantity=qty,
                    refills_allowed=item_data.get("refills_allowed", 0),
                    instructions=item_data.get("instructions", ""),
                    is_substitution_allowed=item_data.get("is_substitution_allowed", True),
                    unit_price=unit_price,
                    total_price=unit_price * qty
                )
                session.add(pi)
            return rx.id

    def get_prescription(self, rx_id: int) -> dict | None:
        with self.get_session() as session:
            rx = session.get(Prescription, rx_id)
            if rx:
                return self._prescription_to_dict(rx, session)
        return None

    def get_prescriptions_by_patient(self, patient_id: int) -> list[dict]:
        with self.get_session() as session:
            rxs = session.query(Prescription).filter_by(patient_id=patient_id)\
                .order_by(desc(Prescription.prescribed_date)).all()
            return [self._prescription_to_dict(rx, session) for rx in rxs]

    def get_prescriptions_by_prescriber(self, prescriber_id: int) -> list[dict]:
        with self.get_session() as session:
            rxs = session.query(Prescription).filter_by(prescriber_id=prescriber_id)\
                .order_by(desc(Prescription.prescribed_date)).all()
            return [self._prescription_to_dict(rx, session) for rx in rxs]

    def get_all_prescriptions(self, status: str = None) -> list[dict]:
        with self.get_session() as session:
            q = session.query(Prescription).order_by(desc(Prescription.prescribed_date))
            if status:
                try:
                    q = q.filter(Prescription.status == PrescriptionStatus(status))
                except ValueError:
                    pass
            rxs = q.limit(500).all()
            return [self._prescription_to_dict(rx, session) for rx in rxs]

    def update_prescription_status(self, rx_id: int, status: str) -> bool:
        with self.get_session() as session:
            rx = session.get(Prescription, rx_id)
            if rx:
                rx.status = PrescriptionStatus(status)
                return True
        return False

    def refill_prescription_item(self, item_id: int) -> bool:
        with self.get_session() as session:
            item = session.get(PrescriptionItem, item_id)
            if item and item.refills_used < item.refills_allowed:
                item.refills_used += 1
                return True
        return False

    def _prescription_to_dict(self, rx: Prescription, session: Session) -> dict:
        items = []
        total = 0
        for item in rx.items:
            med = session.get(Medication, item.medication_id)
            price = float(item.total_price) if item.total_price else 0
            total += price
            items.append({
                "id": item.id,
                "medication_id": item.medication_id,
                "medication_name": med.brand_name if med else "Unknown",
                "generic_name": med.generic_name if med else "",
                "dosage": item.dosage, "frequency": item.frequency,
                "duration": item.duration, "quantity": item.quantity,
                "refills_allowed": item.refills_allowed,
                "refills_used": item.refills_used,
                "refills_remaining": item.refills_allowed - item.refills_used,
                "instructions": item.instructions,
                "is_substitution_allowed": item.is_substitution_allowed,
                "unit_price": float(item.unit_price) if item.unit_price else 0,
                "total_price": price
            })
        return {
            "id": rx.id, "rx_number": rx.rx_number,
            "patient_id": rx.patient_id,
            "patient_name": rx.patient.full_name if rx.patient else "",
            "prescriber_id": rx.prescriber_id,
            "prescriber_name": rx.prescriber.display_title if rx.prescriber else "",
            "status": rx.status.value,
            "diagnosis": rx.diagnosis.description if rx.diagnosis else "",
            "notes": rx.notes,
            "prescribed_date": rx.prescribed_date.isoformat() if rx.prescribed_date else None,
            "expiry_date": rx.expiry_date.isoformat() if rx.expiry_date else None,
            "items": items, "total": total
        }

    # ── Appointment CRUD ───────────────────────────────────────────────────

    def create_appointment(self, **kwargs) -> int:
        with self.get_session() as session:
            appt = Appointment(**kwargs)
            session.add(appt)
            session.flush()
            return appt.id

    def get_appointments(self, provider_id: int = None, patient_id: int = None,
                         date_from: date = None, date_to: date = None,
                         status: str = None) -> list[dict]:
        with self.get_session() as session:
            q = session.query(Appointment)
            if provider_id:
                q = q.filter_by(provider_id=provider_id)
            if patient_id:
                q = q.filter_by(patient_id=patient_id)
            if date_from:
                q = q.filter(Appointment.scheduled_datetime >= datetime.combine(date_from, datetime.min.time()))
            if date_to:
                q = q.filter(Appointment.scheduled_datetime <= datetime.combine(date_to, datetime.max.time()))
            if status:
                try:
                    q = q.filter(Appointment.status == AppointmentStatus(status))
                except ValueError:
                    pass
            appts = q.order_by(Appointment.scheduled_datetime).all()
            return [self._appointment_to_dict(a) for a in appts]

    def get_todays_appointments(self, provider_id: int = None) -> list[dict]:
        today = date.today()
        return self.get_appointments(provider_id=provider_id, date_from=today, date_to=today)

    def update_appointment_status(self, appt_id: int, status: str) -> bool:
        with self.get_session() as session:
            appt = session.get(Appointment, appt_id)
            if appt:
                appt.status = AppointmentStatus(status)
                return True
        return False

    @staticmethod
    def _appointment_to_dict(appt: Appointment) -> dict:
        return {
            "id": appt.id, "patient_id": appt.patient_id,
            "patient_name": appt.patient.full_name if appt.patient else "",
            "provider_id": appt.provider_id,
            "provider_name": appt.provider.display_title if appt.provider else "",
            "appointment_type": appt.appointment_type.value if appt.appointment_type else "",
            "scheduled_datetime": appt.scheduled_datetime.isoformat() if appt.scheduled_datetime else None,
            "duration_minutes": appt.duration_minutes,
            "status": appt.status.value if appt.status else "",
            "reason": appt.reason, "notes": appt.notes
        }

    # ── Vitals CRUD ────────────────────────────────────────────────────────

    def add_vitals(self, **kwargs) -> int:
        with self.get_session() as session:
            vital = Vital(**kwargs)
            if vital.weight and vital.height and vital.height > 0:
                h_m = float(vital.height) / 100.0
                vital.bmi = round(float(vital.weight) / (h_m * h_m), 1)
            session.add(vital)
            session.flush()
            return vital.id

    def get_patient_vitals(self, patient_id: int, limit: int = 20) -> list[dict]:
        with self.get_session() as session:
            vitals = session.query(Vital).filter_by(patient_id=patient_id)\
                .order_by(desc(Vital.recorded_at)).limit(limit).all()
            return [{
                "id": v.id, "bp_systolic": v.bp_systolic, "bp_diastolic": v.bp_diastolic,
                "heart_rate": v.heart_rate,
                "temperature": float(v.temperature) if v.temperature else None,
                "respiratory_rate": v.respiratory_rate,
                "oxygen_saturation": float(v.oxygen_saturation) if v.oxygen_saturation else None,
                "weight": float(v.weight) if v.weight else None,
                "height": float(v.height) if v.height else None,
                "bmi": float(v.bmi) if v.bmi else None,
                "recorded_at": v.recorded_at.isoformat() if v.recorded_at else None,
                "recorded_by": v.recorded_by.display_title if v.recorded_by else ""
            } for v in vitals]

    # ── Diagnosis CRUD ─────────────────────────────────────────────────────

    def add_diagnosis(self, **kwargs) -> int:
        with self.get_session() as session:
            dx = Diagnosis(**kwargs)
            session.add(dx)
            session.flush()
            return dx.id

    def get_patient_diagnoses(self, patient_id: int) -> list[dict]:
        with self.get_session() as session:
            dxs = session.query(Diagnosis).filter_by(patient_id=patient_id)\
                .order_by(desc(Diagnosis.diagnosis_date)).all()
            return [{
                "id": d.id, "icd10_code": d.icd10_code,
                "description": d.description, "status": d.status.value,
                "diagnosis_date": d.diagnosis_date.isoformat() if d.diagnosis_date else None,
                "diagnosed_by": d.diagnosed_by.display_title if d.diagnosed_by else "",
                "notes": d.notes
            } for d in dxs]

    # ── Allergy CRUD ───────────────────────────────────────────────────────

    def add_allergy(self, **kwargs) -> int:
        with self.get_session() as session:
            allergy = Allergy(**kwargs)
            session.add(allergy)
            session.flush()
            return allergy.id

    def get_patient_allergies(self, patient_id: int) -> list[dict]:
        with self.get_session() as session:
            allergies = session.query(Allergy).filter_by(patient_id=patient_id).all()
            return [{
                "id": a.id, "allergen": a.allergen, "reaction": a.reaction,
                "severity": a.severity.value if a.severity else None,
                "noted_date": a.noted_date.isoformat() if a.noted_date else None
            } for a in allergies]

    # ── Medical Record CRUD ────────────────────────────────────────────────

    def add_medical_record(self, **kwargs) -> int:
        with self.get_session() as session:
            rec = MedicalRecord(**kwargs)
            session.add(rec)
            session.flush()
            return rec.id

    def get_patient_records(self, patient_id: int, record_type: str = None) -> list[dict]:
        with self.get_session() as session:
            q = session.query(MedicalRecord).filter_by(patient_id=patient_id)
            if record_type:
                from database.models import RecordType
                try:
                    q = q.filter(MedicalRecord.record_type == RecordType(record_type))
                except ValueError:
                    pass
            records = q.order_by(desc(MedicalRecord.record_date)).all()
            return [{
                "id": r.id, "record_type": r.record_type.value if r.record_type else "",
                "title": r.title, "content": r.content,
                "record_date": r.record_date.isoformat() if r.record_date else None,
                "provider": r.provider.display_title if r.provider else "",
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in records]

    # ── Invoice/Payment CRUD ───────────────────────────────────────────────

    def create_invoice(self, patient_id: int, items: list[dict],
                       notes: str = "", due_days: int = 30) -> int:
        with self.get_session() as session:
            inv_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
            subtotal = sum(i.get("total_price", 0) for i in items)
            tax = round(subtotal * 0.0, 2)
            total = subtotal + tax
            inv = Invoice(
                patient_id=patient_id, invoice_number=inv_number,
                invoice_date=date.today(), due_date=date.today() + timedelta(days=due_days),
                subtotal=subtotal, tax=tax, total_amount=total,
                balance_due=total, status=InvoiceStatus.SENT, notes=notes
            )
            session.add(inv)
            session.flush()
            for item_data in items:
                ii = InvoiceItem(
                    invoice_id=inv.id,
                    description=item_data.get("description", ""),
                    service_code=item_data.get("service_code", ""),
                    quantity=item_data.get("quantity", 1),
                    unit_price=item_data.get("unit_price", 0),
                    total_price=item_data.get("total_price", 0),
                    prescription_item_id=item_data.get("prescription_item_id")
                )
                session.add(ii)
            return inv.id

    def create_invoice_from_prescription(self, rx_id: int) -> int | None:
        with self.get_session() as session:
            rx = session.get(Prescription, rx_id)
            if not rx:
                return None
            items = []
            for pi in rx.items:
                med = session.get(Medication, pi.medication_id)
                items.append({
                    "description": f"{med.brand_name} ({med.generic_name}) - {pi.dosage}" if med else pi.dosage,
                    "service_code": "RX",
                    "quantity": pi.quantity,
                    "unit_price": float(pi.unit_price) if pi.unit_price else 0,
                    "total_price": float(pi.total_price) if pi.total_price else 0,
                    "prescription_item_id": pi.id
                })
            # Add consultation fee
            items.append({
                "description": "Medical Consultation",
                "service_code": "99213",
                "quantity": 1,
                "unit_price": 150.00,
                "total_price": 150.00
            })
        return self.create_invoice(rx.patient_id, items)

    def get_invoice(self, invoice_id: int) -> dict | None:
        with self.get_session() as session:
            inv = session.get(Invoice, invoice_id)
            if inv:
                return self._invoice_to_dict(inv)
        return None

    def get_patient_invoices(self, patient_id: int) -> list[dict]:
        with self.get_session() as session:
            invs = session.query(Invoice).filter_by(patient_id=patient_id)\
                .order_by(desc(Invoice.invoice_date)).all()
            return [self._invoice_to_dict(i) for i in invs]

    def get_all_invoices(self, status: str = None) -> list[dict]:
        with self.get_session() as session:
            q = session.query(Invoice).order_by(desc(Invoice.invoice_date))
            if status:
                try:
                    q = q.filter(Invoice.status == InvoiceStatus(status))
                except ValueError:
                    pass
            return [self._invoice_to_dict(i) for i in q.limit(500).all()]

    def get_outstanding_invoices(self) -> list[dict]:
        with self.get_session() as session:
            invs = session.query(Invoice).filter(
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE])
            ).order_by(Invoice.due_date).all()
            return [self._invoice_to_dict(i) for i in invs]

    def record_payment(self, invoice_id: int, amount: float,
                       payment_method: str = "online",
                       portal_account_id: int = None,
                       transaction_ref: str = None, notes: str = "") -> int:
        with self.get_session() as session:
            inv = session.get(Invoice, invoice_id)
            if not inv:
                return -1
            payment = Payment(
                invoice_id=invoice_id,
                portal_account_id=portal_account_id,
                amount=amount,
                payment_method=PaymentMethod(payment_method),
                transaction_reference=transaction_ref or f"TXN-{uuid.uuid4().hex[:10].upper()}",
                status=PaymentStatus.COMPLETED,
                notes=notes
            )
            session.add(payment)
            inv.amount_paid = float(inv.amount_paid or 0) + amount
            inv.balance_due = float(inv.total_amount or 0) - float(inv.amount_paid)
            if inv.balance_due <= 0:
                inv.balance_due = 0
                inv.status = InvoiceStatus.PAID
            else:
                inv.status = InvoiceStatus.PARTIAL
            session.flush()
            return payment.id

    def get_payment_history(self, patient_id: int = None, invoice_id: int = None) -> list[dict]:
        with self.get_session() as session:
            q = session.query(Payment)
            if invoice_id:
                q = q.filter_by(invoice_id=invoice_id)
            elif patient_id:
                q = q.join(Invoice).filter(Invoice.patient_id == patient_id)
            payments = q.order_by(desc(Payment.payment_date)).all()
            return [{
                "id": p.id, "invoice_id": p.invoice_id,
                "invoice_number": p.invoice.invoice_number if p.invoice else "",
                "amount": float(p.amount), "payment_method": p.payment_method.value,
                "transaction_reference": p.transaction_reference,
                "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                "status": p.status.value, "notes": p.notes
            } for p in payments]

    @staticmethod
    def _invoice_to_dict(inv: Invoice) -> dict:
        items = [{
            "id": ii.id, "description": ii.description,
            "service_code": ii.service_code, "quantity": ii.quantity,
            "unit_price": float(ii.unit_price), "total_price": float(ii.total_price)
        } for ii in inv.items]
        return {
            "id": inv.id, "invoice_number": inv.invoice_number,
            "patient_id": inv.patient_id,
            "patient_name": inv.patient.full_name if inv.patient else "",
            "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "subtotal": float(inv.subtotal or 0), "tax": float(inv.tax or 0),
            "discount": float(inv.discount or 0),
            "total_amount": float(inv.total_amount or 0),
            "amount_paid": float(inv.amount_paid or 0),
            "balance_due": float(inv.balance_due or 0),
            "status": inv.status.value, "notes": inv.notes,
            "items": items
        }

    # ── Insurance CRUD ─────────────────────────────────────────────────────

    def add_insurance(self, **kwargs) -> int:
        with self.get_session() as session:
            ins = Insurance(**kwargs)
            session.add(ins)
            session.flush()
            return ins.id

    def get_patient_insurance(self, patient_id: int) -> list[dict]:
        with self.get_session() as session:
            records = session.query(Insurance).filter_by(patient_id=patient_id).all()
            return [{
                "id": i.id, "provider_name": i.provider_name,
                "policy_number": i.policy_number, "group_number": i.group_number,
                "subscriber_name": i.subscriber_name,
                "copay_amount": float(i.copay_amount) if i.copay_amount else 0,
                "coverage_type": i.coverage_type.value if i.coverage_type else "",
                "effective_date": i.effective_date.isoformat() if i.effective_date else None,
                "expiry_date": i.expiry_date.isoformat() if i.expiry_date else None,
                "is_active": i.is_active
            } for i in records]

    # ── Audit Log ──────────────────────────────────────────────────────────

    def log_action(self, user_id: int, action: str, entity_type: str = "",
                   entity_id: int = None, details: dict = None, ip: str = ""):
        with self.get_session() as session:
            log = AuditLog(
                user_id=user_id, action=action, entity_type=entity_type,
                entity_id=entity_id,
                details_json=json.dumps(details) if details else None,
                ip_address=ip
            )
            session.add(log)

    def get_recent_activity(self, limit: int = 10) -> list[dict]:
        with self.get_session() as session:
            logs = session.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()
            return [{
                "id": l.id, "action": l.action, "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "user": l.user.display_title if l.user else "System",
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "details": json.loads(l.details_json) if l.details_json else {}
            } for l in logs]

    # ── Dashboard Statistics ───────────────────────────────────────────────

    def get_dashboard_stats(self) -> dict:
        with self.get_session() as session:
            patient_count = session.query(func.count(Patient.id)).filter_by(is_active=True).scalar() or 0
            active_rx = session.query(func.count(Prescription.id)).filter_by(
                status=PrescriptionStatus.ACTIVE).scalar() or 0

            today_start = datetime.combine(date.today(), datetime.min.time())
            today_end = datetime.combine(date.today(), datetime.max.time())
            today_appts = session.query(func.count(Appointment.id)).filter(
                Appointment.scheduled_datetime.between(today_start, today_end)
            ).scalar() or 0

            month_start = date.today().replace(day=1)
            monthly_revenue = session.query(func.sum(Payment.amount)).filter(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.payment_date >= datetime.combine(month_start, datetime.min.time())
            ).scalar() or 0

            pending_bills = session.query(func.sum(Invoice.balance_due)).filter(
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE])
            ).scalar() or 0

            controlled_rx = session.query(func.count(PrescriptionItem.id)).join(Medication).filter(
                Medication.is_controlled == True
            ).scalar() or 0

            today_revenue = session.query(func.sum(Payment.amount)).filter(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.payment_date.between(today_start, today_end)
            ).scalar() or 0

            return {
                "patient_count": patient_count,
                "active_prescriptions": active_rx,
                "today_appointments": today_appts,
                "monthly_revenue": float(monthly_revenue),
                "today_revenue": float(today_revenue or 0),
                "pending_bills": float(pending_bills),
                "controlled_substances": controlled_rx
            }

    def get_revenue_by_month(self, months: int = 12) -> list[dict]:
        with self.get_session() as session:
            results = []
            for i in range(months - 1, -1, -1):
                d = date.today().replace(day=1) - timedelta(days=30 * i)
                month_start = d.replace(day=1)
                if d.month == 12:
                    month_end = d.replace(year=d.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = d.replace(month=d.month + 1, day=1) - timedelta(days=1)
                revenue = session.query(func.sum(Payment.amount)).filter(
                    Payment.status == PaymentStatus.COMPLETED,
                    Payment.payment_date >= datetime.combine(month_start, datetime.min.time()),
                    Payment.payment_date <= datetime.combine(month_end, datetime.max.time())
                ).scalar() or 0
                results.append({
                    "month": month_start.strftime("%b %Y"),
                    "revenue": float(revenue)
                })
            return results

    def get_top_medications(self, limit: int = 10) -> list[dict]:
        with self.get_session() as session:
            results = session.query(
                Medication.brand_name,
                func.count(PrescriptionItem.id).label("count")
            ).join(PrescriptionItem).group_by(Medication.id)\
                .order_by(desc("count")).limit(limit).all()
            return [{"name": r[0], "count": r[1]} for r in results]

    def get_patient_demographics(self) -> dict:
        with self.get_session() as session:
            from database.models import Gender
            results = {}
            for g in Gender:
                count = session.query(func.count(Patient.id)).filter_by(
                    gender=g, is_active=True).scalar() or 0
                results[g.value] = count
            return results

    # ── Insurance Claims ────────────────────────────────────────────────

    def submit_insurance_claim(self, invoice_id: int, insurance_id: int,
                               patient_id: int, claimed_amount: float,
                               copay_amount: float = 0, notes: str = "") -> int:
        with self.get_session() as session:
            claim_number = f"CLM-{uuid.uuid4().hex[:10].upper()}"
            claim = InsuranceClaim(
                invoice_id=invoice_id, insurance_id=insurance_id,
                patient_id=patient_id, claim_number=claim_number,
                claimed_amount=claimed_amount, copay_amount=copay_amount,
                notes=notes
            )
            session.add(claim)
            session.flush()
            return claim.id

    def get_insurance_claims(self, patient_id: int = None,
                             invoice_id: int = None) -> list[dict]:
        with self.get_session() as session:
            q = session.query(InsuranceClaim)
            if patient_id:
                q = q.filter_by(patient_id=patient_id)
            if invoice_id:
                q = q.filter_by(invoice_id=invoice_id)
            claims = q.order_by(desc(InsuranceClaim.created_at)).all()
            return [{
                "id": c.id, "claim_number": c.claim_number,
                "invoice_id": c.invoice_id,
                "insurance_id": c.insurance_id,
                "insurance_provider": c.insurance.provider_name if c.insurance else "",
                "policy_number": c.insurance.policy_number if c.insurance else "",
                "patient_id": c.patient_id,
                "status": c.status.value,
                "submitted_date": c.submitted_date.isoformat() if c.submitted_date else None,
                "response_date": c.response_date.isoformat() if c.response_date else None,
                "claimed_amount": float(c.claimed_amount),
                "approved_amount": float(c.approved_amount or 0),
                "copay_amount": float(c.copay_amount or 0),
                "deductible_applied": float(c.deductible_applied or 0),
                "denial_reason": c.denial_reason,
                "notes": c.notes
            } for c in claims]

    def update_insurance_claim(self, claim_id: int, **kwargs) -> bool:
        with self.get_session() as session:
            claim = session.get(InsuranceClaim, claim_id)
            if not claim:
                return False
            for k, v in kwargs.items():
                if k == "status":
                    v = InsuranceClaimStatus(v)
                if hasattr(claim, k):
                    setattr(claim, k, v)
            return True

    def process_insurance_payment(self, claim_id: int, approved_amount: float,
                                  copay_amount: float = 0,
                                  deductible: float = 0) -> dict:
        """Process an approved insurance claim into actual payments."""
        with self.get_session() as session:
            claim = session.get(InsuranceClaim, claim_id)
            if not claim:
                return {"error": "Claim not found"}

            claim.approved_amount = approved_amount
            claim.copay_amount = copay_amount
            claim.deductible_applied = deductible
            claim.status = InsuranceClaimStatus.APPROVED
            claim.response_date = date.today()

            # Record insurance payment on the invoice
            insurance_pays = approved_amount - deductible
            if insurance_pays > 0:
                inv = session.get(Invoice, claim.invoice_id)
                if inv:
                    payment = Payment(
                        invoice_id=inv.id, amount=insurance_pays,
                        payment_method=PaymentMethod.INSURANCE,
                        transaction_reference=f"INS-{claim.claim_number}",
                        status=PaymentStatus.COMPLETED,
                        notes=f"Insurance payment via {claim.insurance.provider_name}"
                    )
                    session.add(payment)
                    inv.amount_paid = float(inv.amount_paid or 0) + insurance_pays
                    inv.balance_due = float(inv.total_amount or 0) - float(inv.amount_paid)
                    if inv.balance_due <= 0:
                        inv.balance_due = 0
                        inv.status = InvoiceStatus.PAID
                    else:
                        inv.status = InvoiceStatus.PARTIAL

            session.flush()
            return {
                "claim_id": claim.id,
                "insurance_paid": insurance_pays,
                "patient_copay": copay_amount,
                "remaining_balance": float(claim.invoice.balance_due) if claim.invoice else 0
            }

    # ── Symptoms & Conditions ─────────────────────────────────────────

    def search_symptoms(self, query: str = "", body_system: str = "") -> list[dict]:
        with self.get_session() as session:
            q = session.query(Symptom)
            if query:
                like = f"%{query}%"
                q = q.filter(or_(
                    Symptom.name.ilike(like),
                    Symptom.description.ilike(like)
                ))
            if body_system:
                q = q.filter(Symptom.body_system.ilike(f"%{body_system}%"))
            symptoms = q.order_by(Symptom.name).limit(100).all()
            return [{
                "id": s.id, "name": s.name, "description": s.description,
                "body_system": s.body_system,
                "icd10_codes": s.icd10_codes,
                "common_conditions": s.common_conditions,
                "is_emergency": s.is_emergency
            } for s in symptoms]

    def search_conditions(self, query: str = "", category: str = "") -> list[dict]:
        with self.get_session() as session:
            q = session.query(Condition)
            if query:
                like = f"%{query}%"
                q = q.filter(or_(
                    Condition.name.ilike(like),
                    Condition.icd10_code.ilike(like),
                    Condition.description.ilike(like)
                ))
            if category:
                q = q.filter(Condition.category.ilike(f"%{category}%"))
            conditions = q.order_by(Condition.name).limit(100).all()
            return [{
                "id": c.id, "name": c.name, "icd10_code": c.icd10_code,
                "category": c.category, "description": c.description,
                "common_symptoms": c.common_symptoms,
                "typical_medications": c.typical_medications,
                "prevalence": c.prevalence, "is_chronic": c.is_chronic
            } for c in conditions]

    def get_all_body_systems(self) -> list[str]:
        with self.get_session() as session:
            systems = session.query(Symptom.body_system).distinct().order_by(
                Symptom.body_system).all()
            return [s[0] for s in systems if s[0]]

    def get_all_condition_categories(self) -> list[str]:
        with self.get_session() as session:
            cats = session.query(Condition.category).distinct().order_by(
                Condition.category).all()
            return [c[0] for c in cats if c[0]]

    def is_database_empty(self) -> bool:
        with self.get_session() as session:
            return session.query(func.count(User.id)).scalar() == 0
