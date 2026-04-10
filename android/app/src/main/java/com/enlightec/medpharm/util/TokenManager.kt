/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.util

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Manages JWT tokens using Android EncryptedSharedPreferences.
 * Stores access tokens, refresh tokens, and basic user info securely.
 */
class TokenManager private constructor(context: Context) {

    private val prefs: SharedPreferences

    init {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        prefs = EncryptedSharedPreferences.create(
            context,
            PREFS_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    var accessToken: String?
        get() = prefs.getString(KEY_ACCESS_TOKEN, null)
        set(value) = prefs.edit().putString(KEY_ACCESS_TOKEN, value).apply()

    var refreshToken: String?
        get() = prefs.getString(KEY_REFRESH_TOKEN, null)
        set(value) = prefs.edit().putString(KEY_REFRESH_TOKEN, value).apply()

    var userId: Int
        get() = prefs.getInt(KEY_USER_ID, -1)
        set(value) = prefs.edit().putInt(KEY_USER_ID, value).apply()

    var patientId: Int
        get() = prefs.getInt(KEY_PATIENT_ID, -1)
        set(value) = prefs.edit().putInt(KEY_PATIENT_ID, value).apply()

    var username: String?
        get() = prefs.getString(KEY_USERNAME, null)
        set(value) = prefs.edit().putString(KEY_USERNAME, value).apply()

    var userName: String?
        get() = prefs.getString(KEY_USER_NAME, null)
        set(value) = prefs.edit().putString(KEY_USER_NAME, value).apply()

    var userType: String?
        get() = prefs.getString(KEY_USER_TYPE, null)
        set(value) = prefs.edit().putString(KEY_USER_TYPE, value).apply()

    var userRole: String?
        get() = prefs.getString(KEY_USER_ROLE, null)
        set(value) = prefs.edit().putString(KEY_USER_ROLE, value).apply()

    val isLoggedIn: Boolean
        get() = accessToken != null

    val isPatient: Boolean
        get() = userType == "patient"

    val isStaff: Boolean
        get() = userType == "staff"

    fun saveLoginResponse(
        accessToken: String, refreshToken: String,
        userId: Int, patientId: Int = -1,
        username: String, name: String,
        type: String, role: String = ""
    ) {
        prefs.edit()
            .putString(KEY_ACCESS_TOKEN, accessToken)
            .putString(KEY_REFRESH_TOKEN, refreshToken)
            .putInt(KEY_USER_ID, userId)
            .putInt(KEY_PATIENT_ID, patientId)
            .putString(KEY_USERNAME, username)
            .putString(KEY_USER_NAME, name)
            .putString(KEY_USER_TYPE, type)
            .putString(KEY_USER_ROLE, role)
            .apply()
    }

    fun clearSession() {
        prefs.edit().clear().apply()
    }

    companion object {
        private const val PREFS_NAME = "medpharm_secure_prefs"
        private const val KEY_ACCESS_TOKEN = "access_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
        private const val KEY_USER_ID = "user_id"
        private const val KEY_PATIENT_ID = "patient_id"
        private const val KEY_USERNAME = "username"
        private const val KEY_USER_NAME = "user_name"
        private const val KEY_USER_TYPE = "user_type"
        private const val KEY_USER_ROLE = "user_role"

        @Volatile
        private var instance: TokenManager? = null

        fun getInstance(context: Context): TokenManager {
            return instance ?: synchronized(this) {
                instance ?: TokenManager(context.applicationContext).also { instance = it }
            }
        }
    }
}
