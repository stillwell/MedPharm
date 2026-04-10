/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.prescriptions

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.enlightec.medpharm.data.model.MessageResponse
import com.enlightec.medpharm.data.model.PrescriptionListResponse
import com.enlightec.medpharm.data.repository.MedPharmRepository
import com.enlightec.medpharm.util.Resource
import kotlinx.coroutines.launch

class PrescriptionsViewModel : ViewModel() {

    private val repository = MedPharmRepository()

    private val _prescriptions = MutableLiveData<Resource<PrescriptionListResponse>>()
    val prescriptions: LiveData<Resource<PrescriptionListResponse>> = _prescriptions

    private val _refillResult = MutableLiveData<Resource<MessageResponse>>()
    val refillResult: LiveData<Resource<MessageResponse>> = _refillResult

    fun loadPrescriptions(status: String? = null) {
        _prescriptions.value = Resource.Loading
        viewModelScope.launch {
            _prescriptions.value = repository.getPatientPrescriptions(status)
        }
    }

    fun requestRefill(prescriptionId: Int) {
        viewModelScope.launch {
            _refillResult.value = repository.requestRefill(prescriptionId)
        }
    }
}
