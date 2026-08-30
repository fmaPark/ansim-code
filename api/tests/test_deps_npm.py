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


def _with_lock(tmp_path, resolved: str):
    """package.json(direct) + lock(direct 병합 + transitive) 한 벌. resolved만 바꿔 넣는다."""
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"lodash": "^4.17.15"}}))
    (tmp_path / "package-lock.json").write_text(json.dumps({
        "lockfileVersion": 3,
        "packages": {
            "node_modules/lodash": {"version": "4.17.15", "resolved": resolved},
            "node_modules/nested": {"version": "1.0.0", "resolved": resolved}}}))
    return {d.name: d for d in parse_npm_deps(tmp_path)}


def test_registry_resolved_url_stays_registry(tmp_path):
    """이슈 #28 — 공개 레지스트리 URL이 https://라는 이유로 비레지스트리가 되면 안 된다."""
    deps = _with_lock(tmp_path, "https://registry.npmjs.org/lodash/-/lodash-4.17.15.tgz")
    assert deps["lodash"].registry_source is True      # 매니페스트 선언 + lock 병합 경로
    assert deps["nested"].registry_source is True      # lock 전용(transitive) 경로


def test_git_resolved_url_flagged_nonregistry(tmp_path):
    deps = _with_lock(tmp_path, "git+https://github.com/x/lodash.git#abc123")
    assert deps["lodash"].registry_source is False
    assert deps["nested"].registry_source is False


def test_unknown_host_resolved_url_flagged_nonregistry(tmp_path):
    """사설·임의 호스트는 계속 SCA-10 대상이다."""
    deps = _with_lock(tmp_path, "https://example.com/tarballs/lodash-4.17.15.tgz")
    assert deps["lodash"].registry_source is False
    assert deps["nested"].registry_source is False
