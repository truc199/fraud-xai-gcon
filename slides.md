<!-- ============================================================ -->
<!-- SLIDE DECK – Hệ thống Phát hiện Gian lận Ngân hàng Số       -->
<!-- Dùng cú pháp --- để phân tách slide (Marp / Slidev / Reveal) -->
<!-- ============================================================ -->

---

# Hệ thống Phát hiện Gian lận & Bất thường Giao dịch Ngân hàng Số
### Kết hợp ML + Explainable AI (xAI)

---

## Phần I: Mở đầu

---

### 1.1. Bối cảnh dự án

Ngân hàng số (Digital Banking) đối mặt với các nguy cơ bảo mật ngày càng tinh vi: chiếm đoạt tài khoản (ATO), chuyển tiền trái phép, tài khoản rác (Mule Accounts) rửa tiền, giả mạo tham số giao dịch.

**Thực trạng lừa đảo tài chính tại Việt Nam:** Tội phạm công nghệ cao sử dụng AI Deepfake và mã độc di động để chiếm quyền ATO hoặc dùng mạng lưới tài khoản rác trung chuyển dòng tiền bất hợp pháp. Chi phí xử lý hậu quả gian lận trung bình cao gấp **4,36 lần** số tiền tổn thất (LexisNexis). Kẻ gian dụ dỗ nạn nhân cài mã độc giả mạo cơ quan công quyền → chiếm quyền Accessibility Service → đọc OTP, thu thập đăng nhập → bypass bảo mật → đổi mật khẩu/PIN → rút cạn tiền → tẩu tán qua Structuring/Smurfing và mạng lưới tài khoản rác.

Ngân hàng Nhà nước ban hành **Quyết định 2345/QĐ-NHNN** (01/7/2024): bắt buộc xác thực sinh trắc học trùng CCCD gắn chip cho giao dịch ≥ 10 triệu/lần hoặc tổng dồn ≥ 20 triệu/ngày. Hệ thống **SIMO** chia sẻ danh sách đen giữa các TCTD. Các NHTM triển khai AI phân tích hành vi real-time.

**Hạn chế của hệ thống Rule-based truyền thống:**
- Tỷ lệ báo động giả (False Positive) cao → phiền hà khách hàng hợp pháp, rủi ro pháp lý.
- Khả năng bỏ sót (False Negative) lớn với hành vi gian lận mới, biến đổi liên tục (Behavioral Drift).

**Xu hướng ứng dụng ML + xAI:** Xây dựng hệ thống phát hiện bất thường tự động dựa trên AI kết hợp khả năng giải thích (xAI) giúp quản trị rủi ro chủ động và hiệu quả hơn.

---

### 1.2. Mục tiêu dự án

Khai thác bộ dữ liệu mẫu (thông tin khách hàng, lịch sử giao dịch, hành vi sử dụng dịch vụ số) để thử nghiệm giải pháp Fraud & Anomaly Detection. Mục đích cốt lõi: ứng dụng ML kết hợp giải thích hành vi → phát hiện giao dịch bất thường, giảm thiểu rủi ro bảo mật, xây dựng hệ thống cảnh báo sớm.

Bốn nhiệm vụ trọng tâm:

- **Phát hiện giao dịch nghi vấn:** Tự động nhận diện giao dịch đáng ngờ real-time qua phân tích dòng tiền, hành vi cá nhân, thói quen thiết bị và đặc trưng tương tác phi tuyến (tỷ lệ bao phủ số dư, tần suất cấp tập, Geovelocity).
- **Giảm False Positive & xAI:** Ứng dụng TreeSHAP trích xuất đặc trưng đóng góp chính → chuyển đổi thành văn bản giải trình ngôn ngữ tự nhiên, hỗ trợ chuyên viên rủi ro quyết định nhanh chóng.
- **Counterfactual Recourse:** Tìm kiếm thay đổi tối thiểu đối với thuộc tính giao dịch để đưa giao dịch hợp lệ trở về trạng thái an toàn.
- **Bảo vệ uy tín & niềm tin:** Ứng dụng EWC (Elastic Weight Consolidation) để cập nhật mô hình thích ứng trước concept drift mà không suy giảm hiệu năng nhận diện gian lận lịch sử.

---

### 1.3. Phạm vi & Hướng tiếp cận

**Lựa chọn Hướng 1: Fraud & Anomaly Detection.** Xây dựng pipeline xử lý 5 phase:

| Phase | Nội dung |
| :---- | :---- |
| Phase 1 | Data Extraction — Trích xuất và liên kết dữ liệu thô từ nhiều nguồn |
| Phase 2 | Feature Engineering — Tính toán ~46 đặc trưng số hóa |
| Phase 3 | PU Learning — Huấn luyện mô hình khi không có nhãn gian lận |
| Phase 4 | Tiered Inference — Suy luận phân tầng 3 lớp kết hợp xAI |
| Phase 5 | EWC — Học liên tục chống quên thảm họa |

> **Gợi ý biểu đồ:**
> - Sơ đồ kiến trúc pipeline (Flowchart): Luồng xử lý 5 phase từ Data Extraction → Feature Engineering → PU Learning → Tiered Inference → EWC, thể hiện đầu vào/đầu ra của mỗi phase.

---

### 1.4. Dữ liệu sử dụng

Bộ dữ liệu mẫu gồm 6 bảng liên kết, quy mô ~20 triệu bản ghi:

| Bảng dữ liệu | Số bản ghi | Mô tả |
| :---- | :---- | :---- |
| Customer | 290.223 | Hồ sơ khách hàng cá nhân (nhân khẩu học, nghề nghiệp, ngày đăng ký) |
| Transaction | 1.418.030 | Giao dịch chuyển tiền (P2P, thanh toán, nạp ví) |
| Activity | 16.132.675 | Nhật ký hoạt động ứng dụng (đăng nhập, thao tác) |
| Deposit | 1.258.424 | Thông tin tiền gửi |
| Lending | 576.431 | Bản ghi dư nợ cho vay theo tháng |
| Card | 871.589 | Bản ghi thẻ tín dụng |

---

## Phần II: Phân tích Khám phá Dữ liệu (EDA)

Trích xuất số liệu thống kê tổng quan từ bộ dữ liệu mẫu, làm tiền đề xây dựng mô hình phát hiện hành vi bất thường.

---

### 2.1. Tổng quan quy mô & cấu trúc dữ liệu

**Số lượng bản ghi:** 1.418.030 giao dịch từ 46.204 khách hàng duy nhất có hoạt động P2P, trên nền tảng 290.223 hồ sơ đăng ký. Tỷ lệ kích hoạt dịch vụ chỉ **18,1%** (52.488/290.223), còn lại 81,9% bất hoạt.

