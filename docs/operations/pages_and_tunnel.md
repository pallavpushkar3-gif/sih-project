# GitHub Pages and local HTTPS demo

Open **https://pallavpushkar3-gif.github.io/sih-project/**. This publishes the original React application and aircraft assets, through `.github/workflows/deploy-pages.yml`. Hash navigation supports refreshes on Pages under `/sih-project/`. The workflow also publishes `/full-app/` static assets for the single-origin fallback; the tunneled HTML uses these CDN assets while API requests and cookies stay on its own origin. The tunnel proxy permits only this explicit asset origin in its content security policy and compresses API JSON.

The backend remains local: FastAPI, PostgreSQL, RabbitMQ, Celery and outbox dispatcher. `compose.tunnel.yaml` uses separate `fleet-tunnel-demo` volumes and the `fleet_public_demo` database. It exposes only the web proxy on **127.0.0.1:18080**, with no public database, broker or API ports. Do not tunnel the ordinary local development installation.

## First installation

Keep Docker Desktop running. Use the repository's verified Node/pnpm setup from README. Copy `.env.tunnel.example` to `.env.tunnel`, generate separate database and broker passwords, and put them in the two password fields and matching connection URLs. Use URL-encoded credentials in URLs. Retain the exact database name. Set allowed origins to the Pages **origin** (`https://pallavpushkar3-gif.github.io`, without the repository path) and your tunnel origin.

```sh
docker compose --env-file .env.tunnel -f compose.yaml -f compose.production.yaml -f compose.tunnel.yaml build
docker compose --env-file .env.tunnel -f compose.yaml -f compose.production.yaml -f compose.tunnel.yaml up -d postgres rabbitmq --wait
docker compose --env-file .env.tunnel -f compose.yaml -f compose.production.yaml -f compose.tunnel.yaml run --rm --no-deps api alembic upgrade head
```

The runtime requires the verified model/sample bundle; a source clone alone has no learned model. Retained bytes can be packaged with the shared application rather than retraining or inventing predictions:

```sh
docker run --rm -v "$PWD:/workspace" -w /workspace -e PYTHONPATH=/workspace/backend/src fleet-maintenance-test python scripts/demo_bundle.py package --model artifacts/models/customer-trial-v1 --sample artifacts/release-v2/public-demo-sample.json --output artifacts/demo-bundle.tar.gz
```

