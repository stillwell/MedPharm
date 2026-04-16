/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.medications

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.enlightec.medpharm.data.model.MedicationsResponse
import com.enlightec.medpharm.data.repository.MedPharmRepository
import com.enlightec.medpharm.util.Resource
import kotlinx.coroutines.launch

class MedicationsViewModel : ViewModel() {

    private val repository = MedPharmRepository()

    private val _medications = MutableLiveData<Resource<MedicationsResponse>>()
    val medications: LiveData<Resource<MedicationsResponse>> = _medications

    fun loadMedications() {
        _medications.value = Resource.Loading
        viewModelScope.launch {
            _medications.value = repository.getPatientMedications()
        }
    }

    fun searchMedications(query: String) {
        _medications.value = Resource.Loading
        viewModelScope.launch {
            _medications.value = repository.searchMedications(query)
        }
    }
}
