import pytest

from src.rules.engine import (
    rule_civ01, rule_civ02, rule_lab01, rule_lab02, rule_lab03, rule_lea01,
)

P = {
    "LAB-01": {"citation": "c"},
    "CIV-01": {"max_annual_rate_pct": 20.0, "citation": "c"},
    "CIV-02": {"max_penalty_pct": 8.0, "citation": "c"},
    "LAB-02": {"max_probation_days": {"quan_ly": 180, "cao_dang": 60, "trung_cap": 30, "mac_dinh": 6}, "citation": "c"},
    "LAB-03": {"min_notice_days": {"khong_xac_dinh_thoi_han": 45, "xac_dinh_thoi_han": 30, "duoi_12_thang": 3}, "citation": "c"},
}


@pytest.mark.parametrize("text,expected", [
    ("Chậm trả chịu lãi 1,5%/tháng trên số tiền nợ.", None),          # 18%/năm
    ("Chậm trả chịu lãi 2%/tháng trên số tiền nợ.", "vi_pham"),        # 24%/năm
    ("Lãi chậm trả 0,15% mỗi ngày.", "vi_pham"),                       # ~54,75%/năm
    ("Chịu lãi 1% theo thỏa thuận.", "can_xem_xet"),                   # thiếu đơn vị
])
def test_civ01(text, expected):
    out = rule_civ01(text, {}, P["CIV-01"])
    if expected is None:
        assert out == []
    else:
        assert out and out[0].status == expected


def test_civ02_penalty():
    assert rule_civ02("Bên vi phạm chịu phạt vi phạm 10% giá trị hợp đồng.", {}, P["CIV-02"])[0].status == "vi_pham"
    assert rule_civ02("Bên vi phạm chịu phạt vi phạm 5% giá trị hợp đồng.", {}, P["CIV-02"]) == []


def test_lab01_retention():
    assert rule_lab01("Người sử dụng lao động giữ bản chính bằng cấp.", {}, P["LAB-01"])
    assert rule_lab01("Người lao động tự giữ bản chính bằng cấp.", {}, P["LAB-01"]) == []


def test_lab02_probation_default_limit():
    assert rule_lab02("Thời gian thử việc là 90 ngày.", {}, P["LAB-02"])
    assert rule_lab02("Thời gian thử việc là 5 ngày.", {}, P["LAB-02"]) == []


def test_lab02_role_raises_limit():
    assert rule_lab02("Vị trí quản lý thử việc 120 ngày.", {}, P["LAB-02"]) == []


def test_lab03_notice():
    assert rule_lab03("Người lao động đơn phương chấm dứt hợp đồng xác định thời hạn, báo trước 3 ngày.", {}, P["LAB-03"])
    assert rule_lab03("Đơn phương chấm dứt hợp đồng không xác định thời hạn, báo trước 45 ngày.", {}, P["LAB-03"]) == []


def test_lea01_non_refundable():
    assert rule_lea01("Tiền đặt cọc 5.000.000 đồng không hoàn lại.", {}, {})
    assert rule_lea01("Đặt cọc không hoàn lại nếu bên thuê hủy hợp đồng.", {}, {}) == []
