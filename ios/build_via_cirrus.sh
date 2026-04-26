#!/usr/bin/env bash
# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# Email: Andrew.Stillwell@enlightec.com
# License: GNU General Public License v3.0
#
# ==============================================================================
# Build the iOS client on Cirrus CI (free macOS-on-M1 minutes for public OSS)
# from a Linux / Windows shell. Use this when GitHub Actions macOS runners
# are billing-blocked or quota-exhausted — Cirrus is independent of GitHub
# billing.
#
# What it does:
#   1. Pushes your current branch to `origin` so Cirrus has a commit to build.
#   2. Polls the public Cirrus REST API (no auth required for public repos)
#      for the build's status until both iOS tasks finish.
#   3. Downloads the produced artifacts to ./build/.
#
# Requirements:
#   - One-time: install the Cirrus CI GitHub App on the repo
#       https://github.com/marketplace/cirrus-ci
#   - `git`, `curl`, `jq` on PATH.
#   - The repo's `origin` remote points at the GitHub fork that hosts the
#     `.cirrus.yml`.
#
# Usage:
#   ./build_via_cirrus.sh                 # build current HEAD on its branch
#   ./build_via_cirrus.sh --no-push       # rely on a previous push, just poll
#   ./build_via_cirrus.sh --no-download   # trigger only, skip artifact pull
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUT_DIR="${SCRIPT_DIR}/build"

PUSH=true
DOWNLOAD=true
for arg in "$@"; do
    case "$arg" in
        --no-push)     PUSH=false ;;
        --no-download|--trigger-only) DOWNLOAD=false ;;
        --help|-h)     sed -n '8,30p' "$0"; exit 0 ;;
        *) echo "Unknown argument: $arg (use --help)" >&2; exit 1 ;;
    esac
done

for tool in git curl jq; do
    command -v "$tool" >/dev/null 2>&1 \
        || { echo "ERROR: '$tool' is required (install via your package manager)"; exit 1; }
done

cd "$REPO_ROOT"

OWNER_REPO="$(git remote get-url origin | sed -E 's#.*github\.com[:/]([^/]+/[^/.]+)(\.git)?#\1#')"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
SHA="$(git rev-parse HEAD)"

echo "──────────────────────────────────────────────────────────────"
echo "  MedPharm iOS — remote build via Cirrus CI"
echo "──────────────────────────────────────────────────────────────"
echo "  Repository : $OWNER_REPO"
echo "  Branch     : $BRANCH"
echo "  Commit     : $SHA"
echo

if [[ "$PUSH" == "true" ]]; then
    echo "[1/3] Pushing $BRANCH to origin so Cirrus has a commit to pick up..."
    git push origin "$BRANCH"
else
    echo "[1/3] Skipping push (--no-push); using whatever Cirrus already has."
fi

# ── Find the Cirrus build for this commit ────────────────────────────────────
# The public GraphQL endpoint at api.cirrus-ci.com requires no auth for OSS
# repos. We poll until a build for our SHA appears (Cirrus normally picks up
# the push within ~10 s).
GQL_URL="https://api.cirrus-ci.com/graphql"
echo "[2/3] Locating Cirrus build for $SHA ..."

build_id=""
for attempt in $(seq 1 30); do
    payload=$(jq -nc --arg owner "${OWNER_REPO%%/*}" --arg name "${OWNER_REPO##*/}" --arg sha "$SHA" '{
      query: "query($owner:String!,$name:String!,$sha:String!){ ownerRepository(platform:\"github\",owner:$owner,name:$name){ builds(last:20){ edges{ node{ id changeIdInRepo status branch tasks{ id name status } } } } } }",
      variables: { owner: $owner, name: $name, sha: $sha }
    }')
    resp=$(curl -fsS -H 'Content-Type: application/json' -X POST -d "$payload" "$GQL_URL" || echo '{}')
    build_id=$(echo "$resp" | jq -r --arg sha "$SHA" \
        '.data.ownerRepository.builds.edges[]?.node | select(.changeIdInRepo==$sha) | .id' \
        | head -1)
    [[ -n "$build_id" && "$build_id" != "null" ]] && break
    sleep 5
done

if [[ -z "$build_id" || "$build_id" == "null" ]]; then
    echo "ERROR: No Cirrus build found for $SHA after 150 s."
    echo "       Check that the Cirrus CI GitHub App is installed on this repo:"
    echo "         https://github.com/marketplace/cirrus-ci"
    echo "       And that .cirrus.yml is present at the repo root."
    exit 1
fi

echo "      Cirrus build: https://cirrus-ci.com/build/$build_id"

# ── Wait for the iOS tasks to finish ─────────────────────────────────────────
echo "      Waiting for iOS tasks to complete..."
while :; do
    payload=$(jq -nc --arg id "$build_id" '{
      query: "query($id:ID!){ build(id:$id){ status tasks{ name status } } }",
      variables: { id: $id }
    }')
    resp=$(curl -fsS -H 'Content-Type: application/json' -X POST -d "$payload" "$GQL_URL")
    overall=$(echo "$resp" | jq -r '.data.build.status')
    echo "        $(date +%H:%M:%S) build=$overall  $(echo "$resp" | jq -r '.data.build.tasks[] | select(.name|test("iOS")) | "[\(.name): \(.status)]"' | tr '\n' ' ')"
    case "$overall" in
        COMPLETED|FAILED|ABORTED|ERRORED) break ;;
        *) sleep 10 ;;
    esac
done

ios_failed=$(echo "$resp" | jq -r '.data.build.tasks[] | select(.name|test("iOS")) | select(.status!="COMPLETED") | .name' | head -1)
if [[ -n "$ios_failed" ]]; then
    echo "ERROR: iOS task did not complete cleanly: $ios_failed"
    echo "       Full log: https://cirrus-ci.com/build/$build_id"
    exit 1
fi

if [[ "$DOWNLOAD" != "true" ]]; then
    echo "[3/3] Skipped artifact download (--no-download)."
    exit 0
fi

# ── Download artifacts ───────────────────────────────────────────────────────
# Cirrus serves task artifacts at:
#   https://api.cirrus-ci.com/v1/artifact/build/<build_id>/<task_name>/<artifact_name>/<file>
mkdir -p "$OUT_DIR"
echo "[3/3] Downloading artifacts to $OUT_DIR ..."
ios_tasks=$(echo "$resp" | jq -r '.data.build.tasks[] | select(.name|test("iOS")) | .name')
while IFS= read -r task_name; do
    [[ -z "$task_name" ]] && continue
    # Map task name -> artifact name + filename per .cirrus.yml
    case "$task_name" in
        *Simulator*) artifact=app;     file=MedPharm-iOS-Simulator.app.zip ;;
        *Device*)    artifact=archive; file=MedPharm-iOS-Device-Unsigned.xcarchive.zip ;;
        *)           echo "  skipping unknown task: $task_name"; continue ;;
    esac
    encoded_task=$(printf '%s' "$task_name" | jq -sRr @uri)
    url="https://api.cirrus-ci.com/v1/artifact/build/${build_id}/${encoded_task}/${artifact}/${file}"
    echo "  fetch $file"
    if ! curl -fsSL -o "$OUT_DIR/$file" "$url"; then
        echo "    WARN: could not fetch $file from $url"
    fi
done <<< "$ios_tasks"

echo
echo "──────────────────────────────────────────────────────────────"
echo "  Done. Artifacts:"
find "$OUT_DIR" -maxdepth 2 -type f -name '*.zip' -printf '    %p\n'
echo "──────────────────────────────────────────────────────────────"
