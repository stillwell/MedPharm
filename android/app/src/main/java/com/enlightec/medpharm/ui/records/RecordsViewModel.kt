/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.records

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.enlightec.medpharm.data.model.RecordsResponse
import com.enlightec.medpharm.data.repository.MedPharmRepository
import com.enlightec.medpharm.util.Resource
import kotlinx.coroutines.launch

class RecordsViewModel : ViewModel() {

    private val repository = MedPharmRepository()

    private val _records = MutableLiveData<Resource<RecordsResponse>>()
    val records: LiveData<Resource<RecordsResponse>> = _records

    fun loadRecords(type: String? = null) {
        _records.value = Resource.Loading
        viewModelScope.launch {
            _records.value = repository.getPatientRecords(type)
        }
    }
}