**Phân bố giao dịch theo thời gian:**
- *Theo giờ:* Trung bình 1,03 GD/giờ, p99 = 2 GD/giờ. Bất kỳ tài khoản nào đạt 3 GD/giờ đã nằm ngoài top 1%.
- *Theo ngày:* 99% KH chỉ thực hiện tối đa 11 lệnh/ngày.
- *Theo ngày trong tuần:* Mật độ tập trung cao ngày giữa tuần (T2–T6), khung 8h–17h. Khung 00h–05h ghi nhận 46.449 GD ban đêm, trong đó 2.155 GD > 5 triệu VND từ tài khoản hiếm khi hoạt động giờ này → vùng cần giám sát đặc biệt.

**Chất lượng tài sản tín dụng:** 576.431 bản ghi dư nợ và 871.589 bản ghi thẻ tín dụng. 17.665 KH có nợ quá hạn, trong đó 2.593 KH hoạt động trong mạng P2P → nhóm "neo rủi ro" phơi nhiễm nợ xấu lan truyền qua mạng lưới chuyển tiền.

> **Gợi ý biểu đồ:**
> - Biểu đồ thanh so sánh: Số lượng khách hàng đăng ký vs. khách hàng thực sự phát sinh giao dịch (290.223 vs. 46.204), tỷ lệ kích hoạt dịch vụ.
> - Biểu đồ heatmap theo giờ × ngày trong tuần: Mật độ giao dịch theo `TRANS_HOUR` × `DAY_OF_WEEK`, làm nổi bật vùng đêm khuya (00h – 05h).
> - Biểu đồ phễu (Funnel chart): 290.223 khách hàng → 17.665 có nợ quá hạn → 2.593 hoạt động trong mạng P2P, thể hiện mức độ lọc rủi ro theo tầng.

---

### 2.2. Phân tích phân bố giao dịch

**Phân bố số tiền giao dịch (skewness/heavy tail):** Phân phối lệch phải cực đoan. Hơn 50% KH giao dịch ở mức 640.000 VND/lệnh. Top 5% vọt lên 38 triệu, top 1% đạt 163 triệu, cá biệt 2,458 tỷ VND. Chênh lệch p50 ↔ p99: **255 lần**. Tổng dòng tiền 30 ngày: bình thường ~17,9 triệu, top 5% chạm 977,7 triệu/tháng.

**Phân bố theo loại giao dịch:** P2P chiếm 69,7% (989.006 GD). Còn lại: cước viễn thông (Vinaphone 59.446, Mobifone 59.403, Viettel 58.963) và nạp ví (ShopeePay 42.741).

**Phân bố theo thiết bị iOS/Android/Web:** iOS 54,39%, Android 40,16%, Web 5,45%. Hệ sinh thái đồng nhất cao. Đăng nhập sinh trắc học (FaceID/vân tay) chiếm ~22%.

**Phân bố địa lý:** Hà Nội (478.915 GD, 21.621 KH) và TP.HCM (417.417 GD, 19.325 KH). Đô thị loại hai: Đà Nẵng 139.878, Hải Phòng 99.558, Cần Thơ 80.058, Bình Dương 71.776. 64.262 IP được dùng chung bởi nhiều KH (cao nhất 45 KH/IP) — đặc thù IP động nhà mạng di động VN.

> **Gợi ý biểu đồ:**
> - Biểu đồ histogram log-scale: Phân bố giá trị giao dịch (`TRANS_AMOUNT`), đánh dấu các phân vị p50, p95, p99.
> - Biểu đồ thanh xếp chồng (Stacked bar chart): Khối lượng giao dịch phân theo kênh (`BANK_TRANSFER_GATEWAY`, `TELCO_*`, `SHOPEEPAY`, khác).
> - Biểu đồ boxplot: So sánh phân phối giá trị giao dịch giữa các kênh.
> - Biểu đồ donut: Tỷ trọng hệ điều hành (iOS / Android / Web).
> - Biểu đồ thanh ngang: Top 10 tỉnh/thành phố theo khối lượng giao dịch và số lượng khách hàng.

---

### 2.3. Phân tích hành vi theo nhóm khách hàng (Cohort)

**Phân tích theo nhóm nghề nghiệp:** Sinh viên có p99 đạt 257,5 triệu VND, cao hơn doanh nhân (159,4 triệu) và công chức (140,1 triệu). Hưu trí p99 = 495 triệu. Tài khoản phân khúc thu nhập thấp có thể bị lợi dụng làm tài khoản trung chuyển dòng tiền.

| Nhóm nghề nghiệp | Phân vị p99 số tiền giao dịch (VND) |
| :---- | :---- |
| STUDENT | **257.551.350** |
| PENSIONER | **495.080.000** |
| UNEMPLOYED | **149.692.566** |
| COMMERCIAL ASSOCIATE | 188.000.000 |
| WORKING | 161.500.000 |
| BUSINESSMAN | 159.444.000 |
| STATE SERVANT | 140.124.000 |

**Phân tích theo nhóm tuổi:** 394 GD > 38 triệu VND bởi KH dưới 18 hoặc trên 70 tuổi — hai nhóm có năng lực tài chính và giám sát hạn chế.

**Phân tích theo thời gian hoạt động tài khoản:** Trong 27.352 GD phát sinh 7 ngày đầu sau mở tài khoản, 2.357 GD (8,62%) > 50 triệu VND (tỷ lệ nền ~1%) → mẫu hành vi gian lận có tổ chức: mở tài khoản → nhận tiền → rút cạn. Thêm 2.201 KH (4,2%) bỏ trống tài khoản > 90 ngày rồi đột ngột kích hoạt (có tài khoản ngưng tới 357 ngày).

> **Gợi ý biểu đồ:**
> - Bar chart: Phân vị p99 số tiền giao dịch theo từng nhóm nghề nghiệp, tô đậm STUDENT, UNEMPLOYED, PENSIONER.
> - Histogram: Phân bố độ tuổi khách hàng thực hiện giao dịch > 38.000.000 VND, đánh dấu hai vùng cực đoan (< 18 và > 70).
> - Scatter plot: `TENURE_DAYS` (số ngày tuổi tài khoản, trục X) × `TRANS_AMOUNT` (trục Y), zoom vào vùng ≤ 7 ngày.

---

### 2.4. Phân tích chuỗi hoạt động & sự kiện bảo mật

**Tần suất đổi mật khẩu/PIN:** 111.835 sự kiện bảo mật (đổi mật khẩu, PIN, cập nhật sổ địa chỉ). 14.172 lệnh rút tiền lớn (1% tổng GD) xảy ra trong 24 giờ sau sự kiện bảo mật. Đặc biệt ~1.200 GD diễn ra chưa đầy 1 giờ sau đổi thông tin — khả năng ATO rút tiền tức thì.

