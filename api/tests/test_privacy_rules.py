"""Task 15 — 개인정보 10종(P1~P10) + 보조 4종(AUX) 룰: 룰별 양성·음성 케이스.

semgrep 실행 룰(P2·P3·P6·AUX-*)은 실제 semgrep CLI로 1회 스캔해 검증한다
(semgrep 미설치 환경은 skip — docker 이미지에는 동봉).
repo 단위 검사(P5·P7·P8·P9·P10)는 순수 파이썬이라 항상 돈다.
단언 기준: rule_id·status가 카탈로그 표의 verdict와 일치할 것.
"""
import shutil
import textwrap

import pytest

HAS_SEMGREP = shutil.which("semgrep") is not None


# ── semgrep 룰 (양성·음성 한 저장소에 모아 1회 스캔) ─────────────────────────

@pytest.fixture(scope="module")
def semgrep_hits(tmp_path_factory):
    if not HAS_SEMGREP:
        pytest.skip("semgrep 없음 — docker compose run api pytest로 검증")
    root = tmp_path_factory.mktemp("repo")
    (root / "pos_p6.py").write_text(textwrap.dedent("""\
        def save(db, rrn):
            db.execute("insert into users values (%s)", (rrn,))
    """))
    (root / "neg_p6.py").write_text(textwrap.dedent("""\
        def save(db, rrn):
            db.execute("insert into users values (%s)", (encrypt(rrn),))
    """))
    (root / "pos_p2.py").write_text('def collect(request):\n    return request.form["phone"]\n')
    (root / "neg_p2.py").write_text('def collect(request):\n    return request.form["csrf_token"]\n')
    (root / "pos_p3.py").write_text('def collect(request):\n    return request.form["health_record"]\n')
    # 이슈 #32 — Django·DRF 요청 객체. 이게 빠져 있어 PyGoat에서 P1·P2·P3가 동시에 침묵했다.
    (root / "pos_p2_django.py").write_text(textwrap.dedent("""\
        def collect(request):
            email = request.POST.get("email")
            phone = request.GET["phone"]
            birth = request.data["birth_date"]
            return email, phone, birth
    """))
    (root / "neg_p2_django.py").write_text('def collect(request):\n    return request.POST.get("page")\n')
    (root / "pos_p3_django.py").write_text(
        'def collect(request):\n    return request.POST["health_record"]\n')
    (root / "pos_p2_express.js").write_text(
        "function collect(req) {\n  return [req.query.email, req.params.phone];\n}\n")
    (root / "pos_aux1.py").write_text(
        'def q(cur, x):\n    cur.execute(f"select * from t where id={x}")\n')
    (root / "neg_aux1.py").write_text(
        'def q(cur, x):\n    cur.execute("select * from t where id=%s", (x,))\n')
    (root / "pos_aux2.py").write_text("DEBUG = True\n")
    (root / "pos_aux3.py").write_text(
        'app.add_middleware(CORSMiddleware, allow_origins=["*"])\n')
    # 이슈 #31 — Express에서 압도적으로 흔한 cors 미들웨어 형태.
    (root / "pos_aux3_cors.js").write_text(
        'const cors = require("cors");\napp.use(cors({ origin: "*" }));\n')
    (root / "pos_aux3_cors_noargs.js").write_text(
        'const cors = require("cors");\napp.use(cors());\n')
    (root / "neg_aux3_cors.js").write_text(
        'const cors = require("cors");\napp.use(cors({ origin: ["https://ok.example"] }));\n')
    (root / "pos_aux4.py").write_text("import pickle\n\ndef load(d):\n    return pickle.loads(d)\n")
    (root / "neg_aux4.py").write_text(
        "import yaml\n\ndef load(f):\n    return yaml.load(f, Loader=yaml.SafeLoader)\n")
    from app.engine.semgrep_runner import run_ansim_semgrep

    return run_ansim_semgrep(root)


def _rules_hit_in(hits, filename):
    return {h.ansim_rule for h in hits if h.file.endswith(filename)}


def test_p6_positive_negative(semgrep_hits):
    assert "P6" in _rules_hit_in(semgrep_hits, "pos_p6.py")
    assert "P6" not in _rules_hit_in(semgrep_hits, "neg_p6.py")


def test_p2_positive_negative(semgrep_hits):
    assert "P2" in _rules_hit_in(semgrep_hits, "pos_p2.py")
    assert "P2" not in _rules_hit_in(semgrep_hits, "neg_p2.py")


def test_p2_django_and_express(semgrep_hits):
    """이슈 #32 — Flask 밖의 요청 객체도 잡는다."""
    assert "P2" in _rules_hit_in(semgrep_hits, "pos_p2_django.py")
    assert "P2" not in _rules_hit_in(semgrep_hits, "neg_p2_django.py")
    assert "P2" in _rules_hit_in(semgrep_hits, "pos_p2_express.js")


def test_p3_positive(semgrep_hits):
    assert "P3" in _rules_hit_in(semgrep_hits, "pos_p3.py")
    assert "P3" in _rules_hit_in(semgrep_hits, "pos_p3_django.py")      # 이슈 #32


def test_aux_rules(semgrep_hits):
    assert "AUX-01" in _rules_hit_in(semgrep_hits, "pos_aux1.py")
    assert "AUX-01" not in _rules_hit_in(semgrep_hits, "neg_aux1.py")
    assert "AUX-02" in _rules_hit_in(semgrep_hits, "pos_aux2.py")
    assert "AUX-03" in _rules_hit_in(semgrep_hits, "pos_aux3.py")
    assert "AUX-04" in _rules_hit_in(semgrep_hits, "pos_aux4.py")
    assert "AUX-04" not in _rules_hit_in(semgrep_hits, "neg_aux4.py")


