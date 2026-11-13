"""Điểm vào cho Kaggle Notebook (kernel kiểu script).

Tìm thư mục dự án trong /kaggle/input (dataset mã nguồn), thêm vào sys.path,
rồi chạy pipeline trên hợp đồng đầu vào. Kết quả ghi vào /kaggle/working.
"""
import glob
import os
import sys

CODE_MARKER = "src/pipeline.py"
candidates = glob.glob(f"/kaggle/input/*/{CODE_MARKER}") + glob.glob(f"/kaggle/input/*/*/{CODE_MARKER}")
if not candidates:
    raise FileNotFoundError("Không tìm thấy mã nguồn trong /kaggle/input. Hãy gắn dataset mã nguồn vào Notebook.")

project_root = os.path.dirname(os.path.dirname(candidates[0]))
os.environ["RISK_PROJECT_ROOT"] = project_root
sys.path.insert(0, project_root)

from src.pipeline import main  # noqa: E402

INPUT_FILE = os.environ.get("CONTRACT_INPUT", os.path.join(project_root, "data/raw/sample_contract_synthetic.txt"))
main(["--input", INPUT_FILE, "--output", "/kaggle/working/report.json"])
