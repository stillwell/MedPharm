# MedPharm — macOS Client

Native SwiftUI patient portal for **macOS 13 Ventura and later**.

Build instructions: [`docs/COMPILATION.md § macOS`](../docs/COMPILATION.md#macos-swift--xcode).
Feature inventory: [`docs/CLIENTS.md § macOS`](../docs/CLIENTS.md#macos).

---

## Tech stack

| Layer | Technology |
|-------|------------|
| UI | SwiftUI `NavigationSplitView`, `Table` |
| Async | Swift async/await |
| Networking | `URLSession` + `Codable` |
| Secure storage | Keychain Services |
| Min macOS | 13.0 Ventura |
| Swift | 5.9+ |

The `Models/` and `Services/` layers are **shared verbatim** with the iOS target in [`../ios`](../ios).

---

## Project layout

```
macos/MedPharm/
├── MedPharm.xcodeproj
└── MedPharm/
    ├── Models/       # Shared with iOS
    ├── Services/     # APIClient, AuthManager, KeychainHelper
    ├── Views/        # macOS-optimised SwiftUI views
    └── Assets.xcassets
```

---

## Build

### Xcode (GUI)

1. Open `MedPharm.xcodeproj`.
2. Select the **MedPharm (macOS)** scheme.
3. Run (`⌘R`) or archive (**Product → Archive**).

### CLI

```bash
xcodebuild -project MedPharm.xcodeproj \
  -scheme MedPharm -configuration Release \
  -destination 'platform=macOS' \
  -archivePath build/MedPharm.xcarchive archive

xcodebuild -exportArchive \
  -archivePath build/MedPharm.xcarchive \
  -exportOptionsPlist ExportOptions.plist \
  -exportPath build/app
# build/app/MedPharm.app
```

---

## Notarization

Required for distribution outside the Mac App Store:

```bash
ditto -c -k --keepParent build/app/MedPharm.app MedPharm.zip
xcrun notarytool submit MedPharm.zip \
  --apple-id you@example.com --team-id TEAMID \
  --password app-specific-password --wait
xcrun stapler staple build/app/MedPharm.app
```

---

## Configure API host

Same mechanism as the iOS client — edit `APIClient.swift` or inject `API_BASE_URL` via an `.xcconfig`.

---

## macOS-specific features

* Sidebar navigation (`NavigationSplitView`) instead of tabs
* Native **SwiftUI Table** with sortable columns for prescriptions / medications
* Keyboard shortcuts (`⌘F` focus search, `⌘R` refresh)
* Menu bar: MedPharm → Preferences → API Host
