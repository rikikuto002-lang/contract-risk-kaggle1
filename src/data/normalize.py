"""Chuẩn hóa văn bản tiếng Việt trước khi xử lý.

- Chuẩn hóa Unicode về dạng NFC (dấu thanh có thể được mã hóa nhiều cách).
- Thay khoảng trắng đặc biệt, xóa ký tự zero-width, gộp khoảng trắng thừa.
Giữ nguyên dấu xuống dòng để phân đoạn cấu trúc Điều/Khoản.
"""
from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace(" ", " ").replace("​", "").replace("﻿", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(lines)
