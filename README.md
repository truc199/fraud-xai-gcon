# Banking Fraud & xAI Pipeline V3 (25 Features & Tiered Inference)

An advanced, production-ready machine learning framework for banking fraud detection and Explainable AI (xAI). Phiên bản V3 này được nâng cấp đáng kể với kiến trúc **Tiered Inference (Định tuyến phân tầng 3 lớp)**, **25 đặc trưng số hóa (features)** (bao gồm Thiết bị, Hạ tầng mạng, Tín dụng), và **PU Learning kết hợp EWC (Elastic Weight Consolidation)** để chống quên thảm họa (Catastrophic Forgetting).

---

## 1. Yêu Cầu Dữ Liệu & Cài Đặt (Setup & Data Requirements)

Các bộ dữ liệu thô có kích thước lớn nên không được đưa vào version control (Git). Bạn cần đặt các tệp dữ liệu nguyên bản vào thư mục `data/` trước khi chạy hệ thống.

### Cấu trúc thư mục `data/` yêu cầu:
```text
gcontest/
└── data/
    ├── 0.Data Guidline.xlsx       # Metadata guidelines sheet
    ├── Data_Customer.csv          # Customer profile demographics
    ├── Data_Transaction.csv       # Financial transaction logs
    ├── Data_Activity.csv          # Digital activity audit trails
    ├── Data_Deposit.csv           # checking/saving balances
    ├── Data_Lending.csv           # Lending and liability accounts
    └── Data_Card.csv              # Credit/debit card profiles
```

---

## 2. Hướng Dẫn Chạy Pipeline (Step-by-Step Execution Guide)

Dự án này tuân thủ chuẩn quản lý gói `uv`. Vui lòng **KHÔNG DÙNG `pip install`** hay `python <file.py>`.

### Bước 1: Cài đặt Dependencies
```bash
uv sync
```

### Bước 2: Làm sạch dữ liệu và Xây dựng Database SQLite
Chạy kịch bản tiền xử lý để dọn dẹp file CSV thô và chuyển vào SQLite (giúp truy vấn tốc độ cao):
```bash
uv run clean_and_build_db.py
```
**Chức năng:**
* Chuẩn hóa ngày tháng, tên cột, chuyển giá trị boolean thành 1/0.
* Đọc CSV dạng streaming để tránh tràn RAM.
* Tạo index trên `CUSTOMER_NUMBER` để tối ưu hóa hiệu năng tính toán cửa sổ trượt.

### Bước 3: Chạy Pipeline Thực Thi Đầu-Cuối (End-to-End Pipeline)
Chạy script chính để kích hoạt luồng 3 Tầng, PU Learning, và Continuous Learning (EWC):
```bash
uv run run_pipeline.py
```
**Chức năng của Pipeline V3:**
* Khởi tạo **Fraud2026DataLoader** và **CustomPreprocessor** để trích xuất 25 features mạnh mẽ.
* **Tier 1 (Rules):** Áp dụng 5 quy tắc định tuyến (SequenceRarity, VelocityBypass, LowRiskChannelBypass, DormancyWakeup, ATOPanic) để BLOCK gian lận очев hoặc BYPASS giao dịch an toàn (lọc ~30% lượng giao dịch).
* **Tier 2 (ML):** Chạy thuật toán Positive-Unlabeled (PU) XGBoost kết hợp Calibration (NNPUCModelAgent) cho tập dữ liệu Vùng xám (Ambiguous).
* **Tier 3 (xAI):** Sử dụng `CustomBRACEExplainer` để tạo giải thích TreeSHAP, ma trận tương tác độc hại (Toxic Interactions) và Counterfactual Recourse (tìm mức giảm số tiền để an toàn).
* **Phase 5 (EWC):** Mô phỏng Continuous Learning chống Distribution Drift bằng Autoencoder và Fisher Information Matrix.

### Bước 4: Chạy Web Dashboard
Kích hoạt giao diện UI Web FastAPI (Glassmorphism Dark Theme):
```bash
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```
Mở trình duyệt tại [http://localhost:8000](http://localhost:8000). Tại đây bạn có thể xem luồng console trực tiếp (SSE), quét lịch sử các lần chạy trong `data/exports` và theo dõi từng thẻ giao dịch bị cảnh báo.

---

## 3. Các Tệp Đầu Ra (Output Files)

Mỗi lần chạy `run_pipeline.py`, các tệp sau sẽ được tự động tạo trong thư mục `data/`:

*   `data/anomaly_alerts_latest.csv`: Danh sách các giao dịch bị đánh dấu gian lận (Anomalies). Các cột xAI quan trọng (`ANOMALY_SCORE`, `EXPLANATION`, `TOP_SHAP_CONTRIBUTORS`, v.v.) được đẩy lên đầu để dễ đọc.
*   `data/anomaly_alerts_latest_metadata.json`: Tệp lưu trữ cấu hình Metadata (lưu chính xác tên class Loader, Preprocessor, Model, Explainer đã chạy).
*   `data/evaluation_report.md`: Báo cáo thống kê tổng quan (phân bố rủi ro, tần suất xuất hiện feature, tương tác độc hại).
*   `data/exports/anomaly_alerts_YYYYMMDD_HHMMSS.csv`: Tệp lưu trữ (archive) kết quả chạy có đánh dấu thời gian.
*   `data/exports/anomaly_alerts_YYYYMMDD_HHMMSS_metadata.json`: Tệp metadata archive tương ứng.

---

## 4. Chính Sách Mở Rộng Component (Không Xóa Code Cũ)

Kiến trúc tuân thủ Python Protocols trong `src/pipeline/protocols.py`. Để thử nghiệm cơ chế mới:

1.  **KHÔNG XÓA** hoặc ghi đè code class cũ (ví dụ không xóa `advanced_preprocessor.py`).
2.  **TẠO FILE MỚI** (ví dụ `custom_preprocessor.py`) và định nghĩa class mới thực thi Protocol tương ứng.
3.  **CẮM (PLUG)** class mới vào `run_pipeline.py` ở hàm `main()`:
    ```python
    # Thay vì dùng bản cũ:
    # preprocessor = AdvancedPreprocessor()
    
    # Hãy cắm bản V3 mới vào:
    preprocessor = CustomPreprocessor()
    ```
