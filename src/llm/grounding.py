"""Kiểm tra trích dẫn (groundedness) để giảm ảo giác.

Mọi đoạn trích do LLM hoặc rule sinh ra phải tồn tại nguyên văn trong hợp đồng gốc
sau khi chuẩn hóa khoảng trắng, dấu câu và chữ hoa/thường. Trích dẫn không hợp lệ
bị loại bỏ, không được đưa vào báo cáo.
"""
from __future__ import annotations

import re
import unicodedata


def _canon(s: str) -> str:
    s = unicodedata.normalize("NFC", s).lower()
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def is_grounded(quote: str | None, source: str) -> bool:
    if not quote:
        return False
    q = _canon(quote)
    return bool(q) and q in _canon(source)


def filter_grounded(items: list[dict], source: str, key: str = "trich_dan") -> tuple[list[dict], int]:
    """Giữ các mục có trích dẫn hợp lệ. Trả về (mục_hợp_lệ, số_mục_bị_loại)."""
    kept = [it for it in items if is_grounded(it.get(key), source)]
    return kept, len(items) - len(kept)