def test_aux3_cors_middleware(semgrep_hits):
    """이슈 #31 — 응답 헤더 직접 조작만 잡던 JS 룰이 cors 미들웨어도 잡는다."""
    assert "AUX-03" in _rules_hit_in(semgrep_hits, "pos_aux3_cors.js")
    assert "AUX-03" in _rules_hit_in(semgrep_hits, "pos_aux3_cors_noargs.js")
    assert "AUX-03" not in _rules_hit_in(semgrep_hits, "neg_aux3_cors.js")


def test_semgrep_draft_status_follows_catalog(semgrep_hits):
    # G3: confirmed 룰(P6·AUX)은 confirmed, LLM 경유 룰(P2·P3)은 review_needed
    from app.engine.analysis import drafts_from_semgrep

    drafts = drafts_from_semgrep(semgrep_hits)
    by_rule = {d.rule_id: d for d in drafts}
    assert by_rule["P6"].status == "confirmed" and by_rule["P6"].severity == "critical"
    assert by_rule["P2"].status == "review_needed" and by_rule["P2"].severity == "high"
    assert by_rule["P3"].status == "review_needed"
    assert by_rule["AUX-01"].status == "confirmed" and by_rule["AUX-01"].severity == "high"


# ── repo 단위 검사 (P5·P7·P8·P9·P10 — 순수 파이썬) ──────────────────────────

def _mk(root, name, content):
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def test_p9_privacy_policy_absent_and_present(tmp_path):
    from app.engine.repo_checks import run_repo_checks

    _mk(tmp_path, "app.py", "x = 1\n")
    hits = {d.rule_id: d for d in run_repo_checks(tmp_path)}
    assert "P9" in hits and hits["P9"].status == "confirmed" and hits["P9"].file_path is None

    _mk(tmp_path, "privacy_policy.md", "개인정보처리방침\n")
    assert "P9" not in {d.rule_id for d in run_repo_checks(tmp_path)}


def test_p9_not_silenced_by_code_filename(tmp_path):
    """이슈 #34 — 파일명에 privacy가 든 코드 파일은 처리방침이 아니다.

    부재 판정 룰이라 거짓 매칭 하나가 발견 전체를 없앤다. fixture는 tmp_path에만 만든다
    (이 테스트 파일 자신의 이름이 원래 오판정의 원인 중 하나였다).
    """
    from app.engine.repo_checks import run_repo_checks

    _mk(tmp_path, "app.py", "x = 1\n")
    _mk(tmp_path, "rules/privacy.yaml", "rules: []\n")
    _mk(tmp_path, "src/usePrivacySettings.ts", "export const x = 1;\n")
    assert "P9" in {d.rule_id for d in run_repo_checks(tmp_path)}

    _mk(tmp_path, "docs/privacy.md", "개인정보처리방침\n")     # 문서가 생기면 정상적으로 꺼진다
    assert "P9" not in {d.rule_id for d in run_repo_checks(tmp_path)}


def test_p7_route_without_auth(tmp_path):
    from app.engine.repo_checks import run_repo_checks

    _mk(tmp_path, "admin.py", '@app.route("/admin/users")\ndef users():\n    return []\n')
    hits = {d.rule_id: d for d in run_repo_checks(tmp_path)}
    assert "P7" in hits and hits["P7"].status == "confirmed"

    _mk(tmp_path, "admin.py",
        '@app.route("/admin/users")\n@login_required\ndef users():\n    return []\n')
    assert "P7" not in {d.rule_id for d in run_repo_checks(tmp_path)}


def test_p8_pii_without_logging(tmp_path):
    from app.engine.repo_checks import run_repo_checks

    _mk(tmp_path, "svc.py", "def f(jumin):\n    return jumin\n")
    hits = {d.rule_id: d for d in run_repo_checks(tmp_path)}
    assert "P8" in hits and hits["P8"].status == "confirmed" and hits["P8"].severity == "low"

    _mk(tmp_path, "svc.py", "import logging\n\ndef f(jumin):\n    return jumin\n")
    assert "P8" not in {d.rule_id for d in run_repo_checks(tmp_path)}


def test_p5_scraping_with_pii(tmp_path):
    from app.engine.repo_checks import run_repo_checks

    _mk(tmp_path, "crawler.py",
        "import requests\nfrom bs4 import BeautifulSoup\n\n"
        "def crawl(url):\n    soup = BeautifulSoup(requests.get(url).text)\n"
        "    return soup.select('.phone')\n")
    hits = {d.rule_id: d for d in run_repo_checks(tmp_path)}
    assert "P5" in hits and hits["P5"].status == "review_needed"   # LLM 경유 → G3


def test_p10_model_without_deletion(tmp_path):
    from app.engine.repo_checks import run_repo_checks

    _mk(tmp_path, "models.py", "class User(db.Model):\n    name = db.Column()\n")
    hits = {d.rule_id: d for d in run_repo_checks(tmp_path)}
    assert "P10" in hits and hits["P10"].status == "review_needed"

    _mk(tmp_path, "cleanup.py", "def purge_expired():\n    User.query.delete()\n")
    assert "P10" not in {d.rule_id for d in run_repo_checks(tmp_path)}