| Chỉ số | Giá trị | % |
| :---- | :---- | :---- |
| Tổng sự kiện bảo mật | 111.835 | — |
| GD trong 24h sau sự kiện bảo mật | 14.172 | 1,00% |
| GD cửa sổ ≤ 1 giờ | ~1.200 | — |
| Login Drift alerts | 2.364 | 0,17% |

**Hạ cấp phương thức bảo mật:** 2.364 GD (0,17%) — KH quen dùng FaceID/vân tay (>50% đăng nhập) đột ngột chuyển sang mật khẩu tĩnh ngay trước lệnh chuyển tiền.

**Phân bố hoạt động đăng nhập/chuyển tiền — cơ sở thiết kế feature:**
- *Giao dịch ban đêm bất thường:* 46.449 GD ban đêm (00h–05h), 2.155 GD > 5 triệu VND từ KH có tỷ lệ thức đêm < 5%. 601 KH chuyển tiền 100% chỉ vào giữa đêm.
- *Tốc độ giao dịch bất thường:* Ngưỡng bất thường: 3 lệnh/giờ, 6 lệnh/giờ, 34 lệnh/ngày. Quy mô lệnh vọt gấp 3,48×, 6,89×, thậm chí 82,65× thói quen.
- *Thiết bị bất thường:* 8.227 GD (0,58%) đổi OS thiết bị trong 24h. 42.449 GD (3%) Impossible Travel — hai lệnh liên tiếp từ hai tỉnh/thành < 1 giờ.

Các dấu hiệu trên là cơ sở thiết kế feature: `HOURS_SINCE_SEC_EVENT`, `HIST_BIOMETRIC_RATIO`, `NIGHT_ANOMALY`, `VELOCITY_RATIO_*`, `ACTIVITY_SEQ_RARITY`.

> **Gợi ý biểu đồ:**
> - Histogram: Phân bố `HOURS_SINCE_SEC_EVENT` cho các giao dịch xảy ra sau sự kiện bảo mật, đánh dấu ngưỡng 1 giờ và 24 giờ.
> - Stacked bar chart: Phân loại sự kiện bảo mật (CHANGE_PASSWORD, SET_PIN, ADDRESS_BOOK_UPDATE) theo số lượng, kèm tỷ lệ dẫn tới giao dịch bất thường trong 24h.
> - Heatmap giờ × ngày trong tuần: Mật độ giao dịch, tô đậm vùng 00h – 05h.
> - Histogram log-scale: Phân bố `COUNT_1H` và `COUNT_24H`, đánh dấu ngưỡng p99 và vùng bất thường.

---

### 2.5. Nhận định chung về tình hình hoạt động của ngân hàng

Bộ dữ liệu phản ánh ngân hàng số bán lẻ hoạt động tích cực, ổn định nhưng tiềm ẩn rủi ro cấu trúc.

**Các chỉ số tích cực:**
- Nền tảng KH đa dạng: 290.223 hồ sơ, nhiều phân khúc nghề nghiệp/tuổi.
- Dòng tiền dồi dào: hơn 1,4 triệu GD, P2P chi phối 69,7%.
- Số hóa khả quan: 16 triệu bản ghi hoạt động, sinh trắc học 22%.
- Phân bố địa lý cân đối: Hà Nội & TP.HCM + các đô thị vệ tinh.

**Các chỉ số cần cảnh báo:**
- *Tỷ lệ kích hoạt dịch vụ thấp:* Chỉ 18,1% KH phát sinh GD. 81,9% bất hoạt — rủi ro Mule Account.
- *Chất lượng tín dụng xuống cấp:* 17.665 KH (6,1%) nợ quá hạn, 2.593 KH vừa nợ xấu vừa hoạt động P2P.
- *Tỷ lệ sinh trắc học thấp:* 78% KH phụ thuộc mật khẩu tĩnh — nguy cơ phishing, mã độc.
- *Phân phối lệch phải cực đoan:* Chênh lệch p50 ↔ p99 = 255 lần → cần mô hình phân cụm (cohort) thay vì ngưỡng chung.

> **Gợi ý biểu đồ:**
> - Biểu đồ radar (Spider chart): Tổng hợp 5 trục đánh giá (Quy mô khách hàng, Thanh khoản dòng tiền, Chất lượng tín dụng, Mức độ số hóa, Độ phủ địa lý) trên thang điểm chuẩn hóa.
> - Biểu đồ waterfall: Phân rã 290.223 khách hàng thành các nhóm: hoạt động bình thường → nợ quá hạn → ngủ đông → nghi vấn gian lận.

---

### 2.6. Nhận định về giới hạn của bộ dữ liệu

Một số giới hạn cấu trúc ảnh hưởng trực tiếp đến độ tin cậy mô hình ML.

**1. Không có nhãn gian lận (Zero Fraud Labels):** `confirmed_frauds.json` rỗng.
- Không thể supervised learning truyền thống.
- PU Learning phải dựa nhãn proxy từ Isolation Forest → vòng lặp giả định không thể kiểm chứng.
- Không có test set với nhãn thật để đo precision/recall.

**2. Toàn bộ dữ liệu chỉ trong 1 năm (2019):**
- Không có baseline dài hạn, không so sánh seasonal patterns qua các năm.
- `TENURE_DAYS` bị nén trong 0–365 ngày (thực tế tài khoản có thể tồn tại 10–20 năm).

**3. Khối lượng giao dịch tăng trưởng bất thường:** Tháng 1 (3.203) chỉ bằng 1% tháng 12 (323.689) — tăng 100× cùng năm. Survivorship bias → velocity ratio bị sai lệch ở đầu năm.

| Tháng | Số giao dịch | % so với tháng 12 |
| :---- | :---- | :---- |
| 01/2019 | 3.203 | 1,0% |
| 06/2019 | 74.970 | 23,2% |
| 09/2019 | 172.971 | 53,4% |
| 12/2019 | 323.689 | 100% |

**4. Thiếu hụt thông tin xác thực (45% null):**
- `IB_REGISTER_DATE`: 131.248/290.223 (45,22%) null.
- `VERIFY_METHOD`: 131.276/290.223 (45,23%) null.
- Giảm khả năng phát hiện Login Drift — chỉ báo quan trọng nhất cho ATO.

**5. Phân phối giao dịch lệch phải cực đoan (Heavy-Tailed):** 54,2% < 1 triệu, chỉ 4% ≥ 50 triệu. Chênh mean/median = 13,7×. ML dễ bias giao dịch nhỏ; GD lớn hợp lệ bị coi là outlier; Z-score mất phân giải ở đuôi phân phối.

