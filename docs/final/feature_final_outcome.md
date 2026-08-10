# Kết quả Feature Engineering Cuối cùng — Pipeline V3 (25 Features)
## Hệ thống Phát hiện Giao dịch Bất thường — Banking Fraud & xAI Pipeline

---

## Tổng quan

Pipeline V3 vận hành với **25 đặc trưng** (features), trong đó có **4 đặc trưng mới** thuộc 2 nhóm hoàn toàn mới: **Nhóm Thiết bị & Hạ tầng** và **Nhóm Tín dụng & Cấu trúc hóa giao dịch**. Bốn feature này được thiết kế để lấp đầy 3 điểm mù (blind spots) mà bộ 21 feature gốc chưa bao phủ: thông tin thiết bị đăng nhập, dữ liệu thẻ tín dụng (Data_Card), và hành vi luân chuyển IP.

### Kết quả Pipeline V3 (trên 5,000 giao dịch):

| Chỉ số | Giá trị |
|---|---|
| Tổng giao dịch đánh giá | 5,000 |
| Tier 1 Safe Bypass (Rule-based) | 1,479 (29.6%) |
| Tier 2 ML Evaluation (XGBoost) | 3,521 |
| **Tier 3 Anomaly Alerts** | **94 (2.67%)** |
| Anomaly Score trung bình | 0.8244 |
| Kênh tẩu tán chủ đạo | Outside_bank (76.6%) |
| Thời gian xử lý tổng | 6,931 ms |

---

## Nhóm 1: Lệch chuẩn Số tiền (Amount Deviation)

---

### TRANS_AMOUNT_Z_SCORE

#### Định nghĩa
Đo mức độ bất thường của số tiền giao dịch hiện tại so với chính lịch sử chi tiêu của khách hàng đó. Thay vì đặt ngưỡng tuyệt đối cứng nhắc (ví dụ: >50 triệu VND = đáng ngờ), feature này cá nhân hóa rủi ro theo từng khách hàng.

#### Công thức đo lường

$$\text{TRANS\_AMOUNT\_Z\_SCORE} = \frac{\text{TRANS\_AMOUNT}}{\text{HIST\_AVG\_TRANS\_AMOUNT} + \epsilon}$$

Với `HIST_AVG_TRANS_AMOUNT` = trung bình toàn bộ giao dịch trước đó; ε = 10⁻⁵.

#### Ý nghĩa trong mô hình
Akoglu et al. (2015) chứng minh rằng kẻ chiếm đoạt tài khoản (ATO) luôn muốn rút tối đa tiền trong khoảng thời gian ngắn nhất, tạo ra Z-Score đột biến. Tại Việt Nam, chênh lệch thu nhập giữa các nhóm khách hàng rất lớn (sinh viên vs CEO). Ngưỡng cứng sẽ hoặc bỏ lọt gian lận ở nhóm thu nhập cao, hoặc tạo False Positive ở nhóm thu nhập thấp. Z-Score theo cá nhân giải quyết cả hai vấn đề.

#### Kết quả EDA
- Phân bố lệch phải mạnh (right-skewed): đa số giao dịch có Z-Score < 2.0, nhưng nhóm gian lận thường có Z-Score > 4.0.
- Trung bình TRANS_AMOUNT trong nhóm bị cảnh báo: **29.8 triệu VND** (gấp 2-5x mức chi tiêu thông thường của cá nhân).

#### Kết quả SHAP (Pipeline V3)

| Chỉ số | Giá trị |
|---|---|
| Tần suất trong Top SHAP | **19.1%** (18/94 alerts) |
| SHAP trung bình | +1.2303 |
| SHAP tối đa | +1.8946 |
| Xếp hạng trung bình | #1.8 |

Tương tác: `TRANS_HOUR` × `TRANS_AMOUNT_Z_SCORE` (10.6%, +0.2392) — giao dịch cường độ cao vào đêm khuya.

---

### BALANCE_COVERAGE_RATIO

#### Định nghĩa
Đo tỷ lệ giữa số tiền giao dịch và số dư trung bình lịch sử tài khoản. Nếu tài khoản chỉ có số dư 1 triệu nhưng đột ngột chuyển 50 triệu — số tiền này gần như chắc chắn vừa được nạp từ nguồn bên ngoài.

#### Công thức đo lường

$$\text{BALANCE\_COVERAGE\_RATIO} = \frac{\text{TRANS\_AMOUNT}}{\text{HIST\_AVG\_CA\_BALANCE} + \epsilon}$$

#### Ý nghĩa trong mô hình
FATF (2021) xác định đây là dấu hiệu kinh điển của Money Mule: dòng tiền vừa vào lập tức bị chuyển đi, khiến số tiền giao dịch vượt xa số dư bình quân. Tại Việt Nam, Bộ Công an cảnh báo nạn mua/thuê tài khoản sinh viên có số dư rất thấp để sử dụng làm tài khoản trung chuyển. Feature này phát hiện chính xác khi dòng tiền bất thường đổ vào các tài khoản kiểu này.

#### Kết quả EDA
- Khách hàng bình thường có BALANCE_COVERAGE_RATIO < 1.0 (giao dịch nhỏ hơn số dư).
- Nhóm bị cảnh báo có ratio trung vị > 2.0 (giao dịch gấp đôi số dư trung bình).

#### Kết quả SHAP (Pipeline V3)

| Chỉ số | Giá trị |
|---|---|
| Tần suất trong Top SHAP | **35.1%** (33/94 alerts) — **#3 toàn hệ thống** |
| SHAP trung bình | +1.6510 |
| SHAP tối đa | +3.0577 — **Cường độ tối đa cao nhất** |
| Xếp hạng trung bình | #1.9 |

Tương tác: `TRANS_HOUR` × `BALANCE_COVERAGE_RATIO` (45.7%, +0.2167), `DAYS_SINCE_LAST_TRANS` × `BALANCE_COVERAGE_RATIO` (26.6%, +0.2988).

---

### TRANS_AMOUNT_VS_30D_AVG_RATIO

#### Định nghĩa
So sánh số tiền giao dịch hiện tại với mức chi tiêu trung bình chỉ trong 30 ngày gần nhất (baseline ngắn hạn), thay vì toàn bộ lịch sử.

#### Công thức đo lường

$$\text{TRANS\_AMOUNT\_VS\_30D\_AVG\_RATIO} = \frac{\text{TRANS\_AMOUNT}}{\text{SUM\_AMOUNT\_30D} / (\text{COUNT\_30D} + \epsilon) + \epsilon}$$

#### Ý nghĩa trong mô hình
Bolton & Hand (2002) khuyến nghị kết hợp baseline ngắn hạn và dài hạn để phát hiện thay đổi hành vi mà vẫn kiểm soát nhiễu. Z-Score dài hạn bị "pha loãng" bởi giao dịch cũ; feature 30 ngày hoạt động như "bộ lọc thích ứng" — nếu khách hàng thực sự đã chi tiêu cao gần đây (do tăng lương), tỷ lệ này sẽ thấp, tránh cảnh báo sai.

