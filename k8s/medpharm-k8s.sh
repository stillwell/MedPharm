#!/usr/bin/env bash
# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# Email: Andrew.Stillwell@enlightec.com
# License: GNU General Public License v3.0
#
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  MedPharm ERP - Kubernetes Installer / Deployer / Manager                  ║
# ║                                                                            ║
# ║  Installs and operates the enlightec/medpharm-server image on any         ║
# ║  Kubernetes cluster. Supports GKE, EKS, Linode, DigitalOcean, and         ║
# ║  bare-metal clusters via the kustomize overlays in this directory.        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

set -euo pipefail

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
CYAN=$'\033[0;36m'
BOLD=$'\033[1m'
DIM=$'\033[2m'
NC=$'\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${SCRIPT_DIR}/base"
OVERLAYS_DIR="${SCRIPT_DIR}/overlays"

NAMESPACE="${MEDPHARM_NAMESPACE:-medpharm}"
DEPLOYMENT="medpharm-server"
SERVICE="medpharm-server"
INGRESS="medpharm-server"
SECRET_NAME="medpharm-secrets"
IMAGE_REPO="enlightec/medpharm-server"
DEFAULT_TAG="1.7.3"

CLOUD=""
HOSTNAME_OVERRIDE=""
IMAGE_TAG=""
KUBECONFIG_FLAG=""
CONFIRM_YES=false
KEEP_DATA=false

# ── Output helpers ────────────────────────────────────────────────────────────

log()   { printf "${CYAN}==>${NC} %s\n" "$*"; }
ok()    { printf "${GREEN}✓${NC}  %s\n" "$*"; }
warn()  { printf "${YELLOW}!${NC}  %s\n" "$*"; }
err()   { printf "${RED}✗${NC}  %s\n" "$*" >&2; }
die()   { err "$*"; exit 1; }

header() {
    echo ""
    printf "${BOLD}${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}\n"
    printf "${BOLD}${BLUE}║${NC}  ${BOLD}%-76s${NC}${BOLD}${BLUE}║${NC}\n" "$1"
    printf "${BOLD}${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}\n"
}

# ── kubectl wrapper (carries --kubeconfig if set) ─────────────────────────────

k() {
    if [[ -n "$KUBECONFIG_FLAG" ]]; then
        kubectl --kubeconfig="$KUBECONFIG_FLAG" "$@"
    else
        kubectl "$@"
    fi
}

kn() { k -n "$NAMESPACE" "$@"; }

# ── Preflight ─────────────────────────────────────────────────────────────────

preflight_tools() {
    command -v kubectl >/dev/null 2>&1 || die "kubectl not found in PATH. Install from https://kubernetes.io/docs/tasks/tools/"
    [[ -d "$BASE_DIR" ]] || die "Base manifests not found at $BASE_DIR"
    [[ -d "$OVERLAYS_DIR" ]] || die "Overlays not found at $OVERLAYS_DIR"
}

preflight() {
    preflight_tools
    command -v openssl >/dev/null 2>&1 || die "openssl required for secret generation."

    if ! k cluster-info >/dev/null 2>&1; then
        die "Cannot reach a Kubernetes cluster. Check your kubeconfig or --kubeconfig flag."
    fi

    local ctx
    ctx="$(k config current-context 2>/dev/null || echo 'unknown')"
    ok "Cluster reachable (context: ${BOLD}${ctx}${NC})"
}

# ── Cloud detection ───────────────────────────────────────────────────────────

detect_cloud() {
    if [[ -n "$CLOUD" ]]; then echo "$CLOUD"; return; fi
    local ctx
    ctx="$(k config current-context 2>/dev/null || true)"
    case "$ctx" in
        gke_*|*-gke-*)            echo "gcp" ;;
        *eks*|arn:aws:eks:*)      echo "aws" ;;
        *)                        echo "generic" ;;
    esac
}

# ── Manifest rendering ────────────────────────────────────────────────────────
#
# We render the kustomize overlay once, apply an optional hostname
# substitution and image-tag substitution, and pipe the result into
# `kubectl apply -f -`. This avoids mutating files on disk.

