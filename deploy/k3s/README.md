# Deploying to k3s

## What changes versus running locally

Running Celery in its own pod changes one thing structurally: **SQLite stops
being viable.** The web pod and the worker pod are separate processes on
possibly separate nodes, and there is no safe way for both to write to one
SQLite file. Postgres becomes mandatory.

Nothing in the application code changes for this — it already reads
`DATABASE_URL`. Only the Secret and `10-postgres.yaml` are involved.

| Local | In-cluster |
|---|---|
| SQLite file | Postgres StatefulSet with a PVC |
| `CELERY_TASK_ALWAYS_EAGER=True` | `False` — a real worker Deployment |
| Redis not running | Redis Deployment with a PVC |
| Vite dev server proxies `/api` | Traefik Ingress routes `/api` |
| `runserver` | gunicorn, 3 workers × 2 replicas |
| Static files from the dev server | WhiteNoise, collected at image build |

## First deploy

Namespace first, then the Secret (which everything else references):

```bash
kubectl apply -f deploy/k3s/00-namespace.yaml
```

Create the Secret imperatively so real values never enter git:

```bash
kubectl -n job-outreach create secret generic joa-secrets --from-literal=DJANGO_SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(64))')" --from-literal=POSTGRES_PASSWORD='CHANGE-ME' --from-literal=DATABASE_URL='postgres://joa:CHANGE-ME@joa-postgres:5432/job_outreach'
```

> The password appears twice and the two must match — Postgres is initialised
> with one and the app connects with the other.

Then config and the stateful services:

```bash
kubectl apply -f deploy/k3s/01-config.yaml -f deploy/k3s/10-postgres.yaml -f deploy/k3s/11-redis.yaml
```

Wait for the database before migrating:

```bash
kubectl -n job-outreach rollout status statefulset/joa-postgres --timeout=180s
```

Migrate, then bring up the application:

```bash
kubectl apply -f deploy/k3s/20-migrate-job.yaml && kubectl -n job-outreach wait --for=condition=complete job/joa-migrate --timeout=300s
```

```bash
kubectl apply -f deploy/k3s/21-backend.yaml -f deploy/k3s/22-worker.yaml -f deploy/k3s/23-frontend.yaml -f deploy/k3s/30-ingress.yaml
```

Point the hostname at your node (on the machine you browse from):

```bash
echo "<node-ip> joa.local" | sudo tee -a /etc/hosts
```

On Windows the file is `C:\Windows\System32\drivers\etc\hosts` and needs an
administrator editor.

The app is then at <http://joa.local>.

## Creating the first admin user

```bash
kubectl -n job-outreach exec -it deploy/joa-backend -- python manage.py createsuperuser
```

## Deploying a new image

CI publishes `latest` and a `sha-<commit>` tag on every push that touches the
relevant directory. `imagePullPolicy: Always` plus a restart is enough:

```bash
kubectl -n job-outreach rollout restart deployment/joa-backend deployment/joa-worker
```

Pinning to an exact build is better than trusting `latest`:

```bash
kubectl -n job-outreach set image deployment/joa-backend backend=haze21/joa-backend:sha-<commit>
```

**Re-run the migration Job whenever a deploy includes a migration**, before
restarting the backend:

```bash
kubectl -n job-outreach delete job joa-migrate --ignore-not-found && kubectl apply -f deploy/k3s/20-migrate-job.yaml
```

## Scaling

Workers are the thing to scale — scans are slow and I/O bound:

```bash
kubectl -n job-outreach scale deployment/joa-worker --replicas=4
```

Each pod runs `--concurrency=2`, so four pods give eight concurrent scans.
Remember every one of them holds a Postgres connection.

## Gotchas worth knowing before they bite

**`SECURE_SSL_REDIRECT` must stay `False` until TLS exists.** The production
settings default it to `True`; without a certificate, Django redirects http to
https, nothing terminates https, and the browser loops. It is set to `False` in
the ConfigMap with a comment — flip it, and `SECURE_HSTS_SECONDS`, once
cert-manager is issuing certificates.

**Health probes need a `Host` header.** Kubernetes probes address the pod by
IP. Django compares that against `ALLOWED_HOSTS`, does not find it, and answers
`400` — the probe fails and the pod is killed on a loop. `21-backend.yaml` sets
an explicit `Host` header; keep it in `DJANGO_ALLOWED_HOSTS`.

**`CRAWLER_ALLOW_PRIVATE_NETWORKS` must stay `False`.** It is more dangerous in
a cluster than on a laptop: the pod network can reach every other Service, and
the cloud metadata endpoint sits on a link-local address. It exists only so the
test suite can crawl a local fixture server.

**Redis uses `Recreate`, not `RollingUpdate`.** Two pods cannot share one
ReadWriteOnce volume, so a rolling update would hang waiting for a mount the
outgoing pod still holds.

## Checking it works

```bash
kubectl -n job-outreach get pods,svc,ingress
```

```bash
kubectl -n job-outreach logs -f deployment/joa-worker
```

Start a scan from the UI and watch it land in the worker log. That log line
moving from the backend pod to the worker pod is the proof Celery is genuinely
running out of process.
