# Phân Tích Các Loại Gian Lận Ngân Hàng: 2018 → Nay
### Đánh giá tính hiện diện trong dữ liệu năm 2019 & Khả năng tồn tại xuyên suốt

---

> **Câu hỏi trung tâm**: Trong số các loại gian lận đã tồn tại từ 2018 đến nay, loại nào **có thể được quan sát trong dữ liệu năm 2019** và loại nào **chỉ xuất hiện sau đó**? Đây là câu hỏi nhân quả, không phải thống kê — một loại gian lận tồn tại về mặt pháp lý chưa chắc để lại dấu vết đủ mật độ để mô hình học được.

---

## Phần I — Bức tranh 2018-2019 tại Việt Nam: Điểm xuất phát

### Bối cảnh kỹ thuật số năm 2019 — Thấp hơn nhiều so với hiện tại

Để đánh giá đúng loại gian lận nào hiện diện trong dataset 2019, cần hiểu trạng thái kỹ thuật số của thị trường Việt Nam lúc đó:

| Chỉ số | Năm 2019 | Năm 2024-2025 |
|---|---|---|
| Tỉ lệ người lớn có tài khoản ngân hàng | ~30-40% | 87% |
| Chủ yếu xác thực bằng | OTP SMS + mật khẩu | OTP + sinh trắc học (từ 7/2024) |
| Phương thức chuyển khoản phổ biến | ATM + Internet Banking desktop | Mobile banking app |
| Số cuộc tấn công mạng vào ngân hàng | 8,319 vụ (2018, Vietcombank) | >100,000 vụ (2024, Bộ CA) |
| Tỉ lệ fraud trong tài chính số | 58.2% (cao nhất SEA, 3/2019, AppsFlyer) | Tiếp tục leo thang |
| Số máy tính nhiễm malware ngân hàng | 560,000 (2018) | Không đo được tương đương |

**Hàm ý cho dataset 2019**: Phần lớn giao dịch vẫn chạy qua kênh Internet Banking truyền thống (desktop), xác thực chủ yếu qua OTP SMS. Sinh trắc học gần như chưa triển khai. Đây là điều kiện kỹ thuật quyết định **loại gian lận nào khả thi** trong năm đó.

---

## Phần II — Phân loại Gian Lận theo Dòng Thời Gian

### Loại 1 — Gian Lận Thẻ Vật Lý (Card Skimming)

**Thời điểm hình thành**: Trước 2015 tại Việt Nam.
**Trạng thái năm 2019**: **Rất phổ biến** — một trong ba loại tấn công hàng đầu (cùng với hacking và phishing), được xác nhận trong nghiên cứu học thuật về tội phạm mạng trong ngân hàng VN (ResearchGate, 2020, dữ liệu 2018-2019).

**Cơ chế vận hành năm 2019**:
```
Thiết bị skimmer gắn vào ATM/POS
    → Đọc track data từ dải từ thẻ
    → Quay camera lấy PIN
    → Tạo thẻ clone
    → Rút tiền mặt tại ATM
```

**Dấu vết trong dữ liệu 2019**:
- `TRANS_LV1/LV2`: Giao dịch ATM bất thường (rút tiền mặt, không phải chuyển khoản)
- `TRANS_HOUR`: Rút tiền đêm khuya hoặc rạng sáng — nạn nhân không biết, kẻ tấn công hành động khi ATM ít người
- `IP_Address_Proxy`: Có thể phát hiện nếu rút tiền ở tỉnh thành khác địa bàn thường dùng thẻ
- `Device_OS`: Không áp dụng cho giao dịch ATM (kênh vật lý)

**Phán quyết khả năng phát hiện**: Pipeline hiện tại **yếu** với loại này vì giao dịch ATM không có Device_ID_Hash hay Activity log. `TRANS_AMOUNT_Z_SCORE` có thể bắt được nếu rút nhiều lần liên tiếp, nhưng không phải tín hiệu mạnh.