render() {
    local cloud="$1"
    local overlay="${OVERLAYS_DIR}/${cloud}"
    [[ -d "$overlay" ]] || die "Unknown cloud '$cloud' — expected one of: gcp, aws, generic"

    # kubectl has kustomize built in via `kubectl kustomize DIR`
    local rendered
    rendered="$(k kustomize "$overlay")"

    if [[ -n "$HOSTNAME_OVERRIDE" ]]; then
        rendered="$(printf '%s' "$rendered" | sed "s/medpharm\.example\.com/${HOSTNAME_OVERRIDE}/g")"
    fi

    if [[ -n "$IMAGE_TAG" ]]; then
        rendered="$(printf '%s' "$rendered" | sed -E "s|(image: ${IMAGE_REPO}):[^[:space:]]+|\1:${IMAGE_TAG}|g")"
    fi

    printf '%s' "$rendered"
}

# ── Namespace + secret bootstrap ──────────────────────────────────────────────

ensure_namespace() {
    if k get namespace "$NAMESPACE" >/dev/null 2>&1; then
        ok "Namespace ${BOLD}${NAMESPACE}${NC} exists"
    else
        log "Creating namespace ${BOLD}${NAMESPACE}${NC}"
        k create namespace "$NAMESPACE"
        ok "Namespace created"
    fi
}

ensure_secret() {
    if kn get secret "$SECRET_NAME" >/dev/null 2>&1; then
        ok "Secret ${BOLD}${SECRET_NAME}${NC} exists (not regenerating — use 'rotate-secrets' to replace)"
        return
    fi
    log "Generating ${BOLD}${SECRET_NAME}${NC} (JWT + session keys via openssl rand -base64 48)"
    kn create secret generic "$SECRET_NAME" \
        --from-literal=MEDPHARM_JWT_SECRET="$(openssl rand -base64 48)" \
        --from-literal=MEDPHARM_SECRET_KEY="$(openssl rand -base64 48)"
    ok "Secret created"
}

rotate_secrets() {
    preflight
    ensure_namespace
    warn "This will REPLACE ${SECRET_NAME} in namespace ${NAMESPACE}."
    confirm "Existing sessions and issued JWTs will be invalidated on next pod restart. Proceed?"
    kn delete secret "$SECRET_NAME" --ignore-not-found
    ensure_secret
    log "Restarting deployment to pick up new secrets"
    kn rollout restart "deploy/$DEPLOYMENT"
    kn rollout status "deploy/$DEPLOYMENT"
    ok "Secrets rotated"
}

confirm() {
    $CONFIRM_YES && return 0
    local prompt="$1"
    printf "${YELLOW}?${NC}  %s [y/N]: " "$prompt"
    local answer
    read -r answer
    [[ "$answer" =~ ^[Yy]([Ee][Ss])?$ ]] || die "Aborted."
}

# ── Commands ──────────────────────────────────────────────────────────────────

cmd_preflight() {
    header "Preflight"
    preflight
    local cloud
    cloud="$(detect_cloud)"
    ok "Cloud overlay: ${BOLD}${cloud}${NC}"
    ok "Default namespace: ${BOLD}${NAMESPACE}${NC}"
    ok "Image: ${BOLD}${IMAGE_REPO}:${IMAGE_TAG:-$DEFAULT_TAG}${NC}"
    [[ -n "$HOSTNAME_OVERRIDE" ]] && ok "Hostname: ${BOLD}${HOSTNAME_OVERRIDE}${NC}"
}

cmd_install() {
    header "Install"
    preflight
    local cloud
    cloud="$(detect_cloud)"
    log "Using ${BOLD}${cloud}${NC} overlay"

    ensure_namespace
    ensure_secret

    log "Applying manifests"
    render "$cloud" | k apply -f -

    log "Waiting for rollout"
    kn rollout status "deploy/$DEPLOYMENT" --timeout=10m
    ok "Deployment ready"

    cmd_status
}

cmd_deploy() {
    header "Deploy / Upgrade"
    preflight
    local cloud
    cloud="$(detect_cloud)"
    local tag="${IMAGE_TAG:-$DEFAULT_TAG}"

    log "Applying ${IMAGE_REPO}:${tag} via ${cloud} overlay"
    render "$cloud" | k apply -f -

    log "Waiting for rollout"
    kn rollout status "deploy/$DEPLOYMENT" --timeout=10m
    ok "Deployed ${IMAGE_REPO}:${tag}"
}