| Khoảng giá trị | Số giao dịch | Tỷ lệ |
| :---- | :---- | :---- |
| < 1 triệu VND | 768.629 | 54,2% |
| 1M – 10M VND | 455.093 | 32,1% |
| 10M – 50M VND | 137.243 | 9,7% |
| ≥ 50 triệu VND | 57.065 | 4,0% |

**6. Thiếu thông tin địa lý thực và thiết bị chi tiết:** Chỉ có `IP_Address_Proxy` (mã hóa tỉnh/thành) và `Device_ID_Hash`. Không có GPS, device fingerprint chi tiết, phân loại IP (VPN/Tor/Residential/Datacenter).

**Định hướng tiếp cận:** Không có nhãn gian lận + heavy-tailed → ML thuần túy không đảm bảo tin cậy → định hướng **rule-based có cơ sở thống kê** (từ EDA 2.1–2.4), kết hợp ML ở vai trò hỗ trợ.

> **Gợi ý biểu đồ:**
> - Histogram log-scale: Phân bố `TRANS_AMOUNT` với đánh dấu mean, median, p95, p99 — thể hiện heavy tail.
> - Bar chart: Khối lượng giao dịch theo tháng (01–12/2019), thể hiện sự tăng trưởng bất thường 100x.
> - Stacked bar: Tỷ lệ null/non-null của `IB_REGISTER_DATE` và `VERIFY_METHOD` trên tổng khách hàng.
> - Pie chart: Phân bố giao dịch theo khoảng giá trị (<1M, 1M–10M, 10M–50M, ≥50M).

---

## Phần III: Trích xuất & Kỹ thuật Đặc trưng (Phase 1-2)

Chuyển hóa dữ liệu thô thành tín hiệu rủi ro định lượng qua hai giai đoạn, tạo bộ ~46 đặc trưng số hóa.

---

### 3.1. Trích xuất dữ liệu thô (Phase 1 — Data Extraction)

Tính toán thống kê tích lũy và kết nối dữ liệu từ 6 bảng CSDL.

| Mục | Hạng mục Trích xuất | Đặc trưng / Tính toán | Ý nghĩa & Dấu hiệu Gian lận |
| :--- | :--- | :--- | :--- |
| 3.1.1 | Nối các nguồn dữ liệu | Nối `Data_Transaction` với `Data_Customer`, `Activity`, `Deposit` (theo `ts_dt`) | Bức tranh toàn cảnh hoạt động khách hàng |
| 3.1.2 | Tổng hợp cửa sổ trượt | `SUM_AMOUNT`, `COUNT` trên 6 cửa sổ: 1h, 3h, 24h, 48h, 7d, 30d | Bắt tín hiệu tiêu tiền bất thường, GD dồn dập (Card testing, Bot) |
| 3.1.3 | Thống kê lịch sử KH | `HIST_AVG_CA_BALANCE`, `HIST_AVG_TRANS_AMOUNT` | Baseline cá nhân để đánh giá độ lệch GD hiện tại |
| 3.1.4 | Khoảng cách thời gian GD | `DAYS_SINCE_LAST_TRANS` (số ngày từ GD trước) | Nhận diện tài khoản "ngủ đông thức dậy" |
| 3.1.5 | Người thụ hưởng 24h | `UNIQUE_BENEFICIARIES_24H` (số tài khoản đích) | Phân tán dòng tiền nhanh (Mule Fan-out) |
| 3.1.6 | Thời gian tới sự kiện bảo mật | `HOURS_SINCE_SEC_EVENT` (từ lần đổi PIN/Pass gần nhất) | < 1h cảnh báo ATO |
| 3.1.7 | Thống kê Sinh trắc học | `HIST_BIOMETRIC_RATIO` (tỷ lệ dùng FaceID/Vân tay) | Phát hiện hạ cấp bảo mật |
| 3.1.8 | Phân tích Benford's Law | `BENFORD_DEV` (KL-Divergence, ngưỡng N ≥ 5) | Đánh giá độ phân kỳ chữ số đầu tiên so với quy luật tự nhiên |
| 3.1.9 | Chuỗi Markov bậc 2 | `ACTIVITY_SEQ_RARITY` (nội suy backoff trên chuỗi thao tác) | Hành vi điều hướng hiếm gặp hoặc bot tự động |

---

### 3.2. Xây dựng bộ lọc rule-based (5 loại rule)

Dựa trên EDA, xây dựng 6 Rule cho Hierarchical Routing Pipeline tại Tier 1. Mục tiêu: **BLOCK** ngay GD rủi ro cực cao (Smoking gun), **BYPASS** GD rủi ro cực thấp nhằm giảm tải ML ở Tier 2.

**1. DormancyWakeupRule (🔴 BLOCK)**
* **Nội dung rule:** `DAYS_SINCE_LAST_TRANS > 90` AND `TRANS_AMOUNT > 10,000,000` AND `TRANS_LV2 = 'Outside_bank'`
* **Cơ sở:** Tội phạm thu mua tài khoản, để "ngủ đông" 3-6 tháng trốn giám sát, rồi đột ngột kích hoạt chuyển tiền bẩn ra ngoài.
* **EDA:** Chỉ 867 GD (0,06%) vi phạm → FP cực thấp.

**2. ATOPanicRule (🔴 BLOCK)**
* **Nội dung rule:** `HOURS_SINCE_SEC_EVENT <= 1.0` AND `TRANS_AMOUNT > 10,000,000` AND `TRANS_LV2 = 'Outside_bank'`. Chặn (Fraud) nếu customer tenure (tuổi tài khoản) $\ge$ 1 ngày; chuyển về diện Nghi vấn (Ambiguous -1) nếu tenure < 1 ngày.
* **Cơ sở:** Chặn hành vi chiếm đoạt tài khoản (ATO) kinh điển. Loại trừ tài khoản mới tạo hoạt động trong ngày đầu (tenure < 1 ngày) sang diện nghi vấn để xử lý mềm thay vì chặn cứng.
* **EDA:** ~1.200 giao dịch trong cửa sổ 1 giờ sau đổi xác thực. Phân nhóm theo tenure giúp giảm thiểu ảnh hưởng đến hành trình đăng ký/kích hoạt của người dùng mới.

**3. HourlyAnomalyRule (🔴 BLOCK)**
* **Nội dung rule:** `TRANS_HOUR_PROB < 0.015` AND `TRANS_AMOUNT > 10,000,000`
* **Cơ sở:** Chặn các giao dịch phát sinh đột xuất vào khoảng thời gian mà lịch sử khách hàng rất ít hoạt động (xác suất < 1.5%), kết hợp số tiền lớn (> 10 triệu) mang dấu ấn của tội phạm ATO thực hiện rút tiền gấp gáp bất kể ngày đêm.
* **EDA:** Rất hiếm khi khách hàng bình thường chuyển tiền lớn vào những khung giờ lạ của chính họ.

