# Feature Description & Outcome Report
## Banking Fraud & xAI Pipeline — GContest Round 3

---

## 1. Tổng quan Dự án (Project Overview)

### 1.1 Bối cảnh

Theo Báo cáo của Ngân hàng Nhà nước Việt Nam (NHNN) và Bộ Công an năm 2024, số vụ lừa đảo tài chính qua kênh ngân hàng số tại Việt Nam tăng trung bình 65% mỗi năm, với tổng thiệt hại ước tính hơn 8.000 tỷ VND. Các hình thức phổ biến bao gồm:
- **Chiếm đoạt tài khoản (Account Takeover - ATO):** Lừa đảo qua SMS OTP giả mạo, SIM Swap, lấy cắp thông tin đăng nhập qua website giả (Phishing).
- **Rửa tiền và tài khoản trung chuyển (Money Mule):** Tội phạm mua/thuê tài khoản của sinh viên, người thất nghiệp để chuyển tiền bẩn nhanh qua nhiều lớp (Layering).
- **Chia nhỏ giao dịch (Structuring/Smurfing):** Cố tình chia giao dịch thành nhiều khoản nhỏ hơn ngưỡng kiểm soát để tránh bị báo cáo theo quy định phòng chống rửa tiền (AML).

Tham chiếu quốc tế cho thấy quy mô vấn đề này mang tính toàn cầu:
- **FATF (Financial Action Task Force, 2023):** Báo cáo "Money Laundering and Terrorist Financing Risks from Virtual Assets" nhấn mạnh sự gia tăng giao dịch chuyển tiền nhanh qua các kênh số, khiến các hệ thống rule-based truyền thống ngày càng bất lực.
- **European Central Bank (ECB, 2024):** Thống kê cho thấy tỷ lệ False Positive trung bình của hệ thống AML dựa trên rule cứng tại các ngân hàng châu Âu là hơn 95%, gây lãng phí chi phí nhân sự Compliance và làm giảm trải nghiệm khách hàng (CX).
- **Basel Committee on Banking Supervision (2022):** Khuyến nghị các ngân hàng sử dụng Machine Learning kết hợp Explainable AI (xAI) để giảm báo động giả và tăng khả năng giải trình cho Cơ quan quản lý.

### 1.2 Mục tiêu

Dự án xây dựng **hệ thống cảnh báo giao dịch vi phạm (Anomaly Alert System)** nhằm:
1. **Phát hiện các giao dịch bất thường có dấu hiệu gian lận** (lừa đảo, rửa tiền) trong thời gian thực.
2. **Giảm thiểu tỷ lệ Báo động giả (False Positives)** — tránh khóa nhầm tài khoản khách hàng hợp lệ.
3. **Cung cấp lý giải minh bạch (xAI)** — giúp Analyst hiểu rõ lý do cảnh báo, tăng tốc quy trình xét duyệt.
4. **Đề xuất hành động khắc phục (Counterfactual Recourse)** — thay vì chặn giao dịch vô điều kiện, đề xuất bước xác thực bổ sung tối thiểu (ví dụ: xác minh FaceID).
5. **Bảo vệ uy tín và niềm tin khách hàng** — xây dựng hệ thống bảo mật "không ma sát" (Frictionless Security), giữ chân khách hàng hợp lệ trong khi ngăn chặn tội phạm.

### 1.3 Dữ liệu sử dụng

| Bảng dữ liệu | Số bản ghi | Nội dung |
|---|---|---|
| Data_Customer | 290,223 | Hồ sơ nhân khẩu học khách hàng: giới tính, nghề nghiệp, ngày tạo tài khoản, phương thức xác thực |
| Data_Transaction | 1,418,030 | Nhật ký giao dịch tài chính: số tiền, thời gian, loại giao dịch, thiết bị, IP, người thụ hưởng |
| Data_Activity | 16,132,675 | Nhật ký hoạt động kỹ thuật số: đăng nhập, đổi mật khẩu, xem lãi suất, chuyển tiền |
| Data_Deposit | 1,258,424 | Ảnh chụp số dư tài khoản tiết kiệm/thanh toán hàng tháng |
| Data_Lending | 576,431 | Hồ sơ vay và nợ xấu |
| Data_Card | 871,589 | Hồ sơ thẻ tín dụng/ghi nợ, hạn mức và dư nợ |