cmd_status() {
    header "Status"
    preflight
    echo ""
    printf "${BOLD}Deployment${NC}\n"
    kn get deploy "$DEPLOYMENT" -o wide 2>/dev/null || warn "No deployment yet — run 'install' first"
    echo ""
    printf "${BOLD}Pods${NC}\n"
    kn get pods -l app.kubernetes.io/name=medpharm -o wide 2>/dev/null || true
    echo ""
    printf "${BOLD}Service${NC}\n"
    kn get svc "$SERVICE" 2>/dev/null || true
    echo ""
    printf "${BOLD}Ingress${NC}\n"
    kn get ingress "$INGRESS" 2>/dev/null || true
    echo ""
    printf "${BOLD}PersistentVolumeClaim${NC}\n"
    kn get pvc medpharm-data 2>/dev/null || true
    echo ""
    if kn get managedcertificate medpharm-cert >/dev/null 2>&1; then
        printf "${BOLD}ManagedCertificate (GKE)${NC}\n"
        kn get managedcertificate medpharm-cert -o wide 2>/dev/null || true
        echo ""
    fi
    if kn get certificate medpharm-tls >/dev/null 2>&1; then
        printf "${BOLD}Certificate (cert-manager)${NC}\n"
        kn get certificate medpharm-tls 2>/dev/null || true
        echo ""
    fi
}

cmd_logs() {
    preflight
    kn logs "deploy/$DEPLOYMENT" "$@"
}

cmd_shell() {
    preflight
    kn exec -it "deploy/$DEPLOYMENT" -- bash
}

cmd_supervisorctl() {
    preflight
    kn exec "deploy/$DEPLOYMENT" -- supervisorctl "$@"
}

cmd_health() {
    preflight
    log "Port-forwarding svc/${SERVICE} 0:80 for health check"
    local pf_log
    pf_log="$(mktemp)"
    kn port-forward "svc/$SERVICE" :80 >"$pf_log" 2>&1 &
    local pf_pid=$!
    trap 'kill "$pf_pid" 2>/dev/null || true; rm -f "$pf_log"' EXIT

    local port="" attempts=0
    while [[ -z "$port" && $attempts -lt 30 ]]; do
        sleep 0.3
        port="$(grep -oE '127\.0\.0\.1:[0-9]+' "$pf_log" | head -1 | cut -d: -f2 || true)"
        attempts=$((attempts+1))
    done
    [[ -n "$port" ]] || die "port-forward never bound a local port"

    local url="http://127.0.0.1:${port}/api/v1/health"
    log "GET $url"
    if curl -fsS "$url"; then
        echo ""
        ok "Health check passed"
    else
        echo ""
        die "Health check failed"
    fi
}

cmd_backup() {
    preflight
    local out="${1:-backup-$(date +%Y%m%d-%H%M%S).db}"
    log "Creating SQLite hot backup → ${BOLD}${out}${NC}"
    kn exec "deploy/$DEPLOYMENT" -- sqlite3 /data/medpharm_erp.db ".backup /tmp/_medpharm_backup.db"
    local pod
    pod="$(kn get pods -l app.kubernetes.io/name=medpharm -o jsonpath='{.items[0].metadata.name}')"
    kn cp "${pod}:/tmp/_medpharm_backup.db" "$out"
    kn exec "deploy/$DEPLOYMENT" -- rm -f /tmp/_medpharm_backup.db
    ok "Backup saved to $out ($(du -h "$out" | cut -f1))"
}

cmd_restore() {
    preflight
    local src="${1:-}"
    [[ -n "$src" ]] || die "Usage: restore <path-to-backup.db>"
    [[ -f "$src" ]] || die "Backup file not found: $src"

    warn "This will OVERWRITE the live database in namespace ${NAMESPACE}."
    confirm "Continue?"

    local pod
    pod="$(kn get pods -l app.kubernetes.io/name=medpharm -o jsonpath='{.items[0].metadata.name}')"

    log "Copying $src to pod"
    kn cp "$src" "${pod}:/tmp/_medpharm_restore.db"

    log "Stopping API + Web workers (nginx stays up)"
    kn exec "$pod" -- supervisorctl stop medpharm-api medpharm-web || true

    log "Replacing /data/medpharm_erp.db"
    kn exec "$pod" -- sh -c 'cp /tmp/_medpharm_restore.db /data/medpharm_erp.db && rm /tmp/_medpharm_restore.db'

    log "Restarting workers"
    kn exec "$pod" -- supervisorctl start medpharm-api medpharm-web

    ok "Restore complete"
}

