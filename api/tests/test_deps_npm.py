import json

from app.engine.deps_npm import parse_npm_deps


def test_lock_integrity_and_transitive(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps(
        {"dependencies": {"express": "^4.18.0"}}))
    (tmp_path / "package-lock.json").write_text(json.dumps({
        "lockfileVersion": 3,
        "packages": {
            "node_modules/express": {"version": "4.18.2", "integrity": "sha512-AAA"},
            "node_modules/accepts": {"version": "1.3.8", "integrity": "sha512-BBB"}}}))
    deps = {d.name: d for d in parse_npm_deps(tmp_path)}
    assert deps["express"].version == "4.18.2" and deps["express"].relationship == "direct"
    assert deps["express"].integrity == "sha512-AAA"
    assert deps["accepts"].relationship == "transitive"


def test_git_dependency_flagged_nonregistry(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps(
        {"dependencies": {"leftpad": "git+https://github.com/x/leftpad.git"}}))
    d = parse_npm_deps(tmp_path)[0]
    assert d.registry_source is False        # SCA-10 입력
