/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.dashboard

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.enlightec.medpharm.data.model.DashboardData
import com.enlightec.medpharm.data.repository.MedPharmRepository
import com.enlightec.medpharm.util.Resource
import kotlinx.coroutines.launch

class DashboardViewModel : ViewModel() {

    private val repository = MedPharmRepository()

    private val _dashboardData = MutableLiveData<Resource<DashboardData>>()
    val dashboardData: LiveData<Resource<DashboardData>> = _dashboardData

    fun loadDashboard() {
        _dashboardData.value = Resource.Loading
        viewModelScope.launch {
            _dashboardData.value = repository.getPatientDashboard()
        }
    }
}
