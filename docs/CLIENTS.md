# MedPharm ERP — Client Applications Guide

Overview of every MedPharm client: architecture, runtime requirements, build targets, and how each consumes the Cloud REST API.

For build instructions see [COMPILATION.md](COMPILATION.md); for server configuration see [SERVER.md](SERVER.md); for API endpoints see [API.md](API.md).

---

## Table of Contents

1. [Client Portfolio](#client-portfolio)
2. [Qt Desktop (Clinical Staff)](#qt-desktop-clinical-staff)
3. [Flask Web Portal (Patients)](#flask-web-portal-patients)
4. [Android](#android)
5. [iOS](#ios)
6. [macOS](#macos)
7. [Windows Desktop](#windows-desktop)
8. [Shared API Contract](#shared-api-contract)
9. [Token Storage Security](#token-storage-security)
10. [Feature Parity Matrix](#feature-parity-matrix)

---

## Client Portfolio

| Client | Target user | Language | UI framework | Distribution |
|--------|-------------|----------|--------------|--------------|
| **Qt Desktop** | Clinical staff | Python 3.10+ | PyQt6 | `pip` / PyInstaller |
| **Web Portal** | Patients | Python 3.10+ | Flask + Jinja2 | Gunicorn |
| **Android** | Patients | Kotlin | AndroidX + Material 3 | APK / Play Store |
| **iOS** | Patients | Swift | SwiftUI | TestFlight / App Store |
| **macOS** | Patients | Swift | SwiftUI (NavigationSplitView) | `.app` bundle |
| **Windows** | Patients | C# (.NET 8) | WPF + MVVM | `.exe` / MSI |

---

## Qt Desktop (Clinical Staff)

**Path:** [`qt_app/`](../qt_app)

Native PyQt6 client for doctors, psychiatrists, pharmacists, and admins. Talks directly to the SQLAlchemy-backed `DatabaseManager` — **no REST layer** required on the same host.

### Architecture

```
qt_app/
├── main_window.py          # QMainWindow + sidebar navigation
├── styles.py               # Dark theme QSS (teal accents)
├── dialogs/                # Login, prescription, patient
└── widgets/
    ├── dashboard_widget.py
    ├── patient_widget.py
    ├── prescription_widget.py
    ├── medication_widget.py
    ├── appointment_widget.py
    ├── records_widget.py
    ├── billing_widget.py
    ├── symptoms_widget.py
    └── analytics_widget.py
```

### Launch

```bash
./start_desktop.sh           # wraps run_qt.py
```

### Features

* 9 feature widgets (dashboard, patients, Rx, meds, appointments, records, billing, symptoms, analytics)
* Drug-drug interaction checking at prescription save time
* matplotlib analytics embedded in the Qt widget tree
* Role-based visibility (admin sees all, pharmacist sees Rx/meds, etc.)

### Runtime

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| PyQt6 | ≥ 6.6 |
| Display server | X11 / Wayland / Windows DWM / macOS WindowServer |

---

## Flask Web Portal (Patients)

**Path:** [`web/`](../web)

Server-rendered Flask + Jinja2 portal. Patients register with 4-factor identity verification, then self-serve billing, Rx, records.

### Architecture

```
web/
├── app.py              # Flask application factory
├── routes.py           # All route handlers
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/          # 14 Jinja2 templates
```

### Launch

```bash
./start_web.sh           # default port 5000
./start_web.sh 8000      # custom port
```

### Session model

* Server-side Flask sessions (cookie-signed)
* CSRF tokens on every POST form
* PBKDF2-SHA256 password hashing (Werkzeug)

### Routes

| Route | Purpose |
|-------|---------|
| `/login`, `/register`, `/logout` | Auth |
| `/dashboard` | Summary |
| `/prescriptions`, `/prescriptions/<id>` | Rx browsing + refill |
| `/billing`, `/billing/<id>/pay` | Invoice payment |
| `/records`, `/appointments` | Medical history |
| `/medications` | Current meds |
| `/profile` | Demographics, insurance, allergies |

---

## Android

**Path:** [`android/`](../android)

Native Kotlin app targeting **Android 8.0 (API 26)** and up.

### Architecture

* **MVVM** with `ViewModel` + `LiveData`
* **Retrofit + OkHttp** for REST
* **Coroutines** for async work
* **EncryptedSharedPreferences** for token storage
* **Material 3** components, dark theme, bottom navigation

### Module layout

```
android/app/src/main/java/com/enlightec/medpharm/
├── data/           # ApiService, Repository, Models, Resource<T>
├── ui/             # Activities, Fragments, ViewModels, Adapters
└── util/           # AuthInterceptor, helpers
```

### API base URL configuration

1. Edit `BuildConfig.API_BASE_URL` in `app/build.gradle.kts`, **or**
2. Override at runtime in `Settings` (saved via EncryptedSharedPreferences).

Debug builds default to `http://10.0.2.2:8080/api/v1/` (the emulator loopback).

### Build

See [COMPILATION.md § Android](COMPILATION.md#android-kotlin--gradle).

---

## iOS

**Path:** [`ios/MedPharm`](../ios/MedPharm)

Pure SwiftUI application targeting **iOS 16+**.

### Architecture

* `APIClient` using `URLSession` + async/await
* `AuthManager` (`ObservableObject`) holds login state
* `KeychainHelper` wraps iOS Keychain Services for token storage
* `NavigationStack` + `.searchable` modifier for filtering

### Module layout

```
ios/MedPharm/MedPharm/
├── Models/          # Codable data models
├── Services/        # APIClient, AuthManager, KeychainHelper
└── Views/           # DashboardView, PrescriptionsView, BillingView, ...
```

### Tabs

Dashboard · Prescriptions · Billing · Appointments · More (records, meds, symptoms, profile).

---

## macOS

**Path:** [`macos/MedPharm`](../macos/MedPharm)

Shares `Models/` and `Services/` source with iOS. Uses `NavigationSplitView` for sidebar-driven navigation.

* Native **SwiftUI Table** for prescriptions and medications
* Mac-idiomatic keyboard shortcuts and menu bar
* Keychain-based token persistence (same helper as iOS)

---

## Windows Desktop

**Path:** [`windows/MedPharm`](../windows/MedPharm)

WPF application on **.NET 8**.

### Architecture

* **MVVM** via `CommunityToolkit.Mvvm`
* **HttpClient** + **Newtonsoft.Json** for REST
* **DPAPI** (Windows Data Protection API) for token-at-rest encryption
* Sidebar navigation, XAML data templates

### Module layout

```
windows/MedPharm/
├── Models/          # API data models
├── Services/        # ApiClient, TokenStore (DPAPI)
├── Views/           # XAML pages + dialogs
├── App.xaml(.cs)
└── MedPharm.csproj
```

### Configure API host

Set an environment variable before launch, or edit `Services/ApiClient.cs`:

```powershell
setx MEDPHARM_API "https://api.example.com/api/v1"
```

---

## Shared API Contract

Every mobile / desktop client speaks the same REST surface documented in [API.md](API.md):

1. `POST /auth/login/patient` → store tokens securely
2. `GET /patient/dashboard` → render home screen
3. Feature screens hit `/patient/prescriptions`, `/patient/billing`, etc.
4. On `401`, call `POST /auth/refresh` with the refresh token; on repeated `401`, force logout.

A reference implementation lives in each client's `APIClient` / `ApiClient` / `ApiService` class.

---

## Token Storage Security

| Platform | Mechanism | Notes |
|----------|-----------|-------|
| Android | `EncryptedSharedPreferences` (Jetpack Security) | AES-256 via KeyStore |
| iOS / macOS | Keychain Services | `kSecClassGenericPassword`, `kSecAttrAccessibleAfterFirstUnlock` |
| Windows | DPAPI (`ProtectedData`) | Per-user scope |
| Web Portal | Server-side session cookie | `HttpOnly`, `Secure` in production |
| Qt Desktop | In-process only | No persistent token store — reauth each launch |

Never log tokens, never send them to analytics, never include them in crash reports.

---

## Feature Parity Matrix

| Feature | Qt | Web | Android | iOS | macOS | Windows |
|---------|:--:|:---:|:-------:|:---:|:-----:|:-------:|
| Dashboard / KPI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Prescriptions view | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Prescription refill request | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| Prescription create | ✅ | — | — | — | — | — |
| Drug interaction check | ✅ | — | — | — | — | — |
| Billing list | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Pay invoice | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Insurance claims — file | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| Insurance claims — process | ✅ | — | — | — | — | — |
| Medical records | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Appointments | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Medication reference | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Symptoms / conditions | ✅ | — | ✅ | ✅ | ✅ | — |
| Analytics (charts) | ✅ | — | — | — | — | — |
| Profile edit | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Role | Staff | Patient | Patient | Patient | Patient | Patient |

✅ = implemented · — = not in scope for that client.