Download the published [verified demo bundle](https://github.com/pallavpushkar3-gif/sih-project/releases/download/demo-bundle-2026-10-05/demo-bundle.tar.gz) to `artifacts/demo-bundle.tar.gz`. Verify its SHA-256 is `18b0e5ae0791aff50a2dc5a77c4b5aec16144fff4fff4a374c018b423e9fef26` (`shasum -a 256 artifacts/demo-bundle.tar.gz` on macOS). This release asset supplies the retained bytes for a fresh clone; no NASA bulk dataset is needed for serving.

Install that trusted bundle, then provision a supervisor with the existing interactive account tool:

```sh
docker compose --env-file .env.tunnel -f compose.yaml -f compose.production.yaml -f compose.tunnel.yaml run --rm --no-deps -v "$PWD:/workspace:ro" api python /workspace/scripts/demo_bundle.py install --bundle /workspace/artifacts/demo-bundle.tar.gz
docker compose --env-file .env.tunnel -f compose.yaml -f compose.production.yaml -f compose.tunnel.yaml run --rm --no-deps -v "$PWD:/workspace:ro" api python /workspace/scripts/provision_user.py demo-supervisor --display-name "Synthetic Demo Supervisor" --role supervisor
docker compose --env-file .env.tunnel -f compose.yaml -f compose.production.yaml -f compose.tunnel.yaml up -d --wait
```

The current synthetic public supervisor uses account **demo-supervisor**, password **AeroCare-Demo-2026!**. This deliberately shared demo account has no administrator privilege. Use synthetic data only; saved cases are visible to other signed-in demo visitors. Do not reuse this password for private or operational installations.

The installer checks file paths, bounded regular files, checksums, model/transformation/calibration loading and the sample's validation partition. It refuses to overwrite different existing model/sample bytes. Readiness refuses a missing or invalid bundle. No model weights arrive from browser uploads.

## Start and rotate the tunnel

The current demonstration uses localhost.run. Keep its SSH process running:

```sh
ssh -nT -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -R 80:127.0.0.1:18080 nokey@localhost.run
```

Copy the generated **HTTPS** origin into `.env.tunnel`'s allowed origins. Recreate the API and reload the proxy after changing it:

```sh
docker compose --env-file .env.tunnel -f compose.yaml -f compose.production.yaml -f compose.tunnel.yaml up -d --wait
docker compose --env-file .env.tunnel -f compose.yaml -f compose.production.yaml -f compose.tunnel.yaml up -d --force-recreate web --wait
```

In GitHub **Settings → Secrets and variables → Actions → Variables**, set:

| Variable | Value |
|---|---|
| `DEMO_API_URL` | `https://YOUR-TUNNEL-HOST/api` |
| `DEMO_FULL_APP_URL` | `https://YOUR-TUNNEL-HOST` |
| `DEMO_FULL_APP_ONLY` | `true` for the verified browser-compatible path |

Run **Actions → Deploy original product to GitHub Pages → Run workflow** after rotating the URL. Pages source must be **GitHub Actions**. Public URL variables are not secrets; never put passwords or tunnel credentials in these variables. The repository About/Website field and README use the stable Pages URL.

## Login, browser boundaries and availability

Cross-origin fetch and SSE use credentials. CORS allows exact configured origins, login requires an allowed Origin, and mutations require both that Origin and the returned CSRF token. Cookies are Secure/HttpOnly and scoped to `/api`; tunnel mode can opt into `SameSite=None`, while production retains Strict. No browser role header overrides session roles.

Chrome verification showed credentialed login and SSE worked across two TLS origins when third-party cookies were allowed. Enabling Chrome's third-party-cookie restriction prevented retention even with None; the UI presented the complete-app link. The public configuration therefore checks backend readiness and opens `/demo` on the tunnel origin automatically. Set `FLEET_COOKIE_SAMESITE=strict` for that single-origin configuration. No session token or password is transported in URLs.

Pages stays available when Docker, the computer or the SSH process stops. It displays **Demo backend offline** with a retry button, rather than a login form or fabricated predictions. API requests have a twelve-second timeout. A free tunnel URL can change or expire; update the origins and Pages variables after reconnecting. Continuous access requires keeping the host awake or moving this stack to a continuously running host.

Cloudflare Quick Tunnels explicitly do not support SSE, so they are not the default for this workflow. See [Cloudflare's limitation](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/), [localhost.run HTTPS operation](https://localhost.run/docs/security/) and [MDN's third-party-cookie boundary](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS).

## Retain and stop

The general backup tool accepts the overlay stack and its database:

```sh
python3 scripts/backup_local.py --env-file .env.tunnel --compose compose.yaml --compose compose.production.yaml --compose compose.tunnel.yaml --database fleet_public_demo --output artifacts/tunnel-backup
docker compose --env-file .env.tunnel -f compose.yaml -f compose.production.yaml -f compose.tunnel.yaml down
```

Stop SSH when finished. Do not use `down -v` unless intentionally deleting the demo database and artifacts. Backups, secrets and runtime state remain outside Git.

## Reproduce public browser verification

After installing web dependencies and Chrome, the repository includes a verification entry point. It asserts trusted TLS, Pages redirection, exact credentialed CORS, rejection of untrusted origins/missing CSRF, secure session-cookie attributes, an actual `connected` SSE event and the offline display. It never prints a cookie or CSRF token.

```sh
FLEET_CHECK_FRONTEND=https://pallavpushkar3-gif.github.io/sih-project/ FLEET_CHECK_BACKEND=https://YOUR-TUNNEL-HOST node scripts/verify_demo_deployment.mjs
```

The published synthetic login is `demo-supervisor` / `AeroCare-Demo-2026!`; it gives only the supervisor role in this shared synthetic workspace. Replace the account/password for any controlled customer rehearsal using `FLEET_CHECK_USER` and `FLEET_CHECK_PASSWORD`. `FLEET_CHECK_LOCAL_TLS=1` accepts self-signed test certificates **only** when both URL hosts are localhost/127.0.0.1; it cannot disable verification for a public origin. Optional `FLEET_CHECK_STORAGE_PATH` retains a private local browser-state file for the live customer-trial suite.

Final executed public verification on 2026-10-05: the standalone deployment check passed all assertions and all five live `customer-trial.spec.ts` journeys passed through the trusted public tunnel in 2.0 minutes after asset optimization. The initial unoptimized public run retained four load-timing failures; no single uninterrupted pass across both builds is claimed.
