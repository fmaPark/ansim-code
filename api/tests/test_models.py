def test_catalog_loads_31_rules():
    from app.engine.catalog import load_rules

    rules = load_rules()
    assert len(rules) == 31
    assert sum(1 for r in rules if r["derivation"] == "direct") == 27
    assert sum(1 for r in rules if r["derivation"] == "aux") == 4
    assert all(r["standard_ref"] for r in rules)


def test_rule_catalog_version_changes_with_content(tmp_path):
    from app.engine.catalog import rule_catalog_version

    (tmp_path / "a.yaml").write_text("x: 1")
    v1 = rule_catalog_version(tmp_path)
    (tmp_path / "a.yaml").write_text("x: 2")
    assert rule_catalog_version(tmp_path) != v1
