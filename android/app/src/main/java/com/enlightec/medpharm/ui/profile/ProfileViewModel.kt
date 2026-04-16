/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.profile

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.enlightec.medpharm.data.model.MessageResponse
import com.enlightec.medpharm.data.model.PatientProfile
import com.enlightec.medpharm.data.model.ProfileUpdateRequest
import com.enlightec.medpharm.data.repository.MedPharmRepository
import com.enlightec.medpharm.util.Resource
import kotlinx.coroutines.launch

class ProfileViewModel : ViewModel() {

    private val repository = MedPharmRepository()

    private val _profile = MutableLiveData<Resource<PatientProfile>>()
    val profile: LiveData<Resource<PatientProfile>> = _profile

    private val _updateResult = MutableLiveData<Resource<MessageResponse>>()
    val updateResult: LiveData<Resource<MessageResponse>> = _updateResult

    fun loadProfile() {
        _profile.value = Resource.Loading
        viewModelScope.launch {
            _profile.value = repository.getPatientProfile()
        }
    }

    fun updateProfile(request: ProfileUpdateRequest) {
        viewModelScope.launch {
            _updateResult.value = repository.updatePatientProfile(request)
        }
    }
}
