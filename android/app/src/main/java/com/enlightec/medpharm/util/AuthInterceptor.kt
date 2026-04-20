/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.util

import okhttp3.Interceptor
import okhttp3.Response

/**
 * Attaches the bearer token from TokenManager to every outgoing request.
 * Skipped for requests that opt out by adding the header "No-Auth: true".
 */
class AuthInterceptor(private val tokenManager: TokenManager) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()
        val token = tokenManager.accessToken
        val request = if (token != null && original.header("No-Auth") == null) {
            original.newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
        } else {
            original.newBuilder().removeHeader("No-Auth").build()
        }
        return chain.proceed(request)
    }
}
