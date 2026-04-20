/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.data.model

import com.google.gson.annotations.SerializedName

// ── Authentication ───────────────────────────────────────────────────────────

data class LoginResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("refresh_token") val refreshToken: String,
    val user: UserInfo,
)

data class UserInfo(
    val id: Int,
    @SerializedName("patient_id") val patientId: Int? = null,
    val username: String,
    val name: String,
    val type: String,
    val role: String? = null,
)

data class RegisterRequest(
    @SerializedName("first_name") val firstName: String,
    @SerializedName("last_name") val lastName: String,
    val dob: String,
    @SerializedName("ssn_last4") val ssnLast4: String,
    val username: String,
    val email: String,
    val password: String,
)

data class MessageResponse(
    val message: String? = null,
    val error: String? = null,
)

// ── Dashboard ────────────────────────────────────────────────────────────────

data class DashboardData(
    @SerializedName("active_prescriptions") val activePrescriptions: Int = 0,
    @SerializedName("upcoming_appointments") val upcomingAppointments: Int = 0,
    @SerializedName("outstanding_balance") val outstandingBalance: Double = 0.0,
)

// ── Profile ──────────────────────────────────────────────────────────────────

data class Patient(
    val id: Int = 0,
    @SerializedName("full_name") val fullName: String = "",
    val dob: String? = null,
    val gender: String? = null,
    @SerializedName("blood_type") val bloodType: String? = null,
    val email: String? = null,
    val phone: String? = null,
    val address: String? = null,
    val city: String? = null,
    val state: String? = null,
    @SerializedName("zip_code") val zipCode: String? = null,
)

data class PatientProfile(
    val patient: Patient,
    val insurance: List<InsuranceRecord> = emptyList(),
    val allergies: List<Map<String, Any>> = emptyList(),
)

data class ProfileUpdateRequest(
    val email: String,
    val phone: String,
    val address: String,
    val city: String,
    val state: String,
    @SerializedName("zip_code") val zipCode: String,
)

// ── Prescriptions ────────────────────────────────────────────────────────────

data class Prescription(
    val id: Int,
    @SerializedName("rx_number") val rxNumber: String,
    val status: String,
    @SerializedName("prescriber_name") val prescriberName: String? = null,
    @SerializedName("prescribed_date") val prescribedDate: String? = null,
    val items: List<PrescriptionItem>? = null,
)

data class PrescriptionItem(
    val id: Int = 0,
    @SerializedName("medication_name") val medicationName: String? = null,
    val dosage: String = "",
    val frequency: String = "",
    @SerializedName("refills_remaining") val refillsRemaining: Int = 0,
)

data class PrescriptionListResponse(
    val prescriptions: List<Prescription> = emptyList(),
)

// ── Medications ──────────────────────────────────────────────────────────────

data class Medication(
    val id: Int,
    @SerializedName("brand_name") val brandName: String = "",
    @SerializedName("generic_name") val genericName: String = "",
    @SerializedName("drug_class") val drugClass: String? = null,
    val dosage: String? = null,
    val frequency: String? = null,
    @SerializedName("prescriber_name") val prescriberName: String? = null,
    val indications: String? = null,
)

data class MedicationsResponse(
    val medications: List<Medication> = emptyList(),
)

// ── Billing ──────────────────────────────────────────────────────────────────

data class Invoice(
    val id: Int,
    @SerializedName("invoice_number") val invoiceNumber: String,
    @SerializedName("invoice_date") val invoiceDate: String? = null,
    @SerializedName("total_amount") val totalAmount: Double = 0.0,
    @SerializedName("balance_due") val balanceDue: Double = 0.0,
    val status: String = "",
)

data class BillingData(
    val invoices: List<Invoice> = emptyList(),
    @SerializedName("outstanding_balance") val outstandingBalance: Double = 0.0,
)

// ── Insurance ────────────────────────────────────────────────────────────────

data class InsuranceRecord(
    val id: Int,
    @SerializedName("provider_name") val providerName: String = "",
    @SerializedName("policy_number") val policyNumber: String = "",
    @SerializedName("is_active") val isActive: Boolean = true,
)

data class InsuranceClaimsResponse(
    val claims: List<Map<String, Any>> = emptyList(),
)

// ── Medical Records ──────────────────────────────────────────────────────────

data class MedicalRecord(
    val id: Int,
    val title: String = "",
    @SerializedName("record_type") val recordType: String = "",
    @SerializedName("record_date") val recordDate: String? = null,
    @SerializedName("provider_name") val providerName: String? = null,
    val content: String? = null,
)

data class RecordsResponse(
    val records: List<MedicalRecord> = emptyList(),
)

// ── Appointments ─────────────────────────────────────────────────────────────

data class Appointment(
    val id: Int,
    @SerializedName("scheduled_datetime") val scheduledDatetime: String? = null,
    @SerializedName("provider_name") val providerName: String? = null,
    @SerializedName("appointment_type") val appointmentType: String? = null,
    val status: String = "",
    val reason: String? = null,
)

data class AppointmentsResponse(
    val appointments: List<Appointment> = emptyList(),
)
