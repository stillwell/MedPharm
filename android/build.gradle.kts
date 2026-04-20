// MedPharm ERP - Android Application
// Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
// Author: Robert Andrew Stillwell
// License: GNU General Public License v3.0

// AGP 8.12.0 + Kotlin 2.1.20 pair with Gradle 9.1.0, which is required
// to launch under JDK 25. Older Gradle (<= 8.13) fails on JDK 25 with
// only the cryptic "25.0.2" error message and no stack trace.
plugins {
    id("com.android.application") version "8.12.0" apply false
    id("org.jetbrains.kotlin.android") version "2.1.20" apply false
}
