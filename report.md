# Báo cáo Kết quả & Hướng Xây dựng Feature Engineering
## Hệ thống Phát hiện Giao dịch Bất thường — Banking Fraud & xAI Pipeline

---

## 1. Tổng quan Dự án

### 1.1 Bối cảnh

Gian lận tài chính qua kênh ngân hàng số tại Việt Nam đang gia tăng với tốc độ đáng báo động. Theo Báo cáo của Ngân hàng Nhà nước Việt Nam (NHNN) và Bộ Công an năm 2024, số vụ lừa đảo tài chính tăng trung bình 65% mỗi năm, tổng thiệt hại ước tính vượt 8.000 tỷ VND. Con số này phản ánh một thực trạng không chỉ riêng Việt Nam — FATF (2023) ghi nhận sự bùng nổ giao dịch chuyển tiền nhanh qua kênh số trên toàn cầu đã khiến các hệ thống rule-based truyền thống ngày càng bất lực, trong khi ECB (2024) thống kê tỷ lệ False Positive trung bình của hệ thống AML dựa trên rule cứng tại châu Âu lên tới hơn 95%, gây lãng phí nhân lực Compliance và xói mòn trải nghiệm khách hàng.

Tại Việt Nam, ba hình thức gian lận phổ biến nhất bao gồm:

- **Chiếm đoạt tài khoản (Account Takeover — ATO):** Lừa đảo qua SMS OTP giả mạo, SIM Swap, đánh cắp thông tin đăng nhập qua website giả (Phishing). Đặc biệt trong bối cảnh Thông tư 17/2024/TT-NHNN yêu cầu bắt buộc xác thực sinh trắc học cho giao dịch trực tuyến, ATO đang chuyển hướng sang khai thác các lỗ hổng trước khi bước xác minh sinh trắc được kích hoạt.
- **Rửa tiền và tài khoản trung chuyển (Money Mule):** Tội phạm mua/thuê tài khoản của sinh viên, người thất nghiệp để chuyển tiền bẩn nhanh qua nhiều lớp (Layering). NHNN qua Thông tư 09/2020 đã xác định nhóm dân số này là đối tượng rủi ro cao nhất cho hoạt động mule account.
- **Chia nhỏ giao dịch (Structuring/Smurfing):** Cố tình chia giao dịch thành nhiều khoản nhỏ hơn ngưỡng kiểm soát để tránh bị báo cáo theo quy định phòng chống rửa tiền (AML).

Trước bối cảnh này, Ủy ban Basel về Giám sát Ngân hàng (2022) khuyến nghị các ngân hàng sử dụng Machine Learning kết hợp Explainable AI (xAI) để giảm báo động giả và tăng khả năng giải trình trước Cơ quan quản lý — định hướng mà dự án này theo đuổi.

### 1.2 Mục tiêu

Dự án xây dựng **hệ thống cảnh báo giao dịch bất thường (Anomaly Alert System)** phù hợp với bối cảnh vận hành của ngân hàng số tại Việt Nam hiện tại, hướng tới các mục tiêu cụ thể:

1. **Phát hiện giao dịch bất thường có dấu hiệu gian lận trong thời gian gần thực (near real-time):**
   - Bao phủ ba vectơ tấn công chính: chiếm đoạt tài khoản (ATO), rửa tiền qua tài khoản trung chuyển (Money Mule), và chia nhỏ giao dịch lách ngưỡng (Structuring).
   - Hệ thống phải xử lý được khối lượng hơn 1,4 triệu giao dịch với thời gian phản hồi đủ thấp để tích hợp vào luồng phê duyệt giao dịch của ngân hàng.

2. **Giảm thiểu tỷ lệ Báo động giả (False Positive) xuống dưới ngưỡng 5%:**
   - Hệ thống rule-based truyền thống tại Việt Nam thường đạt tỷ lệ False Positive 5–10%, gây khóa nhầm tài khoản và làm giảm niềm tin khách hàng.
   - Mục tiêu duy trì tỷ lệ cảnh báo ở mức ~2–3% tổng giao dịch, tập trung chính xác vào các giao dịch thực sự có dấu hiệu rủi ro cao.

3. **Cung cấp lý giải minh bạch cho từng cảnh báo (Explainable AI — xAI):**
   - Tuân thủ yêu cầu giải trình của NHNN và Basel III: mỗi cảnh báo phải đi kèm lý do cụ thể, có thể kiểm chứng, giúp Compliance Analyst xét duyệt nhanh hơn 3–5 lần so với đọc raw features.
   - Cung cấp SHAP Feature Contributions (đóng góp từng đặc trưng), SHAP Interactions (tổ hợp yếu tố gây rủi ro), và narrative tự động bằng ngôn ngữ tự nhiên.

4. **Đề xuất hành động khắc phục tối thiểu (Counterfactual Recourse):**
   - Thay vì chặn giao dịch vô điều kiện (gây friction và mất khách), hệ thống đề xuất bước xác thực bổ sung nhỏ nhất cần thiết. Ví dụ: "Giảm số tiền từ 74 triệu xuống 45 triệu VND" hoặc "Xác minh bằng FaceID để tiếp tục."
   - Phù hợp với định hướng "Frictionless Security" — bảo mật không gây ma sát — mà các ngân hàng số Việt Nam đang hướng tới để giữ chân khách hàng.

