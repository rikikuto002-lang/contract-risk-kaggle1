"""Đọc cấu hình, xác định thư mục gốc và cố định seed."""
from __future__ import annotations

import os
import random
from pathlib import Path

import numpy as np
import yaml


def project_root() -> Path:
    """Thư mục gốc dự án. Có thể ghi đè bằng biến môi trường RISK_PROJECT_ROOT (dùng trên Kaggle)."""
    env = os.environ.get("RISK_PROJECT_ROOT")
    return Path(env) if env else Path(__file__).resolve().parents[2]


def load_config(name: str = "config/config.yaml") -> dict:
    with open(project_root() / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_rules(cfg: dict) -> dict:
    with open(project_root() / cfg["rules_file"], encoding="utf-8") as f:
        return yaml.safe_load(f)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
