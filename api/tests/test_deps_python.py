from app.engine.deps_python import parse_python_deps
from app.engine.imports_py import extract_python_imports


def test_requirements_and_pins(tmp_path):
    (tmp_path / "requirements.txt").write_text("flask==2.0.1\nrequests>=2.0\n")
    deps = {d.name: d for d in parse_python_deps(tmp_path)}
    assert deps["flask"].is_pinned and deps["flask"].version == "2.0.1"
    assert not deps["requests"].is_pinned          # SCA-11 입력
    assert deps["flask"].declared_in == "requirements.txt"


def test_import_extraction_excludes_stdlib_and_local(tmp_path):
    (tmp_path / "util.py").write_text("x=1")
    (tmp_path / "main.py").write_text("import os\nimport util\nimport requests\nfrom PIL import Image\n")
    assert extract_python_imports(tmp_path) == {"requests", "PIL"}