cmd_rollback() {
    preflight
    if [[ -n "$IMAGE_TAG" ]]; then
        log "Setting image to ${IMAGE_REPO}:${IMAGE_TAG}"
        kn set image "deploy/$DEPLOYMENT" "medpharm=${IMAGE_REPO}:${IMAGE_TAG}"
    else
        log "Rolling back to previous revision"
        kn rollout undo "deploy/$DEPLOYMENT"
    fi
    kn rollout status "deploy/$DEPLOYMENT"
    ok "Rollback complete"
}

cmd_uninstall() {
    header "Uninstall"
    preflight
    local cloud
    cloud="$(detect_cloud)"

    warn "This will delete the Deployment, Service, Ingress, ConfigMap, and Secret in namespace ${NAMESPACE}."
    if $KEEP_DATA; then
        warn "The PersistentVolumeClaim (medpharm-data) will be kept."
    else
        err  "The PersistentVolumeClaim (medpharm-data) will ALSO be deleted — all SQLite data will be lost."
        err  "Pass --keep-data to preserve it."
    fi
    confirm "Proceed with uninstall?"

    log "Deleting rendered resources"
    render "$cloud" | k delete --ignore-not-found=true -f - || true

    if ! $KEEP_DATA; then
        log "Deleting PVC medpharm-data"
        kn delete pvc medpharm-data --ignore-not-found=true
    fi

    if kn get all 2>/dev/null | grep -q .; then
        warn "Some resources remain in namespace ${NAMESPACE}; review with 'kubectl get all -n $NAMESPACE'"
    else
        log "Namespace is empty; deleting it"
        k delete namespace "$NAMESPACE" --ignore-not-found=true
    fi
    ok "Uninstalled"
}

cmd_manifests() {
    preflight_tools
    local cloud="${CLOUD:-generic}"
    local overlay="${OVERLAYS_DIR}/${cloud}"
    [[ -d "$overlay" ]] || die "Unknown cloud '$cloud' — expected one of: gcp, aws, generic"
    local rendered
    rendered="$(kubectl kustomize "$overlay")"
    if [[ -n "$HOSTNAME_OVERRIDE" ]]; then
        rendered="$(printf '%s' "$rendered" | sed "s/medpharm\.example\.com/${HOSTNAME_OVERRIDE}/g")"
    fi
    if [[ -n "$IMAGE_TAG" ]]; then
        rendered="$(printf '%s' "$rendered" | sed -E "s|(image: ${IMAGE_REPO}):[^[:space:]]+|\1:${IMAGE_TAG}|g")"
    fi
    printf '%s\n' "$rendered"
}

# ── Argument parsing ──────────────────────────────────────────────────────────

