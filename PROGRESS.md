## Status: 2026-09-15
**Sprint:** 1 & 2 (Foundations)  
**Focus Area:** Containerization & GKE Autopilot Baseline

### Done
- Initial project structure and repository setup
- Hardened container image (`python:3.11-slim`, non-root execution, Gunicorn)
- Basic Kubernetes manifests created (`deployment.yaml`, `service.yaml`)

### Stuck on
- (nothing)

### Next
- Provision GKE Autopilot cluster in `europe-central2`
- Configure Google Artifact Registry and execute remote image deployment

---

## Status: 2026-09-18
**Sprint:** 3A (completed) / 3B (starting)  
**Focus Area:** Microservice Resilience, Health Checks & Day-2 Operations

### Done
- Restored regional GKE Autopilot cluster (`bank-cluster`) in Warsaw (`europe-central2`)
- Configured and validated `readinessProbe` and `livenessProbe` on `/health` (port 8080)
- Enforced Zero-Downtime `RollingUpdate` strategy (`maxSurge: 1`, `maxUnavailable: 0`)
- Tested failure scenario (invalid `:v3` tag → `ImagePullBackOff`) and executed zero-downtime rollback (`kubectl rollout undo`)
- Hardened build hygiene by introducing `.dockerignore`

### Stuck on
- (none — resolved Control Plane I/O timeouts and YAML indentation schema issues)

### Next
- Decouple application configuration into `ConfigMap` (`bank-api-config`)
- Verify runtime environment variables inside container via `kubectl exec`
- Implement Kubernetes `Secret` and volume mounts for sensitive credentials

---

## Status: 2026-09-25
**Sprint:** 3B (completed) / 4A (starting)  
**Focus Area:** Configuration Decoupling, Secrets Management & Runtime Delivery

### Done
- Decoupled configuration into `ConfigMap` (`bank-api-config`) supporting both environment variables and volume mounts[cite: 1, 2]
- Mounted `/etc/bank/config.json` via read-only volume and validated Linux atomic directory swap (`..data` symlinks)[cite: 1, 2]
- Empirically verified frozen process environment behavior vs. dynamic volume sync handled by Kubelet[cite: 1, 2]
- Deployed `Secret` (`bank-api-secret`), injected credentials into pods, and audited Base64 obfuscation vs. encryption at rest[cite: 1, 2]
- Executed rolling restarts to propagate environment changes without downtime[cite: 1, 2]

### Stuck on
- (none — patch state and pod environment lifecycle validated)

### Next
- Transition from Layer 4 `LoadBalancer` Service to Layer 7 GCP Ingress Controller
- Provision Google-managed SSL/TLS Certificate for automated HTTPS termination
- Implement path-based routing and secure health checks on Ingress