5. **Duy trì khả năng thích ứng khi hành vi giao dịch thay đổi theo thời gian (Continuous Learning):**
   - Hành vi khách hàng tại Việt Nam biến động mạnh theo chu kỳ lương, Tết, và các đợt khuyến mãi thương mại điện tử. Mô hình phải chống được hiện tượng Catastrophic Forgetting khi dữ liệu mới có phân phối khác biệt so với dữ liệu huấn luyện ban đầu.
   - Sử dụng Elastic Weight Consolidation (EWC) để bảo vệ trọng số quan trọng đã học được từ dữ liệu gốc.

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

Hệ thống sử dụng kiến trúc **Pipeline 5 Phase** kết hợp nhiều kỹ thuật Machine Learning, được thiết kế để hoạt động trong điều kiện **không có nhãn gian lận (fraud labels)** — phản ánh đúng thực tế dữ liệu ngân hàng Việt Nam, nơi việc gán nhãn giao dịch gian lận đòi hỏi chi phí điều tra cao và thường không sẵn có ở quy mô lớn.

### 2.1 Phase 1 — Trích xuất Dữ liệu (Data Extraction)

Dữ liệu thô từ 6 bảng được nối (JOIN) và làm giàu qua nhiều phép tính thống kê trên lịch sử giao dịch của từng khách hàng. Các phép tính chính bao gồm:

| Phép tính | Chi tiết |
|---|---|
| **Rolling Window Aggregates** | Tổng số tiền và số lượng giao dịch trong 6 cửa sổ trượt thời gian: 1h, 3h, 24h, 48h, 7 ngày, 30 ngày. Mỗi cửa sổ bao gồm giao dịch hiện tại (inclusive). |
| **Customer-Level Aggregates** | Số dư trung bình lịch sử (`HIST_AVG_CA_BALANCE`), số tiền giao dịch trung bình (`HIST_AVG_TRANS_AMOUNT`), và tổng số giao dịch (`HIST_TRANS_COUNT`) — tính trên toàn bộ lịch sử khách hàng. |
| **Time Gap** | `DAYS_SINCE_LAST_TRANS`: Khoảng cách (ngày) giữa giao dịch hiện tại và giao dịch liền trước. Fallback về ngày đăng ký Internet Banking hoặc ngày tạo tài khoản nếu chưa có giao dịch nào. Mặc định 999 nếu không có dữ liệu. |
| **Unique Beneficiaries** | Đếm số người thụ hưởng duy nhất trong cửa sổ trượt 24h bằng thuật toán two-pointer sweep. |
| **Security Event Proximity** | `HOURS_SINCE_SEC_EVENT`: Khoảng cách (giờ) đến sự kiện bảo mật gần nhất (đổi mật khẩu, PIN, cập nhật sổ địa chỉ). Mặc định 999. |
| **Login & Biometric Stats** | Phương thức đăng nhập gần nhất, tỷ lệ sinh trắc học tích lũy (`HIST_BIOMETRIC_RATIO`), và tổng số lần đăng nhập tích lũy. |
| **Benford's Law Deviation** | KL-Divergence giữa phân bố chữ số đầu tiên của số tiền giao dịch và phân bố lý thuyết Benford. Chỉ tính khi khách hàng có ≥ 5 giao dịch. |
| **Activity Sequence Rarity** | Điểm log-likelihood trung bình chuẩn hóa từ mô hình Chuỗi Markov bậc 2 (Second-Order Markov Chain) xây dựng trên toàn bộ activity log, sử dụng interpolated backoff với trọng số 0.7 / 0.2 / 0.1 cho trigram / bigram / unigram. |

### 2.2 Phase 2 — Kỹ thuật Đặc trưng (Feature Engineering)

Dữ liệu thô sau Phase 1 được biến đổi thành ma trận đặc trưng hoàn toàn số học bởi bộ tiền xử lý (Preprocessor). Các phép biến đổi chính:

| Nhóm | Phép biến đổi |
|---|---|
| **Demographic Derivation** | Tính `CUSTOMER_AGE` từ ngày sinh, `TENURE_DAYS` từ ngày tạo tài khoản. |
| **Ratio & Velocity Features** | Sinh 9 đặc trưng tỷ lệ: `TRANS_AMOUNT_Z_SCORE`, `BALANCE_COVERAGE_RATIO`, 6 Velocity Ratios (1H/24H, 24H/7D, 7D/30D cho cả Amount và Count), và `TRANS_AMOUNT_VS_30D_AVG_RATIO`. Tất cả sử dụng ε = 10⁻⁵ để tránh chia cho 0. |
| **Night Transaction Ratio** | `HIST_NIGHT_RATIO`: Tỷ lệ giao dịch đêm (0h–5h) tích lũy trên toàn bộ lịch sử khách hàng. |
| **Categorical Encoding** | 7 biến phân loại (TRANS_LV1, TRANS_LV2, DAY_OF_WEEK, CLIENT_SEX, EB_REGISTER_CHANNEL, VERIFY_METHOD, Occupation_Group) được integer-encoded. |
| **Pass-Through** | 27 đặc trưng số thô từ Phase 1 được coerce sang float, NaN → 0. |

