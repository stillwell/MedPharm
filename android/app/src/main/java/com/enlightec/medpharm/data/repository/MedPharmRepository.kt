/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.data.repository

import com.enlightec.medpharm.data.api.ApiClient
import com.enlightec.medpharm.data.model.AppointmentsResponse
import com.enlightec.medpharm.data.model.BillingData
import com.enlightec.medpharm.data.model.DashboardData
import com.enlightec.medpharm.data.model.InsuranceClaimsResponse
import com.enlightec.medpharm.data.model.LoginResponse
import com.enlightec.medpharm.data.model.MedicationsResponse
import com.enlightec.medpharm.data.model.MessageResponse
import com.enlightec.medpharm.data.model.PatientProfile
import com.enlightec.medpharm.data.model.PrescriptionListResponse
import com.enlightec.medpharm.data.model.ProfileUpdateRequest
import com.enlightec.medpharm.data.model.RecordsResponse
import com.enlightec.medpharm.data.model.RegisterRequest
import com.enlightec.medpharm.util.Resource
import com.google.gson.Gson
import retrofit2.Response

class MedPharmRepository {

    private val api = ApiClient.apiService

    suspend fun patientLogin(username: String, password: String): Resource<LoginResponse> =
        safeCall { api.patientLogin(mapOf("username" to username, "password" to password)) }

    suspend fun staffLogin(username: String, password: String): Resource<LoginResponse> =
        safeCall { api.staffLogin(mapOf("username" to username, "password" to password)) }

    suspend fun register(request: RegisterRequest): Resource<MessageResponse> =
        safeCall { api.register(request) }

    suspend fun getPatientDashboard(): Resource<DashboardData> =
        safeCall { api.getDashboard() }

    suspend fun getPatientProfile(): Resource<PatientProfile> =
        safeCall { api.getProfile() }

    suspend fun updatePatientProfile(request: ProfileUpdateRequest): Resource<MessageResponse> =
        safeCall { api.updateProfile(request) }

    suspend fun getPatientPrescriptions(status: String?): Resource<PrescriptionListResponse> =
        safeCall { api.getPrescriptions(status) }

    suspend fun requestRefill(prescriptionId: Int): Resource<MessageResponse> =
        safeCall { api.requestRefill(prescriptionId) }

    suspend fun getPatientBilling(): Resource<BillingData> =
        safeCall { api.getBilling() }

    suspend fun payInvoice(invoiceId: Int, amount: Double, method: String): Resource<MessageResponse> =
        safeCall {
            api.payInvoice(
                invoiceId,
                mapOf("amount" to amount, "payment_method" to method),
            )
        }

    suspend fun getPatientRecords(type: String?): Resource<RecordsResponse> =
        safeCall { api.getRecords(type) }

    suspend fun getPatientAppointments(): Resource<AppointmentsResponse> =
        safeCall { api.getAppointments() }

    suspend fun getPatientMedications(): Resource<MedicationsResponse> =
        safeCall { api.getMedications() }

    suspend fun searchMedications(query: String): Resource<MedicationsResponse> =
        safeCall { api.searchMedications(query) }

    suspend fun getInsuranceClaims(): Resource<InsuranceClaimsResponse> =
        safeCall { api.getInsuranceClaims() }

    suspend fun submitInsuranceClaim(
        invoiceId: Int,
        insuranceId: Int,
        notes: String?,
    ): Resource<MessageResponse> = safeCall {
        val body = mutableMapOf<String, Any?>(
            "invoice_id" to invoiceId,
            "insurance_id" to insuranceId,
        )
        if (notes != null) body["notes"] = notes
        api.submitInsuranceClaim(body)
    }

    private suspend inline fun <T : Any> safeCall(
        crossinline block: suspend () -> Response<T>,
    ): Resource<T> {
        return try {
            val response = block()
            val body = response.body()
            if (response.isSuccessful && body != null) {
                Resource.Success(body)
            } else {
                Resource.Error(parseErrorMessage(response), response.code())
            }
        } catch (e: Exception) {
            Resource.Error(e.message ?: "Network error")
        }
    }

    private fun parseErrorMessage(response: Response<*>): String {
        val raw = response.errorBody()?.string().orEmpty()
        if (raw.isBlank()) return "Request failed (${response.code()})"
        return try {
            val map = Gson().fromJson(raw, Map::class.java)
            (map?.get("error") ?: map?.get("message"))?.toString()
                ?: "Request failed (${response.code()})"
        } catch (_: Exception) {
            "Request failed (${response.code()})"
        }
    }
}