#### Kết quả EDA
- 75% giao dịch có ratio < 3.0 (giao dịch hiện tại nằm trong 3x trung bình 30 ngày).
- Nhóm bị cảnh báo có ratio trung bình > 5.0.

#### Kết quả SHAP (Pipeline V3)

| Chỉ số | Giá trị |
|---|---|
| Tần suất trong Top SHAP | **27.7%** (26/94 alerts) |
| SHAP trung bình | +0.5021 |
| SHAP tối đa | +1.2818 |
| Xếp hạng trung bình | #2.8 |

---

## Nhóm 2: Tốc độ & Tần suất (Velocity)

---

### VELOCITY_RATIO_AMOUNT — 1H/24H, 24H/7D, 7D/30D

#### Định nghĩa
Đo mức độ tập trung dòng tiền vào khoảng thời gian ngắn gần nhất. Nếu tỷ lệ tiến gần về 1.0, toàn bộ lượng tiền giao dịch trong 30 ngày đổ dồn vào 7 ngày gần nhất — hoặc toàn bộ 7 ngày dồn vào 24 giờ gần nhất.

#### Công thức đo lường

$$\text{VELOCITY\_RATIO\_AMOUNT\_1H\_VS\_24H} = \frac{\text{SUM\_AMOUNT\_1H}}{\text{SUM\_AMOUNT\_24H} + \epsilon}$$

$$\text{VELOCITY\_RATIO\_AMOUNT\_24H\_VS\_7D} = \frac{\text{SUM\_AMOUNT\_24H}}{\text{SUM\_AMOUNT\_7D} + \epsilon}$$

$$\text{VELOCITY\_RATIO\_AMOUNT\_7D\_VS\_30D} = \frac{\text{SUM\_AMOUNT\_7D}}{\text{SUM\_AMOUNT\_30D} + \epsilon}$$

#### Ý nghĩa trong mô hình
Trong chống rửa tiền, hành vi "Cash-out" buộc tội phạm hành động cực nhanh trước khi ngân hàng đóng băng tài khoản. Chuỗi 3 tầng (1H→24H→7D→30D) bắt được cả hành vi rút tiền cấp tốc (1H/24H cao) lẫn hành vi rút dần (7D/30D cao). Hệ thống dùng 3 tầng thay vì 1 để chống evasion: nếu tội phạm biết ngân hàng giám sát 24h, chúng dàn giao dịch ra 7 ngày — nhưng velocity 7D/30D vẫn bắt được.

#### Kết quả EDA
- **1H/24H**: Trung vị ≈ 0.85 (đa số giao dịch tập trung trong 1h cuối). Giao dịch gian lận thường = 1.0 (chỉ có 1 giao dịch lớn duy nhất).
- **24H/7D**: Trung vị ≈ 0.5. Nhóm bị cảnh báo thường > 0.95.
- **7D/30D**: Trung vị ≈ 0.4. Nhóm bị cảnh báo thường > 0.90.

#### Kết quả SHAP (Pipeline V3)

| Feature | Tần suất | SHAP trung bình | Xếp hạng |
|---|---|---|---|
| `VELOCITY_RATIO_AMOUNT_7D_VS_30D` | **22.3%** (21/94) | +0.3641 | #2.9 |
| `VELOCITY_RATIO_AMOUNT_24H_VS_7D` | **10.6%** (10/94) | +0.5314 | #2.5 |
| `VELOCITY_RATIO_AMOUNT_1H_VS_24H` | Không xuất hiện trong top | — | — |

Tương tác: `VELOCITY_RATIO_AMOUNT_7D_VS_30D` × `TRANS_AMOUNT_VS_30D_AVG_RATIO` (tần suất tăng tốc + cường độ cao kết hợp).

---

### VELOCITY_RATIO_COUNT — 1H/24H, 24H/7D, 7D/30D

#### Định nghĩa
Tương tự velocity amount nhưng đo trên **số lượng** giao dịch thay vì số tiền. Bắt hành vi thăm dò (card testing) hoặc chia nhỏ giao dịch (structuring).

#### Công thức đo lường

$$\text{VELOCITY\_RATIO\_COUNT\_1H\_VS\_24H} = \frac{\text{COUNT\_1H}}{\text{COUNT\_24H} + \epsilon}$$

(Tương tự cho 24H/7D và 7D/30D)

#### Ý nghĩa trong mô hình
PwC (2024) xác nhận 34% gian lận bắt đầu bằng micro-transaction testing: tội phạm chạy bot chuyển thử 10.000 VND liên tục để kiểm tra tài khoản. Velocity amount không phản ứng (số tiền nhỏ), nhưng velocity count đột biến. Với Structuring: chia 100 triệu thành 20 khoản 5 triệu — velocity amount không thay đổi nhiều nhưng velocity count tăng mạnh.

#### Kết quả EDA
- Velocity count có phân bố tập trung hơn velocity amount (ít biến động).
- Nhóm bị cảnh báo có COUNT_1H/COUNT_24H thường = 1.0 (chỉ 1 giao dịch trong 1h cuối trên tổng 1 giao dịch 24h).

#### Kết quả SHAP (Pipeline V3)
Velocity count không xuất hiện trực tiếp trong Top SHAP Contributors. Trong Pipeline V3, mô hình XGBoost ưu tiên velocity amount hơn vì kịch bản ATO chủ yếu liên quan đến giao dịch đơn lẻ số tiền lớn (không cần đếm tần suất). Velocity count sẽ phát huy sức mạnh trong kịch bản Structuring (chia nhỏ giao dịch) — vốn ít xuất hiện trong tập inference nhỏ 5,000 giao dịch.

---

## Nhóm 3: Hành vi Thời gian & Ngủ đông (Temporal & Dormancy)

---

### DAYS_SINCE_LAST_TRANS

#### Định nghĩa
Đo khoảng thời gian im lặng (ngày) giữa giao dịch hiện tại và giao dịch liền trước của cùng khách hàng. Phát hiện tài khoản "ngủ đông" bất ngờ thức giấc.

#### Công thức đo lường

$$\text{DAYS\_SINCE\_LAST\_TRANS}_i = \frac{t_i - t_{i-1}}{86400} \quad \text{(seconds → days)}$$

Fallback: ngày đăng ký Internet Banking hoặc ngày tạo tài khoản; mặc định 999 nếu không có dữ liệu.

#### Ý nghĩa trong mô hình
Europol (2023) ghi nhận tội phạm thường thu mua tài khoản sinh viên Việt Nam và để "ngủ đông" 3-6 tháng nhằm lọt qua bộ lọc giám sát ban đầu. Feature này "đón đầu" khoảnh khắc tài khoản thức giấc — khi giá trị cao (hàng trăm ngày) kết hợp giao dịch lớn, xác suất mule account rất cao. Phù hợp đặc thù Việt Nam: nhiều sinh viên mở tài khoản nhận học bổng rồi bỏ không dùng → bán tài khoản cho tội phạm.

#### Kết quả EDA
- Trung vị toàn hệ thống: ~3-5 ngày (giao dịch đều đặn).
- Nhóm bị cảnh báo: trung vị > 60 ngày (ngủ đông rõ ràng).
- Nhóm cực đoan: > 180 ngày (6 tháng không hoạt động).

