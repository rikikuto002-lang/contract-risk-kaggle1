"""Mẫu prompt cho Zero/Few-shot LLM.

Đầu ra bắt buộc là JSON. Trích dẫn phải là nguyên văn, sau đó được kiểm tra bởi grounding.py.
Module này chỉ dựng prompt; không gọi API nào. Việc gọi mô hình thuộc lớp triển khai riêng.
"""
from __future__ import annotations

import json

SYSTEM_PROMPT = (
    "Bạn là trợ lý rà soát hợp đồng. Chỉ dựa trên đoạn văn được cung cấp. "
    "Với mỗi nhãn trong danh sách, trả về JSON gồm: nhan, co_rui_ro (true/false), "
    "muc_do (thap/trung_binh/cao), trich_dan (nguyên văn đoạn văn bản gốc, không được sửa đổi), "
    "giai_thich (không quá 2 câu). Nếu không có căn cứ trong đoạn văn, "
    "trả về co_rui_ro = false và trich_dan = null. Chỉ trả về JSON."
)


def build_prompt(clause_text: str, labels: list[str], examples: list[dict] | None = None) -> str:
    """Dựng prompt. `examples` là các ví dụ few-shot đã gán nhãn, chọn theo độ tương đồng (few-shot động)."""
    parts = [SYSTEM_PROMPT, "", "Nhãn: " + ", ".join(labels)]
    for ex in examples or []:
        parts.append("Ví dụ:\n" + json.dumps(ex, ensure_ascii=False))
    parts.append("Đoạn văn:\n" + clause_text)
    return "\n\n".join(parts)
