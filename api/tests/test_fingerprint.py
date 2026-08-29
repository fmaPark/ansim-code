from app.engine.fingerprint import tree_fingerprint


def _make(root, files: dict):
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


def test_crlf_and_junk_do_not_change_fingerprint(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _make(a, {"m.py": b"x=1\ny=2\n"})
    _make(b, {"m.py": b"x=1\r\ny=2\r\n", ".DS_Store": b"junk"})   # Win 줄바꿈 + Mac 부산물
    assert tree_fingerprint(a) == tree_fingerprint(b)             # TDD §4.3 재업로드 지문 일치


def test_content_change_changes_fingerprint(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _make(a, {"m.py": b"x=1\n"})
    _make(b, {"m.py": b"x=2\n"})
    assert tree_fingerprint(a) != tree_fingerprint(b)
