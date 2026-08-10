# Kế Hoạch Điều Tra Cơ Chế Gian Lận Ngân Hàng
### Phân tích nhân quả & Thiết kế đặc trưng dữ liệu — Dựa trên cấu trúc dữ liệu thực tế & Pipeline hiện hành

---

> **Ghi chú phương pháp luận**: Tài liệu này tuân theo một logic điều tra nghiêm ngặt — mỗi bước là tiền đề logic của bước tiếp theo, không phải danh sách độc lập. Các feature được đề xuất **không** là mặc định kỹ thuật; chúng là kết quả tất yếu từ cơ chế hành vi được phân tích trước đó.

---

## Bước 1 — Cơ chế vận hành cốt lõi của gian lận ngân hàng

*Câu hỏi: Những cơ chế nào cho phép giao dịch gian lận diễn ra thành công, ở quy mô toàn cầu và trong bối cảnh Việt Nam?*

### 1.1 Lý thuyết nền — Tam giác gian lận & Điểm mù của hệ thống xác thực

Mọi vụ gian lận ngân hàng thành công đều phải giải quyết được ba vấn đề đồng thời:

1. **Chiếm đoạt danh tính xác thực**: Không phải chiếm đoạt tài khoản theo nghĩa đen, mà là thuyết phục hệ thống rằng kẻ tấn công *là* chủ tài khoản hợp pháp trong phạm vi cửa sổ thời gian đủ để hoàn tất giao dịch.
2. **Vượt qua ngưỡng kiểm soát giao dịch**: Mỗi ngân hàng có các tầng kiểm soát — hạn mức, OTP, xác thực sinh trắc học — mà kẻ tấn công phải vô hiệu hóa hoặc lách qua.
3. **Tẩu tán tài sản trước khi hệ thống phát hiện**: Toàn bộ hành trình từ lúc kiểm soát bị vượt qua đến lúc tiền ra khỏi hệ sinh thái ngân hàng phải ngắn hơn độ trễ phát hiện của ngân hàng.

Ba vấn đề này quyết định **hình dạng hành vi** của kẻ gian lận — và đó là những gì ta tìm kiếm trong dữ liệu.

### 1.2 Phân loại cơ chế theo bằng chứng toàn cầu

Các báo cáo từ FATF (2023), BIS (2022), và nghiên cứu của ngân hàng trung ương các quốc gia Đông Nam Á xác định ba nhóm cơ chế chính:

#### Nhóm A — Chiếm đoạt tài khoản qua thao túng tâm lý (Account Takeover via Social Engineering)

Đây là cơ chế **thống trị tại Việt Nam** hiện nay, theo báo cáo của NHNN và Cục An toàn thông tin (2022-2024). Kẻ tấn công không cần xâm nhập hệ thống kỹ thuật — chúng thuyết phục chủ tài khoản **tự thực hiện** hoặc **tự cung cấp thông tin xác thực**.

Chuỗi cơ chế:
```
Lừa đảo tâm lý
    → Chủ tài khoản cung cấp OTP / nhấp link cài ứng dụng giả
    → Kẻ tấn công kiểm soát thiết bị HOẶC chiếm phiên đăng nhập
    → Thay đổi mật khẩu / PIN / địa chỉ sách nhận tiền
    → Chuyển khoản toàn bộ số dư trong một phiên duy nhất
    → Tài khoản nhận tiền là tài khoản "mule" — rút tiền mặt ngay lập tức
```

**Biến thể điển hình tại Việt Nam**: Giả mạo cán bộ công an, thuế, bưu chính; lừa đảo qua Zalo/Facebook; cài đặt ứng dụng giả mạo ngân hàng; yêu cầu cài "phần mềm hỗ trợ" từ xa.

#### Nhóm B — Gian lận danh tính tổng hợp (Synthetic Identity Fraud)

Kẻ tấn công xây dựng một định danh khách hàng hợp lệ về mặt hình thức — có CCCD, có địa chỉ, có lịch sử giao dịch — nhưng không tương ứng với một cá nhân thực. Đây là cơ chế phức tạp hơn, thường gắn với các mạng lưới tổ chức, nhắm đến tín dụng (thẻ tín dụng, khoản vay) chứ không phải tiền gửi sẵn có.

#### Nhóm C — Rửa tiền qua hệ thống ngân hàng (Money Laundering via Layering)

Tiền từ nguồn bất hợp pháp (lừa đảo, buôn bán) cần được "làm sạch" qua nhiều lớp giao dịch. Cơ chế:
```
Tiền vào tài khoản mule (placement)
    → Chia nhỏ & chuyển qua nhiều tài khoản trung gian (layering)
    → Hợp nhất tại tài khoản đích, rút tiền mặt hoặc chuyển offshore (integration)
```

