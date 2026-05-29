import re

content_2024 = """## 3. Mô tả Đặc trưng (Feature Description)

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
- **Công thức đo lường:** `KL-Divergence` giữa phân bố thực tế của chữ số đầu tiên và phân bố lý thuyết định luật Benford: `log10(1 + 1/d)`.
- **Vai trò:** **Biến độc lập** (Phát hiện gian lận cấu trúc).
- **Lý luận logic & Thực tế:** Trong số liệu tài chính tự nhiên, số bắt đầu bằng '1' chiếm ~30%, bằng '9' chỉ ~4.6%. Khi tội phạm cố tình "tự nghĩ ra" các con số để chia nhỏ tiền nhằm lách luật AML (Structuring), chúng làm hỏng phân bố tự nhiên này do tâm lý con người không thể ngẫu nhiên hoàn hảo. Nghiên cứu của Nigrini (2012) chứng minh sự sai lệch Benford là công cụ Forensic hiệu quả để chỉ điểm các hành vi bị thao túng có chủ ý.

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
"""

content_2026 = content_2024.replace("21 đặc trưng", "28 đặc trưng").replace("6 nhóm chức năng", "8 nhóm chức năng") + """
---

### 3.7 Nhóm 7: Mạng Lưới & Đồ Thị (Network & Graph Analytics - New 2026)

#### PAGERANK_SCORE & IN_DEGREE_CENTRALITY
- **Nguồn dữ liệu:** Xây dựng đồ thị liên kết, trong đó Node là `CUSTOMER_NUMBER` và Edge là quan hệ gửi/nhận tiền `Beneficiary_CUSTOMER_NUMBER` (từ `Data_Transaction`).
- **Công thức đo lường:** Chạy thuật toán đồ thị có hướng (PageRank) và đếm luồng tiền vào (In-Degree Centrality).
- **Vai trò:** **Biến độc lập** (Khám phá cấu trúc tổ chức tội phạm).
- **Lý luận logic & Thực tế:** Tiền bẩn thường được gom từ hàng chục tài khoản rác (Smurfs) tập trung về một vài tài khoản tổng (Hub). Đo lường Centrality giúp hệ thống phát hiện chính xác các tài khoản Hub này dựa trên sức hút dòng tiền của chúng so với phần còn lại của đồ thị.

---

### 3.8 Nhóm 8: Tín dụng & Chiêu trò tinh vi (Credit & Advanced Structuring - New 2026)

#### BUST_OUT_UTILIZATION
- **Nguồn dữ liệu:** Cột Dư nợ (`OUTSTANDING_BAL_CREDIT`) và Hạn mức (`LIMIT_AMT_CREDIT`) từ bảng `Data_Card`.
- **Công thức đo lường:** `max(OUTSTANDING_BAL_CREDIT / LIMIT_AMT_CREDIT)`
- **Vai trò:** **Biến độc lập**.
- **Lý luận logic & Thực tế:** Chống gian lận Synthetic Identity Fraud: kẻ lừa đảo dùng giấy tờ giả mở thẻ, nuôi lịch sử tín dụng vài tháng cho đẹp rồi đột ngột xài kịch kim 100% hạn mức thẻ (Bust-Out) trước khi cắt liên lạc vĩnh viễn. Tỷ lệ này càng cao, nguy cơ vỡ nợ gian lận càng lớn.

#### STRUCTURING_OVERPAYMENT_FLAG
- **Nguồn dữ liệu:** Lịch sử trả nợ thẻ từ `Data_Card`.
- **Công thức đo lường:** Bằng `1` (True) NẾU Số tiền trả nợ > Dư nợ thẻ VÀ số lần trả thẻ trong 30 ngày ≥ 2.
- **Vai trò:** **Biến độc lập**.
- **Lý luận logic & Thực tế:** Một mánh khóe rửa tiền hiện đại: Tội phạm dùng tiền bẩn thanh toán thẻ tín dụng số tiền lớn hơn dư nợ (Overpayment). Sau đó, chúng yêu cầu ngân hàng hoàn lại phần tiền nộp dư đó vào một tài khoản ngân hàng khác. Lúc này, dòng tiền hoàn lại được xem là "tiền sạch" do chính ngân hàng xuất ra.

#### IP_HOPPING_VELOCITY & AUTH_DOWNGRADE_RISK
- **Nguồn dữ liệu:** Địa chỉ IP `IP_Address_Proxy`, mã thiết bị `Device_ID_Hash` (`Data_Transaction`), và phương thức xác thực `ACTIVITY_NAME` (`Data_Activity`).
- **Công thức đo lường:** 
  - `IP_HOPPING`: Đếm số lượng IP độc nhất đăng nhập trên cùng một thiết bị trong 3 giờ.
  - `AUTH_DOWNGRADE`: Bật cờ (Flag) nếu khách hàng vốn có `HIST_BIOMETRIC_RATIO` cao nhưng nay đăng nhập thiết bị mới bằng Password.
- **Vai trò:** **Biến độc lập**.
- **Lý luận logic & Thực tế:** 
  - Malware di động (ví dụ: GoldPickaxe) thường liên tục nhảy proxy VPN để qua mặt quy tắc địa lý (IP hopping).
  - Khi thiết bị bị chiếm quyền điều khiển nhưng kẻ gian không có dấu vân tay nạn nhân, chúng buộc phải thoái lui về phương thức bảo mật kém hơn (Password tĩnh/OTP). Đo lường Auth Downgrade trên thiết bị lạ là bức tường thép chặn đứng các vụ đánh cắp phiên đăng nhập (Session Hijacking).
"""

def update_file(filepath, new_section):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    
    start_str = "## 3. Mô tả Đặc trưng"
    end_str = "## 4. Kết quả Pipeline"
    
    start_idx = text.find(start_str)
    end_idx = text.find(end_str)
    
    if start_idx != -1 and end_idx != -1:
        sep_idx = text.rfind("---", start_idx, end_idx)
        if sep_idx != -1:
            end_idx = sep_idx
            
        new_text = text[:start_idx] + new_section + "\n" + text[end_idx:]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"Updated {filepath}")
    else:
        print(f"Could not find markers in {filepath}")

update_file("d:/uni/gcontest v3/gcontest/feature_description_outcome.md", content_2024)
update_file("d:/uni/gcontest v3/gcontest/feature_description_outcome_2026.md", content_2026)
