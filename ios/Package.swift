// swift-tools-version:5.9
//
// MedPharm ERP - iOS Client (Linux compile-check facade)
// Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
// Author: Robert Andrew Stillwell
// License: GNU General Public License v3.0
//
// ─────────────────────────────────────────────────────────────────────────────
// THIS IS NOT THE SHIP-IT BUILD.
//
// The iOS app is built with `xcodebuild` against MedPharm.xcodeproj. This
// Package.swift exists so engineers on Linux / Windows can compile the
// portable subset of the codebase (the Foundation-only files: data models
// and the QR-config parser) without owning a Mac:
//
//     swift build         # ~5s, catches type errors and protocol breakage
//     swift test          # if/when MedPharmCoreTests is added
//
// Why only a subset? Anything under Views/ imports SwiftUI, AVFoundation,
// or UIKit — those frameworks are macOS/iOS-only and are not present in
// the Apple-shipped Linux Swift toolchain. APIClient.swift is also
// excluded because it uses Security framework primitives (Keychain).
// For a real device build, see ../README.md → "Build from Linux".
// ─────────────────────────────────────────────────────────────────────────────

import PackageDescription

let package = Package(
    name: "MedPharmCore",
    products: [
        .library(name: "MedPharmCore", targets: ["MedPharmCore"]),
    ],
    targets: [
        .target(
            name: "MedPharmCore",
            path: "MedPharm/MedPharm",
            sources: [
                "Models/Models.swift",
                "Services/QRConfigParser.swift",
            ]
        ),
    ]
)