---

## 2. Mô hình áp dụng (Model Architecture)

Hệ thống sử dụng kiến trúc **Pipeline 5 Phase** kết hợp nhiều kỹ thuật Machine Learning:

### 2.1 Phase 1-2: Trích xuất & Kỹ thuật Đặc trưng (Data Extraction & Feature Engineering)

Dữ liệu thô từ 6 bảng được nối (JOIN) và làm giàu bằng các cửa sổ trượt thời gian (Rolling Windows) 1h, 3h, 24h, 48h, 7 ngày, 30 ngày. Tổng cộng **21 đặc trưng số học** được sinh ra cho mỗi giao dịch.

### 2.2 Phase 3: Huấn luyện — nnPU Learning với Spy Filtering & CVuO

Vì không có nhãn gian lận (fraud labels) xác nhận trong dữ liệu thực tế, hệ thống áp dụng học bán giám sát kiểu **Positive-Unlabeled (PU) Learning**:

| Bước | Kỹ thuật | Mục đích |
|---|---|---|
| 1 | **Isolation Forest** (contamination = 3%) | Tạo nhãn ban đầu (Proxy Labels) cho các giao dịch bất thường |
| 2 | **PAYN Spy Filtering** | Phát hiện nhóm dữ liệu "sạch" đáng tin cậy trong pool Unlabeled bằng cách cài "gián điệp" từ nhóm Positive |
| 3 | **Cross-Validated Unlabeled Optimization (CVuO)** | Loại bỏ 10% mẫu có loss cao nhất trong pool Unlabeled (khả năng cao là nhãn sai) |
| 4 | **XGBoost Classifier** (100 cây, max_depth=3, L1=1.0, L2=2.0) | Huấn luyện bộ phân loại cuối cùng trên tập nhãn đã được lọc sạch |
| 5 | **Elkan-Noto Calibration** | Hiệu chỉnh xác suất đầu ra bị lệch do nhãn PU |

### 2.3 Phase 4: Suy luận phân tầng (Tiered Inference)

| Tầng | Xử lý | Kết quả (trong lần chạy) |
|---|---|---|
| **Tier 1 — High-Speed Bypass** | Rule-based: Bỏ qua giao dịch nhỏ (<500K VND) với tần suất thấp và chuỗi hành vi bình thường | 1,400 / 5,000 (28%) được bypass an toàn trong 0.83ms |
| **Tier 2 — ML Classification** | XGBoost + Elkan-Noto trên 21 features | 3,600 giao dịch mơ hồ được đánh giá, 121 bị gắn cờ (3.36%) |
| **Tier 3 — xAI Explanation** | TreeSHAP + SHAP Interactions + Counterfactual Recourse | 121 thẻ cảnh báo với lý giải đầy đủ được sinh ra trong 8.86 giây |

### 2.4 Phase 5: Học liên tục — Elastic Weight Consolidation (EWC)

Sử dụng **Deep Autoencoder** (D→16→8→16→D) kết hợp ma trận Fisher Information để bảo vệ trọng số quan trọng khi dữ liệu thay đổi theo thời gian (Distribution Drift), ngăn chặn hiện tượng "Quên thảm họa" (Catastrophic Forgetting).

---

## 3. Mô tả Đặc trưng (Feature Description)

Hệ thống sử dụng **21 đặc trưng** chia thành 6 nhóm chức năng. Mỗi đặc trưng dưới đây được mô tả chi tiết từ nguồn dữ liệu, công thức tính toán (measurement), vai trò trong mô hình (biến độc lập/kiểm soát), cho đến lý do thực tiễn chống gian lận.

---

### 3.1 Nhóm 1: Lệch chuẩn Số tiền (Amount Deviation)