Tại Việt Nam, các mạng lưới này thường dùng tài khoản đăng ký tên người khác (thường là người lao động nghèo được thuê bán tài khoản).

### 1.3 Điểm đặc thù của bối cảnh Việt Nam

Ba yếu tố cấu trúc khuếch đại rủi ro gian lận tại Việt Nam:

| Yếu tố cấu trúc | Hệ quả hành vi |
|---|---|
| Tỉ lệ xác thực bằng OTP SMS cao (thay vì sinh trắc học cứng) | SIM swap và chặn OTP là vector tấn công khả thi |
| Hệ sinh thái ứng dụng ngân hàng đa dạng, người dùng ít phân biệt được app giả | Chiếm quyền thiết bị qua app độc hại là phổ biến |
| Thói quen rút tiền mặt vẫn cao ở một số nhóm dân số | Chuỗi giao dịch kết thúc bằng rút ATM nhanh, khó phục hồi |
| Thiếu cơ sở dữ liệu định danh thiết bị liên ngân hàng | Kẻ tấn công dùng thiết bị mới không có lịch sử |

---

## Bước 2 — Ma sát bắt buộc & Dấu vết không thể tránh khỏi

*Câu hỏi: Những hạn chế nào buộc kẻ gian lận phải để lại dấu vết hành vi, thời gian và không gian khác biệt?*

### 2.1 Nguyên lý cốt lõi: Gian lận không phải hành vi tự nhiên

Chủ tài khoản hợp pháp hành động theo **thói quen** — tích lũy qua hàng tháng, hàng năm sử dụng. Kẻ gian lận không có thời gian để xây dựng lịch sử này. Do đó, chúng **bắt buộc** vi phạm ít nhất một trong các ràng buộc sau:

### 2.2 Ma sát thời gian (Temporal Friction)

**Vấn đề của kẻ gian lận**: Chúng có cửa sổ thời gian rất ngắn — từ lúc chiếm quyền kiểm soát đến lúc nạn nhân phát hiện và gọi ngân hàng. Ước tính trung bình 15–90 phút (dựa trên báo cáo của UK Finance 2023 về APP fraud).

**Dấu vết bắt buộc**:
- Giao dịch lớn bất thường xuất hiện **ngay sau** sự kiện bảo mật (đổi mật khẩu, đổi PIN, cập nhật sách địa chỉ). Pipeline hiện tại đã nắm bắt điều này qua `HOURS_SINCE_SEC_EVENT`.
- **Mô hình mới cần thêm**: Khoảng cách thời gian giữa sự kiện bảo mật và giao dịch đầu tiên có giá trị lớn. Cần phân biệt: chủ tài khoản đổi mật khẩu theo định kỳ (ngày thường, không giao dịch ngay), vs. kẻ gian lận đổi mật khẩu và giao dịch ngay trong vài phút.

**Feature bổ sung đề xuất từ Activity**:
```
SEC_TO_TX_INTERVAL = TRANS_DATETIME - LAST_SEC_EVENT_DATETIME (tính bằng phút)
FLAG_SEC_TX_SAME_SESSION = 1 nếu SEC_TO_TX_INTERVAL < 30 phút
```

### 2.3 Ma sát không gian & thiết bị (Spatial & Device Friction)

**Vấn đề của kẻ gian lận**: Chúng thường không ở cùng vị trí địa lý với nạn nhân và dùng thiết bị khác.

**Dấu vết bắt buộc**:
- Thay đổi `IP_Address_Proxy` so với lịch sử — đặc biệt là IP từ tỉnh thành khác hoặc IP proxy/VPN.
- Thay đổi `Device_ID_Hash` — thiết bị chưa từng được dùng bởi tài khoản này.
- Thay đổi `Device_OS` — từ iOS sang Android hoặc ngược lại.

Pipeline hiện tại chưa khai thác `IP_Address_Proxy`, `Device_ID_Hash`, `Device_OS`, và `Merchant_ID_Masked` một cách trực tiếp.

**Feature bổ sung đề xuất từ Transaction**:
```
NEW_DEVICE_FLAG = 1 nếu Device_ID_Hash chưa xuất hiện trong lịch sử của CUSTOMER_NUMBER
NEW_IP_PROVINCE_FLAG = 1 nếu tỉnh/thành từ IP_Address_Proxy khác với tỉnh/thành thường dùng
DEVICE_OS_CHANGED = 1 nếu Device_OS khác với Device_OS của lần đăng nhập gần nhất
```

