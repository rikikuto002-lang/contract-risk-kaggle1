"""Đánh giá theo nhóm hợp đồng (GroupKFold) với macro-F1 và F1 theo từng nhãn.

Chia theo hợp đồng để tránh rò rỉ văn phong của cùng một hợp đồng giữa train và test
(báo cáo rà soát mục 4.3; phương pháp xử lý dữ liệu mục 1.2).
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import GroupKFold


def group_cv_report(texts: np.ndarray, Y: np.ndarray, groups: np.ndarray,
                    build_fn, n_splits: int, label_names: list[str]) -> dict:
    n_groups = len(np.unique(groups))
    if n_groups < n_splits:
        raise ValueError(f"Cần ít nhất {n_splits} hợp đồng (nhóm) để chia {n_splits} fold; hiện có {n_groups}.")

    pred = np.zeros(Y.shape, dtype=int)
    for tr, te in GroupKFold(n_splits=n_splits).split(texts, Y, groups):
        model = build_fn()
        model.fit(texts[tr], Y[tr])
        pred[te] = model.predict(texts[te])

    p, r, f, _ = precision_recall_fscore_support(Y, pred, average=None, zero_division=0)
    return {
        "n_splits": n_splits,
        "macro_f1": float(np.mean(f)),
        "per_label": {
            name: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i])}
            for i, name in enumerate(label_names)
        },
    }
