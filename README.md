# k8s-platform-lab

Kubernetes platform built step by step on GKE, as a hands-on DevOps learning project.

Current state: containerized Python API running on GKE Autopilot, with health checks,
zero-downtime rolling updates, ConfigMaps and Secrets.
Planned: Terraform, CI/CD, Helm, Ingress with TLS, monitoring.

Progress and lessons learned: [PROGRESS.md](PROGRESS.md)

## Architecture

```mermaid
flowchart TB
    dev["Developer workstation (WSL + Docker Desktop)<br/>docker, gcloud, kubectl"]
    user["User"]

    subgraph gcp["GCP project: bank-devops-lab"]
        ar["Artifact Registry<br/>bank-apps-repo"]
        subgraph gke["GKE Autopilot: k8s-platform-lab (europe-central2)"]
            svc["Service: LoadBalancer<br/>port 80 → 8080"]
            deploy["Deployment: bank-api<br/>2 replicas, probes, rolling update"]
            cm["ConfigMap: bank-api-config<br/>env vars + /etc/bank/config.json"]
            sec["Secret: bank-api-secret<br/>VAULT_TOKEN"]
        end
    end

    dev -- "docker build & push" --> ar
    dev -- "kubectl apply" --> gke
    user -- "HTTP :80" --> svc
    svc --> deploy
    ar -- "image pull" --> deploy
    cm --> deploy
    sec --> deploy
```