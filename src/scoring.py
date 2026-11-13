"""Chấm điểm rủi ro tổng hợp: điểm = Σ w_k × c_k (báo cáo rà soát mục 5.7).

Mỗi cặp (rule, khoản) chỉ được tính một lần. c_k là độ tin cậy theo trạng thái cảnh báo.
Ngưỡng do chuyên gia đặt trong config; không trình bày điểm như chỉ số khách quan tuyệt đối.
"""
from __future__ import annotations


def score_findings(findings: list, weights: dict, confidence: dict, thresholds: dict) -> dict:
    seen: set[tuple[str, str]] = set()
    total = 0.0
    for f in findings:
        key = (f.rule_id, f.clause_key)
        if key in seen:
            continue
        seen.add(key)
        total += weights.get(f.rule_id, 0.5) * confidence.get(f.status, 0.0)

    if total >= thresholds["high"]:
        level = "cao"
    elif total >= thresholds["medium"]:
        level = "trung_binh"
    else:
        level = "thap" if total > 0 else "khong_co"
    return {"diem": round(total, 3), "muc_do": level, "so_canh_bao": len(seen)}
