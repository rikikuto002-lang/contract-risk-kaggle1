"""Pipeline phân tích một hợp đồng: phân đoạn -> rule -> (tùy chọn) ML -> chấm điểm -> báo cáo JSON.

Chạy:
    python -m src.pipeline --input data/raw/sample_contract_synthetic.txt
    python -m src.pipeline --input <file.txt> --model models/baseline_tfidf_lr.joblib
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import joblib

from src.data.normalize import normalize_text
from src.data.segment import Clause, segment_clauses
from src.llm.grounding import is_grounded
from src.rules.engine import run_rules
from src.scoring import score_findings
from src.utils.config import load_config, load_rules, project_root, set_seed


def classify_clauses(clauses: list[Clause], bundle: dict, threshold: float) -> list[dict]:
    if not clauses:
        return []
    proba = bundle["model"].predict_proba([c.text for c in clauses])
    labels = bundle["labels"]
    return [
        {"clause_key": c.key,
         "nhan": {lab: round(float(p), 3) for lab, p in zip(labels, row) if p >= threshold}}
        for c, row in zip(clauses, proba)
    ]


def analyze_contract(raw_text: str, cfg: dict, rules_cfg: dict,
                     model_bundle: dict | None = None, context: dict | None = None) -> dict:
    text = normalize_text(raw_text)
    clauses = segment_clauses(text, min_chars=cfg["data"]["min_clause_chars"])
    findings = run_rules(clauses, rules_cfg, context)

    canh_bao = []
    for f in findings:
        d = f.to_dict()
        d["trich_dan_hop_le"] = is_grounded(f.evidence, text)  # kiểm tra chống ảo giác
        canh_bao.append(d)

    result = {
        "so_dieu_khoan": len(clauses),
        "canh_bao": canh_bao,
        "tong_hop": score_findings(findings, cfg["scoring"]["weights"],
                                   cfg["scoring"]["confidence"], cfg["scoring"]["thresholds"]),
        "mien_trach_nhiem": cfg["disclaimer"],
    }
    if model_bundle is not None:
        result["ml"] = classify_clauses(clauses, model_bundle, cfg["model"]["decision_threshold"])
    return result


def main(argv: list[str] | None = None) -> dict:
    p = argparse.ArgumentParser(description="Rà soát rủi ro điều khoản hợp đồng")
    p.add_argument("--input", required=True, help="File văn bản hợp đồng (.txt)")
    p.add_argument("--output", default=None, help="Đường dẫn báo cáo JSON")
    p.add_argument("--model", default=None, help="File .joblib của mô hình baseline (tùy chọn)")
    args = p.parse_args(argv)

    cfg = load_config()
    set_seed(cfg["seed"])
    rules_cfg = load_rules(cfg)

    bundle = joblib.load(args.model) if args.model else None
    raw = Path(args.input).read_text(encoding="utf-8")
    result = analyze_contract(raw, cfg, rules_cfg, bundle)
    result["tep_dau_vao"] = Path(args.input).name
    result["thoi_gian"] = datetime.now().isoformat(timespec="seconds")

    out = Path(args.output) if args.output else (
        project_root() / cfg["paths"]["outputs"] / "reports" / f"report_{datetime.now():%Y%m%d_%H%M%S}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Ghi báo cáo: {out}")
    return result


if __name__ == "__main__":
    main()