usage() {
    cat <<USAGE
${BOLD}MedPharm ERP — Kubernetes Installer / Deployer / Manager${NC}

${BOLD}Usage:${NC}
  ./medpharm-k8s.sh <command> [options]

${BOLD}Commands:${NC}
  ${CYAN}install${NC}           Install onto the current cluster (namespace, secret, deploy)
  ${CYAN}deploy${NC}            Apply or upgrade manifests (idempotent; use --tag to upgrade)
  ${CYAN}status${NC}            Show Deployment, Pod, Service, Ingress, PVC, and TLS status
  ${CYAN}logs${NC} [args…]      Tail pod logs (passes extra args to 'kubectl logs')
  ${CYAN}shell${NC}             Exec an interactive bash into the pod
  ${CYAN}supervisorctl${NC} …   Run a supervisorctl command inside the pod
  ${CYAN}health${NC}            Port-forward + curl /api/v1/health
  ${CYAN}backup${NC} [file]     Copy a SQLite hot backup off-cluster
  ${CYAN}restore${NC} <file>    Restore a backup into the live pod (destructive)
  ${CYAN}rollback${NC}          Roll back to previous revision (or --tag=X to pin)
  ${CYAN}rotate-secrets${NC}    Regenerate JWT + session keys and restart the pod
  ${CYAN}manifests${NC}         Print rendered kustomize output to stdout
  ${CYAN}uninstall${NC}         Delete all resources (use --keep-data to preserve PVC)
  ${CYAN}preflight${NC}         Check kubectl, cluster, and detected cloud overlay

${BOLD}Options:${NC}
  --cloud=<gcp|aws|generic>   Force a cloud overlay (default: auto-detect from context)
  --namespace=<ns>            Target namespace (default: medpharm, or \$MEDPHARM_NAMESPACE)
  --hostname=<host>           Replace medpharm.example.com in Ingress
  --tag=<version>             Image tag (default: ${DEFAULT_TAG}, or \$MEDPHARM_IMAGE_TAG)
  --kubeconfig=<path>         Use a specific kubeconfig file
  --keep-data                 Preserve the PVC during uninstall
  --yes, -y                   Skip confirmation prompts
  --help, -h                  Show this help

${BOLD}Environment:${NC}
  MEDPHARM_NAMESPACE          Default namespace
  MEDPHARM_IMAGE_TAG          Default image tag
  KUBECONFIG                  Kubeconfig path (honored by kubectl)

${BOLD}Examples:${NC}
  # First install on GKE with a real hostname
  ./medpharm-k8s.sh install --cloud=gcp --hostname=erp.acme.com

  # Upgrade to 1.7.3 on the current cluster
  ./medpharm-k8s.sh deploy --tag=1.7.3

  # Rolling rollback to previous revision
  ./medpharm-k8s.sh rollback

  # Pinned rollback
  ./medpharm-k8s.sh rollback --tag=1.5.1

  # Take a backup before upgrading
  ./medpharm-k8s.sh backup pre-upgrade-\$(date +%F).db
  ./medpharm-k8s.sh deploy --tag=1.7.3

  # Keep data on uninstall (e.g. migrating to a new cluster)
  ./medpharm-k8s.sh uninstall --keep-data
USAGE
}

if [[ $# -eq 0 ]]; then
    usage
    exit 0
fi

COMMAND=""
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --cloud=*)      CLOUD="${1#--cloud=}"; shift ;;
        --namespace=*)  NAMESPACE="${1#--namespace=}"; shift ;;
        --hostname=*)   HOSTNAME_OVERRIDE="${1#--hostname=}"; shift ;;
        --tag=*)        IMAGE_TAG="${1#--tag=}"; shift ;;
        --kubeconfig=*) KUBECONFIG_FLAG="${1#--kubeconfig=}"; shift ;;
        --keep-data)    KEEP_DATA=true; shift ;;
        --yes|-y)       CONFIRM_YES=true; shift ;;
        --help|-h)      usage; exit 0 ;;
        --*)            die "Unknown option: $1 (see --help)" ;;
        *)
            if [[ -z "$COMMAND" ]]; then
                COMMAND="$1"
            else
                ARGS+=("$1")
            fi
            shift
            ;;
    esac
done

# Apply env defaults after flag parsing so --tag wins over $MEDPHARM_IMAGE_TAG.
: "${IMAGE_TAG:=${MEDPHARM_IMAGE_TAG:-}}"

case "$COMMAND" in
    install)        cmd_install ;;
    deploy|upgrade) cmd_deploy ;;
    status)         cmd_status ;;
    logs)           cmd_logs "${ARGS[@]}" ;;
    shell|exec)     cmd_shell ;;
    supervisorctl)  cmd_supervisorctl "${ARGS[@]}" ;;
    health)         cmd_health ;;
    backup)         cmd_backup "${ARGS[@]}" ;;
    restore)        cmd_restore "${ARGS[@]}" ;;
    rollback)       cmd_rollback ;;
    rotate-secrets) rotate_secrets ;;
    manifests)      cmd_manifests ;;
    uninstall)      cmd_uninstall ;;
    preflight)      cmd_preflight ;;
    "")             usage; exit 1 ;;
    *)              die "Unknown command: $COMMAND (see --help)" ;;
esac
