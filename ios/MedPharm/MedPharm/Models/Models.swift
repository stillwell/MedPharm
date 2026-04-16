/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import Foundation

// MARK: - Auth

struct LoginRequest: Encodable {
    let username: String
    let password: String
}

struct LoginResponse: Decodable {
    let access_token: String
    let refresh_token: String
    let user: UserInfo
}

struct UserInfo: Decodable, Identifiable {
    let id: Int
    let patient_id: Int?
    let username: String
    let name: String
    let type: String
    let role: String?
}

struct RegisterRequest: Encodable {
    let first_name: String
    let last_name: String
    let dob: String
    let ssn_last4: String
    let username: String
    let email: String
    let password: String
}

struct MessageResponse: Decodable {
    let message: String?
    let error: String?
}

struct ErrorResponse: Decodable {
    let error: String
}

// MARK: - Dashboard

struct DashboardData: Decodable {
    let active_prescriptions: Int
    let upcoming_appointments: Int
    let outstanding_balance: Double
    let recent_prescriptions: [Prescription]
    let next_appointments: [Appointment]
    let recent_invoices: [Invoice]
}

// MARK: - Patient

struct Patient: Decodable, Identifiable {
    let id: Int
    let first_name: String
    let last_name: String
    let full_name: String
    let dob: String?
    let age: Int?
    let gender: String?
    let email: String?
    let phone: String?
    let address: String?
    let city: String?
    let state: String?
    let zip_code: String?
    let blood_type: String?
}

struct PatientProfile: Decodable {
    let patient: Patient
    let insurance: [[String: AnyCodable]]
    let allergies: [[String: AnyCodable]]
}

struct ProfileUpdateRequest: Encodable {
    let email: String?
    let phone: String?
    let address: String?
    let city: String?
    let state: String?
    let zip_code: String?
}

// MARK: - Prescriptions

struct PrescriptionListResponse: Decodable {
    let prescriptions: [Prescription]
}

struct PrescriptionDetailResponse: Decodable {
    let prescription: Prescription
}

struct Prescription: Decodable, Identifiable {
    let id: Int
    let patient_id: Int?
    let rx_number: String
    let status: String
    let prescriber_name: String?
    let prescribed_date: String?
    let expiry_date: String?
    let notes: String?
    let items: [PrescriptionItem]?
}

struct PrescriptionItem: Decodable, Identifiable {
    let id: Int
    let medication_id: Int
    let medication_name: String?
    let dosage: String
    let frequency: String
    let duration: String?
    let quantity: Int
    let refills_allowed: Int
    let refills_used: Int
    let refills_remaining: Int
    let instructions: String?
    let unit_price: Double?
    let total_price: Double?
}

// MARK: - Billing

struct BillingData: Decodable {
    let invoices: [Invoice]
    let payments: [Payment]
    let outstanding_balance: Double
}

struct Invoice: Decodable, Identifiable {
    let id: Int
    let patient_id: Int?
    let invoice_number: String
    let invoice_date: String?
    let due_date: String?
    let total_amount: Double
    let amount_paid: Double
    let balance_due: Double
    let status: String
}

struct Payment: Decodable, Identifiable {
    let id: Int
    let invoice_id: Int
    let amount: Double
    let payment_method: String
    let payment_date: String?
    let status: String
}

struct PaymentRequest: Encodable {
    let amount: Double
    let payment_method: String
}

// MARK: - Insurance Claims

struct InsuranceListResponse: Decodable {
    let insurance: [[String: AnyCodable]]
}

struct InsuranceClaimRequest: Encodable {
    let invoice_id: Int
    let insurance_id: Int
    let notes: String?
}

struct InsuranceClaimsResponse: Decodable {
    let claims: [InsuranceClaim]
}

struct InsuranceClaim: Decodable, Identifiable {
    let id: Int
    let claim_number: String
    let invoice_id: Int
    let insurance_provider: String?
    let status: String
    let submitted_date: String?
    let claimed_amount: Double
    let approved_amount: Double?
    let copay_amount: Double?
}

// MARK: - Appointments

struct AppointmentsResponse: Decodable {
    let appointments: [Appointment]
}

struct Appointment: Decodable, Identifiable {
    let id: Int
    let provider_name: String?
    let appointment_type: String?
    let scheduled_datetime: String?
    let duration_minutes: Int?
    let status: String
    let reason: String?
}

// MARK: - Records

struct RecordsResponse: Decodable {
    let records: [MedicalRecord]
}

struct MedicalRecord: Decodable, Identifiable {
    let id: Int
    let record_type: String
    let title: String
    let content: String?
    let record_date: String?
    let provider_name: String?
}

// MARK: - Medications

struct MedicationsResponse: Decodable {
    let medications: [Medication]
}

struct Medication: Decodable, Identifiable {
    let id: Int
    let brand_name: String
    let generic_name: String
    let drug_class: String?
    let strength: String?
    let form: String?
    let indications: String?
    let side_effects: String?
    let dosage: String?
    let frequency: String?
    let prescriber_name: String?
}

// MARK: - Notifications

struct NotificationsResponse: Decodable {
    let count: Int
    let notifications: [AppNotification]
}

struct AppNotification: Decodable, Identifiable {
    var id: String { message }
    let type: String
    let title: String?
    let message: String
}

// MARK: - Symptoms & Conditions

struct SymptomsResponse: Decodable {
    let symptoms: [SymptomRef]
}

struct SymptomRef: Decodable, Identifiable {
    let id: Int
    let name: String
    let description: String?
    let body_system: String?
    let common_conditions: String?
    let is_emergency: Bool?
}

struct ConditionsResponse: Decodable {
    let conditions: [ConditionRef]
}

struct ConditionRef: Decodable, Identifiable {
    let id: Int
    let name: String
    let icd10_code: String?
    let category: String?
    let description: String?
    let common_symptoms: String?
    let typical_medications: String?
    let is_chronic: Bool?
}

// MARK: - AnyCodable Helper

struct AnyCodable: Decodable {
    let value: Any

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let intVal = try? container.decode(Int.self) { value = intVal }
        else if let doubleVal = try? container.decode(Double.self) { value = doubleVal }
        else if let boolVal = try? container.decode(Bool.self) { value = boolVal }
        else if let strVal = try? container.decode(String.self) { value = strVal }
        else { value = "" }
    }
}
