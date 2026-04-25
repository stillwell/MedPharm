# MedPharm ERP — Kubernetes Deployment Guide

This guide deploys the full-stack `enlightec/medpharm-server` image (Nginx +
Cloud API + Patient Portal in one container) to any Kubernetes cluster.
Manifests are organized as **kustomize** bases and overlays and ship in the
`k8s/` directory.

```
k8s/
├── medpharm-k8s.sh          # installer / deployer / manager CLI
├── base/                    # cloud-agnostic manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.example.yaml  # template — replace before production
│   ├── pvc.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── kustomization.yaml
└── overlays/
    ├── gcp/                 # GKE: GCE ingress + ManagedCertificate
    ├── aws/                 # EKS: ALB ingress + gp3 EBS volume
    └── generic/             # Linode, DigitalOcean, bare-metal (ingress-nginx)
```

---

## Table of Contents

1. [Architecture Notes](#architecture-notes)
2. [Prerequisites](#prerequisites)
3. [Quick Start (any cluster)](#quick-start-any-cluster)
4. [Google Cloud (GKE)](#google-cloud-gke)
5. [Amazon Web Services (EKS)](#amazon-web-services-eks)
6. [Linode / DigitalOcean / Bare-metal](#linode--digitalocean--bare-metal)
7. [Upgrades & Rollback](#upgrades--rollback)
8. [Scaling Considerations](#scaling-considerations)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Notes

The published `enlightec/medpharm-server:1.7.6` image runs Nginx, the Cloud
REST API (Gunicorn on `:8080`), and the Patient Web Portal (Gunicorn on
`:5000`) inside one container, supervised by `supervisord`. Nginx on `:80` is
the only port exposed by the Service and Ingress.

**State** lives in `/data/medpharm_erp.db` (SQLite) on a `ReadWriteOnce` PVC
(10 Gi by default). The Deployment is pinned to `replicas: 1` with
`strategy: Recreate` — multiple replicas would race on the SQLite file.
See [Scaling Considerations](#scaling-considerations) for horizontal scale-out.

**Secrets** (`MEDPHARM_JWT_SECRET`, `MEDPHARM_SECRET_KEY`) must be created
out-of-band before the first apply. The file `secret.example.yaml` exists as
a template only; never apply it with the placeholder values.

**Probes** hit `/api/v1/health` through Nginx on port 80:

| Probe | Initial | Period | Failure threshold |
|-------|---------|--------|-------------------|
| startup | — | 5s | 30 (≈150 s to come up) |
| readiness | — | 10s | 3 |
| liveness | — | 30s | 5 |

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| `kubectl` | 1.28+ | kustomize is built in (`-k`) |
| Container runtime | any | manifests pull from Docker Hub |
| Ingress controller | cloud-specific | GCE LB (GKE), AWS LB Controller (EKS), ingress-nginx (generic) |
| cert-manager | optional | required for Let's Encrypt on the `generic` overlay |
| StorageClass | cluster default, plus `standard-rwo` (GKE) or `gp3` (EKS) |

Clone the repo and move into it:

```bash
git clone https://github.com/stillwell/MedPharm.git
cd MedPharm
```

---

## Quick Start (any cluster)

> **Applies to any vanilla cluster with a default `StorageClass` and any
> ingress controller.** For a production-ready deploy, skip to the
> cloud-specific section below.

### Option A — wrapper script (`medpharm-k8s.sh`)

The repo ships an installer/deployer/manager that wraps the kustomize
overlays. It auto-detects the cloud from the current kube-context and
handles namespace, secret generation, rollout, and lifecycle operations.

```bash
./k8s/medpharm-k8s.sh install --hostname=erp.example.com
./k8s/medpharm-k8s.sh status
./k8s/medpharm-k8s.sh health            # port-forwarded smoke check
./k8s/medpharm-k8s.sh logs -f           # tail pod logs
./k8s/medpharm-k8s.sh backup            # SQLite hot backup off-cluster
./k8s/medpharm-k8s.sh deploy --tag=1.7.6
./k8s/medpharm-k8s.sh rollback          # or --tag=1.5.1 to pin
./k8s/medpharm-k8s.sh uninstall --keep-data
./k8s/medpharm-k8s.sh --help            # full command reference
```

Set `--cloud=gcp|aws|generic` to force an overlay if auto-detection
picks the wrong one.

### Option B — raw kubectl

1. **Create the namespace and secrets** (once per cluster):

   ```bash
   kubectl create namespace medpharm

   # App secrets
   kubectl -n medpharm create secret generic medpharm-secrets \
     --from-literal=MEDPHARM_JWT_SECRET="$(openssl rand -base64 48)" \
     --from-literal=MEDPHARM_SECRET_KEY="$(openssl rand -base64 48)"

   # TLS cert (self-signed for dev — use a CA-issued cert or cert-manager in prod)
   openssl req -x509 -nodes -newkey rsa:4096 -days 825 -sha256 \
     -keyout /tmp/tls.key -out /tmp/tls.crt \
     -subj "/CN=medpharm.example.com/O=MedPharm ERP (self-signed)" \
     -addext "subjectAltName=DNS:medpharm.example.com"
   kubectl -n medpharm create secret tls medpharm-tls \
     --cert=/tmp/tls.crt --key=/tmp/tls.key
   rm /tmp/tls.key /tmp/tls.crt
   ```

   > `medpharm-k8s.sh install` does all of the above automatically — use raw kubectl only if you have a reason.

2. **Edit the hostname** in `k8s/base/ingress.yaml` (replace
   `medpharm.example.com`) or use an overlay.

3. **Apply the base**:

   ```bash
   kubectl apply -k k8s/base
   ```

4. **Wait and verify**:

   ```bash
   kubectl -n medpharm rollout status deploy/medpharm-server
   kubectl -n medpharm port-forward svc/medpharm-server 8443:443
   curl -sk https://localhost:8443/api/v1/health
   ```

---

## Google Cloud (GKE)

### 1. Create or reuse a GKE cluster

```bash
gcloud container clusters create-auto medpharm \
  --region us-central1 \
  --release-channel regular
gcloud container clusters get-credentials medpharm --region us-central1
```

### 2. Reserve a global static IP and DNS record

```bash
gcloud compute addresses create medpharm-ip --global
gcloud compute addresses describe medpharm-ip --global --format='value(address)'
# → point medpharm.example.com (A record) at this IP
```

### 3. Edit the overlay

In `k8s/overlays/gcp/managedcertificate.yaml`, replace
`medpharm.example.com` with your production hostname. Apply the same change
in `k8s/base/ingress.yaml`.

### 4. Create the secret

```bash
kubectl create namespace medpharm
kubectl -n medpharm create secret generic medpharm-secrets \
  --from-literal=MEDPHARM_JWT_SECRET="$(openssl rand -base64 48)" \
  --from-literal=MEDPHARM_SECRET_KEY="$(openssl rand -base64 48)"
```

### 5. Apply the GCP overlay

```bash
kubectl apply -k k8s/overlays/gcp
kubectl -n medpharm rollout status deploy/medpharm-server
kubectl -n medpharm describe managedcertificate medpharm-cert
# wait until status shows "Active" — can take 10–60 min while the cert provisions
```

### Resources created

* `ManagedCertificate medpharm-cert` — Google-managed TLS
* `FrontendConfig medpharm-frontend` — HTTP→HTTPS redirect
* `Ingress` on `gce` class — binds to reserved IP `medpharm-ip`
* PVC bound to `standard-rwo` (regional persistent disk)

---

## Amazon Web Services (EKS)

### 1. Prerequisites

* An EKS cluster with the **AWS Load Balancer Controller** installed:
  <https://kubernetes-sigs.github.io/aws-load-balancer-controller/>
* **EBS CSI driver** with a `gp3` StorageClass.
* An **ACM certificate** covering your domain in the same region as the cluster.

### 2. Edit the overlay

Open `k8s/overlays/aws/ingress-patch.yaml` and replace
`alb.ingress.kubernetes.io/certificate-arn` with your ACM ARN. Update the
hostname in `k8s/base/ingress.yaml`.

### 3. Create the secret

```bash
kubectl create namespace medpharm
kubectl -n medpharm create secret generic medpharm-secrets \
  --from-literal=MEDPHARM_JWT_SECRET="$(openssl rand -base64 48)" \
  --from-literal=MEDPHARM_SECRET_KEY="$(openssl rand -base64 48)"
```

### 4. Apply the EKS overlay

```bash
kubectl apply -k k8s/overlays/aws
kubectl -n medpharm get ingress medpharm-server
# wait for ADDRESS column → ALB DNS name; point your CNAME at it
```

### Resources created

* `Ingress` on `alb` class — internet-facing ALB, HTTPS via ACM
* PVC bound to `gp3` (EBS)
* Health check: `GET /api/v1/health`

---

## Linode / DigitalOcean / Bare-metal

Works on any cluster running **ingress-nginx**. Uses cert-manager for TLS
(optional — strip the annotations if you terminate TLS upstream).

### 1. Install ingress-nginx (once per cluster)

```bash
# Linode Kubernetes Engine / DigitalOcean / k3s / kubeadm:
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.2/deploy/static/provider/cloud/deploy.yaml
```

### 2. (Optional) Install cert-manager + Let's Encrypt issuer

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.3/cert-manager.yaml

cat <<'EOF' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: you@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
EOF
```

### 3. Edit the overlay

Update `medpharm.example.com` in `k8s/overlays/generic/ingress-patch.yaml`
and `k8s/base/ingress.yaml`. Point its DNS record at the LoadBalancer IP of
ingress-nginx:

```bash
kubectl -n ingress-nginx get svc ingress-nginx-controller
```

### 4. Create the secret and apply

```bash
kubectl create namespace medpharm
kubectl -n medpharm create secret generic medpharm-secrets \
  --from-literal=MEDPHARM_JWT_SECRET="$(openssl rand -base64 48)" \
  --from-literal=MEDPHARM_SECRET_KEY="$(openssl rand -base64 48)"

kubectl apply -k k8s/overlays/generic
```

---

## Upgrades & Rollback

### Upgrade to a newer image

Edit `images.newTag` in the overlay you use (or in `k8s/base/kustomization.yaml`):

```yaml
images:
  - name: enlightec/medpharm-server
    newTag: "1.7.6"
```

Then re-apply:

```bash
kubectl apply -k k8s/overlays/<cloud>
kubectl -n medpharm rollout status deploy/medpharm-server
```

### Rollback

```bash
kubectl -n medpharm rollout undo deploy/medpharm-server
```

Or pin explicitly:

```bash
kubectl -n medpharm set image deploy/medpharm-server \
  medpharm=enlightec/medpharm-server:1.5.1
```

---

## Scaling Considerations

The shipping image embeds **SQLite**, which serialises all writes through a
single filesystem. The Deployment is therefore capped at `replicas: 1`.

To run more than one replica you must:

1. Migrate `MEDPHARM_DB_PATH` to a networked RDBMS (Postgres / MySQL). The
   code path uses `database.db_manager.DatabaseManager`; swap its backend.
2. Delete the `medpharm-data` PVC (data will live in the database cluster).
3. Raise `spec.replicas` in the Deployment and switch
   `spec.strategy.type` to `RollingUpdate`.
4. (Optional) Add a `HorizontalPodAutoscaler` keyed on CPU or request rate.

Until the database migration is done, vertical scaling (CPU/memory limits,
bigger node type) is the supported path.

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Pod `CrashLoopBackOff` | `kubectl -n medpharm logs deploy/medpharm-server` — usually missing/invalid `MEDPHARM_JWT_SECRET` |
| Pod `Pending` on first apply | `kubectl -n medpharm describe pvc medpharm-data` — no StorageClass? Set one with a PVC patch |
| Ingress has no address (GKE) | Static IP `medpharm-ip` not reserved, or `managedcertificate` still provisioning |
| ALB never appears (EKS) | AWS Load Balancer Controller not installed or lacks IAM permissions |
| 502 through ingress-nginx | Check readiness probe — image takes ~20–40 s on cold start |
| TLS cert stuck pending | `kubectl describe certificate -n medpharm` and verify DNS A record resolves to the LB |
| Data gone after pod delete | PVC was deleted too — treat `medpharm-data` as the authoritative store and back it up |

### Useful commands

```bash
# Live logs
kubectl -n medpharm logs -f deploy/medpharm-server

# Supervisor status inside the pod
kubectl -n medpharm exec deploy/medpharm-server -- supervisorctl status

# Direct health check
kubectl -n medpharm port-forward svc/medpharm-server 8080:80
curl http://localhost:8080/api/v1/health

# Backup the SQLite DB off-cluster
kubectl -n medpharm exec deploy/medpharm-server -- \
  sqlite3 /data/medpharm_erp.db ".backup /tmp/backup.db"
kubectl -n medpharm cp medpharm-server:/tmp/backup.db ./backup-$(date +%F).db
```

---

## See Also

* [INSTALLATION.md](INSTALLATION.md) — bare-metal / single-host Docker install
* [SERVER.md](SERVER.md) — ops runbook and hardening checklist
* [COMPILATION.md](COMPILATION.md) — building images from source