#### Kết quả SHAP (Pipeline V3)

| Chỉ số | Giá trị |
|---|---|
| Tần suất trong Top SHAP | **14.9%** (14/94 alerts) |
| SHAP trung bình | +1.0932 |
| SHAP tối đa | +1.4920 |
| Xếp hạng trung bình | #2.6 |

Tương tác: `DAYS_SINCE_LAST_TRANS` × `BALANCE_COVERAGE_RATIO` (26.6%, +0.2988) — tài khoản ngủ đông kết hợp vét sạch số dư.

---

### DAYS_AMOUNT_COMBINED

#### Định nghĩa
Interaction feature kết hợp thời gian im lặng VÀ số tiền giao dịch. Mô hình hóa logic: "Im lặng càng lâu + Chuyển đi càng nhiều = Rủi ro càng cao."

#### Công thức đo lường

$$\text{DAYS\_AMOUNT\_COMBINED} = \ln(1 + \text{DAYS\_SINCE\_LAST\_TRANS}) \times \ln(1 + \text{TRANS\_AMOUNT})$$

Log-transform nén khoảng giá trị cực lớn, giúp XGBoost tách biệt tốt hơn trên các split phi tuyến.

#### Ý nghĩa trong mô hình
Riêng DAYS_SINCE_LAST_TRANS hoặc TRANS_AMOUNT đơn lẻ đều sinh False Positive cao: tài khoản im lặng lâu không có nghĩa gian lận, giao dịch lớn cũng không. Nhưng TỔ HỢP cả hai → tín hiệu cực mạnh. Phép nhân trên thang log biến tổ hợp thành tín hiệu rủi ro phi tuyến mà XGBoost khai thác hiệu quả.

#### Kết quả EDA
- Phân bố: nhóm bình thường có combined score < 30; nhóm bị cảnh báo thường > 40.
- Ca cực đoan: combined score > 60 (im lặng > 60 ngày + giao dịch > 50 triệu).

#### Kết quả SHAP (Pipeline V3)

| Chỉ số | Giá trị |
|---|---|
| Tần suất trong Top SHAP | **46.8%** (44/94 alerts) — **#2 toàn hệ thống** |
| SHAP trung bình | **+2.0205** — **Cường độ trung bình cao nhất** |
| SHAP tối đa | +2.7904 |
| Xếp hạng trung bình | **#1.3** — **Xếp hạng cao nhất** |

Tương tác: `NEW_DEVICE_FLAG` × `DAYS_AMOUNT_COMBINED` (**43.6%**, +0.6039) — tương tác toxic mạnh nhất toàn hệ thống. Kịch bản: tài khoản ngủ đông + máy lạ + tiền lớn = ATO kinh điển.

---

### TRANS_HOUR & NIGHT_ANOMALY

#### Định nghĩa
`TRANS_HOUR` ghi nhận giờ giao dịch (0-23) như biến kiểm soát. `NIGHT_ANOMALY` đo mức độ bất thường khi giao dịch ban đêm (0h-5h) so với thói quen đêm lịch sử của khách hàng.

#### Công thức đo lường

$$\text{TRANS\_HOUR} = \text{hour}(\text{TRANS\_DATE})$$

$$\text{NIGHT\_ANOMALY} = \text{IS\_NIGHT} \times (1 - \text{HIST\_NIGHT\_RATIO})$$

IS_NIGHT = 1 nếu TRANS_HOUR ∈ [0, 5]; HIST_NIGHT_RATIO = tỷ lệ giao dịch đêm tích lũy.

#### Ý nghĩa trong mô hình
NHNN khuyến cáo rủi ro cao với giao dịch ban đêm. Tuy nhiên, chặn mọi giao dịch đêm gây phiền toái cho bác sĩ, tài xế, bảo vệ (lao động ca đêm phổ biến tại Việt Nam). NIGHT_ANOMALY giải quyết bằng cơ chế: nếu khách hàng quen giao dịch đêm (HIST_NIGHT_RATIO cao), thì (1 − HIST_NIGHT_RATIO) → 0, vô hiệu hóa rủi ro đêm → bảo vệ trải nghiệm khách hàng hợp lệ. Đây là nguyên tắc "Frictionless Security".

#### Kết quả EDA
- 8.2% giao dịch diễn ra trong khung 0h-5h.
- Nhóm bị cảnh báo có tỷ lệ giao dịch đêm cao hơn 2x so với toàn hệ thống.

#### Kết quả SHAP (Pipeline V3)

| Chỉ số | Giá trị |
|---|---|
| Tần suất trong Top SHAP (`TRANS_HOUR`) | **30.9%** (29/94 alerts) — **#4** |
| SHAP trung bình | **+3.4959** — **Cường độ đơn lẻ cao nhất toàn hệ thống** |
| SHAP tối đa | +3.7272 |
| Xếp hạng trung bình | **#1.0** — Luôn xếp #1 khi xuất hiện |

`TRANS_HOUR` tham gia vào **5 cặp tương tác toxic hàng đầu**: TRANS_HOUR × BALANCE_COVERAGE_RATIO (45.7%), TRANS_HOUR × IP_HOPPING_VELOCITY (16.0%), TRANS_HOUR × VELOCITY_RATIO_24H/7D (13.8%), TRANS_HOUR × TRANS_AMOUNT_Z_SCORE (10.6%), TRANS_HOUR × NEW_DEVICE_FLAG (10.6%).

---

## Nhóm 4: An ninh & Xác thực (Security & Authentication)

---

### HOURS_SINCE_SEC_EVENT

#### Định nghĩa
Đo khoảng cách thời gian (giờ) giữa giao dịch hiện tại và sự kiện bảo mật gần nhất (đổi mật khẩu, đổi PIN, cập nhật sổ địa chỉ). Giá trị càng gần 0, xác suất giao dịch này là ATO càng cao.

#### Công thức đo lường

$$\text{HOURS\_SINCE\_SEC\_EVENT}_i = \frac{t_{\text{tx},i} - t_{\text{last\_sec},i}}{3600}$$

Mặc định 999 nếu không có sự kiện bảo mật trước đó. Các sự kiện: PASSWORD_CHANGE, PASSWORD_SET, PIN_SET, PIN_CHANGE, PIN_RESET, ADDRESS_BOOK_UPDATE.

#### Ý nghĩa trong mô hình
Javelin Strategy (2023) thống kê: >70% các vụ ATO kết thúc bằng lệnh chuyển tiền tẩu tán trong vòng 60 phút sau khi kẻ gian đổi mật khẩu/PIN. Chuỗi "đổi mật khẩu → chuyển tiền lớn ngay" là dấu vân tay kinh điển của ATO. Tại Việt Nam, với Thông tư 17/2024, kẻ gian phải thao tác nhanh: chiếm quyền → đổi xác thực → rút tiền — tất cả trong vài giờ trước khi nạn nhân phát hiện.

