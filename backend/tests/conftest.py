import os

os.environ.setdefault("FLEET_DATABASE_URL", "sqlite+pysqlite:////tmp/fleet-maintenance-tests.db")
os.environ.setdefault("FLEET_AUTO_CREATE_SCHEMA", "true")
os.environ.setdefault("FLEET_AUTO_SEED_DEMO", "true")
