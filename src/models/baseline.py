"""Bộ phân loại đa nhãn: TF-IDF + Logistic Regression (One-vs-Rest)."""
from __future__ import annotations

from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import make_pipeline

from src.features.text_features import make_vectorizer


def build_model(model_cfg: dict):
    lr = model_cfg["logreg"]
    clf = OneVsRestClassifier(
        LogisticRegression(C=lr["C"], max_iter=lr["max_iter"], class_weight=lr["class_weight"])
    )
    return make_pipeline(make_vectorizer(model_cfg), clf)