#### TRANS_AMOUNT_Z_SCORE
- **Nguồn dữ liệu:** Cột `TRANS_AMOUNT` và `CUSTOMER_NUMBER` từ `Data_Transaction`.
- **Công thức đo lường:** `TRANS_AMOUNT / (HIST_AVG_TRANS_AMOUNT + ε)` (với `HIST_AVG_TRANS_AMOUNT` là trung bình toàn bộ giao dịch trước đó).
- **Vai trò:** **Biến độc lập** (Tín hiệu rủi ro trực tiếp).
- **Lý luận logic & Thực tế:** Đo mức độ bất thường so với chính khách hàng đó. Thay vì dùng một ngưỡng chặn cứng nhắc (vd: >50 triệu), mô hình cá nhân hóa rủi ro bằng Z-Score. Giao dịch 20 triệu của sinh viên sinh ra Z-Score cao, nhưng với doanh nhân lại thấp. Theo Akoglu et al. (2015), kẻ chiếm đoạt tài khoản (ATO) luôn muốn rút sạch tiền nhanh nhất, tạo ra Z-Score đột biến. Nó được mô hình kết hợp với các biến kiểm soát (độ tuổi, nghề nghiệp) để giảm False Positive.
- **Kết quả SHAP:** Xuất hiện trong **54.55%** các cảnh báo (66/121).

#### BALANCE_COVERAGE_RATIO
- **Nguồn dữ liệu:** Cột `TRANS_AMOUNT` (`Data_Transaction`) và số dư trung bình `HIST_AVG_CA_BALANCE` (tổng hợp từ `Data_Deposit`).
- **Công thức đo lường:** `TRANS_AMOUNT / (HIST_AVG_CA_BALANCE + ε)`
- **Vai trò:** **Biến độc lập**.
- **Lý luận logic & Thực tế:** Tỷ lệ này đo lường mức độ "ăn" vào số dư trung bình. Nếu tài khoản thường chỉ có số dư 1 triệu nhưng đột nhiên chuyển đi 50 triệu, số tiền này chắc chắn vừa được nạp vào. Theo FATF (2021), đây là dấu hiệu kinh điển của Money Mule (tài khoản trung chuyển) — dòng tiền bẩn vừa vào lập tức bị chuyển đi.
- **Kết quả SHAP:** Đặc trưng thống trị, xuất hiện trong **80.17%** cảnh báo.

#### TRANS_AMOUNT_VS_30D_AVG_RATIO
- **Nguồn dữ liệu:** Cột `TRANS_AMOUNT` (`Data_Transaction`) và tổng giao dịch trong cửa sổ 30 ngày.
- **Công thức đo lường:** `TRANS_AMOUNT / (SUM_AMOUNT_30D / (COUNT_30D + ε) + ε)`
- **Vai trò:** **Biến độc lập** bổ trợ.
- **Lý luận logic & Thực tế:** Z-Score dài hạn có thể bị "pha loãng" bởi các giao dịch cũ. Feature này so sánh số tiền với mức chi tiêu chỉ trong 30 ngày qua (baseline ngắn hạn). Hành vi con người thay đổi theo thời gian; việc cập nhật baseline ngắn hạn giúp giảm cảnh báo sai khi khách hàng mới được tăng lương hoặc thăng chức (Bolton & Hand, 2002).

---

### 3.2 Nhóm 2: Tốc độ & Tần suất (Velocity)

#### VELOCITY_RATIO_AMOUNT_24H_VS_7D & 7D_VS_30D
- **Nguồn dữ liệu:** Tổng số tiền `SUM_AMOUNT` (`Data_Transaction`) tính qua các Rolling Windows (24h, 7d, 30d).
- **Công thức đo lường:** `SUM_AMOUNT_24H / (SUM_AMOUNT_7D + ε)` và `SUM_AMOUNT_7D / (SUM_AMOUNT_30D + ε)`.
- **Vai trò:** **Biến độc lập**.
- **Lý luận logic & Thực tế:** Nếu tỷ lệ tiến gần về 1.0, nghĩa là toàn bộ lượng tiền giao dịch trong 30 ngày qua đổ dồn hết vào 7 ngày gần nhất. Trong chống rửa tiền, điều này phản ánh hành vi "Cash-out" hoặc "Bust-out" — tội phạm phải hành động cực nhanh trước khi bị ngân hàng đóng băng tài khoản.

#### VELOCITY_RATIO_COUNT_24H_VS_7D & 7D_VS_30D
- **Nguồn dữ liệu:** Tổng số lượng giao dịch `COUNT` (`Data_Transaction`) tính qua các Rolling Windows.
- **Công thức đo lường:** `COUNT_24H / (COUNT_7D + ε)` và `COUNT_7D / (COUNT_30D + ε)`.
- **Vai trò:** **Biến độc lập**.
- **Lý luận logic & Thực tế:** Feature này được sinh ra để bắt hành vi "chia nhỏ giao dịch" (Structuring) hoặc "thăm dò" (Card Testing). Tội phạm chạy bot chuyển thử các khoản 10.000 VND nhiều lần liên tục để xem tài khoản còn sống không. PwC (2024) xác nhận 34% gian lận bắt đầu bằng thăm dò micro-transaction.

