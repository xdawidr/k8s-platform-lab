## Status: 2026-09-15
Plan week: 1 (Kubernetes fundamentals)
Course: not started yet

### Done
- Repo created, initial project structure
- Basic app + Dockerfile + manifests in place

### Stuck on
- (nothing yet)

### Next
- GKE cluster via console
- Push image to Artifact Registry, deploy to cluster

### Status: 2026-09-18
3A (completed) / 3B (starting)
Course: “Kubernetes in Polish” (Modules 2 & 8 completed, Module 5 started) 

### Done
Restored the regional GKE Autopilot cluster (bank-cluster) in Warsaw (europe-central2). Deployed and verified the readinessProbe and livenessProbe on /health (port 8080) in deployment.yaml. Configured the Zero-Downtime RollingUpdate strategy (maxSurge: 1, maxUnavailable: 0). A failure scenario was tested (invalid :v3 tag $\rightarrow$ ImagePullBackOff) and a rollback was performed (kubectl rollout undo) without any loss of availability. A .dockerignore file was added.. 
### Stuck on 
(none—I/O timeout errors and YAML indentation issues resolved)

### Next
Create configmap.yaml (bank-api-config) and extract the ENV=production variable from deployment.yamlVerify environment variables inside the container using kubectl execDeploy a Secret and mount the configuration as files via volumeMounts
