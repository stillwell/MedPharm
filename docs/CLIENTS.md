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
* Diagnosis picker on the New Prescription dialog — selects from the patient's active/chronic ICD-10 diagnoses, with an inline "+ New Diagnosis" form; the prescriber's NPI (10-digit NPPES identifier) is shown on every prescription header
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

The login screen has a **Server URL** field (with a "Reset to default" link) that
lets the user point the app at any compatible MedPharm API host.

* The value is persisted in `SharedPreferences` (`medpharm_server_prefs`) via
  `com.enlightec.medpharm.data.api.ServerConfig`.
* Built-in default: `https://medpharm-erp.enlightec.com:8080/api/v1`
  (see `ServerConfig.DEFAULT_API_BASE_URL`).
* Change the compiled-in default by editing that constant and rebuilding.
* At runtime, submitting a different URL calls `ApiClient.reconfigure()` so the
  new base URL takes effect without restarting the app.

### TLS / self-signed certs

The app talks HTTPS by default. `res/xml/network_security_config.xml` enforces:

* Production (base-config): HTTPS only, system CA trust anchors only.
* Localhost / `10.0.2.2` (emulator host loopback): cleartext permitted and **user-installed** CAs trusted — so an engineer running the self-signed dev server can import the MedPharm `fullchain.pem` into Android's user credential store and dismiss the warning. OkHttp honors the user CA automatically when the domain-config trust-anchors list includes `user`.

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

### API base URL configuration

The login screen exposes a **Server URL** field (with a "Reset to default" button).

* Built-in default: `https://medpharm-erp.enlightec.com:8080/api/v1`
  (see `APIClient.defaultBaseURL`).
* User overrides are stored in `UserDefaults` under the key `medpharm.apiBaseURL`.
* `APIClient.saveBaseURL(_:)` persists the value and hot-swaps it on the shared
  client actor — no app relaunch required.

### TLS / self-signed certs

`URLSession` enforces full chain validation against the iOS trust store. For a self-signed dev cert, either:

* Drag the `fullchain.pem` onto a running iOS Simulator, then enable it under **Settings → General → About → Certificate Trust Settings**, or
* Email / AirDrop the `.pem` to a physical device, then enable trust in the same settings path.

Never ship a custom `URLSessionDelegate` that blindly accepts invalid certs — that circumvents App Transport Security and is a HIPAA transmission-security violation.

---

## macOS

**Path:** [`macos/MedPharm`](../macos/MedPharm)

Shares `Models/` and `Services/` source with iOS. Uses `NavigationSplitView` for sidebar-driven navigation.

* Native **SwiftUI Table** for prescriptions and medications
* Mac-idiomatic keyboard shortcuts and menu bar
* Keychain-based token persistence (same helper as iOS)

### API base URL configuration

Identical UX to iOS: a **Server URL** field on the login view with an inline
"Reset" link. Persisted in `UserDefaults` (`medpharm.apiBaseURL`) and
hot-applied via `APIClient.saveBaseURL(_:)`.

### TLS / self-signed certs

Import `fullchain.pem` into the macOS **Keychain Access → login** keychain and set it to **Always Trust**. `URLSession` then accepts the cert on the next request — no app restart required.

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

### API base URL configuration

The login window has a **Server URL** field with a "Reset to Default" button.

* Built-in default: `https://medpharm-erp.enlightec.com:8080/api/v1`
  (see `AppSettings.DefaultApiBaseUrl`).
* User overrides are persisted as JSON in
  `%APPDATA%\MedPharm\settings.json` by `SettingsStore`.
* On submit, `App.SaveSettings(...)` updates the on-disk config and
  `ApiClient.BaseUrl` picks up the new value before the login request fires.

### TLS / self-signed certs

`System.Net.Http.HttpClient` uses the Windows certificate store. For a self-signed dev cert:

```powershell
# PowerShell — import fullchain.pem into the current user's trusted roots
Import-Certificate -FilePath fullchain.pem -CertStoreLocation Cert:\CurrentUser\Root
```

After import, `HttpClient` accepts the cert without code changes. Do not disable `ServerCertificateCustomValidationCallback` in production — that bypasses Windows trust validation and is a HIPAA transmission-security violation.

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