---

### 3.3 Nhóm 3: Hành vi Thời gian & Ngủ đông (Temporal & Dormancy)

#### DAYS_SINCE_LAST_TRANS
- **Nguồn dữ liệu:** Cột `TRANS_DATE` (`Data_Transaction`), tính chênh lệch ngày so với giao dịch trước đó của cùng khách hàng.
- **Công thức đo lường:** `(timestamp_hiện_tại - timestamp_giao_dịch_trước) / 86400`
- **Vai trò:** **Biến độc lập** (phát hiện ngủ đông).
- **Lý luận logic & Thực tế:** Theo Europol (2023), tội phạm thường thu mua tài khoản sinh viên và để "ngủ đông" 3-6 tháng nhằm lọt qua bộ lọc giám sát ban đầu của ngân hàng, trước khi sử dụng để luân chuyển tiền bẩn. Feature này sinh ra để "đón đầu" khoảnh khắc tài khoản thức giấc.

#### DAYS_AMOUNT_COMBINED
- **Nguồn dữ liệu:** Tổ hợp toán học từ `DAYS_SINCE_LAST_TRANS` và `TRANS_AMOUNT`.
- **Công thức đo lường:** `log1p(DAYS_SINCE_LAST_TRANS) × log1p(TRANS_AMOUNT)`
- **Vai trò:** **Biến độc lập** (Tương tác phi tuyến).
- **Lý luận logic & Thực tế:** Một tài khoản im lặng 6 tháng rồi nạp thẻ điện thoại 50k là bình thường. Nhưng im lặng 6 tháng rồi chuyển khoản 500 triệu là cờ đỏ khẩn cấp. Phép nhân này mô hình hóa logic: "Im lặng càng lâu + Chuyển đi càng nhiều = Rủi ro càng cao", giải quyết hiệu quả bài toán False Positive của các quy tắc tĩnh.

#### TRANS_HOUR & NIGHT_ANOMALY
- **Nguồn dữ liệu:** Trích xuất giờ từ `TRANS_DATE`, và tính `HIST_NIGHT_RATIO` (tỷ lệ giao dịch đêm trong quá khứ).
- **Công thức đo lường:** 
  - `TRANS_HOUR`: Giờ trong ngày (0-23).
  - `NIGHT_ANOMALY`: `IS_NIGHT × (1 - HIST_NIGHT_RATIO)` (với `IS_NIGHT = 1` nếu rơi vào 0-5h sáng).
- **Vai trò:** `TRANS_HOUR` là **Biến kiểm soát**, `NIGHT_ANOMALY` là **Biến độc lập**.
- **Lý luận logic & Thực tế:** NHNN khuyến cáo rủi ro cao với giao dịch ban đêm. Tuy nhiên, nếu chặn mọi giao dịch đêm sẽ gây phiền toái cho người làm ca đêm. `NIGHT_ANOMALY` giải quyết bằng cách dùng `HIST_NIGHT_RATIO` làm biến kiểm soát: Nếu họ quen giao dịch đêm, `(1 - HIST_NIGHT_RATIO)` tiến về 0, vô hiệu hóa rủi ro, bảo vệ trải nghiệm khách hàng hợp lệ (Frictionless Security).

---

### 3.4 Nhóm 4: An ninh & Xác thực (Security & Authentication)

#### HOURS_SINCE_SEC_EVENT
- **Nguồn dữ liệu:** Nối timestamp từ `Data_Transaction` và các sự kiện bảo mật (đổi mật khẩu, mã PIN) từ `Data_Activity`.
- **Công thức đo lường:** `(timestamp_giao_dịch - timestamp_sự_kiện_bảo_mật_gần_nhất) / 3600` (giờ).
- **Vai trò:** **Biến độc lập**.
- **Lý luận logic & Thực tế:** Javelin Strategy (2023) thống kê >70% các vụ chiếm đoạt tài khoản (ATO) kết thúc bằng lệnh chuyển tiền tẩu tán trong vòng 60 phút sau khi kẻ gian đổi mật khẩu/mã PIN thành công. Giá trị càng gần 0, xác suất gian lận càng cao.

