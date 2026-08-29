"""재진단 발견 diff (Task 21) — TDD §4.7 유스케이스 3.

이전 스캔과 현재 스캔의 발견을 `(rule_id, file_path, line)` 키로 대조해
해결됨·남아 있음·새로 생김 3분류로 나눈다. 지문 비교(코드 실제 변경 여부)는
호출부가 `content_fingerprint`로 판정한다.
"""


def _key(f) -> tuple:
    return (f.rule_id, f.file_path, f.line)


def _summary(f) -> dict:
    return {"id": f.id, "rule_id": f.rule_id, "file_path": f.file_path, "line": f.line,
            "severity": f.severity, "status": f.status}


def diff_findings(prev, curr) -> dict:
    """이전·현재 발견을 3분류. 같은 키가 여러 건이면 각각을 그대로 유지한다."""
    prev, curr = list(prev), list(curr)
    prev_keys = {_key(f) for f in prev}
    curr_keys = {_key(f) for f in curr}

    return {
        "resolved": [_summary(f) for f in prev if _key(f) not in curr_keys],
        "remaining": [_summary(f) for f in curr if _key(f) in prev_keys],
        "new": [_summary(f) for f in curr if _key(f) not in prev_keys],
    }


def compare_scans(previous, current, prev_findings, curr_findings) -> dict:
    """GET /api/scans/{id}의 `previous_comparison` 페이로드 (§4.7)."""
    diff = diff_findings(prev_findings, curr_findings)
    return {
        "previous_grade": previous.grade,
        "grade": current.grade,
        # 같은 지문이면 "코드 미변경" — 재진단이 실제 수정을 증명하는 축이다.
        "fingerprint_changed": previous.content_fingerprint != current.content_fingerprint,
        "diff": {
            "resolved_count": len(diff["resolved"]),
            "remaining_count": len(diff["remaining"]),
            "new_count": len(diff["new"]),
            **diff,
        },
    }
