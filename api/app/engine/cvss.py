"""CVSS 3.x 벡터 → Base/Impact/Exploitability 3값 파생 (0309 §6.14 · TDD §4.3 ⑭).

공식은 CVSS v3.1 Specification §7.1 + Appendix A(roundup)를 그대로 옮긴 것이다.
벡터가 없으면 None을 돌려 호출부가 `cvss_null_reason`을 남기게 한다.
"""

import math

W = {"AV": {"N": .85, "A": .62, "L": .55, "P": .2}, "AC": {"L": .77, "H": .44},
     "UI": {"N": .85, "R": .62}, "CIA": {"H": .56, "L": .22, "N": 0.0},
     "PR_U": {"N": .85, "L": .62, "H": .27}, "PR_C": {"N": .85, "L": .68, "H": .5}}

NULL_REASON_NO_VECTOR = "벡터 미제공"
NULL_REASON_UNPARSABLE = "벡터 해석 불가"


def _roundup(x: float) -> float:      # 스펙 Appendix A roundup
    i = int(round(x * 100000))
    return i / 100000 if i % 10000 == 0 else (math.floor(i / 10000) + 1) / 10.0


def derive_cvss3(vector: str | None) -> tuple[float, float, float, str] | None:
    if not vector or not str(vector).startswith("CVSS:3"):
        return None
    try:
        m = dict(p.split(":") for p in str(vector).split("/")[1:])
        scope_changed = m["S"] == "C"
        pr = (W["PR_C"] if scope_changed else W["PR_U"])[m["PR"]]
        iss = 1 - (1 - W["CIA"][m["C"]]) * (1 - W["CIA"][m["I"]]) * (1 - W["CIA"][m["A"]])
        impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15 if scope_changed else 6.42 * iss
        expl = 8.22 * W["AV"][m["AV"]] * W["AC"][m["AC"]] * pr * W["UI"][m["UI"]]
    except (KeyError, ValueError):
        return None
    if impact <= 0:
        base = 0.0
    elif scope_changed:
        base = _roundup(min(1.08 * (impact + expl), 10))
    else:
        base = _roundup(min(impact + expl, 10))
    sev = ("critical" if base >= 9 else "high" if base >= 7 else
           "medium" if base >= 4 else "low")
    return base, round(impact, 1), round(expl, 1), sev