### 2.4 Ma sát hành vi xác thực (Authentication Behavior Friction)

**Vấn đề của kẻ gian lận**: Khi chiếm quyền thiết bị hoặc phiên, họ thường không dùng sinh trắc học (vân tay, khuôn mặt) — hoặc không thể (thiết bị từ xa), hoặc không biết (ứng dụng giả không thu thập sinh trắc học thực).

**Dấu vết bắt buộc**:
- Đột ngột chuyển từ xác thực sinh trắc học sang OTP SMS.
- Đăng nhập không dùng sinh trắc học trên thiết bị vốn thường dùng sinh trắc học.

Pipeline hiện tại đã có `HIST_BIOMETRIC_RATIO`. Nhưng nó chỉ là tỉ lệ tích lũy — không nắm bắt được **sự đứt gãy đột ngột**.

**Feature bổ sung đề xuất**:
```
BIOMETRIC_BREAK = 1 nếu LAST_LOGIN_METHOD = OTP/PIN nhưng HIST_BIOMETRIC_RATIO > 0.7
(tức là tài khoản vốn hay dùng sinh trắc học, đột nhiên đăng nhập bằng mật khẩu/OTP)
```

### 2.5 Ma sát hành vi sử dụng vốn (Capital Deployment Friction)

**Vấn đề của kẻ gian lận**: Mục tiêu là tối đa hóa số tiền chiếm đoạt trong khoảng thời gian ngắn nhất. Điều này tạo ra:
- Giao dịch có giá trị **bất thường cao** so với lịch sử — pipeline đã có `TRANS_AMOUNT_Z_SCORE` và `BALANCE_COVERAGE_RATIO`.
- Giao dịch đến **nhiều người thụ hưởng khác nhau** nhanh chóng — pipeline đã có `UNIQUE_BENEFICIARIES_24H`.
- **Cạn kiệt số dư** trong một phiên — cần so sánh tổng giao dịch 24H với số dư trung bình.

**Feature bổ sung đề xuất từ Deposit**:
```
BALANCE_DRAWDOWN_RATIO = SUM_AMOUNT_24H / AVG_CA_BALANCE
(Tỉ lệ tổng giao dịch 24H chiếm bao nhiêu % số dư trung bình — nếu gần 1.0, tài khoản gần cạn kiệt)
```

### 2.6 Ma sát trình tự hoạt động (Activity Sequence Friction)

**Vấn đề của kẻ gian lận**: Chuỗi hành động của chúng không tự nhiên — chúng sẽ thực hiện các bước chuẩn bị (đổi mật khẩu, thêm người thụ hưởng) theo trình tự bất thường so với người dùng thực.

Pipeline đã có `ACTIVITY_SEQ_RARITY` dựa trên Markov chain bậc 2. Đây là một trong những feature mạnh nhất về mặt nhân quả.

---

## Bước 3 — Dịch ngược thành Feature Engineering có thể tính toán

*Câu hỏi: Làm thế nào để chuyển hóa các dấu vết hành vi thành đặc trưng toán học dựa trên cấu trúc dữ liệu hiện có?*

### 3.1 Bản đồ feature theo cơ chế nhân quả

| Cơ chế gian lận | Dấu vết hành vi | Feature toán học | Nguồn dữ liệu | Trạng thái trong Pipeline |
|---|---|---|---|---|
| Chiếm quyền thiết bị | Thiết bị mới chưa từng dùng | `NEW_DEVICE_FLAG` | Transaction.Device_ID_Hash | **Chưa có — đề xuất mới** |
| Chiếm quyền thiết bị | IP từ tỉnh thành lạ | `NEW_IP_PROVINCE_FLAG` | Transaction.IP_Address_Proxy | **Chưa có — đề xuất mới** |
| Chiếm quyền phiên | Đột ngột từ bỏ sinh trắc học | `BIOMETRIC_BREAK` | Activity (login method) | **Chưa có — đề xuất mới** |
| Cửa sổ tấn công ngắn | Đổi mật khẩu → giao dịch ngay | `SEC_TO_TX_INTERVAL` | Activity + Transaction | Có một phần qua `HOURS_SINCE_SEC_EVENT` |
| Triển khai vốn cực đại | Số dư gần cạn kiệt trong 24H | `BALANCE_DRAWDOWN_RATIO` | Transaction + Deposit | **Chưa có — đề xuất mới** |
| Triển khai vốn cực đại | Số tiền bất thường vs lịch sử | `TRANS_AMOUNT_Z_SCORE` | Transaction + Customer hist | **Đã có trong Pipeline** |
| Phân tán tiền nhanh | Nhiều người nhận trong 24H | `UNIQUE_BENEFICIARIES_24H` | Transaction | **Đã có trong Pipeline** |
| Chuẩn bị tấn công | Trình tự hoạt động bất thường | `ACTIVITY_SEQ_RARITY` | Activity | **Đã có trong Pipeline** |
| Rửa tiền | Giao dịch đến tài khoản mule | `BENEFICIARY_RISK_SCORE` | Transaction (cross-customer) | **Chưa có — phức tạp** |
| Rửa tiền | Chia nhỏ giao dịch (structuring) | `BENFORD_DEV` + `VELOCITY_RATIO` | Transaction | **Đã có trong Pipeline** |

