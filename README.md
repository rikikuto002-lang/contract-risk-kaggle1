# Rà soát rủi ro điều khoản hợp đồng (Contract Review & Risk Flagging)

Phân loại điều khoản kết hợp **Rule-based engine** và **Zero/Few-shot LLM**, có kiểm tra trích dẫn chống ảo giác.
Phạm vi: hợp đồng lao động, hợp đồng thuê nhà và hợp đồng thương mại đơn giản bằng tiếng Việt.

> Hệ thống chỉ gắn cờ và giải thích rủi ro để tham khảo. Không thay thế tư vấn của luật sư.
> Các ngưỡng pháp lý trong `config/rules.yaml` là giá trị minh họa; phải đối chiếu hiệu lực trước khi vận hành.

## Cấu trúc thư mục

```
├── config/config.yaml          # seed, đường dẫn, trọng số chấm điểm, ngưỡng
├── config/rules.yaml           # tham số pháp lý của rule (có căn cứ và cảnh báo hiệu lực)
├── data/raw/                   # dữ liệu thô (chỉ có hợp đồng tổng hợp)
├── src/
│   ├── data/                   # chuẩn hóa Unicode, phân đoạn Điều/Khoản
│   ├── features/               # TF-IDF
│   ├── models/                 # baseline TF-IDF + Logistic Regression (One-vs-Rest)
│   ├── rules/engine.py         # CIV-01, CIV-02, LAB-01/02/03, LEA-01
│   ├── llm/                    # dựng prompt few-shot, kiểm tra trích dẫn
│   ├── evaluation/metrics.py   # GroupKFold, macro-F1, F1 theo nhãn
│   ├── scoring.py              # điểm rủi ro = Σ w_k × c_k
│   ├── pipeline.py             # phân tích một hợp đồng -> báo cáo JSON
│   └── train.py                # huấn luyện và đánh giá baseline
├── tests/                      # kiểm thử rule, phân đoạn, grounding, pipeline
├── docs/diagrams/              # sơ đồ Mermaid: kiến trúc, luồng, huấn luyện, MLOps, triển khai
├── kaggle/                     # metadata và điểm vào cho Kaggle
├── models/  outputs/           # trọng số và kết quả (không đưa vào git)
└── requirements.txt
```

## Cài đặt và chạy

```bash
pip install -r requirements.txt
pytest                                    # kiểm thử
python -m src.pipeline --input data/raw/sample_contract_synthetic.txt
```

Báo cáo JSON gồm: số khoản, danh sách cảnh báo (`vi_pham` hoặc `can_xem_xet`), trích dẫn nguyên văn kèm cờ `trich_dan_hop_le`, điểm và mức rủi ro, và phần miễn trừ trách nhiệm.

Huấn luyện baseline khi đã có dữ liệu nhãn (xem `data/raw/README.md`):

```bash
python -m src.train --data data/processed/clauses_labeled.csv
python -m src.pipeline --input <hop_dong.txt> --model models/baseline_tfidf_lr.joblib
```

## Nguyên tắc kỹ thuật

- **Chia dữ liệu theo hợp đồng** (`GroupKFold` theo `contract_id`), không chia theo điều khoản, để tránh rò rỉ văn phong.
- **Rule không kết luận khi không chắc.** Lãi có % nhưng thiếu đơn vị thời gian chỉ được đánh dấu `can_xem_xet`.
- **Mọi trích dẫn phải tồn tại nguyên văn** trong hợp đồng gốc (so khớp sau khi chuẩn hóa). Trích dẫn không khớp bị loại.
- **Thứ tự ưu tiên khi xung đột**: rule định lượng > classifier tin cậy cao > LLM (LLM chỉ xác nhận hoặc giải thích).
- **Không đặt khóa API trong mã.** Dùng Kaggle Secrets.

## Đưa lên Kaggle

1. Đặt `TODO_USERNAME` trong `kaggle/dataset-metadata.json` và `kaggle/kernel-metadata.json` bằng tên tài khoản của bạn.
2. Tạo `kaggle.json` từ Account > API (không commit file này).
3. Đẩy mã nguồn thành dataset:
   ```bash
   kaggle datasets create -p .        # lần đầu; các lần sau dùng: kaggle datasets version -p . -m "mô tả"
   ```
   Nên loại trừ `data/raw` và `models/` nếu chứa dữ liệu nhạy cảm.
4. Đẩy Notebook:
   ```bash
   kaggle kernels push -p kaggle/
   ```
5. Trong Notebook, `kernel_entry.py` tự tìm mã nguồn trong `/kaggle/input` và ghi báo cáo vào `/kaggle/working/report.json`.
6. Chạy lại từ đầu (Restart & Run All) trước khi xuất bản.

Kaggle phù hợp cho nghiên cứu, huấn luyện và chia sẻ kết quả. Không dùng Kaggle để phục vụ suy luận cho người dùng thật (xem `docs/diagrams/deployment.mmd`).

## Sơ đồ

| File | Nội dung |
|---|---|
| `docs/diagrams/architecture.mmd` | Kiến trúc tổng thể, từ tải tệp đến báo cáo |
| `docs/diagrams/pipeline_flow.mmd` | Thứ tự gọi hàm trong pipeline |
| `docs/diagrams/training_workflow.mmd` | Huấn luyện và đánh giá theo nhóm hợp đồng |
| `docs/diagrams/mlops_lifecycle.mmd` | Vòng đời MLOps, điều kiện huấn luyện lại |
| `docs/diagrams/deployment.mmd` | Tách phần Kaggle và phần production |

## Việc còn mở

- Xây dựng bộ dữ liệu nhãn tiếng Việt (150–300 hợp đồng ẩn danh), gán nhãn theo hướng dẫn bằng văn bản.
- Tách từ tiếng Việt (VnCoreNLP) nếu chuyển sang PhoBERT; hiện baseline dùng TF-IDF trên văn bản đã chuẩn hóa.
- Module OCR (VietOCR) và lớp gọi LLM chưa được triển khai; `src/llm/prompt.py` và `grounding.py` đã sẵn sàng.
- Notebook EDA và huấn luyện (`notebooks/`) sẽ tạo sau khi có dữ liệu thật.