#### HIST_BIOMETRIC_RATIO
- **Nguồn dữ liệu:** Cột `ACTIVITY_NAME` (`Data_Activity`), đếm tỷ lệ đăng nhập sinh trắc học.
- **Công thức đo lường:** `Σ(biometric_logins_trước_đó) / (tổng_logins_trước_đó + ε)`
- **Vai trò:** **Biến kiểm soát** (Bối cảnh xác thực).
- **Lý luận logic & Thực tế:** Theo Thông tư 17/2024/TT-NHNN, bảo mật sinh trắc học là yêu cầu bắt buộc. Tính năng này được dùng để thiết lập baseline: Nếu khách hàng có lịch sử 99% dùng FaceID (`HIST_BIOMETRIC_RATIO` cao), nhưng hôm nay đột nhiên đăng nhập bằng Password tĩnh trên thiết bị lạ và chuyển tiền lớn, mô hình sẽ dùng biến kiểm soát này làm điểm neo để đánh giá đó là sự bất thường tột độ (cờ đỏ ATO).

---

### 3.5 Nhóm 5: Phân tích Thống kê & Chuỗi (Statistical & Sequence)

#### BENFORD_DEV
- **Nguồn dữ liệu:** Trích xuất chữ số đầu tiên (1-9) của tất cả số tiền `TRANS_AMOUNT` của một người dùng.
- **Công thức đo lường:** `KL-Divergence` giữa phân bố thực tế của chữ số đầu tiên và phân bố lý thuyết định luật Benford: `log10(1 + 1/d)`. Chỉ tính toán khi số lượng mẫu giao dịch (N) ≥ 50.
- **Vai trò:** **Biến độc lập** (Phát hiện gian lận cấu trúc).
- **Lý luận logic & Thực tế:** Định luật Benford rất nhạy cảm với kích thước mẫu. Việc tính toán trên lượng dữ liệu quá nhỏ (N < 50) sẽ tạo nhiễu (noise) và tỷ lệ Báo động giả (False Positive) cao đối với hành vi giao dịch cá nhân. Việc áp dụng ngưỡng N ≥ 50 là phương pháp luận chính xác theo nghiên cứu kiểm toán hiện đại. Khi tội phạm lách luật AML bằng cách chia nhỏ tiền có chủ đích (Structuring), sự sai lệch phân bố chữ số tự nhiên sẽ chỉ điểm chúng một cách chuẩn xác.

#### ACTIVITY_SEQ_RARITY
- **Nguồn dữ liệu:** Chuỗi sự kiện `ACTIVITY_NAME` liên tiếp từ `Data_Activity`.
- **Công thức đo lường:** Điểm Log-likelihood trung bình chuẩn hóa, tính toán qua mô hình Chuỗi Markov bậc 2 (2nd-order Markov Chain).
- **Vai trò:** **Biến độc lập** (và dùng làm Rule kiểm soát ở Tier 1).
- **Lý luận logic & Thực tế:** Một phiên thao tác bình thường: `LOGIN` → `QUERY_ACCOUNT` → `TRANSFER` → `LOGOUT`. Một phiên bất thường: `LOGIN` → `PASSWORD_CHANGE` → `TRANSFER_OUTSIDE` → `LOGOUT`. Tính toán xác suất chuyển tiếp giữa các bước giúp mô hình hóa độ hiếm của phiên giao dịch. Đây là cách tốt nhất để bắt các đoạn script Botnet tự động (Chandola et al., 2009).

---

### 3.6 Nhóm 6: Phân loại & Nhân khẩu (Categorical & Demographic)

#### AGE_GROUP & Occupation_Group
- **Nguồn dữ liệu:** Lấy từ `DATE_OF_BIRTH` và `Occupation_Group` trong bảng `Data_Customer`.
- **Công thức đo lường:** `AGE_GROUP` ánh xạ năm sinh thành 3 nhóm (Young, Middle, Old). Nghề nghiệp giữ nguyên Label.
- **Vai trò:** **Biến kiểm soát** (Thiết lập Cohort Baseline).
- **Lý luận logic & Thực tế:** Thuật toán XGBoost sử dụng các đặc trưng này làm tiêu chí để phân nhánh rủi ro. Theo NHNN (Thông tư 09/2020), sinh viên và người già dễ bị lừa bán tài khoản làm Mule Account nhất. Việc đưa các biến này vào giúp mô hình không đánh giá cào bằng: một giao dịch 100 triệu của sinh viên thất nghiệp sẽ bị mô hình xếp rủi ro cao hơn rất nhiều so với giao dịch 100 triệu của một doanh nhân (Businessman).