---

### Loại 2 — Phishing Credentials (Trang Web Giả Mạo)

**Thời điểm hình thành**: 2015-2017 tại Việt Nam, tăng tốc mạnh 2018-2019.
**Trạng thái năm 2019**: **Rất phổ biến và đang tăng trưởng mạnh** — được ghi nhận trong hàng loạt vụ án tại Vietcombank, DongA Bank, HDBank (Vietnam Law Magazine). Trong 2018, 8,319 cuộc tấn công mạng vào ngân hàng VN được ghi nhận.

**Cơ chế vận hành năm 2019**:
```
Email/SMS chứa link giả mạo trang ngân hàng
    → Nạn nhân nhập username + password + OTP
    → Kẻ tấn công replay credentials ngay lập tức (cửa sổ OTP ~60 giây)
    → Đổi mật khẩu + thêm người thụ hưởng mới
    → Chuyển toàn bộ số dư
```

**Đặc điểm quan trọng năm 2019**: OTP SMS là lớp bảo mật DUY NHẤT. Kẻ tấn công cần thực hiện phiên tấn công **đồng thời thời gian thực** với nạn nhân nhập OTP — tạo ra áp lực thời gian cực lớn dẫn đến hành vi đặc trưng trong dữ liệu.

**Dấu vết trong dữ liệu 2019**:
- `HOURS_SINCE_SEC_EVENT` rất ngắn (đổi mật khẩu → giao dịch ngay trong vài phút)
- `UNIQUE_BENEFICIARIES_24H` cao (thêm người nhận mới ngay trước khi chuyển tiền)
- `TRANS_AMOUNT_Z_SCORE` cao bất thường (muốn rút tối đa)
- `BALANCE_COVERAGE_RATIO` gần 1.0
- `ACTIVITY_SEQ_RARITY` thấp (chuỗi bất thường: login → đổi mật khẩu → thêm beneficiary → transfer)

**Phán quyết khả năng phát hiện**: **Cao** — đây là loại gian lận mà pipeline hiện tại được thiết kế tốt nhất để phát hiện. Tất cả các feature cốt lõi đều phù hợp.

---

### Loại 3 — Chiếm Đoạt Tài Khoản qua Malware (Banking Trojan)

**Thời điểm hình thành**: 2013-2015 toàn cầu (Carbanak), xuất hiện tại VN từ 2016-2017.
**Trạng thái năm 2019**: **Hiện diện** — 560,000 máy tính tại VN nhiễm malware có khả năng đánh cắp thông tin ngân hàng vào năm 2018.

**Cơ chế vận hành năm 2019**:
```
Malware cài trên thiết bị nạn nhân
    → Keylogger ghi username/password
    → Screen capture ghi OTP
    → Kẻ tấn công kiểm soát từ thiết bị KHÁC (C&C server)
    → Giao dịch giả mạo chạy từ thiết bị của kẻ tấn công
```

**Dấu vết trong dữ liệu 2019**:
- `Device_ID_Hash`: Thay đổi đột ngột (từ thiết bị nạn nhân sang thiết bị kẻ tấn công)
- `IP_Address_Proxy`: IP khác, thường là proxy/VPN hoặc tỉnh thành khác
- `Device_OS`: Có thể thay đổi (từ iOS sang Android)
- `HIST_BIOMETRIC_RATIO`: Nếu nạn nhân đã dùng biometric nhưng kẻ tấn công không thể → đột ngột xuống 0

**Phán quyết khả năng phát hiện**: **Trung bình-Cao** — nhưng phụ thuộc vào việc `Device_ID_Hash`, `IP_Address_Proxy` có được tính thành feature `NEW_DEVICE_FLAG` không. Pipeline hiện tại chưa khai thác hai trường này, dù dữ liệu đã có trong Transaction.

---

### Loại 4 — Tài Khoản Mule (Money Mule Network)