**4. LowRiskChannelBypassRule (🟢 BYPASS)**
* **Nội dung rule:** `TRANS_LV2 IN ('Utilities_payment', 'Credit_card_repayment', 'Lending_repayment', 'Cable', 'Game', 'Lifestyle_payment', 'MCPP')` AND `TRANS_AMOUNT < 5,000,000`
* **Cơ sở:** Kẻ gian không dùng tiền ăn cắp thanh toán hóa đơn/trả nợ thẻ cho nạn nhân.
* **EDA:** Lọc ~14.000 GD/ngày. Ngưỡng 5M (thay vì 10M) đề phòng Structuring Overpayment.

**5. SequenceRarityRule (🟢 BYPASS)**
* **Nội dung rule:** `ACTIVITY_SEQ_RARITY > -1.0` AND `TRANS_AMOUNT < 500,000`
* **Cơ sở:** Chuỗi hành động điển hình + GD nhỏ → rủi ro gần bằng 0.
* **EDA:** Markov bậc 2 cho thấy đa phần GD sinh hoạt đi theo luồng thao tác quen thuộc. 54,2% GD < 1 triệu.

**6. VelocityBypassRule (🟢 BYPASS)**
* **Nội dung rule:** `TRANS_AMOUNT < 500,000` AND `COUNT_1H <= 1` AND `COUNT_24H <= 2`
* **Cơ sở:** Tần suất thưa + quy mô nhỏ → không phải Card Testing hay Mule Fan-out.
* **EDA:** Trung bình 1,03 GD/giờ, 99% KH ≤ 11 lệnh/ngày. Kẻ gian thường 3-6 lệnh/giờ.

---

### 3.3. Kỹ thuật đặc trưng (Phase 2 — Feature Engineering)

`AdvancedPreprocessor` tổng hợp thành ratios, z-scores, interaction features → khắc phục heavy-tailed, thiết lập cơ sở nhận diện bất thường. Tạo bộ **25 đặc trưng, 8 nhóm chức năng**.

#### Nhóm 1: Lệch chuẩn Số tiền (Amount Deviation)

Cá nhân hóa rủi ro theo từng KH thay vì ngưỡng tuyệt đối — giải quyết chênh lệch thu nhập giữa các phân khúc.

| Tên Đặc trưng | Định nghĩa | Measurement | Ý nghĩa trong mô hình |
| :--- | :--- | :--- | :--- |
| `TRANS_AMOUNT_Z_SCORE` | Mức độ bất thường số tiền GD so với lịch sử chi tiêu cá nhân | `TRANS_AMOUNT / (HIST_AVG_TRANS_AMOUNT + ε)` | ATO rút tối đa → Z-Score đột biến. Z-Score cá nhân tránh FP ở nhóm thu nhập thấp. |
| `BALANCE_COVERAGE_RATIO` | Tỷ lệ số tiền GD / số dư trung bình lịch sử | `TRANS_AMOUNT / (HIST_AVG_CA_BALANCE + ε)` | Money Mule (FATF, 2021): ratio > 1.0 = "rút cạn" / trung chuyển. |
| `TRANS_AMOUNT_VS_30D_AVG_RATIO` | So sánh GD hiện tại với chi tiêu trung bình 30 ngày | `TRANS_AMOUNT / (SUM_AMOUNT_30D / (COUNT_30D + ε) + ε)` | Bộ lọc thích ứng: KH tăng lương → ratio thấp → tránh FP. Cảnh báo thường > 5.0. |

---

#### Nhóm 2: Tốc độ & Tần suất (Velocity)

Đo mức tập trung dòng tiền/số lượng GD vào thời gian ngắn. Chuỗi 3 tầng (1H→24H→7D→30D) chống kỹ thuật lách.

| Tên Đặc trưng | Định nghĩa | Measurement | Ý nghĩa trong mô hình |
| :--- | :--- | :--- | :--- |
| `VELOCITY_RATIO_AMOUNT` (1H/24H, 24H/7D, 7D/30D) | Mức tập trung dòng tiền vào cửa sổ ngắn nhất. Ratio → 1.0 = tất cả đổ dồn. | `SUM_AMOUNT_1H / (SUM_AMOUNT_24H + ε)`, tương tự cho 24H/7D, 7D/30D | Cash-out: ratio > 0.95 = rút toàn bộ tài sản. |
| `VELOCITY_RATIO_COUNT` (1H/24H, 24H/7D, 7D/30D) | Tương tự nhưng đo số lượng GD thay vì số tiền. | `COUNT_1H / (COUNT_24H + ε)`, tương tự cho 24H/7D, 7D/30D | 34% gian lận bắt đầu bằng micro-transaction testing (PwC, 2024). Velocity amount không phản ứng, nhưng count đột biến. |

---

#### Nhóm 3: Hành vi Thời gian & Ngủ đông (Temporal & Dormancy)

Khai thác khoảng im lặng, giờ GD, hành vi ban đêm → phát hiện tài khoản ngủ đông bị kích hoạt và tấn công theo khung giờ.

| Tên Đặc trưng | Định nghĩa | Measurement | Ý nghĩa trong mô hình |
| :--- | :--- | :--- | :--- |
| `DAYS_SINCE_LAST_TRANS` | Số ngày im lặng giữa GD hiện tại và GD trước. | `(t_i − t_{i−1}) / 86400`. Mặc định 999. | Tội phạm thu mua tài khoản → "ngủ đông" 3-6 tháng (Europol, 2023). Giá trị cao + GD lớn → mule account. |
| `DAYS_AMOUNT_COMBINED` | Interaction feature: Im lặng càng lâu + Chuyển càng nhiều = Rủi ro càng cao. | `ln(1 + DAYS_SINCE_LAST_TRANS) × ln(1 + TRANS_AMOUNT)` | Tổ hợp tạo tín hiệu phi tuyến mạnh. Bình thường < 30; cảnh báo > 40. |
| `TRANS_HOUR` | Giờ GD (0-23), biến kiểm soát thời gian. | `hour(TRANS_DATE)` | GD ban đêm + tín hiệu rủi ro khác → SHAP đơn lẻ cao nhất (+3.50 trung bình). |
| `NIGHT_ANOMALY` | Mức bất thường GD ban đêm (0h-5h) so với thói quen đêm cá nhân. | `IS_NIGHT × (1 − HIST_NIGHT_RATIO)` | Frictionless Security: KH quen đêm (bác sĩ, tài xế) → HIST_NIGHT_RATIO cao → vô hiệu hóa cảnh báo. |

---

#### Nhóm 4: An ninh & Xác thực (Security & Authentication)

