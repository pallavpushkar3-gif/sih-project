#!/usr/bin/env bash
# Fresh Ubuntu 24.04 installation. Run only on the authorized EC2 instance.
# Database/broker secrets are generated on the server and never printed.
# HTTPS issuance explicitly accepts Let's Encrypt's subscriber agreement.
set -euo pipefail
umask 077

if [[ ${EUID} -ne 0 || $# -ne 1 ]]; then
  echo "Usage on EC2: sudo bash deploy_aws_demo.sh PUBLIC_IPV4" >&2
  exit 1
fi
PUBLIC_IPV4=$1
python3 - "$PUBLIC_IPV4" <<'PY'
import ipaddress
import sys
address = ipaddress.IPv4Address(sys.argv[1])
if not address.is_global:
    raise SystemExit("A public IPv4 address is required")
PY
. /etc/os-release
if [[ $ID != ubuntu || $VERSION_ID != 24.04 ]]; then
  echo "This installer requires Ubuntu 24.04." >&2
  exit 1
fi

DEPLOYMENT_DOMAIN="sih-${PUBLIC_IPV4//./-}.sslip.io"
PROJECT_DIRECTORY=/home/ubuntu/sih-project
SOURCE_REVISION=c6f2f57625bed7fddabcc0fe72fddfa7e7f1e94f
BUNDLE_SHA256=18b0e5ae0791aff50a2dc5a77c4b5aec16144fff4fff4a374c018b423e9fef26
export DEBIAN_FRONTEND=noninteractive

echo "Installing official Ubuntu/Docker packages..."
apt-get update
apt-get install -y ca-certificates curl git openssl python3 certbot
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
cat > /etc/apt/sources.list.d/docker.sources <<'EOF'
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Architectures: amd64
Signed-By: /etc/apt/keyrings/docker.asc
EOF
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
docker compose version

echo "Checking out the reviewed source revision..."
if [[ ! -e $PROJECT_DIRECTORY ]]; then
  git clone https://github.com/pallavpushkar3-gif/sih-project.git "$PROJECT_DIRECTORY"
  git -C "$PROJECT_DIRECTORY" checkout --detach "$SOURCE_REVISION"
elif [[ ! -d $PROJECT_DIRECTORY/.git ]] || [[ $(git -C "$PROJECT_DIRECTORY" rev-parse HEAD) != "$SOURCE_REVISION" ]]; then
  echo "Existing source directory differs; retain it and review manually." >&2
  exit 1
fi
cd "$PROJECT_DIRECTORY"
# The runtime container is unprivileged. Only tracked source is made readable;
# private environment files retain mode 600.
python3 - <<'PY'
import os
from pathlib import Path
import stat
import subprocess
root = Path.cwd()
root.chmod(0o755)
for name in subprocess.check_output(['git', 'ls-files', '-z']).split(b'\0'):
    if not name:
        continue
    path = root / os.fsdecode(name)
    path.chmod(0o755 if path.stat().st_mode & stat.S_IXUSR else 0o644)
    for parent in path.parents:
        if parent == root:
            break
        parent.chmod(0o755)
PY
cat > compose.aws-demo.yaml <<'EOF'
name: fleet-aws-demo
services:
  postgres:
    environment:
      POSTGRES_DB: fleet_public_demo
    healthcheck:
      test: [CMD-SHELL, pg_isready -U fleet -d fleet_public_demo]
  rabbitmq:
    volumes:
      - aws-broker-data:/var/lib/rabbitmq
  api:
    environment: &aws_demo_environment
      FLEET_ENVIRONMENT: tunnel_demo
      FLEET_COOKIE_SAMESITE: strict
  worker:
    environment: *aws_demo_environment
    command: [celery, -A, fleet_maintenance.workers.celery_app:app, worker, --loglevel=INFO, --concurrency=2, --without-mingle, --without-gossip]
  outbox:
    environment: *aws_demo_environment
volumes:
  aws-broker-data:
EOF

if [[ ! -f .env.production ]]; then
  DATABASE_PASSWORD=$(openssl rand -hex 24)
  BROKER_PASSWORD=$(openssl rand -hex 24)
  cat > .env.production <<EOF
DEPLOYMENT_DOMAIN=$DEPLOYMENT_DOMAIN
FLEET_ALLOWED_ORIGINS='["https://$DEPLOYMENT_DOMAIN"]'
FLEET_POSTGRES_PASSWORD=$DATABASE_PASSWORD
FLEET_RABBITMQ_PASSWORD=$BROKER_PASSWORD
FLEET_RELEASE_DATABASE_URL=postgresql+psycopg://fleet:$DATABASE_PASSWORD@postgres:5432/fleet_public_demo
FLEET_RELEASE_BROKER_URL=amqp://fleet:$BROKER_PASSWORD@rabbitmq:5672//
FLEET_TLS_DIRECTORY=/etc/letsencrypt
FLEET_ACME_DIRECTORY=/var/lib/fleet-maintenance/acme
FLEET_PROXY_TEMPLATE=ec2-bootstrap.conf.template
EOF
  unset DATABASE_PASSWORD BROKER_PASSWORD
else
  if ! existing_domain=$(sed -n 's/^DEPLOYMENT_DOMAIN=//p' .env.production) || [[ $existing_domain != "$DEPLOYMENT_DOMAIN" ]]; then
    echo "Existing deployment uses another hostname; review before changing it." >&2
    exit 1
  fi
fi
chmod 600 .env.production

dc() {
  docker compose --env-file .env.production -f compose.yaml \
    -f compose.production.yaml -f compose.aws-demo.yaml -f compose.ec2.yaml "$@"
}
mkdir -p /etc/letsencrypt /var/lib/fleet-maintenance/acme artifacts
chmod 755 artifacts
mkdir -p /var/lib/fleet-maintenance/acme/.well-known/acme-challenge
chmod 755 /var/lib/fleet-maintenance/acme \
  /var/lib/fleet-maintenance/acme/.well-known \
  /var/lib/fleet-maintenance/acme/.well-known/acme-challenge
dc config --quiet
dc build
dc up -d postgres rabbitmq --wait
dc run --rm --no-deps api alembic upgrade head

echo "Downloading and verifying the retained demo model..."
curl -fL --retry 3 \
  https://github.com/pallavpushkar3-gif/sih-project/releases/download/demo-bundle-2026-10-05/demo-bundle.tar.gz \
  -o artifacts/demo-bundle.tar.gz
echo "$BUNDLE_SHA256  artifacts/demo-bundle.tar.gz" | sha256sum --check
chmod 644 artifacts/demo-bundle.tar.gz
dc run --rm --no-deps -v "$PROJECT_DIRECTORY:/workspace:ro" api \
  python /workspace/scripts/demo_bundle.py install --bundle /workspace/artifacts/demo-bundle.tar.gz

echo "Starting the certificate challenge server..."
dc up -d --wait
if ! getent ahostsv4 "$DEPLOYMENT_DOMAIN" | awk '{print $1}' | sort -u | grep -Fxq "$PUBLIC_IPV4"; then
  echo "Hostname does not resolve to this public IP; HTTPS issuance stopped." >&2
  exit 1
fi
# nginx workers must be able to read the public HTTP-01 challenge files.
umask 022
certbot certonly --webroot -w /var/lib/fleet-maintenance/acme \
  -d "$DEPLOYMENT_DOMAIN" --register-unsafely-without-email --agree-tos --non-interactive
sed -i 's/^FLEET_PROXY_TEMPLATE=.*/FLEET_PROXY_TEMPLATE=ec2-tls.conf.template/' .env.production
dc up -d --force-recreate web
dc exec -T web nginx -t

mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/fleet-reload.sh <<'EOF'
#!/bin/sh
set -eu
cd /home/ubuntu/sih-project
dc() {
  /usr/bin/docker compose --env-file .env.production -f compose.yaml \
    -f compose.production.yaml -f compose.aws-demo.yaml -f compose.ec2.yaml "$@"
}
dc exec -T web nginx -t
dc exec -T web nginx -s reload
EOF
chmod 750 /etc/letsencrypt/renewal-hooks/deploy/fleet-reload.sh
systemctl enable --now certbot.timer
certbot renew --dry-run --run-deploy-hooks
curl -fsS --retry 8 --retry-delay 3 --retry-all-errors "https://$DEPLOYMENT_DOMAIN/api/health/ready"
dc ps
echo
echo "HTTPS deployment ready: https://$DEPLOYMENT_DOMAIN"
echo "Next: provision a private supervisor account using scripts/provision_user.py; verify the browser workflow."