**Thời điểm hình thành**: Trước 2015 toàn cầu, có mặt tại VN từ 2017-2018.
**Trạng thái năm 2019**: **Hiện diện nhưng chưa có quy mô lớn như sau 2021** — phần lớn là mule bị động (người bị lừa cho mượn tài khoản) chứ chưa phải mạng lưới có tổ chức từ nước ngoài.

**Cơ chế vận hành năm 2019**:
```
Tài khoản mule nhận tiền từ nạn nhân (do phishing hoặc ATO)
    → Rút tiền mặt ngay (thường trong vòng 30-60 phút)
    → Chuyển sang tài khoản mule lớp 2 (ít phổ biến hơn năm 2019)
```

**Dấu vết trong dữ liệu 2019** — **ĐÂY LÀ ĐIỂM QUAN TRỌNG**:
Khi nhìn từ phía tài khoản mule (là nạn nhân thứ cấp trong dataset):
- Nhận tiền từ nhiều nguồn trong thời gian ngắn → `COUNT_24H` cao, `UNIQUE_BENEFICIARIES_24H` cao về phía incoming
- Rút tiền mặt hoặc chuyển đi ngay sau khi nhận → `VELOCITY_RATIO_AMOUNT_1H_VS_24H` cao
- Lịch sử giao dịch bình thường trước đó (thấp), đột ngột có luồng lớn

**Phán quyết khả năng phát hiện**: **Trung bình** từ phía nguồn, **Thấp** từ phía mule vì pipeline nhìn từ sender perspective. Cần feature `PASS_THROUGH_RATIO` để phát hiện mule.

---

### Loại 5 — Gian Lận Thẻ Tín Dụng (Credit Card Fraud)

**Thời điểm hình thành**: Luôn tồn tại song song với thẻ tín dụng.
**Trạng thái năm 2019**: **Có mặt** — chỉ 30% ngân hàng VN có chứng chỉ PCI DSS vào thời điểm đó. Thẻ tín dụng VN thường chỉ có dải từ (magnetic stripe) chứ chưa phổ biến chip EMV → rất dễ clone.

**Dấu vết trong dữ liệu**: Liên quan đến `Card` table — `OVERDUE_CREDIT`, `OUTSTANDING_BALANCE/LIMIT_AMT`. Gian lận thẻ thường tạo ra: chi tiêu đột biến lên đến hạn mức, rồi bỏ không thanh toán.

---

### Loại 6 — Giả Mạo Cán Bộ Nhà Nước (Impersonation Scam — "Công An Giả")

**Thời điểm hình thành**: **Bắt đầu lan rộng từ 2020-2021**.
**Trạng thái năm 2019**: **Chưa phổ biến** — vector này cần hạ tầng xã hội đủ phát triển (Zalo, mạng xã hội) và nạn nhân đủ quen với mobile banking để tự chuyển tiền ngay lập tức. Năm 2019 cả hai điều kiện chưa đủ chín muồi.

**Bằng chứng**: Vụ án điển hình như case Techcombank/Vietcombank (VnExpress) xảy ra năm **2022**, không phải 2019.

**Phán quyết cho dataset 2019**: **Gần như không tồn tại** trong dữ liệu 2019. Nếu có, xảy ra rải rác và không đủ mật độ để model học được.

---

### Loại 7 — SIM Swap có Tổ Chức

**Thời điểm hình thành**: 2018-2020 toàn cầu, VN từ 2020-2021.
**Trạng thái năm 2019**: **Rất sơ khai** — FBI ghi nhận 320 khiếu nại SIM swap cho cả giai đoạn 2018-2020 (Prelude). Tại VN, hạ tầng để thực hiện SIM swap quy mô lớn (mua chuộc nhân viên telco, làm giả CCCD) chưa được tổ chức.

**Phán quyết cho dataset 2019**: **Hiếm** — có thể tồn tại dưới dạng vài case đơn lẻ nhưng không đủ đại diện để trở thành pattern học được.

