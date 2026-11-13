from pathlib import Path

from src.data.segment import segment_clauses
from src.llm.grounding import filter_grounded, is_grounded
from src.pipeline import analyze_contract
from src.utils.config import load_config, load_rules, project_root


def test_segment_keeps_article_context():
    text = "Điều 2. Thanh toán\n1. Chậm trả chịu lãi 2%/tháng trên số tiền nợ.\n2. Phạt vi phạm 10% giá trị.\n"
    cl = segment_clauses(text, min_chars=5)
    assert [c.key for c in cl] == ["Điều 2. Thanh toán|1", "Điều 2. Thanh toán|2"]


def test_segment_joins_continuation_lines():
    text = "Điều 1. X\n1. Đoạn đầu của khoản\ntiếp tục ở dòng sau.\n"
    cl = segment_clauses(text, min_chars=5)
    assert cl[0].text.endswith("tiếp tục ở dòng sau.")


def test_grounding_rejects_fabricated_quote():
    src = "Tiền đặt cọc không hoàn lại trong mọi trường hợp."
    assert is_grounded("tiền đặt cọc  không hoàn lại", src)
    assert not is_grounded("bên thuê được hoàn cọc đầy đủ", src)
    kept, dropped = filter_grounded([{"trich_dan": "không hoàn lại"}, {"trich_dan": "bịa đặt"}], src)
    assert len(kept) == 1 and dropped == 1


def test_pipeline_on_synthetic_contract():
    cfg = load_config()
    rules = load_rules(cfg)
    raw = (project_root() / "data/raw/sample_contract_synthetic.txt").read_text(encoding="utf-8")
    res = analyze_contract(raw, cfg, rules)
    rule_ids = {c["rule_id"] for c in res["canh_bao"]}
    assert {"LAB-01", "LAB-02", "LAB-03", "CIV-01", "CIV-02", "LEA-01"} <= rule_ids
    assert all(c["trich_dan_hop_le"] for c in res["canh_bao"])
    assert res["tong_hop"]["muc_do"] == "cao"
    assert "mien_trach_nhiem" in res
