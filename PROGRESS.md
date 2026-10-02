# Progress log

Short notes from building this project: what I did, what broke, what I learned.
The cluster only runs while I'm working on it and gets deleted afterwards to keep costs down.

---

## 2026-09-29: Housekeeping

- Fixed a typo in the `.dockerignore` filename (it was `.dockeringore`).
  Docker was silently ignoring the file, so nothing was actually excluded
  from the build context. Good reminder to verify things, not just add them.
- Noticed that `secret.yaml` had been committed to this public repo.
  The values were only test placeholders, but it's still a bad pattern:
  base64 isn't encryption, so anyone could decode them in one command.
  Removed the file from git history with `git filter-repo`, added it to
  `.gitignore`, and committed a `secret.example.yaml` template instead.
- Rewrote this log in my own words and added the problems I actually hit.

---

## 2026-09-25: ConfigMaps and Secrets

**Done**
- Recreated the cluster under a new name, `k8s-platform-lab` (previously `bank-cluster`).
- Moved app config out of the image into a ConfigMap (`bank-api-config`).
  The app reads it two ways: as env vars and as a file mounted at `/etc/bank/config.json`.
- Added a Secret (`bank-api-secret`) and injected `VAULT_TOKEN` into the pod as an env var.
- Used `kubectl rollout restart` to pick up config changes without downtime.

**What surprised me**
- After patching the ConfigMap, the env vars inside the running pod didn't change.
  Env vars are read once when the container starts, so the pod needs a restart.
  The mounted file did update after a while. `ls -la /etc/bank` shows why:
  kubelet keeps the files behind a `..data` symlink and swaps it atomically.
- Secrets are only base64-encoded, not encrypted. One `kubectl get secret ... | base64 --decode`
  and the password is in plain text. Anyone with read access to Secrets can do the same,
  which is why I want to move to Google Secret Manager later.

**Problems**
- I changed the ConfigMap with `kubectl patch`, then ran `kubectl apply -f configmap.yaml`
  and my patch was gone. The file in git is the source of truth, and manual changes
  get overwritten by the next apply.

**Next**
- Replace the L4 LoadBalancer Service with an Ingress (L7).
- Google-managed TLS certificate for HTTPS.

---

## 2026-09-18: Health checks and rollbacks

**Done**
- First deploy to GKE Autopilot in `europe-central2` (Warsaw), exposed through
  a LoadBalancer Service. Checked resource usage with `kubectl top`.
- Deleted the cluster after the session to save money, recreated it later.
  For now clusters are created by hand with `gcloud`.
- Added readiness and liveness probes on `/health` (port 8080).
- Set RollingUpdate to `maxSurge: 1, maxUnavailable: 0` so there's always
  at least one healthy pod during a deploy.

**Breaking things on purpose**
- Deployed a tag that doesn't exist (`:v3`). The new pod went into `ImagePullBackOff`,
  but thanks to `maxUnavailable: 0` the old pods kept serving traffic.
  Checked `kubectl rollout history` and rolled back with `kubectl rollout undo`.

**Problems**
- `kubectl` couldn't authenticate to GKE at first. It needs `gke-gcloud-auth-plugin`,
  and `gcloud components install` didn't work because my gcloud was installed via apt.
  Installing the plugin as an apt package fixed it.
- `kubectl apply` kept timing out. Most likely cause: I had deleted the cluster
  to save costs, and my kubeconfig still pointed to the old control plane endpoint.
  Recreating the cluster with `create-auto` (which also updates kubeconfig) fixed it.
  Lesson: clean up the kubeconfig context after deleting a cluster.
- YAML indentation errors. `--dry-run=client` and `--dry-run=server` helped find them
  before anything reached the cluster.

**Next**
- Move config into a ConfigMap, then add a Secret.

---

## 2026-09-15: Container and first manifests

**Done**
- Repo structure and first Dockerfile: `python:3.11-slim`, runs as a non-root user,
  served by Gunicorn instead of the Flask dev server.
- Basic `deployment.yaml` and `service.yaml`.

**Next**
- GKE Autopilot cluster and Artifact Registry: push the image and deploy it.

---

## 2026-10-02: Ingress, managed TLS, and HTTPS redirect

**Done**
- Replaced the L4 LoadBalancer Service with GKE Ingress (L7 external Application Load Balancer).
- Pointed `bank.testnginxraz2.online` to the load balancer IP in Cloudflare
  (DNS only, proxy disabled, so Google can verify the domain for the certificate).
- Added a Google-managed certificate (`ManagedCertificate: bank-api-cert`),
  so Google handles issuing and renewing it.
- Added a `FrontendConfig` (`bank-frontend-config`) with `redirectToHttps` to force HTTPS.
- Checked the result with `curl -IL`: port 80 returns `301` to HTTPS,
  then `200 OK` over HTTP/2 and TLS 1.3.

**What surprised me**
- The managed certificate took about 40–50 minutes to provision. While it was
  still `Provisioning`, `curl` over HTTPS failed with `unexpected eof while reading`,
  because the load balancer had no certificate to complete the TLS handshake with.
- The Service is only `ClusterIP`, yet the load balancer reaches it. GKE automatically
  added the `cloud.google.com/neg` annotation (container-native load balancing),
  so traffic goes straight to Pod IPs instead of through the nodes.
  `neg-status` also showed endpoints in two zones (`europe-central2-b` and `-c`),
  so my two replicas run in different zones.

**Problems**
- After creating the `FrontendConfig`, port 80 still returned `200 OK` instead of a redirect.
  `kubectl describe ingress` showed why: the resource does nothing on its own,
  the Ingress needs the `networking.gke.io/v1beta1.FrontendConfig` annotation to use it.
  After adding it, the 301 redirect started working.

**Next**
- Persistent storage: PVC and StorageClass backed by GCP Persistent Disk.
- Deploy PostgreSQL and check that data survives Pod restarts.

---