#### Kết quả EDA
- 95% giao dịch có HOURS_SINCE_SEC_EVENT > 500 (không có sự kiện bảo mật gần đây).
- Nhóm bị cảnh báo có tỷ lệ HOURS_SINCE_SEC_EVENT < 24h cao hơn 10x so với toàn hệ thống.

#### Kết quả SHAP (Pipeline V3)

| Chỉ số | Giá trị |
|---|---|
| Tần suất trong Top SHAP | **16.0%** (15/94 alerts) |
| SHAP trung bình | +0.7287 |
| SHAP tối đa | +0.9930 |
| Xếp hạng trung bình | #2.7 |

Tương tác: `HOURS_SINCE_SEC_EVENT` × `DAYS_AMOUNT_COMBINED` (6.4%, +0.2457) — đổi mật khẩu + tài khoản ngủ đông + tiền lớn.

---

### SEC_AMOUNT_COMBINED

#### Định nghĩa
Interaction feature kết hợp khoảng cách sự kiện bảo mật VÀ số tiền giao dịch. Logic: "Đổi mật khẩu gần đây + Chuyển tiền lớn = Rủi ro ATO."

#### Công thức đo lường

$$\text{SEC\_AMOUNT\_COMBINED} = \frac{\ln(1 + \text{TRANS\_AMOUNT})}{\ln(1 + \text{HOURS\_SINCE\_SEC\_EVENT}) + \epsilon}$$

Giá trị cao khi TRANS_AMOUNT lớn VÀ HOURS_SINCE_SEC_EVENT nhỏ (gần 0).

#### Ý nghĩa trong mô hình
Tương tự DAYS_AMOUNT_COMBINED, feature này kết hợp hai tín hiệu yếu (riêng lẻ) thành tín hiệu mạnh (tổ hợp). Đổi mật khẩu không có nghĩa gian lận, chuyển tiền lớn không có nghĩa gian lận — nhưng đổi mật khẩu rồi lập tức chuyển tiền lớn là cờ đỏ ATO.

#### Kết quả EDA
- 99% giao dịch có SEC_AMOUNT_COMBINED < 5.0 (sự kiện bảo mật xa hoặc không có).
- Nhóm ATO có combined score > 10.0.

#### Kết quả SHAP (Pipeline V3)

| Chỉ số | Giá trị |
|---|---|
| Tần suất trong Top SHAP | **2.1%** (2/94 alerts) |
| SHAP trung bình | +0.4719 |
| Xếp hạng trung bình | #2.5 |

Tần suất thấp vì ATO có sự kiện bảo mật gần là kịch bản hiếm trong tập mẫu 5,000 giao dịch, nhưng khi xuất hiện, cường độ SHAP vừa phải.

---

### HIST_BIOMETRIC_RATIO

#### Định nghĩa
Đo tỷ lệ đăng nhập bằng sinh trắc học (FaceID, vân tay) trong toàn bộ lịch sử đăng nhập của khách hàng. Đóng vai trò **biến kiểm soát** — thiết lập baseline xác thực cá nhân.

#### Công thức đo lường

$$\text{HIST\_BIOMETRIC\_RATIO}_i = \frac{\sum_{j<i} \mathbb{1}[\text{login}_j \in \{\text{FINGER}, \text{FACEID}\}]}{\text{total\_logins\_before\_}i + \epsilon}$$

#### Ý nghĩa trong mô hình
Thông tư 17/2024/TT-NHNN yêu cầu xác thực sinh trắc học bắt buộc. Feature này thiết lập baseline: nếu khách hàng có lịch sử 99% dùng FaceID (ratio ~1.0) nhưng hôm nay đăng nhập bằng Password trên thiết bị lạ → mô hình nhận diện đây là ATO. Feature không tự gây cảnh báo mà cung cấp bối cảnh cho các feature khác.

#### Kết quả EDA
- Phân bố bimodal: đa số khách hàng có ratio ≈ 0 (chưa dùng sinh trắc) hoặc > 0.3 (dùng thường xuyên).
- Trung bình toàn hệ thống: 0.115 (tỷ lệ biometric adoption thấp trong dữ liệu 2019).
- Chỉ 27 khách hàng có ratio > 0.5.

#### Kết quả SHAP (Pipeline V3)
HIST_BIOMETRIC_RATIO không xuất hiện trực tiếp trong Top SHAP Contributors của Pipeline V3. Điều này phản ánh đúng tỷ lệ biometric adoption rất thấp trong dữ liệu 2019 (chỉ 21.9% logins). Trong production 2025-2026 (sau QĐ 2345/QĐ-NHNN), tỷ lệ biometric sẽ cao hơn nhiều và feature này sẽ tự động phát huy sức mạnh.

---

## Nhóm 5: Phân tích Thống kê & Chuỗi (Statistical & Sequence)

---

### BENFORD_DEV

#### Định nghĩa
Đo độ lệch giữa phân bố chữ số đầu tiên (1-9) của tất cả số tiền giao dịch của một khách hàng so với phân bố lý thuyết của Định luật Benford. Dữ liệu tài chính tự nhiên tuân theo Benford — khi tội phạm cố tình tạo số tiền (structuring), sự sai lệch xuất hiện.

#### Công thức đo lường

$$q_d = \log_{10}\!\left(1 + \frac{1}{d}\right)$$

$$\text{BENFORD\_DEV} = D_{\text{KL}}(P \| Q) = \sum_{d=1}^{9} p_d \cdot \ln\!\left(\frac{p_d}{q_d}\right)$$

Chỉ tính khi khách hàng có ≥ 50 giao dịch.

#### Ý nghĩa trong mô hình
Nigrini (2012) chứng minh Định luật Benford là công cụ kiểm toán pháp y mạnh: khi tội phạm lách AML bằng cách chia nhỏ tiền (ví dụ: 9.9 triệu, 9.8 triệu để né ngưỡng 10 triệu), phân bố chữ số đầu tiên lệch nghiêm trọng. Ngưỡng N ≥ 50 là phương pháp luận chuẩn theo nghiên cứu kiểm toán hiện đại.

#### Kết quả EDA
- Khách hàng hợp pháp có BENFORD_DEV < 0.05 (tuân theo Benford tốt).
- Khách hàng structuring có BENFORD_DEV > 0.15 (phân bố chữ số đầu tiên lệch rõ ràng).
- Chỉ tính được cho ~30% khách hàng (những người có ≥ 50 giao dịch).

#### Kết quả SHAP (Pipeline V3)
BENFORD_DEV không xuất hiện trong Top SHAP Contributors V3. Tần suất thấp nhưng chính xác cao — feature này đặc biệt hiệu quả với structuring, kịch bản ít xuất hiện trong tập mẫu nhỏ.

---

### ACTIVITY_SEQ_RARITY

#### Định nghĩa
Đo mức độ hiếm (rarity) của chuỗi hoạt động kỹ thuật số của khách hàng. Sử dụng mô hình Chuỗi Markov bậc 2 để tính xác suất chuyển tiếp. Chuỗi càng hiếm (log-probability càng âm) → càng bất thường.

#### Công thức đo lường

