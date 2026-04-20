/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.data.api

import android.content.Context
import android.content.SharedPreferences

/**
 * Persists the user-configured API base URL.
 *
 * Users may enter either the full API URL
 * (https://host:port/api/v1) or the host origin (https://host:port);
 * normalizeForRetrofit() strips the "/api/v1" suffix since
 * [ApiService] already prefixes each endpoint with "api/v1/".
 */
class ServerConfig private constructor(context: Context) {

    private val prefs: SharedPreferences =
        context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    var apiBaseUrl: String
        get() = prefs.getString(KEY_API_BASE_URL, DEFAULT_API_BASE_URL) ?: DEFAULT_API_BASE_URL
        set(value) {
            val trimmed = value.trim().trimEnd('/')
            val toStore = if (trimmed.isEmpty()) DEFAULT_API_BASE_URL else trimmed
            prefs.edit().putString(KEY_API_BASE_URL, toStore).apply()
        }

    /** Retrofit base URL — host origin only, trailing slash included. */
    fun normalizeForRetrofit(): String {
        val url = apiBaseUrl
        val stripped = if (url.endsWith("/api/v1")) url.removeSuffix("/api/v1") else url
        return stripped.trimEnd('/') + "/"
    }

    companion object {
        const val DEFAULT_API_BASE_URL = "https://medpharm-erp.enlightec.com:8080/api/v1"
        private const val PREFS_NAME = "medpharm_server_prefs"
        private const val KEY_API_BASE_URL = "api_base_url"

        @Volatile
        private var instance: ServerConfig? = null

        fun getInstance(context: Context): ServerConfig {
            return instance ?: synchronized(this) {
                instance ?: ServerConfig(context).also { instance = it }
            }
        }
    }
}
