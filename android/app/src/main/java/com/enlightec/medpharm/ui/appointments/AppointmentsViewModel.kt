/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.appointments

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.enlightec.medpharm.data.model.AppointmentsResponse
import com.enlightec.medpharm.data.repository.MedPharmRepository
import com.enlightec.medpharm.util.Resource
import kotlinx.coroutines.launch

class AppointmentsViewModel : ViewModel() {

    private val repository = MedPharmRepository()

    private val _appointments = MutableLiveData<Resource<AppointmentsResponse>>()
    val appointments: LiveData<Resource<AppointmentsResponse>> = _appointments

    fun loadAppointments() {
        _appointments.value = Resource.Loading
        viewModelScope.launch {
            _appointments.value = repository.getPatientAppointments()
        }
    }
}
