"""Biểu diễn đặc trưng văn bản bằng TF-IDF (mốc baseline theo báo cáo mục 3.3)."""
from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer


def make_vectorizer(cfg: dict) -> TfidfVectorizer:
    t = cfg["tfidf"]
    return TfidfVectorizer(
        ngram_range=tuple(t["ngram_range"]),
        min_df=t["min_df"],
        sublinear_tf=t["sublinear_tf"],
    )