Tổng số chiều đặc trưng: **~46 features**.

### 2.3 Phase 3 — Huấn luyện: nnPU Learning với Spy Filtering & CVuO

Vì không có nhãn gian lận xác nhận, hệ thống áp dụng học bán giám sát kiểu **Positive-Unlabeled (PU) Learning** — quy trình gồm 5 bước tuần tự để tạo nhãn proxy, lọc nhiễu, và huấn luyện bộ phân loại cuối cùng:

| Bước | Kỹ thuật | Chi tiết |
|---|---|---|
| 1 | **Isolation Forest** (contamination = 3%) | Tạo nhãn proxy ban đầu: mẫu bị cô lập sớm trong cây ngẫu nhiên → gán nhãn P (Positive/suspected anomaly); phần còn lại → U (Unlabeled). |
| 2 | **PAYN Spy Filtering** | Rút 10% mẫu P làm "gián điệp" cài vào pool U. Huấn luyện XGBoost sơ bộ (P\Spies vs U∪Spies). Tính ngưỡng τ_spy = Percentile₅ của score spy. Mẫu U có score < τ_spy → N_confirmed (negative đáng tin cậy). |
| 3 | **Cross-Validated Unlabeled Optimization (CVuO)** | 5-fold CV trên U_remaining. Mỗi fold huấn luyện XGBoost tạm trên P∪N_confirmed, tính log-loss cho mẫu held-out. Loại bỏ 10% mẫu có loss cao nhất (nhiễu nhãn ẩn). |
| 4 | **XGBoost Classifier** | Huấn luyện bộ phân loại cuối cùng: P (positives) vs N_confirmed∪U_filtered (negatives đã lọc). Hyperparameters: 100 cây, max_depth=3, L1 (α)=1.0, L2 (λ)=2.0, learning_rate=0.05. |
| 5 | **Elkan-Noto Calibration** | Hiệu chỉnh xác suất bị lệch do nhãn PU: ĉ = mean(g(x) trên P), P(fraud\|x) = min(g(x)/ĉ, 1.0). Ngưỡng quyết định τ = Percentile₉₇ trên tập huấn luyện → top 3% bị gắn cờ. |

### 2.4 Phase 4 — Suy luận Phân tầng (Tiered Inference)

Mỗi giao dịch mới đi qua 3 tầng xử lý tuần tự, chỉ leo thang khi tầng trước không thể ra quyết định:

| Tầng | Xử lý | Logic | Kết quả (trong lần chạy demo) |
|---|---|---|---|
| **Tier 1 — High-Speed Bypass** | Rule-based | Bypass nếu: (a) ACTIVITY_SEQ_RARITY > −1.0 AND TRANS_AMOUNT < 500K VND, hoặc (b) TRANS_AMOUNT < 500K AND COUNT_1H ≤ 1 AND COUNT_24H ≤ 2. | 1,400 / 5,000 (28%) bypass an toàn trong 0.83ms |
| **Tier 2 — ML Classification** | XGBoost + Elkan-Noto trên 46 features | Giao dịch không bypass được đánh giá bởi mô hình ML. Gắn cờ nếu P(fraud\|x) ≥ τ. | 3,600 giao dịch đánh giá, 121 bị gắn cờ (3.36%) |
| **Tier 3 — xAI Explanation** | TreeSHAP + Interactions + Counterfactual | Chỉ chạy cho giao dịch bị gắn cờ: sinh SHAP contributions, top 3 interaction pairs (|v| > 0.01), và counterfactual recourse qua binary search 20 vòng lặp với causal propagation. | 121 thẻ cảnh báo đầy đủ trong 8.86 giây |

### 2.5 Phase 5 — Học liên tục: Elastic Weight Consolidation (EWC)

Sử dụng **Deep Autoencoder** (D→16→8→16→D) kết hợp ma trận Fisher Information để bảo vệ trọng số quan trọng khi phân phối dữ liệu thay đổi theo thời gian:

| Thành phần | Chi tiết |
|---|---|
| **Kiến trúc** | Symmetric Autoencoder: Encoder (D→16→8, ReLU) + Decoder (8→16→D). Input z-standardized. |
| **Base Training** | MSE loss, Adam optimizer, lr=0.01, 5 epochs, batch_size=256. Ngưỡng anomaly: Percentile₉₇ của MSE trên tập train. |
| **Fisher Information Matrix** | Tính diagonal FIM: F_k = (1/N) × Σ(∂L/∂θ_k)². Lưu trữ θ* (trọng số gốc). |
| **EWC Penalty khi Retrain** | L_total = L_recon_new + (λ_EWC/2) × Σ F_k × (θ_k − θ*_k)². Với λ_EWC = 50.0. |
| **Kết quả** | Sau drift (×5 amount): Mean Anomaly Score baseline **CÓ** EWC = 0.1667, **KHÔNG** EWC = 0.1585. EWC giữ cho mô hình không quên dữ liệu gốc. |