---

### Loại 8 — Đầu Tư Giả / Pig Butchering

**Thời điểm hình thành**: **2020-2021**, bùng nổ sau COVID-19 do các trung tâm lừa đảo ở Campuchia/Myanmar.
**Trạng thái năm 2019**: **Chưa tồn tại** tại VN ở quy mô đáng kể.

**Phán quyết cho dataset 2019**: **Không có**.

---

### Loại 9 — Gian Lận Danh Tính Tổng Hợp (Synthetic Identity Fraud)

**Thời điểm hình thành**: Phổ biến ở Mỹ/châu Âu từ 2015-2016; VN từ 2019-2020.
**Trạng thái năm 2019**: **Có mặt nhưng yếu** — KYC của ngân hàng VN năm 2019 chủ yếu dựa vào CMND vật lý, dễ bị bypass bằng CMND giả. Tuy nhiên, fraud này nhắm vào khoản vay/thẻ tín dụng, không phải chiếm đoạt tiền gửi — tín hiệu khác loại.

**Dấu vết**: `Lending.OVERDUE_LENDING` cao + không có lịch sử giao dịch thực → tài khoản "warms up" rồi default. Khó phát hiện bằng transaction-level features.

---

## Phần III — Ma Trận Đánh Giá: Tồn Tại trong Dataset 2019?

| Loại Gian Lận | Tồn tại năm 2019? | Mật độ đủ để học? | Feature pipeline phát hiện được? | Phán quyết cuối |
|---|---|---|---|---|
| **Card Skimming (vật lý)** | ✅ Rất phổ biến | ✅ Cao | ⚠️ Yếu (giao dịch ATM ít digital trace) | **Có nhưng khó phát hiện** |
| **Phishing Credentials** | ✅ Rất phổ biến | ✅ Cao | ✅ Mạnh | **Có & phát hiện được tốt** |
| **Banking Trojan / Malware ATO** | ✅ Có mặt | ✅ Trung bình-Cao | ⚠️ Trung bình (cần NEW_DEVICE feature) | **Có, cần bổ sung feature** |
| **Tài khoản Mule** | ✅ Có mặt | ✅ Trung bình | ⚠️ Trung bình (phía sender tốt hơn phía receiver) | **Có, phát hiện một phần** |
| **Credit Card Fraud** | ✅ Có mặt | ✅ Trung bình | ⚠️ Yếu-Trung bình (cần Card data) | **Có, cần khai thác Card table** |
| **Impersonation / Công An Giả** | ❌ Gần như không | ❌ Thấp | N/A | **Không đáng kể trong 2019** |
| **SIM Swap có tổ chức** | ⚠️ Rất sơ khai | ❌ Thấp | N/A | **Không đủ signal** |
| **Pig Butchering / Đầu Tư Giả** | ❌ Không | ❌ Không | N/A | **Không tồn tại** |
| **Synthetic Identity Fraud** | ⚠️ Sơ khai | ⚠️ Thấp | ⚠️ Yếu | **Hiếm, tập trung lending** |

---

## Phần IV — Đặc Điểm Gian Lận Thực Tế trong Dataset 2019

Từ ma trận trên, dataset 2019 của bạn **gần như chắc chắn** chứa chủ yếu ba loại:

### Profile A — Phishing + Credential Replay (Chiếm Đoạt Phiên)
Đặc trưng giao dịch:
- **Một giao dịch lớn duy nhất** (hoặc 2-3 giao dịch trong vài phút)
- **Người thụ hưởng mới hoàn toàn** — chưa từng xuất hiện trong lịch sử
- **Đổi mật khẩu hoặc thêm beneficiary ngay trước đó** (trong vòng <30 phút)
- **Giờ giao dịch bất thường** — có thể bất kỳ giờ nào, nhưng thường không phải giờ nạn nhân hay giao dịch
- **TRANS_AMOUNT gần bằng toàn bộ số dư**

