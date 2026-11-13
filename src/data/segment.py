"""Phân đoạn hợp đồng thành Điều / Khoản.

Đơn vị phân đoạn là Khoản, kèm tiêu đề Điều làm ngữ cảnh (theo báo cáo mục 3.1).
Các trường hợp đánh số không chuẩn được gom vào khoản gần nhất và ghi chú khóa.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from src.data.normalize import normalize_text

ARTICLE_RE = re.compile(r"^\s*(Điều\s+\d+[.:]?.*)$", re.IGNORECASE)
CLAUSE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)[.)]\s+(.*)$")


@dataclass
class Clause:
    key: str        # "<tiêu đề điều>|<số khoản>", dùng để truy vết
    article: str
    text: str


def segment_clauses(text: str, min_chars: int = 20) -> list[Clause]:
    text = normalize_text(text)
    clauses: list[Clause] = []
    article = "Mở đầu"
    current: Clause | None = None

    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue

        art = ARTICLE_RE.match(line)
        if art:
            article = art.group(1).strip()
            current = None
            continue

        cl = CLAUSE_RE.match(line)
        if cl:
            current = Clause(key=f"{article}|{cl.group(1)}", article=article, text=cl.group(2).strip())
            clauses.append(current)
        elif current is not None:
            # dòng tiếp theo của khoản hiện tại (xuống dòng giữa câu)
            current.text = f"{current.text} {line}"
        else:
            current = Clause(key=f"{article}|0", article=article, text=line)
            clauses.append(current)

    return [c for c in clauses if len(c.text) >= min_chars]
