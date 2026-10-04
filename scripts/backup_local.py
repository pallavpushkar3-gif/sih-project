"""Coordinated local Compose backup; stop writers, retain DB and artifacts together.

Archives contain application records and must be handled as sensitive data. Secrets
are deliberately excluded; operators must retain deployment secrets separately.
"""

import argparse
import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def run(*args: str) -> bytes:
    return subprocess.check_output(args)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compose", default="compose.yaml")
    args = parser.parse_args()
    destination = args.output.resolve()
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(destination, 0o700)
    compose = ["docker", "compose", "-f", args.compose]
    services = ["api", "worker", "outbox", "web"]
    active = run(*compose, "ps", "--status", "running", "--services").decode().splitlines()
    restart = [service for service in services if service in active]
    started = datetime.now(UTC)
    try:
        subprocess.check_call([*compose, "stop", *services])
        pg = run(*compose, "ps", "-q", "postgres").decode().strip()
        api = run(*compose, "ps", "-aq", "api").decode().strip()
        with (destination / "database.dump").open("wb") as stream:
            subprocess.run(
                [
                    "docker",
                    "exec",
                    pg,
                    "pg_dump",
                    "-U",
                    "fleet",
                    "-d",
                    "fleet",
                    "-Fc",
                    "--no-owner",
                    "--no-acl",
                ],
                stdout=stream,
                check=True,
            )
        (destination / "globals.sql").write_bytes(
            run(
                "docker",
                "exec",
                pg,
                "pg_dumpall",
                "-U",
                "fleet",
                "--globals-only",
                "--no-role-passwords",
            )
        )
        subprocess.check_call(
            [
                "docker",
                "cp",
                f"{api}:/var/lib/fleet-maintenance/artifacts",
                str(destination / "artifacts"),
            ]
        )
        schema = (
            run(
                "docker",
                "exec",
                pg,
                "psql",
                "-U",
                "fleet",
                "-d",
                "fleet",
                "-Atc",
                "SELECT version_num FROM alembic_version",
            )
            .decode()
            .strip()
        )
        tables = (
            run(
                "docker",
                "exec",
                pg,
                "psql",
                "-U",
                "fleet",
                "-d",
                "fleet",
                "-Atc",
                "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename",
            )
            .decode()
            .splitlines()
        )
        fingerprints = {}
        for table in tables:
            quoted = '"' + table.replace('"', '""') + '"'
            query = (
                "SELECT count(*),md5(coalesce(string_agg(to_jsonb(t)::text,E'\\n' "
                "ORDER BY to_jsonb(t)::text),'')) FROM "
                + quoted
                + " t"
            )
            fingerprints[table] = (
                run(
                    "docker",
                    "exec",
                    pg,
                    "psql",
                    "-U",
                    "fleet",
                    "-d",
                    "fleet",
                    "-Atc",
                    query,
                )
                .decode()
                .strip()
            )
        inventory = {
            str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(destination.rglob("*"))
            if path.is_file()
        }
        record = {
            "created_at": datetime.now(UTC).isoformat(),
            "started_at": started.isoformat(),
            "schema": schema,
            "table_fingerprints": fingerprints,
            "files": inventory,
            "source_head": run("git", "rev-parse", "HEAD").decode().strip(),
            "working_tree": "uncommitted; preserve release source manifest separately",
            "configuration": {
                "compose_sha256": hashlib.sha256(Path(args.compose).read_bytes()).hexdigest(),
                "scope": "single_agency",
                "secrets": "retained separately",
            },
            "role_handling": "Dump omits ownership/ACL; restore uses precreated fleet owner. "
            "Review globals.sql before applying; never replay cluster roles blindly.",
        }
        (destination / "backup.json").write_text(json.dumps(record, indent=2) + "\n")
        for path in destination.rglob("*"):
            if path.is_file():
                os.chmod(path, 0o600)
        print(json.dumps({"backup": str(destination), "schema": schema, "files": len(inventory)}))
    finally:
        if restart:
            subprocess.check_call([*compose, "start", *restart])


if __name__ == "__main__":
    main()
