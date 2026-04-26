#!/usr/bin/env bash
# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# Email: Andrew.Stillwell@enlightec.com
# License: GNU General Public License v3.0
#
# ==============================================================================
# Build the macOS client on Cirrus CI (free macOS-on-M1 minutes for public OSS)
# from a Linux / Windows shell.
#
# Mirrors ios/build_via_cirrus.sh but downloads only the macOS task's
# artifact (MedPharm-macOS.app.zip).
#
# Usage:
#   ./build_via_cirrus.sh                 # build current HEAD on its branch
#   ./build_via_cirrus.sh --no-push       # rely on previous push, just poll
#   ./build_via_cirrus.sh --no-download   # trigger only
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
        --help|-h)     sed -n '8,22p' "$0"; exit 0 ;;
        *) echo "Unknown argument: $arg (use --help)" >&2; exit 1 ;;
    esac
done

for tool in git curl jq; do
    command -v "$tool" >/dev/null 2>&1 \
        || { echo "ERROR: '$tool' is required (install via your package manager)"; exit 1; }
done

cd "$REPO_ROOT"

OWNER_REPO="$(git remote get-url origin | sed -E 's#.*github\.com[:/]##; s#\.git$##; s#/$##')"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
SHA="$(git rev-parse HEAD)"

echo "──────────────────────────────────────────────────────────────"
echo "  MedPharm macOS — remote build via Cirrus CI"
echo "──────────────────────────────────────────────────────────────"
echo "  Repository : $OWNER_REPO"
echo "  Branch     : $BRANCH"
echo "  Commit     : $SHA"
echo

if [[ "$PUSH" == "true" ]]; then
    echo "[1/3] Pushing $BRANCH to origin..."
    git push origin "$BRANCH"
else
    echo "[1/3] Skipping push (--no-push)."
fi

GQL_URL="https://api.cirrus-ci.com/graphql"
OWNER="${OWNER_REPO%%/*}"
NAME="${OWNER_REPO##*/}"

echo "[2/3] Confirming Cirrus knows about $OWNER_REPO ..."
repo_check=$(jq -nc --arg owner "$OWNER" --arg name "$NAME" '{
  query: "query($owner:String!,$name:String!){ ownerRepository(platform:\"github\",owner:$owner,name:$name){ id } }",
  variables: { owner: $owner, name: $name }
}')
repo_resp=$(curl -fsS -H 'Content-Type: application/json' -X POST -d "$repo_check" "$GQL_URL" || echo '{}')
repo_id=$(echo "$repo_resp" | jq -r '.data.ownerRepository.id // empty')

if [[ -z "$repo_id" ]]; then
    cat <<EOM
ERROR: Cirrus CI does not know about $OWNER_REPO.

  Cirrus only sees a repo after you install its GitHub App on it (one-time):

      https://github.com/marketplace/cirrus-ci

  Click "Install" → grant access to $OWNER_REPO → re-run this script.

  The free-tier OSS plan is automatic for public repos; no payment method
  is required.
EOM
    exit 1
fi
echo "      Repo registered: cirrus-ci.com/github/$OWNER_REPO  (id=$repo_id)"

echo "      Locating build for $SHA ..."
build_id=""
for attempt in $(seq 1 30); do
    payload=$(jq -nc --arg owner "$OWNER" --arg name "$NAME" --arg sha "$SHA" '{
      query: "query($owner:String!,$name:String!,$sha:String!){ ownerRepository(platform:\"github\",owner:$owner,name:$name){ builds(last:20){ edges{ node{ id changeIdInRepo status tasks{ id name status } } } } } }",
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
    echo "ERROR: Cirrus knows the repo but found no build for $SHA after 150 s."
    echo "       This usually means .cirrus.yml at the tip of $BRANCH did not"
    echo "       trigger any task, or the push has not reached Cirrus yet."
    echo "       Check https://cirrus-ci.com/github/$OWNER_REPO"
    exit 1
fi

echo "      Cirrus build: https://cirrus-ci.com/build/$build_id"
echo "      Waiting for the macOS task to complete..."
while :; do
    payload=$(jq -nc --arg id "$build_id" '{
      query: "query($id:ID!){ build(id:$id){ status tasks{ name status } } }",
      variables: { id: $id }
    }')
    resp=$(curl -fsS -H 'Content-Type: application/json' -X POST -d "$payload" "$GQL_URL")
    overall=$(echo "$resp" | jq -r '.data.build.status')
    macos_status=$(echo "$resp" | jq -r '.data.build.tasks[] | select(.name|test("macOS")) | .status' | head -1)
    echo "        $(date +%H:%M:%S) build=$overall macos=$macos_status"
    case "$overall" in
        COMPLETED|FAILED|ABORTED|ERRORED) break ;;
        *) sleep 10 ;;
    esac
done

if [[ "$macos_status" != "COMPLETED" ]]; then
    echo "ERROR: macOS task did not complete cleanly (status=$macos_status)"
    echo "       Full log: https://cirrus-ci.com/build/$build_id"
    exit 1
fi

if [[ "$DOWNLOAD" != "true" ]]; then
    echo "[3/3] Skipped artifact download (--no-download)."
    exit 0
fi

mkdir -p "$OUT_DIR"
echo "[3/3] Downloading artifact to $OUT_DIR ..."
task_name=$(echo "$resp" | jq -r '.data.build.tasks[] | select(.name|test("macOS")) | .name' | head -1)
encoded_task=$(printf '%s' "$task_name" | jq -sRr @uri)
url="https://api.cirrus-ci.com/v1/artifact/build/${build_id}/${encoded_task}/app/MedPharm-macOS.app.zip"
echo "  fetch MedPharm-macOS.app.zip"
if ! curl -fsSL -o "$OUT_DIR/MedPharm-macOS.app.zip" "$url"; then
    echo "  WARN: could not fetch from $url"
fi

echo
echo "──────────────────────────────────────────────────────────────"
echo "  Done. Artifact:"
find "$OUT_DIR" -maxdepth 2 -type f -name '*.zip' -printf '    %p\n'
echo
echo "  Install on a Mac:"
echo "    unzip -q build/MedPharm-macOS.app.zip -d /Applications"
echo "    xattr -cr /Applications/MedPharm.app"
echo "    open /Applications/MedPharm.app"
echo "──────────────────────────────────────────────────────────────"
