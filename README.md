# k8s-platform-lab

Kubernetes platform built step by step on GKE, as a hands-on DevOps learning project.

Current state: containerized Python API (v2) running on GKE Autopilot with health checks,
zero-downtime rolling updates, ConfigMaps, Secrets, HTTPS through GKE Ingress
with a Google-managed certificate, and a stateful PostgreSQL database with persistent storage on GCP Persistent Disk.
Planned: network isolation (NetworkPolicies), multi-tenancy / namespaces, Helm packaging, CI/CD, monitoring.

The cluster runs only during work sessions, so the public URL is usually offline.

Progress and lessons learned: [PROGRESS.md](PROGRESS.md)

## Architecture

```mermaid
flowchart TB
    dev["Developer workstation (WSL + Docker Desktop)<br/>docker, gcloud, kubectl"]
    user["User"]
    dns["Cloudflare DNS<br/>bank.testnginxraz2.online<br/>(DNS only)"]

    subgraph gcp["GCP project: bank-devops-lab"]
        ar["Artifact Registry<br/>bank-apps-repo"]
        disk[("GCP Persistent Disk<br/>regional/zonal storage")]
        subgraph gke["GKE Autopilot: k8s-platform-lab (europe-central2)"]
            ing["Ingress: bank-api-ingress<br/>external Application Load Balancer<br/>ManagedCertificate + FrontendConfig (HTTP → HTTPS)"]
            svc["Service: ClusterIP<br/>port 80 → 8080 (NEG)"]
            deploy["Deployment: bank-api (v2)<br/>2 replicas across 2 zones, probes, rolling update"]
            cm["ConfigMap: bank-api-config<br/>env vars + /etc/bank/config.json"]
            sec["Secret: bank-api-secret<br/>VAULT_TOKEN, DB_PASSWORD"]
            dbsvc["Service: postgres<br/>ClusterIP :5432"]
            db["StatefulSet: postgres-0<br/>PostgreSQL 16"]
            pvc["PersistentVolumeClaim<br/>postgres-pvc (10Gi)"]
        end
    end

    dev -- "docker build & push" --> ar
    dev -- "kubectl apply" --> gke
    user -- "DNS lookup" --> dns
    user -- "HTTPS :443" --> ing
    ing --> svc
    svc --> deploy
    ar -- "image pull" --> deploy
    cm --> deploy
    sec --> deploy
    deploy -- "SQL queries :5432" --> dbsvc
    dbsvc --> db
    db --> pvc
    pvc -. "backed by" .-> disk

## Repository structure

```
app/        Python API (Flask + Gunicorn, psycopg2) and Dockerfile
k8s/        Kubernetes manifests deployment, service, configmap, secret template,
            ingress, managed certificate, frontend config,
            postgres-pvc, postgres-service, postgres-statefulset
PROGRESS.md Work log: what I did, what broke, what I learned
```

## Deploy

Requires an existing GKE cluster, `kubectl` configured for it,
and a domain pointing to the Ingress IP.

```bash
# create your own secret from the template (never commit it)
cp k8s/secret.example.yaml k8s/secret.yaml
# edit k8s/secret.yaml and fill in the values

# configuration, secrets and database storage
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/postgres-statefulset.yaml

# application workloads & networking
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/certificate.yaml
kubectl apply -f k8s/frontend-config.yaml
kubectl apply -f k8s/ingress.yaml
```

The Google-managed certificate can take 40–60 minutes to become `Active`:

```bash
kubectl get managedcertificate bank-api-cert
```