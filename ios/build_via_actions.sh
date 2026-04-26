#!/usr/bin/env bash
# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# Email: Andrew.Stillwell@enlightec.com
# License: GNU General Public License v3.0
#
# ==============================================================================
# Build the iOS client from a Linux / Windows shell using GitHub Actions.
#
# Apple's toolchain only runs on macOS, so this script outsources the actual
# `xcodebuild` to the project's `ios-build.yml` workflow on a GitHub-hosted
# macos-14 runner. From your perspective on Linux it looks like a single
# command — under the hood it:
#
#   1. Triggers the workflow with `gh workflow run`.
#   2. Tails progress with `gh run watch`.
#   3. Downloads the produced .app bundles into ./build/.
#
# Requirements:
#   - GitHub CLI (`gh`)            sudo apt install gh   |   brew install gh
#   - You have authenticated:      gh auth login
#   - The repo's remote points at the GitHub fork that hosts the workflow.
#
# Usage:
#   ./build_via_actions.sh                 # Release build (default)
#   ./build_via_actions.sh Debug           # Debug build
#   ./build_via_actions.sh --no-download   # Trigger only, skip artifact pull
#
# Output:
#   build/MedPharm-iOS-Simulator.app.zip      — runnable in iOS Simulator
#   build/MedPharm-iOS-Device-Unsigned.xcarchive.zip
#       — compile-only proof; not installable on a real phone without signing
# ==============================================================================

set -euo pipefail

WORKFLOW_FILE="ios-build.yml"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUT_DIR="${SCRIPT_DIR}/build"

CONFIG="Release"
DOWNLOAD=true
for arg in "$@"; do
    case "$arg" in
        Debug|Release) CONFIG="$arg" ;;
        --no-download|--trigger-only) DOWNLOAD=false ;;
        --help|-h)
            sed -n '8,30p' "$0"
            exit 0
            ;;
        *) echo "Unknown argument: $arg (use --help)" >&2; exit 1 ;;
    esac
done

command -v gh >/dev/null 2>&1 || {
    echo "ERROR: GitHub CLI 'gh' is required."
    echo "  Install: https://github.com/cli/cli#installation"
    echo "  Then:    gh auth login"
    exit 1
}

cd "$REPO_ROOT"

echo "──────────────────────────────────────────────────────────────"
echo "  MedPharm iOS — remote build via GitHub Actions"
echo "──────────────────────────────────────────────────────────────"
echo "  Workflow      : $WORKFLOW_FILE"
echo "  Configuration : $CONFIG"
echo "  Repository    : $(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo

echo "[1/3] Dispatching workflow..."
gh workflow run "$WORKFLOW_FILE" --ref "$(git rev-parse --abbrev-ref HEAD)" -f "configuration=${CONFIG}"

# gh workflow run returns immediately. Give the API a moment to register
# the new run, then grab its ID.
sleep 4
RUN_ID="$(gh run list --workflow "$WORKFLOW_FILE" --limit 1 --json databaseId -q '.[0].databaseId')"
echo "      Run ID: $RUN_ID  (https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/runs/${RUN_ID})"

echo "[2/3] Watching run progress (Ctrl-C to detach; build keeps running)..."
gh run watch "$RUN_ID" --exit-status

if [[ "$DOWNLOAD" != "true" ]]; then
    echo "[3/3] Skipped artifact download (--no-download)."
    exit 0
fi

echo "[3/3] Downloading artifacts to ${OUT_DIR}..."
mkdir -p "$OUT_DIR"
gh run download "$RUN_ID" --dir "$OUT_DIR"

echo
echo "──────────────────────────────────────────────────────────────"
echo "  Done. Artifacts:"
find "$OUT_DIR" -maxdepth 3 -type f \( -name '*.zip' -o -name '*.ipa' -o -name '*.app' \) -printf '    %p\n'
echo
echo "  Run the simulator build on a Mac:"
echo "    unzip -q build/MedPharm-iOS-Simulator/MedPharm-iOS-Simulator.app.zip"
echo "    xcrun simctl install booted MedPharm.app"
echo "    xcrun simctl launch booted com.enlightec.medpharm"
echo "──────────────────────────────────────────────────────────────"