### 3.2 Feature mới: `NEW_DEVICE_FLAG` và `DEVICE_HISTORY_COUNT`

**Cơ sở nhân quả**: Kẻ tấn công dùng thiết bị của họ, không phải thiết bị của nạn nhân. Khi chiếm quyền kiểm soát từ xa (qua TeamViewer, AnyDesk giả mạo), `Device_ID_Hash` sẽ phản ánh thiết bị của kẻ tấn công.

**Công thức**:
$$\text{DEVICE\_HISTORY\_COUNT}_i = \bigl|\{d : d = \text{Device\_ID\_Hash},\; \exists \text{ transaction by same customer}\}\bigr|$$

$$\text{NEW\_DEVICE\_FLAG}_i = \mathbb{1}[\text{DEVICE\_HISTORY\_COUNT}_i = 1]$$

**Điều kiện thực thi**: `Device_ID_Hash` trong bảng Transaction phải được join theo lịch sử của từng `CUSTOMER_NUMBER`. Cần cửa sổ lịch sử đủ dài (tối thiểu 90 ngày) để xác định "thiết bị đã biết".

### 3.3 Feature mới: `BALANCE_DRAWDOWN_RATIO`

**Cơ sở nhân quả**: Kẻ gian lận cố rút toàn bộ số dư. Tỉ lệ này tiến gần 1.0 trong các vụ chiếm đoạt tài khoản điển hình.

$$\text{BALANCE\_DRAWDOWN\_RATIO}_i = \frac{\text{SUM\_AMOUNT\_24H}_i}{\text{HIST\_AVG\_CA\_BALANCE}_i + \epsilon}$$

Pipeline hiện tại đã có `BALANCE_COVERAGE_RATIO` cho *một* giao dịch. `BALANCE_DRAWDOWN_RATIO` mở rộng sang tổng 24H — phản ánh chính xác hơn ý đồ triển khai vốn cực đại.

**Điều kiện thực thi**: `HIST_AVG_CA_BALANCE` đã được tính trong Phase 1.3 của pipeline. `SUM_AMOUNT_24H` đã có trong Phase 1.2. Feature này có thể thêm ngay vào Phase 2.3 mà không cần dữ liệu mới.

### 3.4 Feature mới: `BIOMETRIC_BREAK_SCORE`

**Cơ sở nhân quả**: Khi kẻ tấn công chiếm quyền kiểm soát từ xa hoặc dùng thiết bị mới, họ không thể xác thực bằng sinh trắc học của nạn nhân.

$$\text{BIOMETRIC\_BREAK\_SCORE}_i = \text{HIST\_BIOMETRIC\_RATIO}_{i-1} \times \mathbb{1}[\text{LAST\_LOGIN\_METHOD}_i \notin \{\text{FINGER, FACEID}\}]$$

Giá trị cao (ví dụ > 0.5) = tài khoản vốn xác thực bằng sinh trắc học, nhưng lần đăng nhập hiện tại lại dùng phương thức khác. Đây là tín hiệu mạnh về sự gián đoạn kiểm soát.

**Điều kiện thực thi**: `HIST_BIOMETRIC_RATIO` và `LAST_LOGIN_METHOD` đã được tính trong Phase 1.7. Feature này có thể thêm vào Phase 2.3.

### 3.5 Feature từ Card & Lending: Áp lực tài chính như bối cảnh

Dữ liệu Card và Lending hiện chưa được pipeline sử dụng. Chúng không nắm bắt hành vi gian lận trực tiếp, nhưng cung cấp **ngữ cảnh** quan trọng:

