# MedPharm — Android Client

Native Kotlin patient portal for Android 8.0+ (API 26).

Build instructions: [`docs/COMPILATION.md § Android`](../docs/COMPILATION.md#android-kotlin--gradle).
Feature inventory: [`docs/CLIENTS.md § Android`](../docs/CLIENTS.md#android).

---

## Tech stack

| Layer | Technology |
|-------|------------|
| UI | AndroidX + Material 3, ViewBinding |
| Architecture | MVVM (`ViewModel`, `LiveData`) + Repository |
| Async | Kotlin Coroutines |
| Networking | Retrofit 2 + OkHttp 4 + Gson |
| Secure storage | `EncryptedSharedPreferences` (Jetpack Security) |
| Minimum SDK | 26 (Android 8.0) |
| Target SDK | 34 (Android 14) |

---

## Project layout

```
android/
├── app/
│   ├── build.gradle.kts
│   ├── proguard-rules.pro
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/com/enlightec/medpharm/
│       │   ├── data/          # ApiService, Repository, Models, Resource<T>
│       │   ├── ui/            # Activities, Fragments, ViewModels, Adapters
│       │   └── util/          # AuthInterceptor, helpers
│       └── res/               # Layouts, drawables, strings, themes
├── build.gradle.kts
├── gradle/
├── gradle.properties
├── gradlew / gradlew.bat
└── settings.gradle.kts
```

---

## Build

```bash
# Debug APK
./gradlew assembleDebug
# app/build/outputs/apk/debug/app-debug.apk

# Release AAB (requires signing config — see COMPILATION.md)
./gradlew bundleRelease
```

Install on a connected device or emulator:

```bash
./gradlew installDebug
```

---

## Configure API host

Default in debug: `http://10.0.2.2:8080/api/v1/` (Android emulator loopback to host).

Override per build variant in `app/build.gradle.kts`:

```kotlin
android {
    buildTypes {
        debug   { buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8080/api/v1/\"") }
        release { buildConfigField("String", "API_BASE_URL", "\"https://api.example.com/api/v1/\"") }
    }
}
```

Alternatively expose an in-app Settings screen that writes to `EncryptedSharedPreferences` and pass the value to the Retrofit builder.

---

## Required permissions

| Permission | Reason |
|------------|--------|
| `INTERNET` | REST API calls |
| `ACCESS_NETWORK_STATE` | Offline detection for UX |

No location, contacts, camera, or microphone permissions are requested.
