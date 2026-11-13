# Dữ liệu thô

- `sample_contract_synthetic.txt`: hợp đồng **tổng hợp** dùng để kiểm thử pipeline. Không phải hợp đồng thật.
- Dữ liệu hợp đồng thật **không** được đưa vào repo hay dataset Kaggle công khai. Chỉ đặt dữ liệu đã ẩn danh và có sự đồng ý sử dụng (Nghị định 13/2023/NĐ-CP).

## Định dạng nhãn huấn luyện (`data/processed/clauses_labeled.csv`)

| Cột | Ý nghĩa |
|---|---|
| `contract_id` | Mã hợp đồng ẩn danh, dùng làm nhóm khi chia train/test |
| `contract_type` | `lao_dong`, `thue_nha` hoặc `thuong_mai` |
| `article`, `clause_id` | Vị trí điều khoản |
| `text` | Nội dung khoản (đã ẩn danh) |
| `lao_dong`, `thue_nha_rui_ro`, `thanh_toan_phat`, `trach_nhiem_boi_thuong`, `du_lieu_bao_mat`, `trung_tinh` | Nhãn đa nhãn, 0/1 |

Quy trình gán nhãn: hai người độc lập, chuyên gia thứ ba giải quyết bất đồng, đo Cohen's kappa; kappa dưới ~0,6 với một nhãn thì viết lại định nghĩa nhãn đó.
