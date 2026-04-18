# MedPharm — iOS Client

Native SwiftUI patient portal targeting **iOS 16+**.

Build instructions: [`docs/COMPILATION.md § iOS`](../docs/COMPILATION.md#ios-swift--xcode).
Feature inventory: [`docs/CLIENTS.md § iOS`](../docs/CLIENTS.md#ios).

---

## Tech stack

| Layer | Technology |
|-------|------------|
| UI | SwiftUI, `NavigationStack`, `.searchable` |
| Async | Swift async/await |
| Networking | `URLSession` + `Codable` |
| Secure storage | Keychain Services (`kSecClassGenericPassword`) |
| Min iOS | 16.0 |
| Swift | 5.9+ |

---

## Project layout

```
ios/MedPharm/
├── MedPharm.xcodeproj
└── MedPharm/
    ├── Models/           # Codable data models
    ├── Services/         # APIClient, AuthManager, KeychainHelper
    ├── Views/            # DashboardView, PrescriptionsView, BillingView, ...
    └── Assets.xcassets
```

The `Models/` and `Services/` sources are shared with the macOS target in [`../macos`](../macos).

---

## Build

### Xcode (GUI)

1. Open `MedPharm.xcodeproj`.
2. Select the **MedPharm** scheme and pick a signing team.
3. Choose a simulator or device and **Run** (`⌘R`), or **Product → Archive** for distribution.

### CLI

```bash
xcodebuild -project MedPharm.xcodeproj \
  -scheme MedPharm -configuration Release -sdk iphoneos \
  -destination 'generic/platform=iOS' \
  -archivePath build/MedPharm.xcarchive archive

xcodebuild -exportArchive \
  -archivePath build/MedPharm.xcarchive \
  -exportOptionsPlist ExportOptions.plist \
  -exportPath build/ipa
```

---

## Configure API host

Edit `baseURL` in `Services/APIClient.swift`, or create an `.xcconfig` file:

```xcconfig
API_BASE_URL = https:/$()/api.example.com/api/v1
```

and reference it from `Info.plist` as `API_BASE_URL`, read at runtime by `APIClient`.

---

## Distribution

| Channel | Notes |
|---------|-------|
| TestFlight | Beta distribution up to 10,000 testers |
| App Store | Requires App Review submission |
| Ad-hoc | Signed `.ipa` installable on provisioned UDIDs |

Signing requires an Apple Developer account and a valid provisioning profile.