Khai thác nhật ký sự kiện bảo mật và lịch sử sinh trắc học → dấu vân tay ATO.

| Tên Đặc trưng | Định nghĩa | Measurement | Ý nghĩa trong mô hình |
| :--- | :--- | :--- | :--- |
| `HOURS_SINCE_SEC_EVENT` | Khoảng cách (giờ) từ GD đến sự kiện bảo mật gần nhất. Càng gần 0 → ATO càng cao. | `(t_tx − t_last_sec) / 3600`. Mặc định 999. | >70% ATO chuyển tiền trong 60 phút sau đổi mật khẩu/PIN (Javelin, 2023). |
| `SEC_AMOUNT_COMBINED` | "Đổi mật khẩu gần + Chuyển tiền lớn = ATO." | `ln(1 + TRANS_AMOUNT) / (ln(1 + HOURS_SINCE_SEC_EVENT) + ε)` | 99% GD score < 5.0; nhóm ATO > 10.0. |
| `HIST_BIOMETRIC_RATIO` | Tỷ lệ đăng nhập sinh trắc học trong lịch sử. Biến kiểm soát. | `Σ login_biometric / (total_logins + ε)` | KH 99% FaceID → hôm nay Password + thiết bị lạ → ATO. |

---

#### Nhóm 5: Phân tích Thống kê & Chuỗi (Statistical & Sequence)

Định luật Benford và Markov bậc 2 → phát hiện cấu trúc hóa GD và luồng thao tác bất thường.

| Tên Đặc trưng | Định nghĩa | Measurement | Ý nghĩa trong mô hình |
| :--- | :--- | :--- | :--- |
| `BENFORD_DEV` | Độ lệch phân bố chữ số đầu tiên so với Benford. Chỉ tính khi KH ≥ 50 GD. | KL-Divergence: `D_KL(P ‖ Q)` với `q_d = log₁₀(1 + 1/d)` | Structuring: chia nhỏ 9.9M, 9.8M né ngưỡng 10M → lệch nghiêm trọng. Hợp pháp < 0.05; structuring > 0.15. |
| `ACTIVITY_SEQ_RARITY` | Mức hiếm chuỗi hoạt động kỹ thuật số. Markov bậc 2 + nội suy backoff. | `P_interp = 0.7·P_2nd + 0.2·P_1st + 0.1·P_global`. Score = trung bình log-prob. | Bình thường: LOGIN→QUERY→TRANSFER→LOGOUT. Bất thường: LOGIN→PASSWORD_CHANGE→TRANSFER_OUTSIDE→LOGOUT. |

---

#### Nhóm 6: Phân loại & Nhân khẩu (Categorical & Demographic)

Cohort Baseline — phân tầng rủi ro theo nhân khẩu học và kênh GD thay vì ngưỡng chung.

| Tên Đặc trưng | Định nghĩa | Measurement | Ý nghĩa trong mô hình |
| :--- | :--- | :--- | :--- |
| `AGE_GROUP` & `Occupation_Group` | Phân nhóm tuổi (Young, Middle, Old) và nghề nghiệp. | Label Encoding. | Sinh viên, người già dễ bị lừa bán tài khoản Mule (NHNN TT09/2020). GD 100M của sinh viên thất nghiệp rủi ro cao hơn doanh nhân. |
| `TRANS_LV1` & `TRANS_LV2` | Phân loại 2 tầng: Transfer/Payment; Within_bank/Outside_bank. | Label Encoding. | Outside_bank rủi ro cao nhất (tiền rời hệ thống gốc không thể thu hồi). 35% GD nhưng 76,6% cảnh báo. |
| `CUSTOMER_AGE` & `TENURE_DAYS` | Tuổi KH tại thời điểm GD; số ngày từ khi tạo tài khoản. | `year(t_tx) − year(DOB)` và `t_tx − t_creation` | Tài khoản mới (tenure thấp) + GD lớn = rủi ro cao: mở/mua tài khoản → dùng trong 30 ngày → bỏ. |

---

#### Nhóm 7: Thiết bị & Hạ tầng kỹ thuật (Device & Infrastructure)

Khai thác `Device_ID_Hash` và `IP_Address_Proxy` — chiều dữ liệu chưa bao phủ bởi các nhóm trước.

| Tên Đặc trưng | Định nghĩa | Measurement | Ý nghĩa trong mô hình |
| :--- | :--- | :--- | :--- |
| `NEW_DEVICE_FLAG` | GD trên thiết bị KH chưa từng dùng. | `1` nếu `cumcount = 0`; `0` nếu ngược lại. | >80% ATO bắt đầu từ thiết bị mới (Javelin, 2023). Xuất hiện gấp 2.8× trong nhóm cảnh báo (48,9% vs 17,5%). |
| `IP_HOPPING_VELOCITY` | Số IP duy nhất mà một thiết bị dùng trong 3 giờ. | Đếm IP duy nhất trong `W_3h` trên cùng Device_ID_Hash. | Proxy rotation (> 3 IP/3h). Mã độc GoldPickaxe (Group-IB, 2024) nhắm NHTM Việt Nam có khả năng xoay IP tự động. |

---

#### Nhóm 8: Tín dụng & Cấu trúc hóa Giao dịch (Credit & Structuring)

Khai thác `Data_Card` — mở rộng giám sát từ "giao dịch" sang "tín dụng", nhìn vào dòng tiền vào (inbound).

| Tên Đặc trưng | Định nghĩa | Measurement | Ý nghĩa trong mô hình |
| :--- | :--- | :--- | :--- |
| `LIMIT_UTILIZATION_VELOCITY` | Tốc độ tăng tỷ lệ sử dụng hạn mức thẻ tín dụng (MoM). | `velocity = utilization_t − utilization_{t−1}`; lấy max toàn lịch sử. | Bust-out (FBI, 2023 — $6B/năm): nuôi uy tín 3-6 tháng (5-10%) → vét sạch hạn mức 1 tháng (velocity > +0.5) → biến mất. 507 KH (1,45%) > 0.5. |
| `STRUCTURING_OVERPAYMENT_FLAG` | Nạp tiền vượt dư nợ thẻ tín dụng qua nhiều lần chia nhỏ. | `1` nếu `Σ REPAY_AMOUNT_30d > OUTSTANDING_BAL` VÀ `số lần nạp ≥ 2`. | Credit Card Overpayment Laundering (FATF, 2021): chia nhỏ tiền bẩn nạp vượt dư nợ → tạo "số dư có" → yêu cầu hoàn tiền → hợp thức hóa. 1.099 KH (31,1% nhóm có thẻ). |

#### Tổng kết Biến đổi

