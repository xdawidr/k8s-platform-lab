# Progress log

Short notes from building this project: what I did, what broke, what I learned.
The cluster only runs while I'm working on it and gets deleted afterwards to keep costs down.

---

#### 2026-10-10: Namespaces and NetworkPolicies (Sprint 5A)
**Done**
* Created two separate namespaces: `bank-dev` and `bank-prod` to start isolating environments.
* Added a `default-deny-all` NetworkPolicy in `bank-prod` to lock down all incoming and outgoing traffic.
* Confirmed the flat network issue: created an attacker pod in `bank-dev` and easily connected to `postgres.default:5432` (`open`).
* Added `postgres-allow-api` NetworkPolicy in `default` namespace so only pods with the label `app: bank-api` can access port 5432.
* Verified the database policy: the real API via public Ingress still works (200 OK), but the attacker pod in `bank-dev` gets a `Connection timed out` (packets are silently dropped).

**What surprised me / What broke**
* I confused Service port with container port: `bank-api-service` listens on port 80 and forwards to container port 8080. When I tried hitting port 8080 on the Service, the request timed out.
* Defense in Depth lesson: protecting only the database is not enough. I proved this by running `attacker-curl` in `bank-dev` against `bank-api-service.default:80/accounts`. The API returned Joe Doe's data without issues because `bank-api` had no firewall in front of it.

**Next**
* Create a NetworkPolicy for `bank-api` so it only accepts traffic from the Ingress controller.
* Move our database and API workloads from `default` into `bank-prod`.

---

## 2026-10-09: PostgreSQL persistence, Chaos test, and API v2

**Done**
- Deployed PostgreSQL as a `StatefulSet` (`postgres-0`) backed by a `PersistentVolumeClaim` (PVC) on GCP Persistent Disk.
- Added internal ClusterIP Service for Postgres on port 5432 and seeded the `accounts` table (`Joe Doe`, 10,000 balance).
- Performed a Chaos Engineering test: deleted `postgres-0` with `kubectl delete pod`. The StatefulSet recreated the Pod with the exact same name, re-attached the PVC, and SQL queries confirmed zero data loss.
- Implemented `/accounts` endpoint in `app/app.py` using `psycopg2-binary` to fetch records from the database.
- Built `bank-api:v2` locally and pushed it to GCP Artifact Registry (`europe-central2`).
- Updated `deployment.yaml` with the `:v2` image tag and ran a zero-downtime rolling update (`kubectl rollout status`).
- Verified end-to-end flow: `curl -i https://bank.testnginxraz2.online/accounts` returned `200 OK` with JSON account data.

**What surprised me**
- How predictable `StatefulSet` pod recovery is compared to `Deployment`. When the DB pod was killed, it didn't get a random hash name—it came right back as `postgres-0` and immediately re-bound to the existing storage volume.
- The entire path worked seamlessly through our previously built L7 Ingress: external HTTPS request -> TLS termination -> ClusterIP -> API v2 pod -> CoreDNS resolving `postgres` -> DB on persistent disk.

**Problems**
- Hitting `/accounts` initially returned a `404 Not Found` from Gunicorn. Looking at `app.py` made it obvious: version 1 only had routes for `/` and `/health`, with no DB drivers installed.
- `docker push` failed with `Unauthenticated request` on Artifact Registry. Local Docker needed GCP credentials configured via `gcloud auth configure-docker europe-central2-docker.pkg.dev` before it could upload layers.

**Next**
- Sprint 5A: Multi-tenancy and network security (`NetworkPolicy` to isolate PostgreSQL so only `bank-api` pods can reach port 5432).

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