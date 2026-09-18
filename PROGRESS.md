## Status: 2026-09-15
**Plan week:** 1 (Kubernetes fundamentals)  
**Course:** not started yet

### Done
- Repo created, initial project structure
- Basic app + Dockerfile + manifests in place

### Stuck on
- (nothing yet)

### Next
- GKE cluster via console
- Push image to Artifact Registry, deploy to cluster

---

## Status: 2026-09-18
**Sprint:** 3A (completed) / 3B (starting)  
**Course:** "Kubernetes in Polish" (Modules 2 & 8 completed, Module 5 started)

### Done
- Restored the regional GKE Autopilot cluster (`bank-cluster`) in Warsaw (`europe-central2`)
- Deployed and verified `readinessProbe` and `livenessProbe` on `/health` (port 8080) in `deployment.yaml`
- Configured Zero-Downtime `RollingUpdate` strategy (`maxSurge: 1`, `maxUnavailable: 0`)
- Tested failure scenario (invalid `:v3` tag → `ImagePullBackOff`) and performed rollback (`kubectl rollout undo`) without service disruption
- Added `.dockerignore` file and hardened project configuration

### Stuck on
- (none — I/O timeout errors and YAML indentation issues resolved)

### Next
- Create `configmap.yaml` (`bank-api-config`) and extract `ENV=production` variable from `deployment.yaml`
- Verify environment variables inside the container using `kubectl exec`
- Deploy a Secret and mount configuration as files via `volumeMounts`