25 đặc trưng, 8 nhóm chức năng. Categorical fields (`TRANS_LV1`, `TRANS_LV2`, `DAY_OF_WEEK`, `CLIENT_SEX`, `EB_REGISTER_CHANNEL`, `VERIFY_METHOD`, `Occupation_Group`) dùng **Label Encoding** + gán `UNKNOWN` cho giá trị null/blank.

---

## Phần IV: Kiến trúc Pipeline & Mô hình Phân tích

Dựa trên dữ liệu và đặc trưng đã trích xuất, hệ thống vận hành qua một Pipeline 3 tầng, kết hợp Machine Learning và các quy tắc nghiệp vụ.

---

### 4.1. Giải quyết bài toán "Không có nhãn gian lận" (PU Learning)

Bộ dữ liệu không có nhãn gian lận được xác nhận. Nếu dùng phương pháp thông thường sẽ không thể huấn luyện mô hình.
Hệ thống sử dụng phương pháp **Positive-Unlabeled (PU) Learning**:

- **Khởi tạo:** Dùng thuật toán không giám sát (Isolation Forest) để lọc ra một nhóm nhỏ các giao dịch "nghi vấn nhất" (nhãn Proxy).
- **Lọc nhiễu:** Áp dụng các thuật toán (Spy Filtering, CVuO) để loại bỏ các giao dịch bình thường bị nhận diện nhầm, dần khoanh vùng chính xác các hành vi gian lận.
- **Huấn luyện:** Dùng tập dữ liệu đã làm sạch để huấn luyện mô hình phân loại (XGBoost) cuối cùng.

> **Gợi ý biểu đồ:**
> - Sơ đồ Flowchart đơn giản minh họa dữ liệu từ "Chưa có nhãn" đi qua "Bộ lọc nhiễu" và đưa vào "Mô hình XGBoost".

---

### 4.2. Kiến trúc Suy luận Phân tầng (3-Tier Inference)

Giao dịch thực tế đi qua 3 tầng kiểm duyệt để cân bằng giữa tốc độ và độ chính xác:

- **Tầng 1 - Bộ lọc Rule-based (Tốc độ cao):** 
  - Chặn đứng ngay lập tức các giao dịch có độ rủi ro cực đoan (Ví dụ: Đổi mật khẩu rồi rút tiền ngay).
  - Tự động cho qua (Bypass) các giao dịch rủi ro cực thấp (như thanh toán điện nước). Giúp giảm tải 30-95% lượng tính toán.
- **Tầng 2 - Mô hình Machine Learning (XGBoost):**
  - Các giao dịch ở "vùng xám" sẽ được phân tích toàn diện dựa trên 25 đặc trưng.
  - Mô hình chấm điểm rủi ro $P(\text{fraud}|x)$. Vượt ngưỡng sẽ bị gắn cờ bất thường.
- **Tầng 3 - Trí tuệ Nhân tạo Có thể giải thích (xAI):**
  - Áp dụng TreeSHAP để trích xuất lý do vì sao giao dịch bị gắn cờ, dịch ra ngôn ngữ tự nhiên cho chuyên viên rủi ro đọc hiểu.
  - Phân tích tương tác đặc trưng (Ví dụ: Tài khoản ngủ đông + Thiết bị lạ).

---

### 4.3. Chống "Quên thảm họa" với EWC (Học liên tục)

- **Vấn đề:** Khi hành vi khách hàng thay đổi theo thời gian (ví dụ: mùa lễ tết), việc cập nhật mô hình với dữ liệu mới có thể khiến mô hình quên mất các dấu hiệu gian lận cốt lõi đã học trước đó (Catastrophic Forgetting).
- **Giải pháp:** Áp dụng **Elastic Weight Consolidation (EWC)**. Hệ thống bảo vệ các "trọng số" quan trọng nhất của mô hình, cho phép mô hình học các xu hướng mới mà vẫn giữ nguyên được "trí nhớ" về các thủ đoạn gian lận cũ.

---
## Phần VII: Kết quả & Phân tích

Toàn bộ 5.000 GD mẫu qua hệ thống 3 Tầng với 25 đặc trưng cấu trúc mới.

---

### 7.1. Thống kê tổng quan (Kết quả Rule-based & ML)

- **Tổng giao dịch đánh giá:** 5.000
- **Tier 1 (Safe Bypass):** 1.479 GD (29,58%) — lọc bỏ an toàn ~30% chi phí tính toán ML.
- **Tier 2 (ML XGBoost):** 3.521 GD vùng xám → phân tích rủi ro đầy đủ 25 đặc trưng.
- **Tier 3 (Anomaly Alerts):** **94 GD bất thường** (1,88%) từ 64 KH duy nhất. Anomaly Score trung bình = **0.8244**. Rất sát tỷ lệ gian lận thực tế trong NHTM.

---

### 7.2. Phân bố rủi ro theo nhóm Feature

- **Về số tiền:** GD bất thường trung bình 29,85 triệu VND (trung vị hệ thống 5M). Tội phạm chuyển lớn nhất có thể trước khi bị phong tỏa.
- **Về thiết bị:** iOS 62,77%, Android 36,17%, Web 1,06%.
- **Về kênh chuyển tiền:** **Outside_bank chiếm 76,60%** tổng cảnh báo — kẻ gian tẩu tán tài sản ra ngoài hệ thống gốc (irreversible). Within_bank chỉ 14,89%.

---

### 7.3. Đóng góp Đặc trưng (Ranked SHAP Contributors)

TreeSHAP trên 94 cảnh báo, tần suất đóng góp của tất cả các đặc trưng:

