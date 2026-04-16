/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.billing

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.enlightec.medpharm.data.model.BillingData
import com.enlightec.medpharm.data.model.InsuranceClaimsResponse
import com.enlightec.medpharm.data.model.MessageResponse
import com.enlightec.medpharm.data.model.PatientProfile
import com.enlightec.medpharm.data.repository.MedPharmRepository
import com.enlightec.medpharm.util.Resource
import kotlinx.coroutines.launch

class BillingViewModel : ViewModel() {

    private val repository = MedPharmRepository()

    private val _billingData = MutableLiveData<Resource<BillingData>>()
    val billingData: LiveData<Resource<BillingData>> = _billingData

    private val _paymentResult = MutableLiveData<Resource<MessageResponse>>()
    val paymentResult: LiveData<Resource<MessageResponse>> = _paymentResult

    private val _profile = MutableLiveData<Resource<PatientProfile>>()
    val profile: LiveData<Resource<PatientProfile>> = _profile

    private val _claims = MutableLiveData<Resource<InsuranceClaimsResponse>>()
    val claims: LiveData<Resource<InsuranceClaimsResponse>> = _claims

    private val _claimResult = MutableLiveData<Resource<MessageResponse>>()
    val claimResult: LiveData<Resource<MessageResponse>> = _claimResult

    fun loadBilling() {
        _billingData.value = Resource.Loading
        viewModelScope.launch {
            _billingData.value = repository.getPatientBilling()
        }
    }

    fun payInvoice(invoiceId: Int, amount: Double, method: String) {
        viewModelScope.launch {
            _paymentResult.value = repository.payInvoice(invoiceId, amount, method)
        }
    }

    fun loadProfile() {
        viewModelScope.launch {
            _profile.value = repository.getPatientProfile()
        }
    }

    fun loadClaims() {
        viewModelScope.launch {
            _claims.value = repository.getInsuranceClaims()
        }
    }

    fun submitInsuranceClaim(invoiceId: Int, insuranceId: Int, notes: String?) {
        viewModelScope.launch {
            _claimResult.value = repository.submitInsuranceClaim(invoiceId, insuranceId, notes)
        }
    }
}