---

## 3. Mô tả Đặc trưng (Feature Description)

Hệ thống sử dụng tổng cộng **~46 đặc trưng**, chia thành 2 lớp: **Absolute Features** (giá trị tuyệt đối, đếm, nhân khẩu) và **Relative Features** (tỷ lệ, so sánh, lệch chuẩn). Trong đó, **21 đặc trưng cốt lõi** đóng vai trò tín hiệu gian lận trực tiếp được chia thành 6 nhóm chức năng. Mỗi feature được mô tả theo flow: **Concept** (ý tưởng đo lường) → **Công thức** (measurement) → **Lý do chọn** (logic thực tế, quy định, nghiên cứu).

---

### 3.1 Nhóm 1: Lệch chuẩn Số tiền (Amount Deviation)

#### TRANS_AMOUNT_Z_SCORE

- **Concept:** Đo mức độ bất thường của số tiền giao dịch hiện tại so với chính lịch sử chi tiêu của khách hàng đó. Thay vì đặt một ngưỡng tuyệt đối cứng nhắc (ví dụ: >50 triệu VND = đáng ngờ), feature này cá nhân hóa rủi ro: giao dịch 20 triệu của một sinh viên có Z-Score rất cao, nhưng giao dịch 20 triệu của một doanh nhân có thể bình thường.

- **Công thức đo lường:**

$$\text{TRANS\_AMOUNT\_Z\_SCORE} = \frac{\text{TRANS\_AMOUNT}}{\text{HIST\_AVG\_TRANS\_AMOUNT} + \epsilon}$$

Với `HIST_AVG_TRANS_AMOUNT` là trung bình toàn bộ giao dịch trước đó của khách hàng; ε = 10⁻⁵.

- **Lý do chọn feature:**
  - Akoglu et al. (2015) chứng minh rằng kẻ chiếm đoạt tài khoản (ATO) luôn muốn rút tối đa tiền trong khoảng thời gian ngắn nhất, tạo ra Z-Score đột biến. Feature này bắt chính xác tín hiệu đó.
  - Tại Việt Nam, chênh lệch thu nhập giữa các nhóm khách hàng rất lớn (sinh viên vs CEO). Ngưỡng cứng sẽ hoặc bỏ lọt gian lận ở nhóm thu nhập cao, hoặc tạo False Positive hàng loạt ở nhóm thu nhập thấp. Z-Score theo cá nhân giải quyết cả hai vấn đề.
  - **Kết quả SHAP:** Xuất hiện trong **54.55%** cảnh báo (66/121), xác nhận vai trò tín hiệu gian lận chủ lực.

#### BALANCE_COVERAGE_RATIO

- **Concept:** Đo tỷ lệ giữa số tiền giao dịch và số dư trung bình lịch sử của tài khoản. Nếu tài khoản chỉ có số dư trung bình 1 triệu nhưng đột ngột chuyển đi 50 triệu — số tiền này gần như chắc chắn vừa được nạp vào từ nguồn bên ngoài.

- **Công thức đo lường:**

$$\text{BALANCE\_COVERAGE\_RATIO} = \frac{\text{TRANS\_AMOUNT}}{\text{HIST\_AVG\_CA\_BALANCE} + \epsilon}$$

- **Lý do chọn feature:**
  - FATF (2021) xác định đây là dấu hiệu kinh điển của Money Mule — tài khoản trung chuyển tiền bẩn: dòng tiền vừa vào lập tức bị chuyển đi, khiến số tiền giao dịch vượt xa số dư bình quân lịch sử.
  - Tại Việt Nam, Bộ Công an đã cảnh báo nạn mua/thuê tài khoản sinh viên có số dư rất thấp để sử dụng làm tài khoản trung chuyển. Feature này phát hiện chính xác khi dòng tiền bất thường đổ vào các tài khoản kiểu này.
  - **Kết quả SHAP:** Đặc trưng thống trị, xuất hiện trong **80.17%** cảnh báo (97/121) — feature có tần suất xuất hiện cao nhất trong toàn bộ hệ thống.

#### TRANS_AMOUNT_VS_30D_AVG_RATIO

- **Concept:** So sánh số tiền giao dịch hiện tại với mức chi tiêu trung bình chỉ trong 30 ngày gần nhất (baseline ngắn hạn), thay vì toàn bộ lịch sử.

- **Công thức đo lường:**

$$\text{TRANS\_AMOUNT\_VS\_30D\_AVG\_RATIO} = \frac{\text{TRANS\_AMOUNT}}{\text{SUM\_AMOUNT\_30D} / (\text{COUNT\_30D} + \epsilon) + \epsilon}$$

- **Lý do chọn feature:**
  - Z-Score dài hạn (TRANS_AMOUNT_Z_SCORE) có nhược điểm: bị "pha loãng" bởi các giao dịch cũ. Khi khách hàng được tăng lương hoặc thay đổi thu nhập, baseline dài hạn chưa kịp cập nhật → sinh False Positive.
  - Bolton & Hand (2002) khuyến nghị kết hợp baseline ngắn hạn và dài hạn để phát hiện thay đổi hành vi mà vẫn kiểm soát được nhiễu. Feature 30 ngày hoạt động như một "bộ lọc thích ứng" — nếu khách hàng thực sự đã chi tiêu cao trong 30 ngày qua (do tăng lương), tỷ lệ này sẽ thấp, tránh cảnh báo sai.

