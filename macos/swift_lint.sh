#!/usr/bin/env bash
# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# License: GNU General Public License v3.0
#
# Compile the Foundation-only subset of the macOS client (Models +
# QRConfigParser) using the Apple-shipped Swift toolchain on Linux. Catches
# type errors and Codable / protocol breakage in seconds, without xcodebuild
# or a Mac.
#
# Install Swift on Debian/Ubuntu:
#   wget -qO- https://download.swift.org/swift-5.9.2-release/ubuntu2204/swift-5.9.2-RELEASE/swift-5.9.2-RELEASE-ubuntu22.04.tar.gz | tar -xz
#   export PATH="$PWD/swift-5.9.2-RELEASE-ubuntu22.04/usr/bin:$PATH"
#
# Or via Swiftly (Swift's official version manager):
#   curl -L https://swiftlang.github.io/swiftly/swiftly-install.sh | bash
#   swiftly install latest
# ==============================================================================

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v swift >/dev/null 2>&1; then
    echo "ERROR: 'swift' is not on PATH."
    echo "       See the header of this script for install instructions."
    exit 1
fi

echo "Swift toolchain: $(swift --version | head -1)"
echo "Compile-checking portable macOS sources (Models + QRConfigParser)..."
swift build --package-path .
echo "OK — Foundation-only subset compiles cleanly."
