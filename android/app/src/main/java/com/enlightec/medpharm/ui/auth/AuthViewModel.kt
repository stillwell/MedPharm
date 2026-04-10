/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.auth

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.enlightec.medpharm.data.model.LoginResponse
import com.enlightec.medpharm.data.model.MessageResponse
import com.enlightec.medpharm.data.model.RegisterRequest
import com.enlightec.medpharm.data.repository.MedPharmRepository
import com.enlightec.medpharm.util.Resource
import kotlinx.coroutines.launch

class AuthViewModel : ViewModel() {

    private val repository = MedPharmRepository()

    private val _loginResult = MutableLiveData<Resource<LoginResponse>>()
    val loginResult: LiveData<Resource<LoginResponse>> = _loginResult

    private val _registerResult = MutableLiveData<Resource<MessageResponse>>()
    val registerResult: LiveData<Resource<MessageResponse>> = _registerResult

    fun patientLogin(username: String, password: String) {
        _loginResult.value = Resource.Loading
        viewModelScope.launch {
            _loginResult.value = repository.patientLogin(username, password)
        }
    }

    fun staffLogin(username: String, password: String) {
        _loginResult.value = Resource.Loading
        viewModelScope.launch {
            _loginResult.value = repository.staffLogin(username, password)
        }
    }

    fun register(request: RegisterRequest) {
        _registerResult.value = Resource.Loading
        viewModelScope.launch {
            _registerResult.value = repository.register(request)
        }
    }
}