| Đặc trưng (Feature) | Tần suất Top SHAP | Giải thích logic thực tế |
| :--- | :--- | :--- |
| **NEW_DEVICE_FLAG** | 46 alerts (48,94%) | Dấu hiệu số 1 ATO — kẻ gian luôn đăng nhập thiết bị lạ. |
| **DAYS_AMOUNT_COMBINED** | 44 alerts (46,81%) | Money Mule: tài khoản ngủ đông lâu → đột ngột GD lớn. |
| **BALANCE_COVERAGE_RATIO** | 33 alerts (35,11%) | "Dòng tiền qua tay" — chuyển đi vượt xa số dư lịch sử. |
| **TRANS_HOUR** | 29 alerts (30,85%) | Khung giờ 0h-5h — nạn nhân mất cảnh giác, botnet xả tiền. |
| **TRANS_AMOUNT_VS_30D_AVG_RATIO** | 26 alerts (27,66%) | "Rút mẻ lưới cuối" — gấp chục lần thói quen tháng. |
| **VELOCITY_RATIO_AMOUNT_7D_VS_30D** | 21 alerts (22,34%) | Dồn dập tẩu tán tiền trong tuần gần nhất. |
| **TRANS_AMOUNT_Z_SCORE** | 18 alerts (19,15%) | Lệch chuẩn chi tiêu — rút tiền cực đoan. |
| **HOURS_SINCE_SEC_EVENT** | 15 alerts (15,96%) | Đổi mật khẩu/PIN xong lập tức chuyển khoản. |
| **IP_HOPPING_VELOCITY** | 15 alerts (15,96%) | Xoay vòng IP liên tục — mã độc/proxy động. |
| **DAYS_SINCE_LAST_TRANS** | 14 alerts (14,89%) | Sự thức tỉnh của tài khoản rác/ngủ đông. |
| **VELOCITY_RATIO_AMOUNT_24H_VS_7D** | 10 alerts (10,64%) | Rút tiền chớp nhoáng trong 24 giờ qua. |
| **LIMIT_UTILIZATION_VELOCITY** | 8 alerts (8,51%) | Tốc độ tiêu thụ thẻ tín dụng tăng đột ngột (Bust-out). |
| **SEC_AMOUNT_COMBINED** | 2 alerts (2,13%) | Đổi mật khẩu + số tiền lớn = ATO kinh điển. |
| **AGE_GROUP** | 1 alerts (1,06%) | Sinh viên/hưu trí dễ bị lợi dụng làm tài khoản trung chuyển. |

---

### 7.4. Tương tác Đặc trưng Độc hại (Toxic Feature Interactions)

SHAP Interaction ghi nhận các cặp tương tác cộng hưởng rủi ro phi tuyến:

1. **TRANS_HOUR × BALANCE_COVERAGE_RATIO (45,74%):** Vét sạch tiền lúc nửa đêm.
2. **NEW_DEVICE_FLAG × DAYS_AMOUNT_COMBINED (43,62%):** ATO + Mule: thiết bị lạ + ngủ đông + tiền lớn.
3. **DAYS_SINCE_LAST_TRANS × BALANCE_COVERAGE_RATIO (26,60%):** Ngủ đông thức giấc + số dư lệch pha.
4. **TRANS_HOUR × IP_HOPPING_VELOCITY (15,96%):** Xoay vòng IP (proxy/botnet) lúc nửa đêm — chiến dịch tấn công tự động (GoldPickaxe).

---

### 7.5. Ví dụ Counterfactual Recourse

**Case Study thực tế mô phỏng:**
- KH có `HIST_AVG_TRANS_AMOUNT` = 5 triệu VND.
- Hôm nay chuyển **55 triệu VND** (Z-Score > 10). $P(\text{fraud}|x) = 0.92$ → vượt ngưỡng → 🚨 gắn cờ.
- **Causal Propagation:** Giảm thử `TRANS_AMOUNT` → tự động tính lại `Z_SCORE`, `BALANCE_COVERAGE`, `DAYS_AMOUNT_COMBINED` → tái đánh giá.
- **Đề xuất Counterfactual xAI:** *"Giao dịch sẽ an toàn nếu số tiền giảm xuống còn tối đa **15.000.000 VND**."*
- **Quyết định nghiệp vụ:** Thay vì đóng băng thẻ → (1) Chia nhỏ dưới 15M, hoặc (2) Xác thực sinh trắc học Video-Call tăng cường theo QĐ 2345/QĐ-NHNN.

---

### 7.6. Hiệu suất xử lý thực tế

Tổng thời gian xử lý Tier 1–3 cho 5.000 GD: **6.931 ms** → **~1,4 ms/giao dịch**.

Độ trễ cực thấp cho phép can thiệp vào giữa luồng thanh toán core-banking mà không gây suy giảm hiệu năng end-user có thể cảm nhận khi bấm chuyển tiền trên app.

---

## Phần VIII: Giá trị Kinh doanh & Đề xuất

Cân bằng giữa Rủi ro (Risk) và Tăng trưởng (Growth) — giá trị chiến lược cho NHTM tại Việt Nam.

---

### 8.1. Bảo vệ uy tín ngân hàng và Tối ưu chi phí nguồn vốn

- **Giảm thiểu báo động giả (False Positives):** Từ 5-10% (rule-based truyền thống) xuống **~1,88%** anomaly rate, FP ước tính ~2,42%. Không đánh mất KH tốt do phiền toái.
- **Bảo vệ dòng vốn thất thoát:** 76,6% cảnh báo tập trung Outside_bank (irreversible) → chặn đứng dòng tiền "không thể thu hồi" → bảo vệ Trust Index và huy động vốn.

---

### 8.2. Nâng cao trải nghiệm khách hàng (Frictionless Security)

- **Bảo mật không ma sát:** Tier 1 Bypass tự động cho qua ~30% GD rủi ro cực thấp (hóa đơn, nạp thẻ) → Zero-latency Experience.
- **Phản ứng linh hoạt nhờ Counterfactual:** Thay vì Hard-block → đề xuất giải pháp thay thế: xác thực bổ sung FaceID/Video-Call (QĐ 2345/QĐ-NHNN) hoặc chia nhỏ GD. Customer-Centric.

---

### 8.3. Tăng hiệu suất Tuân thủ & Kiểm soát rủi ro (Compliance & AML)

- Điều tra truyền thống: Analyst tra cứu thủ công hàng chục bảng dữ liệu.
- SHAP Value → **narrative tự nhiên (Natural Language Explanations)** → "hồ sơ tóm tắt tội phạm" trên màn hình cảnh báo.
- Ví dụ: *"GD rủi ro do tài khoản ngủ đông 60 ngày, đăng nhập thiết bị mới, chuyển gấp 10 lần số dư."*
- Rút ngắn Decision Time **gấp 3-5 lần**, duy trì hiệu suất mùa cao điểm (Lễ, Tết).

---

### 8.4. Giới hạn hiện tại & Hướng phát triển (Next Steps)

1. **Xây dựng Vòng lặp Phản hồi (Active Feedback Loop):**
   - *Hạn chế:* PU Learning → nhãn tự động, chưa tận dụng trí tuệ con người.
   - *Giải pháp:* Giao diện Analyst bấm `[Xác nhận Gian Lận]` / `[Báo cáo Nhầm lẫn]` → nhãn thực tế → retrain Supervised → mô hình sắc bén hơn.

2. **Nâng cấp Streaming thời gian thực:**
   - *Hạn chế:* Feature Engineering cửa sổ trượt đang batch processing.
   - *Giải pháp:* Apache Kafka + Flink → counter In-memory State → `IP_HOPPING_VELOCITY` < 1ms.

3. **Mở rộng kịch bản Credit Shield:**
   - Tích hợp điểm tín dụng CIC + thói quen TMĐT → phát hiện sớm hơn ý định rửa tiền qua thẻ.

---

## Q&A

Cảm ơn đã lắng nghe!