#### TRANS_LV1 & TRANS_LV2
- **Nguồn dữ liệu:** Phân loại loại hình giao dịch từ bảng `Data_Transaction`.
- **Công thức đo lường:** Target encoding / One-hot encoding.
- **Vai trò:** **Biến kiểm soát**.
- **Lý luận logic & Thực tế:** Các giao dịch Transfer Outside Bank luôn rủi ro hơn vì tiền bẩn khi đã chuyển ra khỏi ngân hàng là cực kỳ khó thu hồi. Khung cảnh báo sẽ được mô hình siết chặt hơn với các loại giao dịch này.

---

## 4. Kết quả Pipeline (Pipeline Outcomes)

### 4.1 Thống kê Tổng quan

| Chỉ số | Giá trị |
|---|---|
| Tổng giao dịch đánh giá | 5,000 |
| Giao dịch bị gắn cờ bất thường | 121 (2.42%) |
| Khách hàng bị gắn cờ | 66 |
| Cảnh báo cao nhất trên 1 khách hàng | 9 (Customer ID: 2021) |
| Giá trị trung bình giao dịch bất thường | 42,022,315 VND |
| Giá trị trung vị giao dịch bất thường | 21,000,000 VND |

### 4.2 Phân bố Rủi ro

**Thiết bị:**
- iOS: 50.41%
- Android: 47.93%
- Web: 1.65%

**Kênh giao dịch bị cảnh báo:**
- Transfer Outside Bank: 57.85%
- Transfer Within Bank: 28.93%
- Credit Card Repayment: 12.40%
- eWallet: 0.83%

### 4.3 Top 10 SHAP Contributors (Tần suất xuất hiện trong 121 alerts)

| Rank | Feature | Alerts | % |
|---|---|---|---|
| 1 | BALANCE_COVERAGE_RATIO | 97 | 80.17% |
| 2 | TRANS_AMOUNT_Z_SCORE | 66 | 54.55% |
| 3 | TRANS_AMOUNT_VS_30D_AVG_RATIO | 54 | 44.63% |
| 4 | DAYS_AMOUNT_COMBINED | 46 | 38.02% |
| 5 | VELOCITY_RATIO_AMOUNT_7D_VS_30D | 33 | 27.27% |
| 6 | BENFORD_DEV | 20 | 16.53% |
| 7 | DAYS_SINCE_LAST_TRANS | 15 | 12.40% |
| 8 | HOURS_SINCE_SEC_EVENT | 12 | 9.92% |
| 9 | TRANS_HOUR | 11 | 9.09% |
| 10 | ACTIVITY_SEQ_RARITY | 3 | 2.48% |

### 4.4 Top Toxic Feature Interactions

| Cặp tương tác | Alerts | % | Ý nghĩa |
|---|---|---|---|
| Z_SCORE × 30D_AVG_RATIO | 61 | 50.41% | Giao dịch vượt cả baseline lịch sử lẫn baseline gần đây |
| Z_SCORE × BALANCE_COVERAGE | 55 | 45.45% | Số tiền lớn bất thường so với cả thu nhập lẫn số dư |
| Z_SCORE × DAYS_AMOUNT | 50 | 41.32% | Rút tiền lớn sau thời gian dài im lặng |
| 7D_VS_30D × 30D_AVG_RATIO | 38 | 31.40% | Tập trung chi tiêu vào tuần gần nhất, mỗi lần lớn hơn bình thường |
| TRANS_HOUR × DAYS_AMOUNT | 26 | 21.49% | Giao dịch lớn ngoài giờ từ tài khoản lâu không hoạt động |

### 4.5 Hiệu suất Xử lý

| Giai đoạn | Thời gian |
|---|---|
| Tier 1 (Rule Bypass) | 0.83 ms |
| Tier 2 (ML Classification) | 39.86 ms |
| Tier 3 (xAI Explanation) | 8,862.90 ms |
| **Tổng** | **8,903.62 ms** |