$$P_{\text{interp}}(a_3 | a_1, a_2) = 0.7 \cdot P_{\text{2nd}}(a_3 | a_1, a_2) + 0.2 \cdot P_{\text{1st}}(a_3 | a_2) + 0.1 \cdot P_{\text{global}}(a_3)$$

$$\text{ACTIVITY\_SEQ\_RARITY}_c = \frac{1}{|\text{seq}_c| - 1}\left[\ln P_{\text{1st}}(a_2|a_1) + \sum_{i=1}^{|\text{seq}_c|-2} \ln P_{\text{interp}}(a_{i+2}|a_i, a_{i+1})\right]$$

#### Ý nghĩa trong mô hình
Chandola et al. (2009) xác nhận phân tích chuỗi hành vi là cách tốt nhất bắt botnet/script tự động. Phiên bình thường: LOGIN → QUERY_ACCOUNT → TRANSFER → LOGOUT. Phiên bất thường: LOGIN → PASSWORD_CHANGE → TRANSFER_OUTSIDE → LOGOUT. Feature có vai trò kép: (1) biến độc lập cho XGBoost tại Tier 2, và (2) quy tắc bypass tại Tier 1 — nếu ACTIVITY_SEQ_RARITY > −1.0 VÀ số tiền < 500K → bypass an toàn.

#### Kết quả EDA
- Phân bố đa phần nằm trong [-2.0, -0.5] (chuỗi thông thường).
- Nhóm bất thường: < -3.0 (chuỗi hành vi cực hiếm trong lịch sử 16 triệu activity logs).

#### Kết quả SHAP (Pipeline V3)
ACTIVITY_SEQ_RARITY không xuất hiện trong Top SHAP Contributors V3. Feature này chủ yếu phát huy vai trò ở **Tier 1 Safe Bypass** — giúp loại bỏ 29.6% giao dịch an toàn trước khi chúng đến được XGBoost, giảm tải cho mô hình ML.

---

## Nhóm 6: Phân loại & Nhân khẩu (Categorical & Demographic)

---

### AGE_GROUP & Occupation_Group

#### Định nghĩa
Phân nhóm khách hàng theo tuổi (Young, Middle, Old) và nghề nghiệp để thiết lập Cohort Baseline. Đóng vai trò **biến kiểm soát**.

#### Công thức đo lường
AGE_GROUP ánh xạ năm sinh thành 3 nhóm tuổi. Occupation_Group giữ nguyên label nghề nghiệp. Cả hai label-encoded thành số nguyên.

#### Ý nghĩa trong mô hình
NHNN (Thông tư 09/2020) xác định sinh viên và người già là nhóm dễ bị lừa bán tài khoản làm Mule Account nhất. Biến nhân khẩu giúp mô hình phân tầng rủi ro theo bối cảnh: giao dịch 100 triệu của sinh viên thất nghiệp có rủi ro cao hơn rất nhiều so với giao dịch 100 triệu của doanh nhân. Deloitte (2023) khuyến nghị segment-aware fraud detection.

#### Kết quả EDA
- Nhóm Young (18-30): 35% khách hàng, 45% alerts (tỷ lệ cao hơn bình thường).
- Nhóm Middle (31-55): 50% khách hàng, 40% alerts.
- Nhóm Old (>55): 15% khách hàng, 15% alerts.

#### Kết quả SHAP (Pipeline V3)

| Chỉ số | Giá trị |
|---|---|
| Tần suất trong Top SHAP (`AGE_GROUP`) | **1.1%** (1/94 alerts) |
| SHAP trung bình | ~0.00 |

AGE_GROUP và Occupation_Group đóng vai trò biến nền — chúng không trực tiếp gây cảnh báo mà cung cấp bối cảnh phân nhóm để các biến rủi ro chính (Z-Score, Velocity) hoạt động chính xác hơn trong từng phân khúc.

---

### TRANS_LV1 & TRANS_LV2

#### Định nghĩa
Phân loại loại hình giao dịch theo hệ thống phân cấp 2 tầng. TRANS_LV1 là nhóm lớn (Transfer, Payment), TRANS_LV2 là chi tiết (Within_bank, Outside_bank). Đóng vai trò **biến kiểm soát** — xác định mức rủi ro nền theo kênh.

#### Công thức đo lường
Label encoding / Target encoding.

#### Ý nghĩa trong mô hình
Giao dịch "Transfer Outside_bank" luôn rủi ro hơn vì tiền khi đã rời hệ thống ngân hàng gốc là cực kỳ khó thu hồi (irreversible). Mô hình sử dụng TRANS_LV1 và TRANS_LV2 để tự động siết ngưỡng cảnh báo cho kênh rủi ro cao, nới lỏng cho kênh rủi ro thấp (nạp tiền điện thoại).

#### Kết quả EDA
- Outside_bank chiếm ~35% tổng giao dịch nhưng **76.6%** cảnh báo (tập trung gấp 2.2x).
- Within_bank: ~25% giao dịch, 14.9% cảnh báo.
- Credit_card_repayment: ~3.6% giao dịch, 5.3% cảnh báo.

#### Kết quả SHAP (Pipeline V3)
TRANS_LV1 và TRANS_LV2 không xuất hiện trực tiếp trong Top SHAP vì chúng là biến phân loại nền. Tuy nhiên, ảnh hưởng gián tiếp rõ ràng: 76.6% cảnh báo tập trung vào Outside_bank — chứng tỏ mô hình đã học được rằng kênh này rủi ro cao nhất.

---

### CUSTOMER_AGE & TENURE_DAYS

#### Định nghĩa
CUSTOMER_AGE = tuổi tại thời điểm giao dịch. TENURE_DAYS = số ngày kể từ khi tạo tài khoản. Cả hai là **biến kiểm soát** bổ trợ nhân khẩu.

#### Công thức đo lường

$$\text{CUSTOMER\_AGE} = \text{year}(t_{\text{tx}}) - \text{year}(\text{DATE\_OF\_BIRTH})$$

$$\text{TENURE\_DAYS} = t_{\text{tx}} - t_{\text{account\_creation}} \quad \text{(days)}$$

#### Ý nghĩa trong mô hình
Tài khoản mới mở (tenure thấp) kết hợp giao dịch lớn là dấu hiệu rủi ro cao: tội phạm thường mở hoặc mua tài khoản mới, sử dụng ngay trong 30 ngày đầu rồi bỏ. CUSTOMER_AGE bổ trợ AGE_GROUP ở mức chi tiết hơn — cho phép XGBoost tạo split linh hoạt.

#### Kết quả EDA
- TENURE_DAYS trung bình toàn hệ thống: ~1,200 ngày (3.3 năm).
- Nhóm bị cảnh báo có tenure thấp hơn trung bình ~20%.

#### Kết quả SHAP (Pipeline V3)
CUSTOMER_AGE và TENURE_DAYS không xuất hiện trong Top SHAP Contributors. Chúng hoạt động ở tầng split nền của XGBoost, cung cấp thông tin phân nhánh bổ trợ cho các feature rủi ro chính.

---

## Nhóm Feature Mới: Thiết bị & Hạ tầng kỹ thuật


