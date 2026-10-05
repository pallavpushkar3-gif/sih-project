import io
import tarfile

import pytest

from fleet_maintenance.services.demo_bundle import FILES, install_bundle
from fleet_maintenance.settings import get_settings


@pytest.mark.parametrize("kind", ["traversal", "duplicate", "symlink", "oversized"])
def test_bundle_rejects_unsafe_archive_before_installation(
    isolated_session,
    monkeypatch,
    tmp_path,
    kind,
):
    settings = get_settings()
    monkeypatch.setattr(settings, "environment", "tunnel_demo")
    monkeypatch.setattr(settings, "authentication_mode", "session")
    monkeypatch.setattr(settings, "artifact_root", tmp_path / "installed")
    bundle = tmp_path / "bad.tar.gz"
    with tarfile.open(bundle, "w:gz") as archive:
        for name in (*FILES, "bundle.json"):
            info = tarfile.TarInfo(name)
            info.size = 2
            if name == "model.joblib":
                if kind == "traversal":
                    info.name = "../outside"
                if kind == "symlink":
                    info.type = tarfile.SYMTYPE
                    info.linkname = "../outside"
                    info.size = 0
                if kind == "oversized":
                    info.size = 50_000_001
                    # A header-only archive is enough to reject the declared size.
                    archive.fileobj.write(info.tobuf())
                    break
            archive.addfile(info, io.BytesIO(b"{}") if info.isfile() else None)
        if kind == "duplicate":
            info = tarfile.TarInfo("bundle.json")
            info.size = 2
            archive.addfile(info, io.BytesIO(b"{}"))
    with pytest.raises((ValueError, tarfile.ReadError)):
        install_bundle(isolated_session, bundle)
    assert not (tmp_path / "outside").exists()
    assert not (settings.artifact_root / "customer-trial-v1").exists()
