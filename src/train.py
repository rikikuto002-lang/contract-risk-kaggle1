"""Huấn luyện baseline TF-IDF + Logistic Regression và đánh giá theo nhóm hợp đồng.

Đầu vào CSV cần các cột: contract_id, text, và mỗi nhãn trong config.data.label_columns (0/1).
Chạy:
    python -m src.train --data data/processed/clauses_labeled.csv
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.data.normalize import normalize_text
from src.evaluation.metrics import group_cv_report
from src.models.baseline import build_model
from src.utils.config import load_config, project_root, set_seed


def main(argv: list[str] | None = None) -> dict:
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--out-dir", default=None)
    args = p.parse_args(argv)

    cfg = load_config()
    set_seed(cfg["seed"])
    labels = cfg["data"]["label_columns"]

    df = pd.read_csv(args.data)
    missing = [c for c in [cfg["data"]["group_column"], cfg["data"]["text_column"], *labels] if c not in df.columns]
    if missing:
        raise ValueError(f"Thiếu cột trong dữ liệu: {missing}")

    texts = df[cfg["data"]["text_column"]].fillna("").map(normalize_text).to_numpy()
    Y = df[labels].to_numpy(dtype=int)
    groups = df[cfg["data"]["group_column"]].to_numpy()

    report = group_cv_report(texts, Y, groups,
                             lambda: build_model(cfg["model"]),
                             n_splits=cfg["evaluation"]["n_splits"], label_names=labels)

    model = build_model(cfg["model"])
    model.fit(texts, Y)

    out_dir = Path(args.out_dir) if args.out_dir else project_root() / cfg["paths"]["models"]
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "labels": labels}, out_dir / "baseline_tfidf_lr.joblib")

    rep_dir = project_root() / cfg["paths"]["outputs"] / "metrics"
    rep_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (rep_dir / f"metrics_baseline_{stamp}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Macro-F1 (GroupKFold, {report['n_splits']} fold): {report['macro_f1']:.3f}")
    return report


if __name__ == "__main__":
    main()
