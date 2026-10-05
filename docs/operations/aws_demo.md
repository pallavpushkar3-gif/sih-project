# AWS demonstration deployment

This deployment runs the retained demonstration model and synthetic workspace on
one Ubuntu 24.04 x86 EC2 instance. `compose.aws-demo.yaml` enables the isolated
`tunnel_demo` application profile with server sessions and secure cookies; HTTPS
terminates directly on EC2. PostgreSQL, RabbitMQ, and the API have no published
ports. Only nginx publishes 80 and 443. Restrict SSH to the operator's IP.

The signup update adds **Create account** to the sign-in screen. Its AWS overlay
enables self-registration with viewer access to the shared synthetic records.
Planning and approval still require an operator-provisioned role. A new account
chooses its own ID and password, then signs in after registration succeeds.
The initial installer pins the baseline release; retain the tested signup source
update alongside it when reproducing this later deployment.

Sign-in and signup retain per-IP proxy rate limits. A blocked attempt returns
HTTP 429 with `Retry-After: 30`; the form explains the wait and disables further
submissions during the countdown. Waiting does not unlock an account locked
after five incorrect passwords; that separate lock lasts fifteen minutes.

## Initial installation

Review `scripts/deploy_aws_demo.sh`, then run it as root on a fresh authorized
Ubuntu 24.04 instance with its public IPv4 address as the only argument. The script
pins the reviewed source revision and verifies the published model bundle's
SHA-256. It generates database and broker passwords on the server, migrates the
database, installs the bundle, obtains HTTPS, and configures certificate renewal.
Certificate issuance accepts the Let's Encrypt subscriber agreement.

The hostname is `sih-<public IPv4 with dashes>.sslip.io`. A public IP change after
an EC2 stop/start requires a new hostname, origin configuration, and certificate.
Rebooting the instance normally preserves its IP. A purchased domain is optional.

## Administration

On the server:

```bash
cd /home/ubuntu/sih-project
dc() {
  sudo docker compose --env-file .env.production -f compose.yaml \
    -f compose.production.yaml -f compose.aws-demo.yaml -f compose.ec2.yaml "$@"
}
dc ps
dc logs --tail 100 api worker outbox web
dc run --rm -v "$PWD:/workspace:ro" api \
  python /workspace/scripts/provision_user.py demo-supervisor \
  --display-name 'Demo Supervisor' --role supervisor
```

The account command prompts privately for a password of at least 14 characters.
Use `scripts/backup_local.py` with all four compose files and database
`fleet_public_demo` before upgrades. Keep environment files, SSH keys, and
credentials out of Git. Never remove the database/artifact volumes to restart.

## Cost control

The AWS Free Plan consumes credits while the instance runs. EC2, EBS, public IPv4,
and data transfer can consume credits separately. Stop the instance from EC2 when
the demonstration is not needed; storage remains allocated and can still incur
usage. Stop/start may change the URL as described above. Check remaining credits
in the AWS Billing console; Free Plan duration does not guarantee enough credits
for continuous operation.