- `OVERDUE_CREDIT` (số ngày quá hạn thẻ tín dụng) — tài khoản có tín dụng quá hạn thường là mục tiêu bán tài khoản.
- `OUTSTANDING_BALANCE / LIMIT_AMT` — tỉ lệ sử dụng hạn mức thẻ cao có thể là dấu hiệu synthetic identity fraud (vay tối đa rồi biến mất).
- `OVERDUE_LENDING` — quá hạn khoản vay có thể dự báo người dùng dễ bị thao túng tâm lý bởi kẻ giả mạo thu hồi nợ.

$$\text{CREDIT\_STRESS\_INDEX} = \frac{\text{OUTSTANDING\_BALANCE}}{\text{LIMIT\_AMT} + \epsilon} + \mathbb{1}[\text{OVERDUE\_CREDIT} > 0]$$

---

## Bước 4 — Trường hợp Dương tính Giả: Ranh giới nhân quả

*Câu hỏi: Khi nào các feature này xuất hiện với cường độ cao nhưng hành vi lại hoàn toàn hợp pháp?*

### 4.1 Bảng phân tích dương tính giả theo feature

| Feature | Tình huống hợp pháp tạo tín hiệu cao | Ranh giới nhân quả phân biệt |
|---|---|---|
| `NEW_DEVICE_FLAG` | Mua điện thoại mới; reset factory; du lịch dùng điện thoại mượn | Nếu đi kèm với `SEC_TO_TX_INTERVAL` thấp và `TRANS_AMOUNT_Z_SCORE` cao → tín hiệu thực. Nếu chỉ có thiết bị mới, với giao dịch nhỏ, thói quen bình thường → hợp pháp. |
| `BALANCE_DRAWDOWN_RATIO` cao | Mua bất động sản, thanh toán hóa đơn lớn, đóng học phí, mua xe | Giao dịch hợp pháp thường đến **một người thụ hưởng đã biết**. Kiểm tra xem `UNIQUE_BENEFICIARIES_24H` có cao không và `Beneficiary_CUSTOMER_NUMBER` có xuất hiện trong lịch sử không. |
| `BIOMETRIC_BREAK_SCORE` cao | Cập nhật điện thoại xóa sinh trắc học; đăng nhập từ thiết bị cũ không có sinh trắc | Kiểm tra xem `Device_ID_Hash` có phải thiết bị đã biết không. Thiết bị đã biết + xác thực mật khẩu = hợp pháp. Thiết bị mới + xác thực mật khẩu = tín hiệu mạnh hơn. |
| `ACTIVITY_SEQ_RARITY` rất thấp | Người dùng mới ít lịch sử; thay đổi sản phẩm ngân hàng; sự kiện đặc biệt trong cuộc đời (kết hôn, về hưu) | Pipeline đã có fallback cho `DAYS_SINCE_LAST_TRANS` dài. Cần thêm: phân biệt rarity thấp do *thiếu lịch sử* vs. rarity thấp do *chuỗi bất thường tích cực*. |
| `HOURS_SINCE_SEC_EVENT` ngắn | Người dùng tự đổi mật khẩu theo nhắc nhở định kỳ của ngân hàng rồi giao dịch ngay | Kiểm tra xem thay đổi bảo mật có đến từ yêu cầu của hệ thống (forced reset) hay tự nguyện. Nếu có thể, thêm cờ phân loại loại sự kiện bảo mật. |
| `UNIQUE_BENEFICIARIES_24H` cao | Doanh nghiệp nhỏ trả lương nhân viên; hộ kinh doanh thanh toán nhiều nhà cung cấp | Nghề nghiệp (`OCCUPATION_GROUP`) và loại giao dịch (`TRANS_LV1`) cung cấp ngữ cảnh. Tài khoản cá nhân thông thường với nhiều người nhận mới = tín hiệu thực. |

### 4.2 Nguyên tắc nhân quả tổng quát

Không có feature đơn lẻ nào có giá trị nhân quả mạnh khi đứng một mình. Tín hiệu trở nên có độ tin cậy cao khi **ít nhất ba ma sát cùng xuất hiện đồng thời**:

- Ma sát thiết bị/không gian (NEW_DEVICE hoặc IP mới)
- Ma sát xác thực (BIOMETRIC_BREAK)
- Ma sát triển khai vốn (BALANCE_DRAWDOWN_RATIO hoặc TRANS_AMOUNT_Z_SCORE cao)

Đây không phải quy tắc AND đơn giản mà là tín hiệu tương tác (interaction). Pipeline đã xử lý điều này qua SHAP interaction values trong Phase 4.3.2 — nhưng cần bổ sung các feature mới vào trước khi interaction có thể được học.

---

## Bước 5 — Điều tra chuyên sâu theo bằng chứng

