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

### Xcode (GUI, on macOS)

1. Open `MedPharm.xcodeproj`.
2. Select the **MedPharm (macOS)** scheme.
3. Run (`⌘R`) or archive (**Product → Archive**).

### CLI (on macOS)

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

### Build from Linux / Windows

Apple's toolchain only runs on macOS. Two complementary paths cover engineers outside the Apple ecosystem:

#### 1a. Remote build via GitHub Actions (produces a runnable `.app`)

`./build_via_actions.sh` triggers the [`macos-build.yml`](../.github/workflows/macos-build.yml) workflow on a GitHub-hosted `macos-14` runner and downloads the resulting `.app` to `macos/build/`.

```bash
sudo apt install gh        # or: brew install gh
gh auth login
./build_via_actions.sh                 # Release build, full pipeline
./build_via_actions.sh Debug           # Debug variant
./build_via_actions.sh --no-download   # Trigger only
```

The artifact is `MedPharm-macOS.app.zip` — an **unsigned** app bundle. It runs on any Apple-silicon or Intel Mac after clearing the quarantine attribute:

```bash
unzip -q MedPharm-macOS.app.zip -d /Applications
xattr -cr /Applications/MedPharm.app   # clear quarantine
open /Applications/MedPharm.app
```

For a notarised, Gatekeeper-passing build, add `APPLE_DEVELOPER_ID` (the `Developer ID Application: …` identity) plus the App Store Connect API-key secrets to the repo and adapt the workflow.

> **Heads-up on GitHub billing.** macOS-runner minutes are billed at 10× the Linux rate and require a valid payment method even for public repos. If a job is rejected immediately with *"The job was not started because your account is locked due to a billing issue,"* fix payment at https://github.com/settings/billing or fall back to path **1b**.

#### 1b. Remote build via Cirrus CI (free macOS-on-M1 minutes for OSS)

Cirrus CI provides a free monthly allotment of macOS minutes for public GitHub repos that is separate from GitHub's billing. Use this when GitHub Actions is billing-blocked.

One-time: install the Cirrus CI GitHub App on the repo — https://github.com/marketplace/cirrus-ci

Per build:

```bash
sudo apt install jq curl git
./build_via_cirrus.sh                   # push, wait, download
./build_via_cirrus.sh --no-push         # rely on a previous push
./build_via_cirrus.sh --no-download     # trigger only
```

Same artifact (`MedPharm-macOS.app.zip`). The Cirrus config lives at [`.cirrus.yml`](../.cirrus.yml) and auto-runs on pushes to `master` that touch `macos/`, plus on tags. PRs from forks are skipped.

#### 2. Offline compile-check with the Apple-shipped Linux Swift toolchain

`./swift_lint.sh` compiles the Foundation-only subset (`Models/Models.swift` + `Services/QRConfigParser.swift`) using the Linux Swift toolchain:

```bash
# One-time: install Swift on Linux
curl -L https://swiftlang.github.io/swiftly/swiftly-install.sh | bash
swiftly install latest

# Then:
./macos/swift_lint.sh
```

Catches type errors and Codable / protocol mismatches in seconds. Does **not** compile anything under `Views/` (SwiftUI / AppKit) or `Services/APIClient.swift` (Keychain). Those go through path 1.

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
