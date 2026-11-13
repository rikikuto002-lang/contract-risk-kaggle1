"""Rule-based engine cho các điều khoản có khả năng bất lợi.

Mỗi rule nhận nội dung một khoản và trả về danh sách Finding.
- status "vi_pham": vi phạm có thể kiểm chứng bằng phép tính hoặc so khớp rõ ràng.
- status "can_xem_xet": có dấu hiệu nhưng không đủ căn cứ để kết luận (ví dụ lãi không rõ đơn vị).
Rule không bao giờ tự kết luận khi không chắc chắn.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from src.data.segment import Clause

UNIT_FACTOR = {"tháng": 12.0, "năm": 1.0, "ngày": 365.0}  # quy đổi về %/năm
NUM = r"(\d+(?:[.,]\d+)?)"
RATE_UNIT = r"(?:/|mỗi|một|hàng)?\s*(?:tháng|năm|ngày)"


@dataclass
class Finding:
    rule_id: str
    status: str
    evidence: str
    explanation: str
    citation: str
    clause_key: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _f(s: str) -> float:
    return float(s.replace(",", "."))


def _finding(rid: str, status: str, evidence: str, explanation: str, params: dict) -> Finding:
    return Finding(rule_id=rid, status=status, evidence=evidence,
                   explanation=explanation, citation=params.get("citation", ""))


# ---------- CIV-01: lãi chậm trả quy đổi về %/năm ----------
def rule_civ01(text: str, ctx: dict, params: dict) -> list[Finding]:
    if "lãi" not in text.lower():
        return []
    out: list[Finding] = []
    unit_re = re.compile(NUM + r"\s*%\s*" + r"(?:/|mỗi|một|hàng)?\s*(tháng|năm|ngày)", re.IGNORECASE)
    for m in unit_re.finditer(text):
        annual = _f(m.group(1)) * UNIT_FACTOR[m.group(2).lower()]
        if annual > params["max_annual_rate_pct"]:
            out.append(_finding(
                "CIV-01", "vi_pham", m.group(0),
                f"Lãi quy đổi khoảng {annual:.1f}%/năm, vượt ngưỡng {params['max_annual_rate_pct']:g}%/năm.",
                params))
    if not unit_re.search(text):
        # có % nhưng không có đơn vị thời gian -> không kết luận, chuyển xem xét
        m = re.search(NUM + r"\s*%(?!\s*" + RATE_UNIT + ")", text, re.IGNORECASE)
        if m:
            out.append(_finding(
                "CIV-01", "can_xem_xet", m.group(0),
                "Có mức lãi % nhưng không rõ đơn vị thời gian (tháng/năm/ngày); cần xem xét thủ công.",
                params))
    return out


# ---------- CIV-02: mức phạt vi phạm ----------
PENALTY_KW = re.compile(r"phạt\s+vi\s+phạm|tiền\s+phạt", re.IGNORECASE)


def rule_civ02(text: str, ctx: dict, params: dict) -> list[Finding]:
    if not PENALTY_KW.search(text):
        return []
    out = []
    for m in re.finditer(NUM + r"\s*%(?!\s*" + RATE_UNIT + ")", text, re.IGNORECASE):
        pct = _f(m.group(1))
        if pct > params["max_penalty_pct"]:
            out.append(_finding(
                "CIV-02", "vi_pham", m.group(0),
                f"Mức phạt {pct:g}% vượt ngưỡng {params['max_penalty_pct']:g}% giá trị nghĩa vụ.",
                params))
    return out


# ---------- LAB-01: giữ giấy tờ gốc ----------
RETAIN_RE = re.compile(
    r"giữ\s+(?:bản\s+chính|bằng\s+cấp|chứng\s+minh\s+nhân\s+dân|căn\s+cước|giấy\s+tờ\s+tùy\s+thân|hộ\s+chiếu)",
    re.IGNORECASE)
SELF_HOLD_RE = re.compile(r"(?:người\s+lao\s+động|nlđ)\s+tự\s+giữ", re.IGNORECASE)


def rule_lab01(text: str, ctx: dict, params: dict) -> list[Finding]:
    m = RETAIN_RE.search(text)
    if not m or SELF_HOLD_RE.search(text):
        return []
    return [_finding("LAB-01", "vi_pham", m.group(0),
                     "Điều khoản cho phép bên sử dụng lao động giữ giấy tờ gốc của người lao động.",
                     params)]


# ---------- LAB-02: thử việc ----------
PROBATION_RE = re.compile(r"thử\s+việc[^.;]*?(\d+)\s*(ngày|tháng)", re.IGNORECASE)
ROLE_PATTERNS = [
    ("quan_ly", r"quản\s+lý|giám\s+đốc|trưởng\s+phòng"),
    ("cao_dang", r"cao\s+đẳng|đại\s+học"),
    ("trung_cap", r"trung\s+cấp"),
]


def _detect_role(text: str) -> str:
    for key, pat in ROLE_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return key
    return "mac_dinh"


def rule_lab02(text: str, ctx: dict, params: dict) -> list[Finding]:
    m = PROBATION_RE.search(text)
    if not m:
        return []
    n = int(m.group(1))
    days = n * 30 if m.group(2).lower() == "tháng" else n
    role = _detect_role(text)
    limit = params["max_probation_days"][role]
    if days > limit:
        return [_finding("LAB-02", "vi_pham", m.group(0),
                         f"Thời gian thử việc {days} ngày vượt mức tối đa {limit} ngày (nhóm: {role}).",
                         params)]
    return []


# ---------- LAB-03: thời hạn báo trước khi đơn phương chấm dứt ----------
NOTICE_RE = re.compile(r"(?:đơn\s+phương\s+chấm\s+dứt|báo\s+trước)[^.;]*?(\d+)\s*(ngày|tháng)", re.IGNORECASE)


def _notice_regime(text: str, ctx: dict) -> str:
    t = text.lower()
    if "không xác định thời hạn" in t:
        return "khong_xac_dinh_thoi_han"
    if re.search(r"dưới\s+12\s+tháng|ngắn\s+hạn", t):
        return "duoi_12_thang"
    return ctx.get("duration_regime", "xac_dinh_thoi_han")


def rule_lab03(text: str, ctx: dict, params: dict) -> list[Finding]:
    m = NOTICE_RE.search(text)
    if not m:
        return []
    days = int(m.group(1)) * (30 if m.group(2).lower() == "tháng" else 1)
    regime = _notice_regime(text, ctx)
    minimum = params["min_notice_days"][regime]
    if days < minimum:
        return [_finding("LAB-03", "vi_pham", m.group(0),
                         f"Báo trước {days} ngày thấp hơn mức tối thiểu {minimum} ngày (loại: {regime}).",
                         params)]
    return []


# ---------- LEA-01: đặt cọc không hoàn lại ----------
DEPOSIT_RE = re.compile(r"đặt\s+cọc", re.IGNORECASE)
NON_REFUND_RE = re.compile(r"không\s+hoàn\s+(?:lại|trả)", re.IGNORECASE)
CONDITION_RE = re.compile(r"\bnếu\b|trừ\s+trường\s+hợp|với\s+điều\s+kiện", re.IGNORECASE)


def rule_lea01(text: str, ctx: dict, params: dict) -> list[Finding]:
    if not DEPOSIT_RE.search(text):
        return []
    m = NON_REFUND_RE.search(text)
    if not m or CONDITION_RE.search(text):
        return []
    return [_finding("LEA-01", "vi_pham", m.group(0),
                     "Tiền đặt cọc không hoàn lại vô điều kiện.", params)]


RULE_FUNCS = {
    "CIV-01": rule_civ01,
    "CIV-02": rule_civ02,
    "LAB-01": rule_lab01,
    "LAB-02": rule_lab02,
    "LAB-03": rule_lab03,
    "LEA-01": rule_lea01,
}


def run_rules(clauses: list[Clause], rules_cfg: dict, context: dict | None = None) -> list[Finding]:
    ctx = context or {}
    findings: list[Finding] = []
    for clause in clauses:
        for rid, fn in RULE_FUNCS.items():
            for f in fn(clause.text, ctx, rules_cfg.get(rid, {})):
                f.clause_key = clause.key
                findings.append(f)
    return findings