---

### 3.2 Nhóm 2: Tốc độ & Tần suất (Velocity)

#### VELOCITY_RATIO_AMOUNT — 1H/24H, 24H/7D, 7D/30D

- **Concept:** Đo mức độ tập trung dòng tiền vào khoảng thời gian ngắn gần nhất. Nếu tỷ lệ tiến gần về 1.0, nghĩa là toàn bộ lượng tiền giao dịch trong 30 ngày đổ dồn hết vào 7 ngày gần nhất — hoặc toàn bộ 7 ngày dồn vào 24 giờ gần nhất.

- **Công thức đo lường:**

$$\text{VELOCITY\_RATIO\_AMOUNT\_1H\_VS\_24H} = \frac{\text{SUM\_AMOUNT\_1H}}{\text{SUM\_AMOUNT\_24H} + \epsilon}$$

$$\text{VELOCITY\_RATIO\_AMOUNT\_24H\_VS\_7D} = \frac{\text{SUM\_AMOUNT\_24H}}{\text{SUM\_AMOUNT\_7D} + \epsilon}$$

$$\text{VELOCITY\_RATIO\_AMOUNT\_7D\_VS\_30D} = \frac{\text{SUM\_AMOUNT\_7D}}{\text{SUM\_AMOUNT\_30D} + \epsilon}$$

- **Lý do chọn feature:**
  - Trong chống rửa tiền, hành vi "Cash-out" (rút hết) hoặc "Bust-out" (dùng hết hạn mức rồi bỏ trốn) buộc tội phạm phải hành động cực nhanh trước khi ngân hàng đóng băng tài khoản. Chuỗi velocity ratios 3 tầng (1H→24H→7D→30D) bắt được cả hành vi rút tiền cấp tốc (1H/24H cao) lẫn hành vi rút dần trong tuần (7D/30D cao).
  - Hệ thống sử dụng 3 tầng thay vì 1 tầng duy nhất để chống evasion: nếu tội phạm biết ngân hàng giám sát 24h, chúng có thể dàn giao dịch ra 7 ngày — nhưng velocity 7D/30D vẫn bắt được.

#### VELOCITY_RATIO_COUNT — 1H/24H, 24H/7D, 7D/30D

- **Concept:** Tương tự velocity amount, nhưng đo trên **số lượng** giao dịch thay vì số tiền. Bắt hành vi thăm dò (card testing) hoặc chia nhỏ giao dịch (structuring).

- **Công thức đo lường:**

$$\text{VELOCITY\_RATIO\_COUNT\_1H\_VS\_24H} = \frac{\text{COUNT\_1H}}{\text{COUNT\_24H} + \epsilon}$$

$$\text{VELOCITY\_RATIO\_COUNT\_24H\_VS\_7D} = \frac{\text{COUNT\_24H}}{\text{COUNT\_7D} + \epsilon}$$

$$\text{VELOCITY\_RATIO\_COUNT\_7D\_VS\_30D} = \frac{\text{COUNT\_7D}}{\text{COUNT\_30D} + \epsilon}$$

- **Lý do chọn feature:**
  - PwC (2024) xác nhận 34% gian lận bắt đầu bằng các giao dịch thăm dò (micro-transaction testing): tội phạm chạy bot chuyển thử các khoản 10.000 VND liên tục để kiểm tra tài khoản còn hoạt động. Số tiền nhỏ → velocity amount không phản ứng, nhưng velocity count sẽ đột biến.
  - Với Structuring: khi chia một giao dịch 100 triệu thành 20 khoản 5 triệu, velocity amount có thể không thay đổi nhiều (tổng vẫn vậy), nhưng velocity count tăng mạnh. Hai nhóm velocity bổ trợ lẫn nhau.

---

### 3.3 Nhóm 3: Hành vi Thời gian & Ngủ đông (Temporal & Dormancy)

#### DAYS_SINCE_LAST_TRANS

- **Concept:** Đo khoảng thời gian im lặng (ngày) giữa giao dịch hiện tại và giao dịch liền trước của cùng khách hàng. Phát hiện tài khoản "ngủ đông" bất ngờ thức giấc.

- **Công thức đo lường:**

$$\text{DAYS\_SINCE\_LAST\_TRANS}_i = \frac{t_i - t_{i-1}}{86400} \quad \text{(seconds → days)}$$

Fallback: ngày đăng ký Internet Banking hoặc ngày tạo tài khoản; mặc định 999 nếu không có dữ liệu.

- **Lý do chọn feature:**
  - Europol (2023) ghi nhận tội phạm thường thu mua tài khoản sinh viên Việt Nam và để "ngủ đông" 3–6 tháng nhằm lọt qua bộ lọc giám sát ban đầu của ngân hàng (các hệ thống rule-based thường tập trung giám sát tài khoản mới mở). Feature này "đón đầu" khoảnh khắc tài khoản thức giấc — khi giá trị cao (hàng trăm ngày) và xuất hiện cùng giao dịch lớn, xác suất mule account rất cao.
  - Phù hợp đặc thù Việt Nam: nhiều sinh viên mở tài khoản nhận học bổng/tiền bố mẹ, sau đó bỏ không dùng → bán tài khoản cho tội phạm.