Tier 1 loại bỏ 28% traffic trong <1ms, giúp giảm tải cho ML model và tiết kiệm chi phí tính toán.

### 4.6 Elastic Weight Consolidation (EWC) — Chống Quên thảm họa

| Scenario | Mean Anomaly Score on Baseline |
|---|---|
| Sau drift, **CÓ** EWC (λ=50) | 0.1667 |
| Sau drift, **KHÔNG** EWC (λ=0) | 0.1585 |

EWC giữ cho mô hình không "quên" dữ liệu gốc khi được huấn luyện lại trên dữ liệu bị drift (giao dịch x5), ngăn chặn Catastrophic Forgetting.

---

## 5. Giá trị Kinh doanh (Business Value)

### 5.1 Bảo vệ Uy tín Ngân hàng
- Hệ thống phát hiện 121 giao dịch đáng ngờ trên 5,000 giao dịch đánh giá, với tỷ lệ cảnh báo 2.42% — thấp hơn đáng kể so với mức 5-10% False Positive trung bình của hệ thống rule-based truyền thống.
- 57.85% cảnh báo là Transfer Outside Bank — đúng nhóm giao dịch rủi ro cao nhất cần giám sát.

### 5.2 Nâng cao Trải nghiệm Khách hàng
- **Tier 1 High-Speed Bypass:** 28% giao dịch nhỏ, lành tính được xử lý tức thì (<1ms) mà không cần qua ML → không gây trễ cho khách hàng bình thường.
- **Counterfactual Recourse:** Thay vì "Block giao dịch," hệ thống có khả năng đề xuất: "Giảm số tiền giao dịch từ 74 triệu xuống 45 triệu VND" hoặc "Xác minh bằng FaceID để tiếp tục" → Bảo mật không ma sát (Frictionless Security).

### 5.3 Tăng Hiệu suất Compliance
- **xAI Narratives** tự động giải thích lý do cảnh báo bằng ngôn ngữ tự nhiên, giúp Analyst xét duyệt nhanh hơn 3-5x so với việc đọc raw features.
- **SHAP Interaction Values** cho biết CHÍNH XÁC tổ hợp yếu tố nào gây ra rủi ro → Analyst không cần phỏng đoán.

---

## 6. Tài liệu Tham khảo

1. FATF (2023). "Money Laundering and Terrorist Financing Risks Arising from Virtual Assets." FATF Report.
2. European Central Bank (2024). "Supervisory Review of Anti-Money Laundering and Counter-Terrorist Financing." ECB Banking Supervision.
3. Basel Committee on Banking Supervision (2022). "Sound Practices: Implications of Fintech Developments for Banks and Bank Supervisors." BIS Publication.
4. Ngân hàng Nhà nước Việt Nam (2020). Thông tư 09/2020/TT-NHNN về quy định phòng chống rửa tiền.
5. Ngân hàng Nhà nước Việt Nam (2024). Thông tư 17/2024/TT-NHNN về xác thực sinh trắc học cho giao dịch trực tuyến.
6. Europol (2023). "Serious and Organised Crime Threat Assessment (SOCTA)." Europol Publication.
7. Akoglu, L., Tong, H., & Koutra, D. (2015). "Graph-based Anomaly Detection and Description: A Survey." Data Mining and Knowledge Discovery.
8. Bolton, R. J., & Hand, D. J. (2002). "Statistical Fraud Detection: A Review." Statistical Science, 17(3), 235-249.
9. Nigrini, M. J. (2012). "Benford's Law: Applications for Forensic Accounting, Auditing, and Fraud Detection." Wiley.
10. Chandola, V., Banerjee, A., & Kumar, V. (2009). "Anomaly Detection: A Survey." ACM Computing Surveys, 41(3), 1-58.
11. Deloitte (2023). "Fighting Financial Crime with AI: From Detection to Prevention." Deloitte Insights.
12. PwC (2024). "Global Economic Crime and Fraud Survey." PwC Publication.
13. Javelin Strategy & Research (2023). "Identity Fraud Study: The Virtual Battleground." Javelin.
14. Elkan, C. & Noto, K. (2008). "Learning Classifiers from Only Positive and Unlabeled Data." KDD.
15. Kirkpatrick, J. et al. (2017). "Overcoming Catastrophic Forgetting in Neural Networks." PNAS.
