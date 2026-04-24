# MedPharm ERP — Cross-Platform Compilation Guide

This guide covers building every MedPharm component **from source** on every target platform. For runtime installation of pre-built artifacts, see [INSTALLATION.md](INSTALLATION.md).

---

## Table of Contents

1. [Build Matrix](#build-matrix)
2. [Common Toolchain Setup](#common-toolchain-setup)
3. [Python Components (Server / API / Qt / Web)](#python-components)
4. [Android (Kotlin / Gradle)](#android-kotlin--gradle)
5. [iOS (Swift / Xcode)](#ios-swift--xcode)
6. [macOS (Swift / Xcode)](#macos-swift--xcode)
7. [Windows (.NET 8 / WPF)](#windows-net-8--wpf)
8. [Docker Image Builds](#docker-image-builds)
9. [Reproducible Release Builds](#reproducible-release-builds)
10. [Continuous Integration](#continuous-integration)

---

## Build Matrix

| Target | Language | Toolchain | Build host | Artifact |
|--------|----------|-----------|-----------|----------|
| Cloud API | Python 3.10+ | `pip` + `gunicorn` | any | WSGI app |
| Web Portal | Python 3.10+ | `pip` + `flask` | any | WSGI app |
| Qt Desktop | Python 3.10+ | `pip` + `PyInstaller` | Linux / macOS / Windows | native binary (optional) |
| Android | Kotlin 1.9 | Gradle 8, AGP 8 | any | `app-release.apk` / `.aab` |
| iOS | Swift 5.9+ | Xcode 15 | macOS only | `.ipa` |
| macOS | Swift 5.9+ | Xcode 15 | macOS only | `.app` |
| Windows | C# .NET 8 | `dotnet` SDK | Windows (Linux cross-compile) | `.exe` / `.msi` |
| Docker API | — | Docker Buildx | any | `enlightec/medpharm-api` |
| Docker Server | — | Docker Buildx | any | `enlightec/medpharm-server` |

---

## Common Toolchain Setup

```bash
# Git + common utilities
sudo apt install git curl unzip build-essential   # Debian / Ubuntu
brew install git curl                             # macOS
winget install Git.Git                            # Windows
```

Clone the repository once and use the same checkout for every platform:

```bash
git clone https://github.com/stillwell/MedPharm.git
cd MedPharm
```

---

## Python Components

### Development build

```bash
python3 -m venv venv
source venv/bin/activate            # PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-cloud.txt reportlab
```

No compilation step is required — Python runs from source. To validate:

```bash
python -m py_compile $(git ls-files '*.py')
```

### Standalone binary (optional)

The Qt desktop app can be packaged into a single binary using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name MedPharm-Desktop \
  --add-data "qt_app/styles.py:qt_app" \
  --add-data "database:database" \
  run_qt.py
# Output: dist/MedPharm-Desktop/
```

For the web/API servers, build a wheel instead:

```bash
pip install build
python -m build --wheel
# Output: dist/medpharm-*.whl
```

---

## Android (Kotlin / Gradle)

### Toolchain

```bash
# Linux
sudo apt install -y openjdk-17-jdk
# macOS
brew install --cask temurin@17
# Windows
winget install EclipseAdoptium.Temurin.17.JDK
```

Install **Android Studio** or the command-line SDK tools. Ensure `ANDROID_HOME` is exported and `platform-tools`, `build-tools;34.0.0`, and `platforms;android-34` are present.

### Debug build

```bash
cd android
./gradlew assembleDebug
# Output: app/build/outputs/apk/debug/app-debug.apk
```

### Release build

```bash
# Generate a release keystore (once)
keytool -genkey -v -keystore medpharm-release.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias medpharm

# Configure signing in ~/.gradle/gradle.properties
cat >> ~/.gradle/gradle.properties <<EOF
MEDPHARM_KEYSTORE=/absolute/path/medpharm-release.jks
MEDPHARM_KEYSTORE_PASSWORD=***
MEDPHARM_KEY_ALIAS=medpharm
MEDPHARM_KEY_PASSWORD=***
EOF

./gradlew assembleRelease bundleRelease
# APK: app/build/outputs/apk/release/app-release.apk
# AAB: app/build/outputs/bundle/release/app-release.aab
```

### API endpoint configuration

Edit `android/app/src/main/res/values/strings.xml` or override `BuildConfig.API_BASE_URL` per build variant:

```kotlin
// app/build.gradle.kts
buildConfigField("String", "API_BASE_URL", "\"https://api.example.com/api/v1/\"")
```

---

## iOS (Swift / Xcode)

### Toolchain

* **macOS 13+** build host
* **Xcode 15+** with the iOS 16 SDK
* Apple Developer account (for signing / TestFlight)

### CLI build

```bash
cd ios/MedPharm
xcodebuild -project MedPharm.xcodeproj \
  -scheme MedPharm \
  -configuration Release \
  -sdk iphoneos \
  -destination 'generic/platform=iOS' \
  -archivePath build/MedPharm.xcarchive archive

xcodebuild -exportArchive \
  -archivePath build/MedPharm.xcarchive \
  -exportOptionsPlist ExportOptions.plist \
  -exportPath build/ipa
# Output: build/ipa/MedPharm.ipa
```

### Xcode GUI build

1. Open `ios/MedPharm/MedPharm.xcodeproj`.
2. Select the **MedPharm** scheme and a signing team.
3. Product → Archive → Distribute App.

### API endpoint configuration

Set `APIClient.baseURL` in `Services/APIClient.swift`, or inject via an `.xcconfig` file:

```xcconfig
API_BASE_URL = https:/$()/api.example.com/api/v1
```

(the `$()` avoids the Xcode `//` comment rule).

---

## macOS (Swift / Xcode)

Same toolchain as iOS. The macOS project lives at `macos/MedPharm/MedPharm.xcodeproj` and shares `Models/` and `Services/` with the iOS target.

### CLI build

```bash
cd macos/MedPharm
xcodebuild -project MedPharm.xcodeproj \
  -scheme MedPharm \
  -configuration Release \
  -destination 'platform=macOS' \
  -archivePath build/MedPharm.xcarchive archive

xcodebuild -exportArchive \
  -archivePath build/MedPharm.xcarchive \
  -exportOptionsPlist ExportOptions.plist \
  -exportPath build/app
# Output: build/app/MedPharm.app
```

### Notarization (for distribution outside Mac App Store)

```bash
ditto -c -k --keepParent build/app/MedPharm.app MedPharm.zip
xcrun notarytool submit MedPharm.zip \
  --apple-id you@example.com --team-id TEAMID --password app-specific-pwd --wait
xcrun stapler staple build/app/MedPharm.app
```

---

## Windows (.NET 8 / WPF)

### Toolchain

```powershell
winget install Microsoft.DotNet.SDK.8
winget install Microsoft.VisualStudio.2022.Community   # optional IDE
```

Linux / macOS hosts can cross-compile using the same `dotnet` SDK.

### Debug run

```powershell
cd windows\MedPharm
dotnet restore
dotnet run
```

### Self-contained release

```powershell
dotnet publish MedPharm.csproj `
  -c Release `
  -r win-x64 `
  --self-contained true `
  -p:PublishSingleFile=true `
  -p:IncludeNativeLibrariesForSelfExtract=true `
  -o publish\win-x64
# Output: publish\win-x64\MedPharm.exe
```

### ARM64 build

```powershell
dotnet publish -c Release -r win-arm64 --self-contained true -o publish\win-arm64
```

### MSI packaging (optional)

Use **WiX Toolset v4** or **MSIX Packaging Tool**. A starter WiX source lives in `windows/MedPharm/Package.wxs` (add if distributing installers).

### API endpoint configuration

Edit `windows/MedPharm/Services/ApiClient.cs` or set the `MEDPHARM_API` user environment variable — the client reads it on startup.

---

## Docker Image Builds

### API-only image

```bash
docker build -t enlightec/medpharm-api:dev .
docker run --rm -p 8080:8080 enlightec/medpharm-api:dev
```

### Full-stack server image

```bash
cd server
docker build -t enlightec/medpharm-server:dev .
docker run --rm -p 80:80 -p 8080:8080 -p 5000:5000 enlightec/medpharm-server:dev
```

### Multi-arch buildx

```bash
docker buildx create --use --name medpharm-builder
docker buildx build --platform linux/amd64,linux/arm64 \
  -t enlightec/medpharm-api:1.7.5 --push .
```

---

## Reproducible Release Builds

To build a release for all platforms in order:

```bash
# 1. Tag the release
git tag -a v1.7.5 -m "MedPharm 1.7.5"
git push origin v1.7.5                 # triggers docker-publish.yml

# 2. Android
(cd android && ./gradlew bundleRelease)

# 3. iOS & macOS (on macOS host)
(cd ios/MedPharm && xcodebuild archive ... )
(cd macos/MedPharm && xcodebuild archive ... )

# 4. Windows (on Windows host)
(cd windows\MedPharm && dotnet publish -c Release -r win-x64 --self-contained true)

# 5. Python wheels
python -m build --wheel
```

---

## Continuous Integration

Docker images are built and pushed automatically by `.github/workflows/docker-publish.yml` on every `v*.*.*` tag. Additional CI recipes:

| Target | Recommended runner | Command |
|--------|-------------------|---------|
| Android | `ubuntu-latest` + `actions/setup-java@v4` (jdk 17) | `./gradlew assembleRelease` |
| iOS / macOS | `macos-14` + `actions/setup-xcode@v1` | `xcodebuild archive ...` |
| Windows | `windows-latest` + `actions/setup-dotnet@v4` (8.0) | `dotnet publish ...` |
| Python wheels | `ubuntu-latest` | `python -m build --wheel` |

Publish artifacts via `actions/upload-artifact@v4` or the GitHub Releases API. Set the signing secrets as encrypted repo secrets (`ANDROID_KEYSTORE`, `APPLE_API_KEY`, `WINDOWS_PFX`, etc.) — never commit them to the repository.