*Câu hỏi: Bằng chứng chỉ về hướng nào — thao túng tâm lý hay rửa tiền có tổ chức?*

### 5.1 Phán quyết bằng chứng từ bối cảnh Việt Nam

Dựa trên các báo cáo công khai của NHNN (2023), Bộ Công an và các tổ chức quốc tế, **bằng chứng hiện tại nghiêng rõ về Nhóm A — Thao túng tâm lý chiếm đoạt tài khoản**, với đặc điểm:

- Phần lớn các vụ án liên quan đến nạn nhân *tự thực hiện* giao dịch hoặc *tự cung cấp OTP*.
- Chuỗi giao dịch đặc trưng: **một giao dịch lớn duy nhất** → đến tài khoản mule → rút tiền mặt ATM.
- Số lượng vụ rửa tiền có cấu trúc phức tạp nhỏ hơn, nhưng giá trị thiệt hại cao hơn và khó phát hiện hơn.

Do đó, **điều tra chuyên sâu tập trung vào bất thường thiết bị và phiên hoạt động**, không phải phân tích đồ thị rửa tiền (dù phần sau vẫn được phác thảo).

### 5.2 Điều tra sâu: Bất thường kiểm soát thiết bị và phiên (Session Hijacking)

#### 5.2.1 Cấu trúc phiên bất thường từ Activity

Bảng `Activity` ghi lại mọi hành động của người dùng trên nền tảng ebank. Một phiên gian lận điển hình tạo ra chuỗi Activity sau:
```
[LOGIN] → [PASSWORD_CHANGE] → [ADDRESS_BOOK_UPDATE] → [FUND_TRANSFER_LARGE] → [LOGOUT]
```
Trong khi phiên hợp pháp thường:
```
[LOGIN] → [BALANCE_CHECK] → [FUND_TRANSFER_SMALL] → [LOGOUT]
hoặc
[LOGIN] → [BILL_PAYMENT] → [LOGOUT]
```

**Feature từ Activity chưa được pipeline khai thác**:

```
ACTIONS_PER_SESSION = số Activity records trong cùng một ACTIVITY_DATE và ACTIVITY_HOUR
SEC_EVENTS_BEFORE_TX_COUNT = số sự kiện bảo mật trong 2 giờ trước giao dịch
SESSION_ENTRY_RATIO = tỉ lệ phiên bắt đầu bằng PASSWORD_CHANGE / tổng phiên lịch sử
```

#### 5.2.2 Bất thường `Merchant_ID_Masked`

Kẻ gian lận thường chuyển tiền đến **tài khoản nhận tiền mới** — chưa từng xuất hiện trong lịch sử. `Merchant_ID_Masked` và `Beneficiary_CUSTOMER_NUMBER` cung cấp thông tin này.

**Feature đề xuất**:
```
BENEFICIARY_IS_NEW = 1 nếu Beneficiary_CUSTOMER_NUMBER chưa xuất hiện trong lịch sử giao dịch của CUSTOMER_NUMBER
FIRST_TIME_LARGE_BENEFICIARY = BENEFICIARY_IS_NEW AND TRANS_AMOUNT_Z_SCORE > 3
```

#### 5.2.3 Mô hình thời gian trong ngày (Time-of-Day Profiling)

Tấn công từ xa thường xảy ra vào **giờ hành chính** (khi kẻ tấn công đang làm việc) hoặc **đêm khuya** (khi nạn nhân ít chú ý). Hành vi này có thể khác biệt với thói quen giao dịch cá nhân của nạn nhân.

**Feature đề xuất (bổ sung vào `HIST_NIGHT_RATIO`)**:
```
HOUR_DEVIATION = |TRANS_HOUR - HIST_AVG_TRANS_HOUR|
(Độ lệch giờ giao dịch hiện tại so với giờ trung bình lịch sử của khách hàng)
```

### 5.3 Phác thảo điều tra: Cấu trúc đồ thị rửa tiền (nếu bằng chứng dịch chuyển)

Nếu phân tích tương lai cho thấy các mạng lưới chuyển tiền có tổ chức trở nên nổi bật hơn, cần điều tra:

#### 5.3.1 Đặc trưng đồ thị (Graph Features)

Từ `Beneficiary_CUSTOMER_NUMBER` trong Transaction, có thể xây dựng đồ thị định hướng:
- **Node**: mỗi `CUSTOMER_NUMBER`
- **Edge**: mỗi giao dịch chuyển khoản, có trọng số là `TRANS_AMOUNT`

Các đặc trưng đồ thị có giá trị nhân quả:

