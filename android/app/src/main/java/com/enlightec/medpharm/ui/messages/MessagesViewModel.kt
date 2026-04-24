/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.messages

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.enlightec.medpharm.data.model.MessageThreadDetailResponse
import com.enlightec.medpharm.data.model.MessageThreadsResponse
import com.enlightec.medpharm.data.model.NewThreadResponse
import com.enlightec.medpharm.data.model.ProvidersResponse
import com.enlightec.medpharm.data.repository.MedPharmRepository
import com.enlightec.medpharm.util.Resource
import kotlinx.coroutines.launch

class MessagesViewModel : ViewModel() {

    private val repository = MedPharmRepository()

    private val _threads = MutableLiveData<Resource<MessageThreadsResponse>>()
    val threads: LiveData<Resource<MessageThreadsResponse>> = _threads

    private val _thread = MutableLiveData<Resource<MessageThreadDetailResponse>>()
    val thread: LiveData<Resource<MessageThreadDetailResponse>> = _thread

    private val _providers = MutableLiveData<Resource<ProvidersResponse>>()
    val providers: LiveData<Resource<ProvidersResponse>> = _providers

    private val _newThread = MutableLiveData<Resource<NewThreadResponse>>()
    val newThread: LiveData<Resource<NewThreadResponse>> = _newThread

    private val _replyResult = MutableLiveData<Resource<*>>()
    val replyResult: LiveData<Resource<*>> = _replyResult

    fun loadThreads() {
        _threads.value = Resource.Loading
        viewModelScope.launch {
            _threads.value = repository.getMessageThreads()
        }
    }

    fun loadThread(threadId: Int) {
        _thread.value = Resource.Loading
        viewModelScope.launch {
            _thread.value = repository.getMessageThread(threadId)
        }
    }

    fun loadProviders() {
        viewModelScope.launch {
            _providers.value = repository.getAvailableProviders()
        }
    }

    fun createThread(subject: String, body: String, providerId: Int?) {
        _newThread.value = Resource.Loading
        viewModelScope.launch {
            _newThread.value = repository.createMessageThread(subject, body, providerId)
        }
    }

    fun reply(threadId: Int, body: String) {
        _replyResult.value = Resource.Loading
        viewModelScope.launch {
            _replyResult.value = repository.replyToThread(threadId, body)
        }
    }
}
