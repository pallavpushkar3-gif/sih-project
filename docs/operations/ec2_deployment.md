# EC2 deployment preparation

Status: configuration prepared for one Ubuntu VM, Docker Compose and the existing Nginx web service. No AWS resource, DNS record, public certificate or external deployment has been created. Public deployment acceptance is **blocked** until the real host/domain exist and checks below execute. `DEPLOYMENT_DOMAIN` is mandatory; no hostname is assigned by this repository.

## Host prerequisites

The operator supplies an authorized EC2 Ubuntu host, team-controlled DNS hostname, SSH access and durable backup destination. Install Docker Engine and the Compose plugin using [Docker's Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/). The override requires Compose support for `!reset` and `!override`; verify `docker compose version` and configuration rendering before startup. Public inbound ports are 80 and 443; restrict SSH to authorized operator addresses. Database, broker, management and API ports must remain unpublished. Docker-published ports require appropriate host/network controls; see Docker's firewall guidance in that installation document.

Copy a reviewed source revision and locked dependencies. Use `cp .env.production.example .env.production`, restrict it to the operator (`chmod 600 .env.production`), and fill every blank. Use separate strong database/broker passwords; URL-encode them in the matching internal connection URLs (`postgresql+psycopg://fleet:…@postgres:5432/fleet`, `amqp://fleet:…@rabbitmq:5672//`). Set `FLEET_ALLOWED_ORIGINS` to a JSON array containing only `https://` plus the actual `DEPLOYMENT_DOMAIN`. Set absolute certificate/webroot directories. Production guards enforce sessions, secure cookies and disabled automatic fixture/schema creation.

Commands below run from the repository directory on that host, after those prerequisites exist. They are instructions, not a record of deployment.

```sh
docker compose --env-file .env.production -f compose.yaml -f compose.production.yaml -f compose.ec2.yaml config --quiet
```

Do not share the expanded configuration: it contains secrets. Verify only web publishes 80/443. Retain reviewed images with immutable registry digests or local image IDs before release; current base-image tags alone do not seal a release.

## Public certificate bootstrap

Create the configured ACME webroot and certificate directories. Point DNS at the host, including correct IPv6 routing if an AAAA record exists. Temporarily set `FLEET_PROXY_TEMPLATE=ec2-bootstrap.conf.template` in `.env.production`. This serves ACME challenges on HTTP and returns 503 for application requests; it does not expose authenticated application traffic over HTTP.

```sh
docker compose --env-file .env.production -f compose.yaml -f compose.production.yaml -f compose.ec2.yaml up -d --build
```

Install the operator-approved Certbot package on the host. Request a certificate with the **actual** domain/webroot and team email using `certbot certonly --webroot -w "$FLEET_ACME_DIRECTORY" -d "$DEPLOYMENT_DOMAIN"` (export those nonsecret values separately; Compose's env file does not export shell variables). Follow [Certbot's webroot and renewal documentation](https://eff-certbot.readthedocs.io/en/stable/using.html). This command contacts the certificate authority and is not authorized/executed during local preparation.

After issuance, restore `FLEET_PROXY_TEMPLATE=ec2-tls.conf.template` and recreate web:

```sh
docker compose --env-file .env.production -f compose.yaml -f compose.production.yaml -f compose.ec2.yaml up -d --force-recreate web
docker compose --env-file .env.production -f compose.yaml -f compose.production.yaml -f compose.ec2.yaml exec -T web nginx -t
```

Mount the whole certificate directory read-only so renewal symlinks resolve. Configure Certbot renewal and a successful-renewal deploy hook that runs `nginx -t` then `nginx -s reload` through the same absolute repository/env-file/Compose paths. Execute `certbot renew --dry-run` and verify the hook explicitly as documented by Certbot. An expiring certificate requires monitoring; a renewal schedule alone is not evidence of successful renewal.

## Application initialization and acceptance

Startup applies reviewed Alembic migrations before API readiness; verify migration head and all container health. Provision real demonstrator accounts using the existing interactive account command in production_readiness.md. Install/hash-verify trusted model directories in the artifact volume before registration. Import only authorized, labelled inputs; there is no automatic production seeding.

Run external checks from a separate machine: publicly trusted certificate/chain/hostname/expiry; HTTP redirect; HTTPS security headers; secure HttpOnly SameSite session cookie; login/logout/expiry; CSRF/origin and denied-role cases; SSE reconnection/session expiry; durable assessment/planning/simulation dispatch; stock/arrival/stale approval/work walkthrough. Verify direct database, broker and API ports are unreachable. Retain commands/results, source/image IDs and domain/date with the acceptance record. Local self-signed TLS checks cannot pass public HTTPS acceptance.

Quiesce API, workers and outbox writers for coordinated database/artifact backups. Retain migration head and manifests, then restore into a separate database and verify registered artifact hashes before switching. Preserve named volumes; never use `down -v` for routine release recovery. Rehearse rollback with compatible schema/data on the actual host. Capacity, monitoring, backup durability, renewal, reboot recovery and deployment-specific load remain to be checked there. Single-host deployment does not provide host failover.