```
IN_DEGREE_RATIO = số nguồn chuyển đến tài khoản / tổng giao dịch nhận
(Tài khoản mule nhận tiền từ nhiều nguồn lạ → IN_DEGREE_RATIO cao bất thường)

PASS_THROUGH_RATIO = tổng tiền ra trong 24H / tổng tiền vào trong 24H
(Tài khoản trung gian rửa tiền có tỉ lệ này gần 1.0)

HOP_DISTANCE_FROM_ORIGIN = số bước từ tài khoản nguồn ban đầu
(Tiền rửa qua nhiều tầng → hop distance tăng)
```

#### 5.3.2 Chỉ số vận tốc thay thế (Alternative Velocity Indicators)

Giao dịch chia nhỏ (structuring) để tránh ngưỡng báo cáo là dấu hiệu cổ điển của rửa tiền:

```
ROUND_AMOUNT_RATIO = tỉ lệ giao dịch có TRANS_AMOUNT là số tròn (chia hết cho 1,000,000)
(Giao dịch chia nhỏ thường có số tròn cố ý)

AMOUNT_CLUSTER_ENTROPY = entropy của phân phối TRANS_AMOUNT trong 7D
(Giao dịch hợp pháp có entropy cao; giao dịch chia nhỏ cố ý có entropy thấp do lặp cùng mức)
```

---

## Bước 6 — Giới hạn mô hình và Điều kiện sụp đổ

*Câu hỏi: Khi nào toàn bộ hệ thống nhận diện mất hiệu lực, và điều này mang lại ngụ ý gì?*

### 6.1 Điều kiện sụp đổ Loại I — Định danh tổng hợp hoàn hảo (Perfect Synthetic Identity)

**Kịch bản**: Kẻ tấn công xây dựng tài khoản "warming" — sử dụng tài khoản trong nhiều tháng với hành vi hoàn toàn bình thường trước khi tấn công. Tất cả lịch sử đều hợp pháp; chỉ giao dịch cuối cùng mới là gian lận.

**Cơ chế sụp đổ**:
- `ACTIVITY_SEQ_RARITY` không phát hiện được vì lịch sử đã được "huấn luyện".
- `HIST_BIOMETRIC_RATIO` cao vì đã xác thực bình thường từ trước.
- `TRANS_AMOUNT_Z_SCORE` có thể cao, nhưng nếu warming bao gồm các giao dịch lớn dần dần, ngay cả điều này cũng bị vô hiệu hóa.

**Ngụ ý**: Không có feature lịch sử hành vi nào đủ mạnh trước kẻ tấn công kiên nhẫn. Đây là lý thuyết trò chơi — chi phí tấn công tăng lên đáng kể, nhưng không bị loại trừ hoàn toàn.

**Phản ứng thiết kế**: Cần thêm lớp phòng thủ không phụ thuộc vào lịch sử hành vi — ví dụ: xác minh thực thể ngoài băng (out-of-band verification) cho giao dịch ngưỡng cao, hoặc so sánh định danh thiết bị với cơ sở dữ liệu liên ngân hàng.

### 6.2 Điều kiện sụp đổ Loại II — Bắt chước hành vi hoàn hảo (Perfect Behavioral Mimicry)

**Kịch bản**: Kẻ tấn công có quyền truy cập vào toàn bộ lịch sử hành vi của nạn nhân (ví dụ: thông qua mã độc trên thiết bị theo dõi trong thời gian dài) và bắt chước chính xác — giao dịch đúng giờ, đúng thiết bị, đúng xác thực sinh trắc học (deepfake hoặc thiết bị vật lý bị chiếm).

**Cơ chế sụp đổ**:
- `NEW_DEVICE_FLAG` = 0 vì dùng đúng thiết bị.
- `BIOMETRIC_BREAK_SCORE` = 0 vì xác thực sinh trắc học đúng.
- `ACTIVITY_SEQ_RARITY` bình thường vì bắt chước đúng chuỗi.

**Ngụ ý**: Đây là giới hạn lý thuyết của mọi hệ thống phát hiện dựa trên hành vi — không phải lỗi thiết kế, mà là bản chất toán học của bài toán phát hiện dị thường khi phân phối đầu vào của kẻ tấn công và người dùng hợp pháp trùng khít.

### 6.3 Điều kiện sụp đổ Loại III — Phân phối drift và catastrophic forgetting

**Kịch bản**: Hành vi gian lận thay đổi cấu trúc (ví dụ: chuyển từ giao dịch lớn đơn lẻ sang nhiều giao dịch nhỏ, hoặc chuyển sang kênh thanh toán mới). Pipeline hiện tại đã nhận ra rủi ro này và có Phase 5 (EWC) để xử lý.