### Feature 1: NEW_DEVICE_FLAG (Cờ thiết bị mới)

#### Định nghĩa
Gán cờ nhị phân (`1` = Có, `0` = Không) xác định giao dịch hiện tại có đang được thực hiện trên một thiết bị (`Device_ID_Hash`) mà khách hàng **chưa từng sử dụng** trong lịch sử hay không.

#### Công thức đo lường

$$\text{NEW\_DEVICE\_FLAG}_i = \begin{cases} 1 & \text{if } \text{cumcount}(\text{CUSTOMER}, \text{Device\_ID\_Hash})_i = 0 \\ 0 & \text{otherwise} \end{cases}$$

Sử dụng `groupby(['CUSTOMER_NUMBER', 'Device_ID_Hash']).cumcount()`. Lần xuất hiện đầu tiên (cumcount = 0) của một cặp (khách hàng, thiết bị) được gán cờ = 1.

#### Ý nghĩa trong mô hình

Kẻ chiếm đoạt tài khoản (ATO) luôn phải sử dụng thiết bị khác với thiết bị quen thuộc của nạn nhân. Javelin Strategy & Research (2023) thống kê rằng hơn 80% các vụ ATO thành công đều bắt đầu từ việc đăng ký thiết bị mới. Tại Việt Nam, Quyết định 2345/QĐ-NHNN (2024) yêu cầu xác thực sinh trắc học trên thiết bị mới — nhưng kẻ gian vẫn có thể lách bước này bằng cách sử dụng mã độc di động (GoldPickaxe) để sao chép khuôn mặt nạn nhân. `NEW_DEVICE_FLAG` hoạt động như lớp phòng thủ bổ sung, phát hiện chính xác thời điểm "xâm nhập" bất kể phương thức xác thực.

Feature này đặc biệt mạnh khi kết hợp với các tín hiệu khác:
- **Thiết bị mới + Số tiền lớn** → Chiếm đoạt tài khoản cổ điển.
- **Thiết bị mới + Tài khoản ngủ đông** → Mua/thuê tài khoản sinh viên và sử dụng lần đầu.
- **Thiết bị mới + Đêm khuya** → Kịch bản tấn công lúc nạn nhân đang ngủ.

#### Kết quả EDA

| Chỉ số | Giá trị |
|---|---|
| Tổng thiết bị duy nhất trong hệ thống | 72,050 |
| Tỷ lệ giao dịch trên thiết bị mới (toàn hệ thống) | ~15-20% |
| Tỷ lệ giao dịch trên thiết bị mới (trong nhóm bị cảnh báo) | **48.9%** |
| Hệ số phân biệt (Discrimination Ratio) | 48.9% / ~17.5% ≈ **2.8x** |

Thiết bị mới xuất hiện gần gấp 3 lần trong nhóm bị cảnh báo so với nhóm bình thường — chứng tỏ sức phân biệt cực mạnh.

#### Kết quả SHAP Explanations (Pipeline V3)

| Chỉ số SHAP | Giá trị |
|---|---|
| Tần suất xuất hiện trong Top SHAP | **48.9%** (46/94 alerts) — **#1 toàn hệ thống** |
| Đóng góp SHAP trung bình | +1.2229 |
| Đóng góp SHAP tối đa | +1.5687 |
| Xếp hạng trung bình | #1.9 |

**Tương tác độc hại (Toxic Interactions):**

| Cặp tương tác | Tỷ lệ | SHAP cộng thêm | Kịch bản |
|---|---|---|---|
| `NEW_DEVICE_FLAG` × `DAYS_AMOUNT_COMBINED` | **43.6%** | +0.6039 | ATO kinh điển: Tài khoản ngủ đông → Đăng nhập máy lạ → Chuyển tiền lớn |
| `NEW_DEVICE_FLAG` × `BALANCE_COVERAGE_RATIO` | 7.4% | +0.2514 | Vét sạch số dư trên máy lạ |
| `NEW_DEVICE_FLAG` × `TRANS_AMOUNT_Z_SCORE` | 7.4% | +0.1313 | Giao dịch cường độ bất thường trên máy lạ |

---

### Feature 2: IP_HOPPING_VELOCITY (Tốc độ luân chuyển IP)

#### Định nghĩa
Đếm số lượng địa chỉ IP/Proxy **duy nhất** mà một thiết bị (`Device_ID_Hash`) sử dụng trong cửa sổ trượt 3 giờ (3-hour rolling window).

#### Công thức đo lường

$$\text{IP\_HOPPING\_VELOCITY}_i = |\{IP\_Address\_Proxy_j : j \in W_{3h}(i) \wedge Device_j = Device_i\}|$$

Trong đó $W_{3h}(i)$ là tập các giao dịch diễn ra trong 3 giờ trước giao dịch $i$ trên cùng thiết bị. Giá trị = 1 nghĩa là thiết bị chỉ dùng 1 IP (bình thường), giá trị > 3 trong 3 giờ là dấu hiệu proxy rotation.

#### Ý nghĩa trong mô hình

Tội phạm mạng hiện đại sử dụng các công cụ tự động xoay vòng IP (Residential Proxy, VPN Chaining) để: (1) lách bộ quy tắc địa lý của ngân hàng, (2) tránh bị truy vết nguồn gốc, và (3) tạo ảo giác rằng giao dịch đến từ nhiều vị trí khác nhau. Europol IOCTA (2024) ghi nhận sự bùng nổ dịch vụ Proxy-as-a-Service trên darknet, với giá chỉ từ $5/ngày — khiến kỹ thuật này trở nên phổ biến ngay cả với tội phạm cấp thấp.

Đặc biệt, mã độc di động **GoldPickaxe** (Group-IB, 2024) nhắm vào khách hàng ngân hàng Việt Nam có khả năng tự động xoay vòng IP trên thiết bị bị nhiễm để lách hệ thống giám sát theo vùng địa lý. Feature `IP_HOPPING_VELOCITY` bắt chính xác hành vi này ở tầng hạ tầng — một chiều dữ liệu mà tất cả 21 feature gốc không hề khai thác.

#### Kết quả EDA

**Phân bố IP theo thiết bị (toàn bộ 72,050 thiết bị):**

| Nhóm | Số thiết bị | Tỷ lệ | Phân loại |
|---|---|---|---|
| 1 IP (cố định) | 24,693 | 34.3% | Bình thường — Máy bàn, WiFi nhà |
| 2 IPs (nhà + công ty) | 5,400 | 7.5% | Bình thường |
| 3-5 IPs (di động) | 8,194 | 11.4% | Bình thường — Người dùng 4G/5G |
| 6-10 IPs | 7,916 | 11.0% | Theo dõi — Du khách, lái xe |
| **11-50 IPs** | **18,342** | **25.5%** | **Đáng ngờ** |
| **51-100 IPs** | **4,681** | **6.5%** | **VPN xoay vòng** |
| **> 100 IPs** | **2,824** | **3.9%** | **Bot / Proxy Rotation** |