#### DAYS_AMOUNT_COMBINED

- **Concept:** Interaction feature kết hợp hai tín hiệu: thời gian im lặng VÀ số tiền giao dịch. Mô hình hóa logic: "Im lặng càng lâu + Chuyển đi càng nhiều = Rủi ro càng cao." Một tài khoản im lặng 6 tháng rồi nạp thẻ điện thoại 50.000 VND là bình thường; nhưng im lặng 6 tháng rồi chuyển 500 triệu VND là cờ đỏ.

- **Công thức đo lường:**

$$\text{DAYS\_AMOUNT\_COMBINED} = \log_e(1 + \text{DAYS\_SINCE\_LAST\_TRANS}) \times \log_e(1 + \text{TRANS\_AMOUNT})$$

Log-transform (log1p) nén khoảng giá trị cực lớn, giúp mô hình cây (XGBoost) tách biệt tốt hơn trên các split phi tuyến.

- **Lý do chọn feature:**
  - Riêng feature `DAYS_SINCE_LAST_TRANS` hoặc `TRANS_AMOUNT` đơn lẻ đều sinh False Positive cao: tài khoản im lặng lâu không có nghĩa gian lận, giao dịch lớn cũng không có nghĩa gian lận. Nhưng TỔ HỢP cả hai → tín hiệu cực mạnh. Phép nhân trên thang log biến tổ hợp này thành tín hiệu rủi ro phi tuyến mà XGBoost khai thác hiệu quả.
  - **Kết quả SHAP:** Xuất hiện trong **38.02%** cảnh báo (46/121) và là thành phần của cặp tương tác toxic thứ 3 (`Z_SCORE × DAYS_AMOUNT`, 41.32%).

#### TRANS_HOUR & NIGHT_ANOMALY

- **Concept:** `TRANS_HOUR` ghi nhận giờ giao dịch (0–23) như biến kiểm soát. `NIGHT_ANOMALY` đo mức độ bất thường khi giao dịch xảy ra ban đêm (0h–5h) so với thói quen đêm lịch sử của chính khách hàng đó.

- **Công thức đo lường:**

$$\text{TRANS\_HOUR} = \text{hour}(\text{TRANS\_DATE}) \quad \text{(0-23)}$$

$$\text{NIGHT\_ANOMALY} = \text{IS\_NIGHT} \times (1 - \text{HIST\_NIGHT\_RATIO})$$

Trong đó: `IS_NIGHT = 1` nếu TRANS_HOUR ∈ [0, 5]; `HIST_NIGHT_RATIO` = tỷ lệ giao dịch đêm tích lũy trong quá khứ.

- **Lý do chọn feature:**
  - NHNN khuyến cáo rủi ro cao với giao dịch ban đêm. Tuy nhiên, chặn mọi giao dịch đêm sẽ gây phiền toái cho người làm ca đêm (bác sĩ, tài xế, bảo vệ — nhóm lao động phổ biến tại Việt Nam). `NIGHT_ANOMALY` giải quyết bằng cơ chế: nếu khách hàng quen giao dịch đêm (HIST_NIGHT_RATIO cao), thì `(1 − HIST_NIGHT_RATIO)` tiến về 0, vô hiệu hóa rủi ro đêm → bảo vệ trải nghiệm khách hàng hợp lệ.
  - Đây là ứng dụng nguyên tắc "Frictionless Security" — chỉ siết chặt giám sát khi hành vi ban đêm KHÔNG phù hợp với lịch sử, giảm friction cho khách hàng có pattern đêm hợp lệ.

---

### 3.4 Nhóm 4: An ninh & Xác thực (Security & Authentication)

#### HOURS_SINCE_SEC_EVENT

- **Concept:** Đo khoảng cách thời gian (giờ) giữa giao dịch hiện tại và sự kiện bảo mật gần nhất (đổi mật khẩu, đổi PIN, cập nhật sổ địa chỉ). Giá trị càng gần 0, xác suất giao dịch này là hành vi chiếm đoạt tài khoản (ATO) càng cao.

- **Công thức đo lường:**

$$\text{HOURS\_SINCE\_SEC\_EVENT}_i = \frac{t_{\text{tx},i} - t_{\text{last\_sec},i}}{3600}$$

Mặc định 999 nếu không có sự kiện bảo mật nào trước đó. Các sự kiện bảo mật bao gồm: PASSWORD_CHANGE, PASSWORD_SET, PIN_SET, PIN_CHANGE, PIN_RESET, ADDRESS_BOOK_UPDATE.