**Giới hạn còn lại**: EWC bảo vệ trọng số cũ nhưng không tự động phát hiện *khi nào* phân phối đã thay đổi đủ để cần retraining. Cần monitoring độc lập về:
```
DRIFT_INDICATOR = KL-divergence giữa phân phối score hiện tại và phân phối score baseline
```

### 6.4 Điều kiện sụp đổ Loại IV — Tấn công đối nghịch vào bản thân hệ thống (Adversarial Attack on Detection)

**Kịch bản**: Kẻ tấn công hiểu mô hình hoạt động như thế nào (hoặc qua thử nghiệm, hoặc qua nội gián) và cố tình duy trì các feature dưới ngưỡng phát hiện — ví dụ: giữ `COUNT_1H = 1`, `TRANS_AMOUNT` vừa đủ dưới ngưỡng Tier 1 bypass.

**Phản ứng thiết kế**: Ngưỡng bypass trong Tier 1 (`TRANS_AMOUNT < 500,000` và `COUNT_1H ≤ 1`) cần được giám sát xem có bị khai thác có hệ thống không. Nếu volume giao dịch có `TRANS_AMOUNT` = 499,999 tăng bất thường → tín hiệu adversarial probing.

---

## Tổng hợp — Ưu tiên thực thi

### Feature đề xuất mới theo thứ tự ưu tiên

| Thứ tự | Feature | Giá trị nhân quả | Khó khăn thực thi | Nguồn dữ liệu |
|---|---|---|---|---|
| 1 | `NEW_DEVICE_FLAG` + `DEVICE_HISTORY_COUNT` | **Rất cao** — trực tiếp phát hiện chiếm quyền thiết bị | Trung bình (cần join lịch sử Device_ID_Hash) | Transaction |
| 2 | `BIOMETRIC_BREAK_SCORE` | **Cao** — phát hiện đứt gãy xác thực | Thấp (đã có data từ Phase 1.7) | Activity |
| 3 | `BALANCE_DRAWDOWN_RATIO` | **Cao** — phát hiện triển khai vốn cực đại | Thấp (đã có SUM_24H và AVG_BALANCE) | Transaction + Deposit |
| 4 | `BENEFICIARY_IS_NEW` + `FIRST_TIME_LARGE_BENEFICIARY` | **Cao** — phát hiện người nhận lạ lần đầu | Trung bình (cần join lịch sử beneficiary) | Transaction |
| 5 | `HOUR_DEVIATION` | **Trung bình** — bổ sung cho HIST_NIGHT_RATIO | Thấp (đã có TRANS_HOUR và lịch sử) | Transaction |
| 6 | `SEC_TO_TX_INTERVAL` (< 30 phút) | **Cao** — nắm bắt cửa sổ tấn công ngắn | Trung bình (cần join Activity timestamp với Transaction) | Activity + Transaction |
| 7 | `NEW_IP_PROVINCE_FLAG` | **Cao** — phát hiện vị trí địa lý lạ | Cao (cần giải mã IP_Address_Proxy thành tỉnh/thành) | Transaction |
| 8 | `CREDIT_STRESS_INDEX` | **Thấp-Trung bình** — ngữ cảnh, không phải tín hiệu trực tiếp | Thấp (Card + Lending data có sẵn) | Card + Lending |

### Nguyên tắc kết hợp feature trong mô hình

XGBoost trong pipeline đã học các tương tác phi tuyến tính giữa các feature. Tuy nhiên, có thể tăng cường bằng cách thêm **interaction feature thủ công** cho hai cặp có giá trị nhân quả rõ ràng nhất:

$$\text{DEVICE\_AUTH\_RISK} = \text{NEW\_DEVICE\_FLAG} \times \text{BIOMETRIC\_BREAK\_SCORE}$$

$$\text{CAPITAL\_ATTACK\_INDEX} = \text{BALANCE\_DRAWDOWN\_RATIO} \times \text{BENEFICIARY\_IS\_NEW}$$

Hai feature tổng hợp này không thay thế mà bổ sung cho khả năng học tương tác của XGBoost — chúng nén thông tin nhân quả vào một tín hiệu duy nhất, giảm số iteration cần thiết để mô hình học được mối quan hệ.

---

*Tài liệu này là kết quả của điều tra logic — không phải danh sách kỹ thuật. Mọi feature đề xuất đều có thể bị bác bỏ nếu bằng chứng dữ liệu thực tế chứng minh ngược lại.*
