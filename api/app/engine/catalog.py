import hashlib
from pathlib import Path

import yaml

from app.config import settings


def load_rules(path: str | None = None) -> list[dict]:
    p = Path(path or settings.rules_dir) / "catalog.yaml"
    return yaml.safe_load(p.read_text())["rules"]


def rule_catalog_version(rules_dir=None) -> str:   # TDD §4.5: rules/ 콘텐츠 해시
    root = Path(rules_dir or settings.rules_dir)
    h = hashlib.sha256()
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        h.update(str(f.relative_to(root)).encode())
        h.update(hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()[:16]