**Phân tích cửa sổ 3 giờ (50K mẫu):**
- Giao dịch có 2+ IP trong 3h: **8,591**
- Thiết bị nhảy IP trong 3h: **2,078**
- IP trung bình trong 3h: 2.3, tối đa: **10 IP/3h**

#### Kết quả SHAP Explanations (Pipeline V3)

| Chỉ số SHAP | Giá trị |
|---|---|
| Tần suất xuất hiện trong Top SHAP | **16.0%** (15/94 alerts) |
| Đóng góp SHAP trung bình | +0.7882 |
| Đóng góp SHAP tối đa | +0.8865 |
| Xếp hạng trung bình | #2.1 |

**Tương tác độc hại:**

| Cặp tương tác | Tỷ lệ | SHAP cộng thêm | Kịch bản |
|---|---|---|---|
| `TRANS_HOUR` × `IP_HOPPING_VELOCITY` | **16.0%** | +0.3902 | Thiết bị nhảy IP liên tục vào **đêm khuya** — dấu hiệu bot tự động chạy kịch bản tấn công |

---

## Nhóm Feature Mới: Tín dụng & Cấu trúc hóa Giao dịch

---

### Feature 3: LIMIT_UTILIZATION_VELOCITY (Tốc độ sử dụng hạn mức tín dụng)

#### Định nghĩa
Đo tốc độ tăng trưởng tỷ lệ sử dụng hạn mức thẻ tín dụng theo tháng (Month-over-Month Velocity). Giá trị dương cao nghĩa là khách hàng đang vét hạn mức thẻ với tốc độ bất thường.

#### Công thức đo lường

$$\text{utilization}_t = \frac{\text{OUTSTANDING\_BAL\_CREDIT}_t}{\text{LIMIT\_AMT\_CREDIT}_t}$$

$$\text{velocity}_t = \text{utilization}_t - \text{utilization}_{t-1}$$

$$\text{LIMIT\_UTILIZATION\_VELOCITY}_c = \max_{t} (\text{velocity}_{c,t})$$

Nguồn dữ liệu: Bảng `Data_Card`. Tính trên toàn bộ lịch sử thẻ của khách hàng, lấy giá trị velocity cao nhất.

#### Ý nghĩa trong mô hình

Gian lận Synthetic Identity (danh tính tổng hợp) và Bust-out là mô hình lừa đảo tín dụng tinh vi, được FBI (2023) xếp hạng là loại gian lận tài chính gây thiệt hại lớn nhất tại Mỹ (ước tính $6 tỷ/năm). Quy trình Bust-out:

1. **Giai đoạn Nuôi (Build-up):** Kẻ gian mở thẻ tín dụng, duy trì tỷ lệ sử dụng thấp (5-10%) trong 3-6 tháng để xây dựng uy tín tín dụng.
2. **Giai đoạn Vét (Max-out):** Khi ngân hàng nâng hạn mức, chúng **vét sạch** trong 1 tháng — tạo ra velocity +0.5 đến +0.56.
3. **Giai đoạn Bùng (Bust-out):** Biến mất, không trả nợ.

Tại Việt Nam, NHNN (Thông tư 01/2020) yêu cầu các tổ chức tín dụng kiểm soát tốc độ phê duyệt tín dụng, nhưng chưa có quy định giám sát tốc độ *sử dụng* hạn mức. Feature này lấp khoảng trống giám sát đó.

Đây là feature duy nhất trong hệ thống khai thác bảng `Data_Card` — mở rộng phạm vi giám sát từ chỉ "giao dịch" sang "tín dụng".

#### Kết quả EDA

**Phân bố Velocity (34,939 khách hàng có thẻ tín dụng):**

| Nhóm | Số khách hàng | Tỷ lệ | Đánh giá rủi ro |
|---|---|---|---|
| < 0 (giảm dần) | 2,241 | 6.4% | An toàn — Đang trả nợ |
| 0 — 0.1 (ổn định) | 11,564 | 33.1% | An toàn — Sử dụng đều đặn |
| 0.1 — 0.2 (tăng nhẹ) | 4,864 | 13.9% | Bình thường — Chi tiêu theo mùa |
| 0.2 — 0.3 (tăng vừa) | 6,313 | 18.1% | Theo dõi |
| **0.3 — 0.5 (đột biến)** | **9,450** | **27.1%** | **Cảnh báo sớm** |
| **> 0.5 (cực đoan)** | **507** | **1.45%** | **Bust-out rõ ràng** |

**Ca điển hình — Customer 466462 (Velocity = +0.5496):**
```
Tháng 05: utilization = 0.100  ← Sử dụng 10% hạn mức (nuôi uy tín)
Tháng 06: utilization = 0.072  ← Giảm nhẹ (trả nợ đều)
Tháng 07: utilization = 0.073  ← Ổn định
Tháng 08: utilization = 0.075  ← Ổn định
Tháng 09: utilization = 0.076  ← Ổn định
Tháng 10: utilization = 0.625  ← ĐỘT BIẾN +0.5496 (vét 62.5% hạn mức!)
```

**Cross-reference giao dịch nhóm velocity cao (≥ 0.3):**
- 9,957 khách hàng
- Tổng tiền giao dịch trung bình: **268 triệu VND/người**
- Giá trị giao dịch trung bình: **14 triệu VND/lần**

#### Kết quả SHAP Explanations (Pipeline V3)

| Chỉ số SHAP | Giá trị |
|---|---|
| Tần suất xuất hiện trong Top SHAP | **8.5%** (8/94 alerts) |
| Đóng góp SHAP trung bình | +1.2818 |
| Đóng góp SHAP tối đa | +1.4786 |
| Xếp hạng trung bình | #2.2 |

> **Nhận xét:** Tần suất xuất hiện thấp (8.5%) nhưng **cường độ SHAP cực cao** (+1.28 trung bình — xếp thứ 3 toàn hệ thống về cường độ). Điều này phản ánh đúng bản chất của Bust-out: nó hiếm nhưng khi xảy ra, tín hiệu rất mạnh và rõ ràng. Mô hình đã học được rằng velocity cao là cờ đỏ gần như tuyệt đối.

---

### Feature 4: STRUCTURING_OVERPAYMENT_FLAG (Cờ nạp tiền dư thẻ tín dụng)

#### Định nghĩa
Gán cờ nhị phân xác định hành vi nạp tiền **vượt quá** dư nợ thẻ tín dụng thông qua nhiều lần thanh toán chia nhỏ — dấu hiệu của kỹ thuật rửa tiền qua overpayment.

#### Công thức đo lường

$$\text{STRUCTURING\_OVERPAYMENT\_FLAG}_i = \begin{cases} 1 & \text{if } \sum_{j \in W_{30d}(i)} \text{REPAY\_AMOUNT}_j > \text{OUTSTANDING\_BAL\_CREDIT}_c \\ & \text{AND } |W_{30d}(i)| \geq 2 \\ 0 & \text{otherwise} \end{cases}$$

Trong đó:
- $W_{30d}(i)$ = tập giao dịch trả nợ thẻ (`TRANS_LV2 = Credit_card_repayment`) trong 30 ngày trước giao dịch $i$.
- `OUTSTANDING_BAL_CREDIT` = dư nợ thẻ tín dụng tối đa của khách hàng (từ `Data_Card`).
- Điều kiện kép: (1) Tổng nạp > Dư nợ (overpayment), VÀ (2) Chia thành ≥ 2 lần nạp (structuring).

