import os
import tempfile
from pathlib import Path

os.environ.setdefault(
    "FLEET_DATABASE_URL",
    f"sqlite+pysqlite:///{Path(tempfile.mkdtemp(prefix='fleet-tests-')) / 'test.db'}",
)
os.environ.setdefault("FLEET_AUTO_CREATE_SCHEMA", "true")
os.environ.setdefault("FLEET_AUTO_SEED_DEMO", "true")
