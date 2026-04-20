/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.data.api

import android.content.Context
import com.enlightec.medpharm.BuildConfig
import com.enlightec.medpharm.util.AuthInterceptor
import com.enlightec.medpharm.util.TokenManager
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Single Retrofit instance for the app. Call [init] once in Application.onCreate.
 */
object ApiClient {

    @Volatile
    private var retrofit: Retrofit? = null

    val apiService: ApiService
        get() = requireNotNull(retrofit) {
            "ApiClient.init(context) must be called before apiService is used"
        }.create(ApiService::class.java)

    fun init(context: Context) {
        if (retrofit != null) return
        synchronized(this) {
            if (retrofit != null) return

            val tokenManager = TokenManager.getInstance(context)

            val logging = HttpLoggingInterceptor().apply {
                level = if (BuildConfig.DEBUG) {
                    HttpLoggingInterceptor.Level.BASIC
                } else {
                    HttpLoggingInterceptor.Level.NONE
                }
            }

            val client = OkHttpClient.Builder()
                .addInterceptor(AuthInterceptor(tokenManager))
                .addInterceptor(logging)
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .build()

            val baseUrl = BuildConfig.API_BASE_URL.trimEnd('/') + "/"

            retrofit = Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
        }
    }
}
