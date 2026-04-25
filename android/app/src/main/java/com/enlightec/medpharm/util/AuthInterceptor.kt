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
 *
 * Also sends `ngrok-skip-browser-warning` so the free-tier ngrok edge
 * does not return its HTML interstitial to a JSON client. Harmless when
 * the API is reached directly without an ngrok tunnel.
 */
class AuthInterceptor(private val tokenManager: TokenManager) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()
        val token = tokenManager.accessToken
        val builder = if (token != null && original.header("No-Auth") == null) {
            original.newBuilder()
                .header("Authorization", "Bearer $token")
        } else {
            original.newBuilder().removeHeader("No-Auth")
        }
        builder.header("ngrok-skip-browser-warning", "true")
        return chain.proceed(builder.build())
    }
}
