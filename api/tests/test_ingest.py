import os
import zipfile

import pytest

from app.engine.ingest import ValidationError, ingest_zip
from app.engine.workspace import scan_workspace


def test_workspace_purged_even_on_exception():   # P0-1 (TDD §9 P0 검증)
    leaked = {}
    with pytest.raises(RuntimeError):
        with scan_workspace() as ws:
            leaked["path"] = ws
            (ws / "code.py").write_text("x=1")
            raise RuntimeError("파이프라인 임의 단계 실패")
    assert not os.path.exists(leaked["path"])    # 강제 예외에도 잔존 0


def test_zip_path_traversal_rejected(tmp_path):
    z = tmp_path / "evil.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("../../etc/passwd", "x")
    with scan_workspace() as ws:
        with pytest.raises(ValidationError):
            ingest_zip(z, ws)


def test_zip_skips_junk_dirs(tmp_path):
    z = tmp_path / "app.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("app/main.py", "import flask")
        f.writestr("app/node_modules/lodash/index.js", "x")
        f.writestr("app/.DS_Store", "x")
    with scan_workspace() as ws:
        r = ingest_zip(z, ws)
        files = {str(p.relative_to(r.root)) for p in r.root.rglob("*") if p.is_file()}
        assert files == {"app/main.py"}
