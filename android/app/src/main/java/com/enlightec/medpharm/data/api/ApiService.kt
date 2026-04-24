/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.data.api

import com.enlightec.medpharm.data.model.AppointmentsResponse
import com.enlightec.medpharm.data.model.BillingData
import com.enlightec.medpharm.data.model.DashboardData
import com.enlightec.medpharm.data.model.InsuranceClaimsResponse
import com.enlightec.medpharm.data.model.LoginResponse
import com.enlightec.medpharm.data.model.MedicationsResponse
import com.enlightec.medpharm.data.model.MessageResponse
import com.enlightec.medpharm.data.model.MessageThreadDetailResponse
import com.enlightec.medpharm.data.model.MessageThreadsResponse
import com.enlightec.medpharm.data.model.NewThreadRequest
import com.enlightec.medpharm.data.model.NewThreadResponse
import com.enlightec.medpharm.data.model.PatientProfile
import com.enlightec.medpharm.data.model.ProvidersResponse
import com.enlightec.medpharm.data.model.ReplyRequest
import com.enlightec.medpharm.data.model.PrescriptionListResponse
import com.enlightec.medpharm.data.model.ProfileUpdateRequest
import com.enlightec.medpharm.data.model.RecordsResponse
import com.enlightec.medpharm.data.model.RegisterRequest
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

interface ApiService {

    @POST("api/v1/auth/login/patient")
    suspend fun patientLogin(@Body body: Map<String, String>): Response<LoginResponse>

    @POST("api/v1/auth/login/staff")
    suspend fun staffLogin(@Body body: Map<String, String>): Response<LoginResponse>

    @POST("api/v1/auth/register")
    suspend fun register(@Body body: RegisterRequest): Response<MessageResponse>

    @GET("api/v1/patient/dashboard")
    suspend fun getDashboard(): Response<DashboardData>

    @GET("api/v1/patient/profile")
    suspend fun getProfile(): Response<PatientProfile>

    @PUT("api/v1/patient/profile")
    suspend fun updateProfile(@Body body: ProfileUpdateRequest): Response<MessageResponse>

    @GET("api/v1/patient/prescriptions")
    suspend fun getPrescriptions(@Query("status") status: String? = null): Response<PrescriptionListResponse>

    @POST("api/v1/patient/prescriptions/{rxId}/refill")
    suspend fun requestRefill(@Path("rxId") rxId: Int): Response<MessageResponse>

    @GET("api/v1/patient/billing")
    suspend fun getBilling(): Response<BillingData>

    @POST("api/v1/patient/billing/{invoiceId}/pay")
    suspend fun payInvoice(
        @Path("invoiceId") invoiceId: Int,
        @Body body: Map<String, @JvmSuppressWildcards Any>,
    ): Response<MessageResponse>

    @GET("api/v1/patient/records")
    suspend fun getRecords(@Query("type") type: String? = null): Response<RecordsResponse>

    @GET("api/v1/patient/appointments")
    suspend fun getAppointments(): Response<AppointmentsResponse>

    @GET("api/v1/patient/medications")
    suspend fun getMedications(): Response<MedicationsResponse>

    @GET("api/v1/medications/search")
    suspend fun searchMedications(@Query("q") query: String): Response<MedicationsResponse>

    @GET("api/v1/patient/insurance/claims")
    suspend fun getInsuranceClaims(): Response<InsuranceClaimsResponse>

    @POST("api/v1/patient/insurance/claims")
    suspend fun submitInsuranceClaim(
        @Body body: Map<String, @JvmSuppressWildcards Any?>,
    ): Response<MessageResponse>

    // ── Secure Messaging (patient-facing) ──

    @GET("api/v1/patient/messages")
    suspend fun getMessageThreads(): Response<MessageThreadsResponse>

    @POST("api/v1/patient/messages")
    suspend fun createMessageThread(@Body body: NewThreadRequest): Response<NewThreadResponse>

    @GET("api/v1/patient/messages/{threadId}")
    suspend fun getMessageThread(@Path("threadId") threadId: Int): Response<MessageThreadDetailResponse>

    @POST("api/v1/patient/messages/{threadId}/reply")
    suspend fun replyToThread(
        @Path("threadId") threadId: Int,
        @Body body: ReplyRequest,
    ): Response<MessageResponse>

    @GET("api/v1/patient/messages/providers")
    suspend fun getAvailableProviders(): Response<ProvidersResponse>
}