Đây là loại gian lận mà pipeline đã được tối ưu tốt nhất.

### Profile B — Card Data Theft + ATM Withdrawal
Đặc trưng giao dịch:
- Giao dịch ATM liên tiếp, tại nhiều máy khác nhau
- Số tiền mỗi lần gần với hạn mức rút một lần (thường là 5-10 triệu VND)
- Xảy ra ngoài giờ hành chính, thường từ 10PM-4AM
- Không có Activity log (giao dịch vật lý không sinh ra event trong ebank)

Pipeline hiện tại bắt được phần nào qua `COUNT_1H`, `SUM_AMOUNT_1H`, và `HIST_NIGHT_RATIO`.

### Profile C — Unauthorized Transfer qua Compromised Credentials
Đặc trưng giao dịch:
- Đăng nhập từ thiết bị lạ hoặc IP lạ
- Số tiền chuyển khoản bất thường so với lịch sử
- Giao dịch kết thúc nhanh (toàn bộ phiên < 5 phút)
- Nạn nhân không biết cho đến khi kiểm tra tài khoản

Pipeline bắt được qua `TRANS_AMOUNT_Z_SCORE`, `ACTIVITY_SEQ_RARITY`. Cần bổ sung `NEW_DEVICE_FLAG`.

---

## Phần V — Sự Liên Tục qua Thời Gian: Cái Gì Vẫn Còn Đó?

### Nguyên lý "Persistent Core" — Cơ Chế Lõi Không Thay Đổi

Mặc dù các vector tấn công cụ thể thay đổi (từ phishing email → app giả mạo → deepfake audio), **cơ chế lõi vẫn nhất quán từ 2018 đến nay**:

```
CHIẾM QUYỀN KIỂM SOÁT XÁC THỰC → TRIỂN KHAI VỐN NHANH → TẨU TÁN TIỀN
```

Điều này có hàm ý quan trọng cho model: **các feature được xây dựng dựa trên cơ chế lõi** sẽ có tính bền vững cao hơn các feature bắt chước vector cụ thể.

### Những gì thay đổi từ 2019 đến nay — và hàm ý cho model

| Chiều thay đổi | 2019 | 2024-2026 | Hàm ý |
|---|---|---|---|
| Phương thức xác thực | OTP SMS chủ đạo | Sinh trắc học bắt buộc (từ 7/2024) | Feature `BIOMETRIC_BREAK` quan trọng hơn nhiều trong data hiện tại |
| Quy mô tấn công | Thủ công, từng vụ | Công nghiệp hóa, tự động hóa | Velocity features quan trọng hơn vì volume tăng |
| Loại thiệt hại | Chủ yếu từ fraud kỹ thuật | Chủ yếu từ social engineering | `ACTIVITY_SEQ_RARITY` quan trọng hơn vì nạn nhân tự thực hiện |
| Tổ chức mạng lưới | Đơn lẻ/nhỏ | Có tổ chức xuyên quốc gia | Graph features (PASS_THROUGH, mule network) quan trọng hơn |

### Những feature nào "bất biến thời gian" — Reliable qua 2019 đến nay

Những feature sau đây có giá trị nhân quả bền vững vì chúng phản ánh **ràng buộc vật lý** của gian lận, không phải vector cụ thể:

1. **Velocity ratio (COUNT_1H_VS_24H, AMOUNT_1H_VS_24H)**: Kẻ gian lận luôn phải nhanh — không phụ thuộc vào phương thức tấn công.
2. **TRANS_AMOUNT_Z_SCORE + BALANCE_COVERAGE_RATIO**: Mục tiêu tối đa hóa tài sản chiếm đoạt không thay đổi.
3. **UNIQUE_BENEFICIARIES_24H**: Tài khoản mule mới luôn cần thiết — luôn để lại dấu vết.
4. **HOURS_SINCE_SEC_EVENT**: Cửa sổ tấn công ngắn tạo ra pattern đổi bảo mật → giao dịch ngay, bất kể năm nào.
5. **ACTIVITY_SEQ_RARITY**: Trình tự hành động bất thường là hằng số — dù cơ chế tấn công có thay đổi.