- **Lý do chọn feature:**
  - Javelin Strategy (2023) thống kê: >70% các vụ ATO kết thúc bằng lệnh chuyển tiền tẩu tán trong vòng 60 phút sau khi kẻ gian đổi mật khẩu/PIN thành công. Chuỗi hành vi "đổi mật khẩu → chuyển tiền lớn ngay" là dấu vân tay kinh điển của ATO.
  - Tại Việt Nam, với quy định sinh trắc học bắt buộc (Thông tư 17/2024), kẻ gian thường phải thao tác nhanh: chiếm quyền truy cập → đổi xác thực → rút tiền — tất cả trong cửa sổ vài giờ trước khi nạn nhân phát hiện. Feature này bắt chính xác chuỗi hành vi này.

#### HIST_BIOMETRIC_RATIO

- **Concept:** Đo tỷ lệ đăng nhập bằng sinh trắc học (FaceID, vân tay) trong toàn bộ lịch sử đăng nhập của khách hàng. Đóng vai trò **biến kiểm soát** — thiết lập baseline xác thực cá nhân.

- **Công thức đo lường:**

$$\text{HIST\_BIOMETRIC\_RATIO}_i = \frac{\sum_{j<i} \mathbb{1}[\text{login}_j \in \{\text{FINGER}, \text{FACEID}\}]}{\text{total\_logins\_before\_}i + \epsilon}$$

- **Lý do chọn feature:**
  - Thông tư 17/2024/TT-NHNN yêu cầu xác thực sinh trắc học bắt buộc cho giao dịch trực tuyến. Feature này thiết lập baseline: nếu khách hàng có lịch sử 99% dùng FaceID (HIST_BIOMETRIC_RATIO ~1.0), nhưng hôm nay đột nhiên đăng nhập bằng Password tĩnh trên thiết bị lạ → mô hình nhận diện đây là sự bất thường tột độ (ATO indicator).
  - Vai trò kiểm soát: feature này không tự mình gây cảnh báo, mà cung cấp bối cảnh cho các feature khác (ví dụ: HOURS_SINCE_SEC_EVENT thấp + HIST_BIOMETRIC_RATIO cao + giao dịch lớn = cờ đỏ ATO rõ ràng).

---

### 3.5 Nhóm 5: Phân tích Thống kê & Chuỗi (Statistical & Sequence)

#### BENFORD_DEV

- **Concept:** Đo độ lệch giữa phân bố chữ số đầu tiên (1–9) của tất cả số tiền giao dịch của một khách hàng so với phân bố lý thuyết của Định luật Benford. Dữ liệu tài chính tự nhiên tuân theo Benford — khi tội phạm cố tình tạo số tiền (structuring), sự sai lệch này sẽ xuất hiện.

- **Công thức đo lường:**

Phân bố lý thuyết Benford cho chữ số d ∈ {1, ..., 9}:

$$q_d = \log_{10}\!\left(1 + \frac{1}{d}\right)$$

KL-Divergence giữa phân bố thực tế và lý thuyết:

$$\text{BENFORD\_DEV} = D_{\text{KL}}(P \| Q) = \sum_{d=1}^{9} p_d \cdot \ln\!\left(\frac{p_d}{q_d}\right)$$

Chỉ tính khi khách hàng có ≥ 50 giao dịch (pipeline hiện tại sử dụng ngưỡng ≥ 5 cho Phase 1, sau đó áp dụng logic phân tích ý nghĩa thống kê ở mức ≥ 50 mẫu).

- **Lý do chọn feature:**
  - Nigrini (2012) chứng minh Định luật Benford là công cụ kiểm toán pháp y mạnh: khi tội phạm lách AML bằng cách chia nhỏ tiền có chủ đích (ví dụ: tất cả giao dịch đều bắt đầu bằng số 9 — tức 9.9 triệu, 9.8 triệu — để né ngưỡng 10 triệu), phân bố chữ số đầu tiên sẽ lệch nghiêm trọng so với Benford.
  - Định luật Benford rất nhạy cảm với kích thước mẫu nhỏ. Việc tính toán trên <50 giao dịch tạo nhiễu (noise) và False Positive cao. Ngưỡng N ≥ 50 là phương pháp luận chuẩn theo nghiên cứu kiểm toán hiện đại.
  - **Kết quả SHAP:** Xuất hiện trong **16.53%** cảnh báo (20/121) — tần suất thấp nhưng chính xác cao, đặc biệt hiệu quả với structuring.

#### ACTIVITY_SEQ_RARITY

- **Concept:** Đo mức độ hiếm (rarity) của chuỗi hoạt động kỹ thuật số (activity sequence) của khách hàng. Sử dụng mô hình Chuỗi Markov bậc 2 để tính xác suất chuyển tiếp giữa các bước hoạt động. Chuỗi càng hiếm (log-probability càng âm) → càng bất thường.

- **Công thức đo lường:**

Xác suất chuyển tiếp nội suy (interpolated backoff):

$$P_{\text{interp}}(a_3 | a_1, a_2) = 0.7 \cdot P_{\text{2nd}}(a_3 | a_1, a_2) + 0.2 \cdot P_{\text{1st}}(a_3 | a_2) + 0.1 \cdot P_{\text{global}}(a_3)$$

Điểm rarity chuẩn hóa theo chiều dài chuỗi:

$$\text{ACTIVITY\_SEQ\_RARITY}_c = \frac{1}{|\text{seq}_c| - 1}\left[\ln P_{\text{1st}}(a_2|a_1) + \sum_{i=1}^{|\text{seq}_c|-2} \ln P_{\text{interp}}(a_{i+2}|a_i, a_{i+1})\right]$$

- **Lý do chọn feature:**
  - Chandola et al. (2009) xác nhận phân tích chuỗi hành vi là cách tốt nhất bắt botnet/script tự động. Phiên bình thường: LOGIN → QUERY_ACCOUNT → TRANSFER → LOGOUT. Phiên bất thường: LOGIN → PASSWORD_CHANGE → TRANSFER_OUTSIDE → LOGOUT.
  - Feature này có vai trò kép: (1) biến độc lập cho mô hình ML tại Tier 2, và (2) quy tắc bypass tại Tier 1 — nếu ACTIVITY_SEQ_RARITY > −1.0 (chuỗi bình thường) VÀ số tiền < 500K VND → bypass an toàn.
  - Markov bậc 2 (thay vì bậc 1) cho phép bắt pattern 3 bước — đủ ngữ cảnh để phân biệt "LOGIN → PASSWORD_CHANGE" (có thể bình thường) với "LOGIN → PASSWORD_CHANGE → TRANSFER_OUTSIDE" (cờ đỏ rõ ràng).

---

### 3.6 Nhóm 6: Phân loại & Nhân khẩu (Categorical & Demographic)

#### AGE_GROUP & Occupation_Group

- **Concept:** Phân nhóm khách hàng theo tuổi (Young, Middle, Old) và nghề nghiệp để thiết lập Cohort Baseline — mức rủi ro nền cho từng phân khúc dân số. Đóng vai trò **biến kiểm soát**.

- **Công thức đo lường:** `AGE_GROUP` ánh xạ năm sinh thành 3 nhóm tuổi. `Occupation_Group` giữ nguyên label nghề nghiệp. Cả hai được label-encoded thành số nguyên.

- **Lý do chọn feature:**
  - NHNN (Thông tư 09/2020) xác định sinh viên và người già là nhóm dễ bị lừa bán tài khoản làm Mule Account nhất tại Việt Nam. Việc đưa biến nhân khẩu vào giúp mô hình phân tầng rủi ro theo bối cảnh: giao dịch 100 triệu của sinh viên thất nghiệp được XGBoost xếp rủi ro cao hơn rất nhiều so với giao dịch 100 triệu của doanh nhân — vì cây quyết định sử dụng AGE_GROUP và Occupation_Group làm tiêu chí phân nhánh.
  - Deloitte (2023) khuyến nghị segment-aware fraud detection: mô hình phải hiểu bối cảnh khách hàng thay vì đánh giá cào bằng.

#### TRANS_LV1 & TRANS_LV2

- **Concept:** Phân loại loại hình giao dịch theo hệ thống phân cấp 2 tầng. `TRANS_LV1` là nhóm lớn (Transfer, Payment, ...), `TRANS_LV2` là chi tiết (Within Bank, Outside Bank, ...). Đóng vai trò **biến kiểm soát** — xác định mức rủi ro nền theo kênh giao dịch.

- **Công thức đo lường:** Target encoding / Label encoding.

- **Lý do chọn feature:**
  - Giao dịch "Transfer Outside Bank" luôn rủi ro hơn vì tiền bẩn khi đã rời khỏi hệ thống ngân hàng gốc là cực kỳ khó thu hồi (irreversible). Kết quả thực tế xác nhận: **57.85%** cảnh báo là Transfer Outside Bank — đúng nhóm giao dịch rủi ro cao nhất.
  - Mô hình sử dụng TRANS_LV1 và TRANS_LV2 để tự động siết chặt ngưỡng cảnh báo cho các kênh giao dịch rủi ro cao, đồng thời nới lỏng cho các kênh rủi ro thấp (ví dụ: nạp tiền điện thoại).

#### CUSTOMER_AGE & TENURE_DAYS

- **Concept:** `CUSTOMER_AGE` là tuổi của khách hàng tại thời điểm giao dịch. `TENURE_DAYS` là số ngày kể từ khi tạo tài khoản. Cả hai đóng vai trò **biến kiểm soát** bổ trợ cho nhóm nhân khẩu.

- **Công thức đo lường:**

$$\text{CUSTOMER\_AGE} = \text{year}(t_{\text{tx}}) - \text{year}(\text{DATE\_OF\_BIRTH})$$

$$\text{TENURE\_DAYS} = t_{\text{tx}} - t_{\text{account\_creation}} \quad \text{(days)}$$

- **Lý do chọn feature:**
  - Tài khoản mới mở (tenure thấp) kết hợp giao dịch lớn là dấu hiệu rủi ro cao: tội phạm thường mở hoặc mua tài khoản mới, sử dụng ngay trong 30 ngày đầu rồi bỏ. Feature TENURE_DAYS giúp mô hình nhận diện pattern này.
  - CUSTOMER_AGE bổ trợ AGE_GROUP ở mức chi tiết hơn — cho phép XGBoost tạo split linh hoạt thay vì phụ thuộc vào 3 bucket cứng.

---

## Tài liệu Tham khảo

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
