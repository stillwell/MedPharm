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

### Xcode (GUI, on macOS)

1. Open `MedPharm.xcodeproj`.
2. Select the **MedPharm** scheme and pick a signing team.
3. Choose a simulator or device and **Run** (`⌘R`), or **Product → Archive** for distribution.

### CLI (on macOS)

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

### Build from Linux / Windows

Apple's toolchain only runs on macOS, so a true local build on Linux is not possible. Two complementary paths cover everything an engineer outside the Apple ecosystem needs:

#### 1a. Remote build via GitHub Actions (produces installable artifacts)

`./build_via_actions.sh` triggers the [`ios-build.yml`](../.github/workflows/ios-build.yml) workflow on a GitHub-hosted `macos-14` runner, watches it complete, and downloads the build artifacts to `ios/build/`.

```bash
sudo apt install gh        # or: brew install gh
gh auth login
./build_via_actions.sh                 # Release build, full pipeline
./build_via_actions.sh Debug           # Debug variant
./build_via_actions.sh --no-download   # Trigger only
```

Two artifacts come back:

| Artifact | Use |
|---|---|
| `MedPharm-iOS-Simulator.app.zip` | Drop onto a Mac, run in any iOS Simulator with `xcrun simctl install booted MedPharm.app`. |
| `MedPharm-iOS-Device-Unsigned.xcarchive.zip` | Compile-only proof — the device-target build succeeded. **Not installable on a real phone** because no Apple Developer signing identity was applied. To produce a signed `.ipa`, add `APPLE_API_KEY_ID` / `APPLE_API_ISSUER_ID` / `APPLE_API_KEY` secrets to the repo and adapt the workflow. |

The workflow also runs automatically on every push to `master` that touches `ios/`, and on every `v*.*.*` tag.

> **Heads-up on GitHub billing.** GitHub charges macOS-runner minutes at 10× the Linux rate and requires a valid payment method on the account even for public repos. If a job comes back almost-instantly with *"The job was not started because your account is locked due to a billing issue,"* fix payment at https://github.com/settings/billing or fall back to path **1b**.

#### 1b. Remote build via Cirrus CI (free macOS-on-M1 minutes for OSS, billing-independent)

Cirrus CI gives public GitHub repos a free monthly allotment of macOS minutes that's separate from GitHub's billing — the right fallback when path 1a is billing-blocked.

One-time setup:

1. Install the Cirrus CI GitHub App on the repo: https://github.com/marketplace/cirrus-ci

Per build:

```bash
sudo apt install jq curl git    # most distros have these already
./build_via_cirrus.sh                   # push current branch, wait, download
./build_via_cirrus.sh --no-push         # rely on a previous push
./build_via_cirrus.sh --no-download     # trigger only
```

The same artifacts come back (`MedPharm-iOS-Simulator.app.zip` and `MedPharm-iOS-Device-Unsigned.xcarchive.zip`). The Cirrus configuration lives at [`.cirrus.yml`](../.cirrus.yml) and runs automatically on every push to `master` that touches `ios/`, plus on tags. PRs from forks are skipped to protect your minute budget.

#### 2. Offline compile-check with the Apple-shipped Linux Swift toolchain

For fast feedback during a Linux editing session — no network, no Mac, no GitHub round-trip — `./swift_lint.sh` builds the Foundation-only subset of the codebase (`Models/Models.swift` + `Services/QRConfigParser.swift`) using `swift build` against the Linux Swift toolchain:

```bash
# One-time: install Swift on Linux
curl -L https://swiftlang.github.io/swiftly/swiftly-install.sh | bash
swiftly install latest

# Then, from anywhere in the repo:
./ios/swift_lint.sh
```

This catches **type errors, Codable schema breakage, and protocol mismatches** in seconds. It does **not** compile anything under `Views/` (those import SwiftUI / UIKit / AVFoundation, which are not present on Linux), nor `Services/APIClient.swift` (Keychain via Security framework). Those layers must go through path 1 to be compiled.

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