---

## Phần VI — Khuyến Nghị Điều Chỉnh cho Dataset 2019

### 1. Điều chỉnh kỳ vọng nhãn (label expectation)

Dataset 2019 sẽ **không chứa** các pattern của:
- Impersonation scam quy mô lớn (công an giả)
- SIM swap có tổ chức
- Pig-butchering
- Deep fake social engineering

Điều này **không làm yếu** giá trị của dataset — nó có nghĩa là mô hình học từ 2019 sẽ tập trung vào **gian lận kỹ thuật** (phishing, credential theft, malware) thay vì **gian lận tâm lý** (social engineering). Cả hai vẫn để lại dấu vết trong transaction data.

### 2. Feature nào ít tin cậy hơn với data 2019

**`HIST_BIOMETRIC_RATIO`**: Năm 2019, biometric adoption rất thấp. Feature này sẽ gần 0 cho hầu hết khách hàng — ít phân biệt được. Không nên dựa nhiều vào feature này khi train trên data 2019.

**`VERIFY_METHOD`**: Năm 2019, gần như toàn bộ sẽ là OTP/PIN — ít variance → ít information gain.

### 3. Feature nào đặc biệt quan trọng với data 2019

**`Device_ID_Hash` làm nguồn cho `NEW_DEVICE_FLAG`**: Năm 2019, kẻ tấn công chủ yếu dùng thiết bị khác (vì chưa chiếm quyền thiết bị vật lý). Đây là tín hiệu mạnh nhất cho dữ liệu thời kỳ này.

**`IP_Address_Proxy`**: Năm 2019, VPN/proxy dùng để che giấu vị trí ít phổ biến hơn — IP lạ là tín hiệu đáng tin cậy hơn so với thời điểm VPN được dùng rộng rãi.

**`HOURS_SINCE_SEC_EVENT` + `ACTIVITY_SEQ_RARITY`**: Phishing credential replay tạo ra pattern đổi mật khẩu → giao dịch ngay rất rõ ràng trong data 2019.

### 4. Về việc thiếu labels trong PU Learning

Pipeline đã giải quyết việc không có ground truth labels bằng PU Learning (Isolation Forest + PAYN spy filtering). Điều này đặc biệt phù hợp với dataset 2019 vì:
- Hầu hết gian lận năm 2019 **không được ngân hàng gắn nhãn chính thức** — phần lớn bị quy cho "lỗi khách hàng" (như các case tại Vietcombank)
- Isolation Forest sẽ phát hiện được các giao dịch có đặc trưng bất thường dù không có label, miễn là mật độ fraud đủ cao (>1-2% tổng giao dịch)

---

## Tổng Kết

**Dataset 2019 là snapshot của một giai đoạn gian lận kỹ thuật thuần túy** — trước khi social engineering quy mô lớn và các mạng lưới xuyên quốc gia thống trị thị trường. Đây vừa là hạn chế vừa là lợi thế:

- **Hạn chế**: Model học từ 2019 sẽ thiếu kinh nghiệm với impersonation scam, SIM swap, pig-butchering.
- **Lợi thế**: Tín hiệu gian lận kỹ thuật trong 2019 sạch hơn và rõ ràng hơn — ít bị nhiễu bởi giao dịch "authorized nhưng bị lừa" (nạn nhân tự chuyển tiền). Pipeline sẽ học được core fraud mechanics có tính bền vững cao.

Các feature velocity, Z-score, sequence rarity và beneficiary anomaly đều phù hợp với cả 2019 lẫn hiện tại — **đây là backbone đáng tin cậy nhất của hệ thống**. Feature thiết bị và IP, nếu được bổ sung, sẽ giải quyết phần lớn blind spot còn lại của dataset 2019.
