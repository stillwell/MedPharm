/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm

import android.app.Application
import com.enlightec.medpharm.data.api.ApiClient

class MedPharmApp : Application() {

    override fun onCreate() {
        super.onCreate()
        ApiClient.init(this)
    }
}