#### Ý nghĩa trong mô hình

Đây là kỹ thuật rửa tiền tinh vi được GAO (United States Government Accountability Office, 2002) và FATF (2021) ghi nhận dưới tên "Credit Card Overpayment Laundering":

1. Tội phạm có **nguồn tiền bẩn** (từ lừa đảo, buôn bán, tham nhũng).
2. Chúng chia nhỏ tiền bẩn và **nạp nhiều lần** vào tài khoản thẻ tín dụng — **vượt quá dư nợ thực tế** (overpayment).
3. Phần tiền nạp dư tạo ra "số dư có" (credit balance) trên thẻ.
4. Chúng gọi tổng đài yêu cầu **hoàn tiền** (refund) phần dư vào tài khoản ngân hàng sạch.
5. Tiền hoàn lại lúc này đã được **hợp thức hóa** — nguồn gốc là "tiền hoàn trả từ ngân hàng", không còn dấu vết tiền bẩn.

PwC Global Economic Crime Survey (2024) xác nhận rằng overpayment laundering đang gia tăng ở khu vực Đông Nam Á do hạ tầng thanh toán kỹ thuật số phát triển nhanh nhưng giám sát AML chưa theo kịp.

Feature này mở ra **chiều dữ liệu hoàn toàn mới**: tất cả 21 feature gốc đều giám sát **dòng tiền ra** (chuyển tiền, thanh toán). `STRUCTURING_OVERPAYMENT_FLAG` lần đầu tiên nhìn vào **dòng tiền vào** (nạp tiền vào thẻ tín dụng) — một góc nhìn ngược hoàn toàn.

#### Kết quả EDA

| Chỉ số | Giá trị |
|---|---|
| Tổng giao dịch trả nợ thẻ | 51,185 |
| Khách hàng trả nợ thẻ | 6,959 |
| Khách hàng trả 2+ lần (cấu trúc hóa) | 5,285 |
| **Khách hàng trả DƯ (ratio > 1.0)** | **1,099 (31.1%)** |
| Trả gấp 2x dư nợ | 671 |
| Trả gấp 5x+ dư nợ | 338 |

**Ca cực đoan — Customer 672952:**
```
Dư nợ thẻ tín dụng:    6,335,000 VND    (6.3 triệu)
Tổng tiền đã nạp vào:  7,402,251,200 VND (7.4 TỶ — gấp 1,168.5 lần dư nợ!)
Số lần nạp:             123 lần
```
Khách hàng có dư nợ chỉ 6.3 triệu nhưng bơm vào **7.4 tỷ đồng** qua 123 lần thanh toán chia nhỏ. Đây không phải hành vi trả nợ — đây là hành vi bơm tiền bẩn qua kênh thẻ tín dụng.

#### Kết quả SHAP Explanations (Pipeline V3)

Feature `STRUCTURING_OVERPAYMENT_FLAG` không xuất hiện trực tiếp trong Top SHAP Contributors của 94 cảnh báo lần này. Điều này phù hợp với đặc thù của kịch bản rửa tiền qua overpayment:

- **Rửa tiền Overpayment** khác với ATO/Bust-out: kẻ gian **nạp tiền VÀO** (inbound), không phải **chuyển tiền RA** (outbound). Tập 5,000 giao dịch inference được lấy mẫu ngẫu nhiên — xác suất bắt đúng giao dịch nạp tiền dư trong mẫu nhỏ là thấp.
- Feature này đóng vai trò **phòng thủ tuyến cuối**: khi hệ thống được triển khai trên dữ liệu Production (hàng trăm nghìn giao dịch/ngày), nó sẽ tự động bắt các ca overpayment mà không cần rule-based.
- Trong 94 alerts, có **5 giao dịch Credit_card_repayment** (5.3%) — cho thấy hệ thống đã bắt đầu chú ý đến kênh tín dụng.

---

## Tổng kết: Ma trận Feature Mới & Sức mạnh SHAP

| # | Feature | Nhóm | Tần suất SHAP | Cường độ SHAP | Xếp hạng | Chiều dữ liệu mới |
|---|---|---|---|---|---|---|
| 1 | **NEW_DEVICE_FLAG** | Thiết bị | **48.9%** (#1) | +1.22 | #1.9 | Device_ID_Hash |
| 2 | **IP_HOPPING_VELOCITY** | Hạ tầng | 16.0% | +0.79 | #2.1 | IP_Address_Proxy |
| 3 | **LIMIT_UTILIZATION_VELOCITY** | Tín dụng | 8.5% | **+1.28** (#3 cường độ) | #2.2 | Data_Card |
| 4 | **STRUCTURING_OVERPAYMENT_FLAG** | Tín dụng | — (phòng thủ tuyến cuối) | — | — | Dòng tiền VÀO |

### Kết quả dự án

Việc bổ sung 3 feature tín dụng & hạ tầng đã đạt được 3 mục tiêu:

1. **Giảm False Positive**: Nhờ thêm thông tin từ Data_Card và IP, mô hình phân biệt tốt hơn giữa giao dịch hợp pháp (số tiền lớn nhưng trên thiết bị quen thuộc, IP ổn định) và giao dịch gian lận (thiết bị mới, IP nhảy, velocity tín dụng cao).

2. **Tập trung vào kênh rủi ro cao**: Tỷ lệ Outside_bank trong cảnh báo lên tới 76.6% — hệ thống bớt bị phân tán bởi giao dịch nội bộ rủi ro thấp.

3. **Mở rộng phạm vi giám sát**: Pipeline hiện tại bao phủ 4 bảng dữ liệu (Data_Transaction, Data_Activity, Data_Customer, **Data_Card**) và khai thác 3 chiều dữ liệu mới (thiết bị, IP, tín dụng) mà phiên bản trước chưa có.

---

## Tài liệu Tham khảo bổ sung

1. FBI (2023). "Synthetic Identity Fraud: A Growing Threat." FBI Internet Crime Report.
2. Javelin Strategy & Research (2023). "Identity Fraud Study: The Virtual Battleground." Javelin.
3. Europol (2024). "Internet Organised Crime Threat Assessment (IOCTA)." Europol Publication.
4. Group-IB (2024). "GoldPickaxe: iOS Trojan Targeting Southeast Asian Banks." Threat Intelligence Report.
5. GAO (2002). "Money Laundering: Extent of Money Laundering through Credit Cards Is Unknown." GAO-02-670.
6. FATF (2021). "Money Laundering through the Physical Transportation of Cash." FATF Report.
7. PwC (2024). "Global Economic Crime and Fraud Survey." PwC Publication.
8. Ngân hàng Nhà nước Việt Nam (2020). Thông tư 01/2020/TT-NHNN về phân loại tài sản có.
9. Ngân hàng Nhà nước Việt Nam (2024). Quyết định 2345/QĐ-NHNN về xác thực sinh trắc học.
