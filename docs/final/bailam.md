## Phần I: Mở đầu

### 1.1. Bối cảnh dự án

Trong kỷ nguyên số hóa ngành tài chính - ngân hàng, các dịch vụ ngân hàng số (Digital Banking) mang lại sự tiện lợi vượt trội nhưng đồng thời cũng đối mặt với các nguy cơ bảo mật ngày càng tinh vi. Các đối tượng gian lận liên tục thay đổi phương thức tấn công: từ chiếm đoạt tài khoản (Account Takeover - ATO), chuyển tiền trái phép, sử dụng tài khoản rác (Mule Accounts) để rửa tiền, cho đến việc giả mạo các tham số giao dịch.

**Thực trạng lừa đảo tài chính tại Việt Nam:** Tình hình lừa đảo ngân hàng số tại Việt Nam gần đây ghi nhận sự gia tăng mạnh mẽ của tội phạm công nghệ cao sử dụng trí tuệ nhân tạo (AI Deepfake) và mã độc di động để thực hiện chiếm quyền điều khiển tài khoản (ATO) hoặc sử dụng mạng lưới tài khoản rác trung chuyển dòng tiền bất hợp pháp. Theo báo cáo từ LexisNexis Risk Solutions, chi phí xử lý hậu quả của gian lận tài chính trung bình cao gấp 4,36 lần số tiền thực tế bị tổn thất. Kẻ gian thường dụ dỗ nạn nhân cài đặt ứng dụng chứa mã độc giả mạo cơ quan công quyền để chiếm quyền trợ năng hệ thống (Accessibility Service), từ đó đọc mã OTP, thu thập thông tin đăng nhập và bypass các cơ chế bảo mật từ xa. Sau khi chiếm quyền, hệ thống ghi nhận các chuỗi hành vi lặp lại như thay đổi thông tin bảo mật (mật khẩu/PIN) và lập tức thực hiện rút cạn tiền trong thời gian ngắn. Dòng tiền bẩn sau khi bị chiếm đoạt được tẩu tán nhanh chóng thông qua kỹ thuật cấu trúc dòng tiền (Structuring/Smurfing) và mạng lưới tài khoản rác.

Để ứng phó, Ngân hàng Nhà nước Việt Nam đã ban hành Quyết định 2345/QĐ-NHNN (hiệu lực từ 01/7/2024), bắt buộc xác thực sinh trắc học khuôn mặt trùng khớp với dữ liệu CCCD gắn chip đối với các giao dịch trực tuyến trên 10 triệu đồng/lần hoặc tổng cộng dồn trong ngày vượt 20 triệu đồng. Ngành ngân hàng cũng đưa vào vận hành hệ thống SIMO để chia sẻ danh sách đen tài khoản nghi vấn giữa các tổ chức tín dụng. Các ngân hàng thương mại đã triển khai AI phân tích hành vi người dùng theo thời gian thực (real-time) để phát hiện bất thường về thiết bị đăng nhập, vị trí, khung giờ.

**Hạn chế của hệ thống Rule-based truyền thống:** Đảm bảo an toàn giao dịch mà không làm suy giảm trải nghiệm người dùng là thách thức chính. Phương pháp tiếp cận truyền thống dựa trên các quy tắc tĩnh (Rule-based) thường bộc lộ hai điểm yếu lớn:

- Tỷ lệ báo động giả (False Positive Rate) cao, gây phiền hà cho khách hàng hợp pháp và có thể dính vào vấn đề pháp lý nếu báo động sai.
- Khả năng bỏ sót (False Negative Rate) lớn đối với các hành vi gian lận mới, tinh vi, có tính chất biến đổi liên tục (Behavioral Drift).

**Xu hướng ứng dụng ML + xAI:** Do đó, xây dựng một hệ thống phát hiện bất thường tự động dựa trên trí tuệ nhân tạo (AI) kết hợp khả năng giải thích (xAI - Explainable AI) là nhiệm vụ giúp các tổ chức tài chính quản trị rủi ro chủ động và hiệu quả hơn.

### 1.2. Mục tiêu dự án

Dựa trên việc khai thác toàn diện bộ dữ liệu mẫu về thông tin khách hàng, lịch sử giao dịch và hành vi sử dụng dịch vụ số, đề án tập trung thử nghiệm và kiểm định các giải pháp công nghệ trong khía cạnh phát hiện bất thường và gian lận (Fraud & Anomaly Detection). Mục đích cốt lõi là ứng dụng các mô hình học máy kết hợp giải thích hành vi nhằm phát hiện các hành vi giao dịch bất thường và giảm thiểu rủi ro bảo mật, từ đó xây dựng hệ thống cảnh báo sớm, bảo vệ người dùng khỏi các thủ đoạn lừa đảo và kiến tạo môi trường giao dịch an toàn. Qua việc tối ưu hóa tính bảo mật và giảm thiểu rủi ro tài chính, đề án hướng tới việc củng cố uy tín thương hiệu của ngân hàng, đồng thời nâng cao trải nghiệm số và niềm tin của khách hàng.

Để hiện thực hóa mục tiêu trên, đề án xây dựng và triển khai bốn nhiệm vụ trọng tâm:

- **Phát hiện giao dịch nghi vấn:** Tự động nhận diện các giao dịch đáng ngờ theo thời gian thực thông qua việc phân tích chuyên sâu dòng tiền, lịch sử hành vi cá nhân, thói quen sử dụng thiết bị và các đặc trưng tương tác phi tuyến (như tỷ lệ bao phủ số dư, tần suất giao dịch cấp tập và Geovelocity).
- **Giảm False Positive & xAI:** Phá vỡ rào cản "hộp đen" của các mô hình học máy phức tạp bằng cách ứng dụng thuật toán TreeSHAP để trích xuất các đặc trưng đóng góp chính. Hệ thống tự động chuyển đổi các giá trị đóng góp toán học thành văn bản giải trình bằng ngôn ngữ tự nhiên, hỗ trợ chuyên viên kiểm soát rủi ro đưa ra quyết định duyệt hoặc chặn giao dịch nhanh chóng và chính xác.
- **Counterfactual Recourse:** Thiết lập cơ chế tìm kiếm phương án thay thế tối thiểu (các thay đổi nhỏ nhất đối với thuộc tính giao dịch như số tiền chuyển) để hướng dẫn khách hàng hoặc hệ thống tự điều chỉnh nhằm đưa giao dịch trở về trạng thái an toàn nếu đó là giao dịch hợp lệ.
- **Bảo vệ uy tín & niềm tin khách hàng:** Ứng dụng giải pháp Elastic Weight Consolidation (EWC) để cập nhật mô hình thích ứng trước sự trôi dạt hành vi (concept drift) và các thủ đoạn lừa đảo mới, bảo đảm không làm suy giảm hiệu năng nhận diện đối với các mẫu hành vi gian lận lịch sử.

### 1.3. Phạm vi & Hướng tiếp cận

**Lựa chọn Hướng 1: Fraud & Anomaly Detection.** Đề án lựa chọn hướng tiếp cận phát hiện gian lận và bất thường, xây dựng pipeline xử lý 5 phase:

| Phase | Nội dung |
| :---- | :---- |
| Phase 1 | Data Extraction — Trích xuất và liên kết dữ liệu thô từ nhiều nguồn |
| Phase 2 | Feature Engineering — Tính toán ~46 đặc trưng số hóa |
| Phase 3 | PU Learning — Huấn luyện mô hình khi không có nhãn gian lận |
| Phase 4 | Tiered Inference — Suy luận phân tầng 3 lớp kết hợp xAI |
| Phase 5 | EWC — Học liên tục chống quên thảm họa |

> **Gợi ý biểu đồ:**
> - Sơ đồ kiến trúc pipeline (Flowchart): Luồng xử lý 5 phase từ Data Extraction → Feature Engineering → PU Learning → Tiered Inference → EWC, thể hiện đầu vào/đầu ra của mỗi phase.

### 1.4. Dữ liệu sử dụng

Bộ dữ liệu mẫu gồm 6 bảng dữ liệu liên kết với quy mô ~20 triệu bản ghi:

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

Dựa trên việc phân tích bộ dữ liệu mẫu được cung cấp, đề án tiến hành trích xuất các số liệu thống kê tổng quan nhằm phục vụ quá trình khám phá dữ liệu (Exploratory Data Analysis - EDA), làm tiền đề xây dựng các mô hình phát hiện hành vi bất thường.

### 2.1. Tổng quan quy mô & cấu trúc dữ liệu

**Số lượng bản ghi:** Hệ thống ghi nhận 1.418.030 giao dịch phát sinh từ 46.204 khách hàng duy nhất có hoạt động P2P, trên nền tảng 290.223 hồ sơ khách hàng đã đăng ký. Tỷ lệ kích hoạt dịch vụ thực tế chỉ đạt 18,1% (52.488/290.223), còn lại 81,9% ở trạng thái bất hoạt hoặc chưa từng sử dụng.

**Phân bố giao dịch theo thời gian:**

- *Theo giờ:* Tần suất giao dịch chuẩn ở mức thưa, trung bình chỉ đạt 1,03 giao dịch/giờ, với phân vị p99 là 2 giao dịch/giờ. Bất kỳ tài khoản nào đạt 3 giao dịch/giờ đã nằm ngoài top 1% phân phối.
- *Theo ngày:* 99% khách hàng chỉ thực hiện tối đa 11 lệnh/ngày.
- *Theo ngày trong tuần:* Phân tích ma trận `TRANS_HOUR` × `DAY_OF_WEEK` cho thấy mật độ giao dịch tập trung cao vào các ngày giữa tuần (Thứ 2 – Thứ 6) trong khung giờ hành chính (8h – 17h). Đáng lưu ý, khung 00h – 05h ghi nhận 46.449 giao dịch ban đêm, trong đó 2.155 giao dịch có giá trị trên 5 triệu VND xuất phát từ các tài khoản hiếm khi hoạt động vào giờ này — tạo thành vùng thời gian cần giám sát đặc biệt.

**Chất lượng tài sản tín dụng:** Dữ liệu tín dụng ghi nhận 576.431 bản ghi dư nợ cho vay và 871.589 bản ghi thẻ tín dụng. Tổng cộng 17.665 khách hàng duy nhất có phát sinh nợ quá hạn, trong đó 2.593 khách hàng hoạt động trong mạng lưới giao dịch P2P, tạo thành nhóm "neo rủi ro" đo lường mức độ phơi nhiễm nợ xấu lan truyền qua mạng lưới chuyển tiền.

> **Gợi ý biểu đồ:**
> - Biểu đồ thanh so sánh: Số lượng khách hàng đăng ký vs. khách hàng thực sự phát sinh giao dịch (290.223 vs. 46.204), tỷ lệ kích hoạt dịch vụ.
> - Biểu đồ heatmap theo giờ × ngày trong tuần: Mật độ giao dịch theo `TRANS_HOUR` × `DAY_OF_WEEK`, làm nổi bật vùng đêm khuya (00h – 05h).
> - Biểu đồ phễu (Funnel chart): 290.223 khách hàng → 17.665 có nợ quá hạn → 2.593 hoạt động trong mạng P2P, thể hiện mức độ lọc rủi ro theo tầng.

### 2.2. Phân tích phân bố giao dịch

**Phân bố số tiền giao dịch (skewness/heavy tail):** Phân phối giao dịch lệch phải cực đoan. Đại đa số (hơn 50%) khách hàng giao dịch ở mức nhỏ lẻ phục vụ sinh hoạt, thông thường ở mức 640.000 VND/lệnh. Tuy nhiên, ở nhóm top 5%, quy mô lệnh vọt lên 38.000.000 VND, và top 1% đạt 163.236.758 VND, cá biệt có giao dịch đơn lẻ trị giá 2.458.000.000 VND. Chênh lệch giữa trung vị (640.000 VND) và p99 (163 triệu VND) lên tới 255 lần.

Sự phân hóa càng rõ khi tính tổng dòng tiền luân chuyển trong 30 ngày: mức lưu chuyển hàng tháng của người dùng bình thường chỉ quanh ngưỡng 17.900.000 VND, trong khi nhóm top 5% chạm mốc 977.744.950 VND/tháng.

**Phân bố theo loại giao dịch:** Kênh chuyển tiền P2P chiếm 69,7% tổng khối lượng (989.006 giao dịch). Các luồng còn lại chủ yếu phục vụ thanh toán sinh hoạt: cước viễn thông (Vinaphone: 59.446; Mobifone: 59.403; Viettel: 58.963) và nạp ví điện tử (ShopeePay: 42.741 giao dịch).

**Phân bố theo thiết bị iOS/Android/Web:** iOS chiếm 54,39%, Android chiếm 40,16% và Web chiếm 5,45%. Hệ sinh thái thiết bị đồng nhất cao, không xuất hiện hệ điều hành hiếm hoặc tùy biến. Phương thức xác thực: đăng nhập bằng sinh trắc học (Face ID/vân tay) chiếm khoảng 22% tổng số lần đăng nhập.

**Phân bố địa lý:** Hoạt động tập trung tại Hà Nội (478.915 giao dịch, 21.621 khách hàng) và TP. Hồ Chí Minh (417.417 giao dịch, 19.325 khách hàng). Các đô thị loại hai: Đà Nẵng (139.878), Hải Phòng (99.558), Cần Thơ (80.058), Bình Dương (71.776). Đặc biệt, 64.262 địa chỉ IP được sử dụng chung bởi nhiều hơn một khách hàng (cao nhất 45 khách hàng trên một IP duy nhất), phản ánh đặc thù IP động của nhà mạng di động Việt Nam.

> **Gợi ý biểu đồ:**
> - Biểu đồ histogram log-scale: Phân bố giá trị giao dịch (`TRANS_AMOUNT`), đánh dấu các phân vị p50, p95, p99.
> - Biểu đồ thanh xếp chồng (Stacked bar chart): Khối lượng giao dịch phân theo kênh (`BANK_TRANSFER_GATEWAY`, `TELCO_*`, `SHOPEEPAY`, khác).
> - Biểu đồ boxplot: So sánh phân phối giá trị giao dịch giữa các kênh.
> - Biểu đồ donut: Tỷ trọng hệ điều hành (iOS / Android / Web).
> - Biểu đồ thanh ngang: Top 10 tỉnh/thành phố theo khối lượng giao dịch và số lượng khách hàng.

### 2.3. Phân tích hành vi theo nhóm khách hàng (Cohort)

**Phân tích theo nhóm nghề nghiệp:** Phân khúc sinh viên có phân vị p99 số tiền giao dịch đạt 257.551.350 VND, cao hơn nhóm doanh nhân (159.444.000 VND) và công chức (140.124.000 VND). Nhóm người thất nghiệp đạt p99 là 149.692.566 VND và nhóm hưu trí đạt p99 là 495.080.000 VND. Điều này cho thấy tài khoản thuộc các phân khúc thu nhập thấp có thể bị lợi dụng làm tài khoản trung chuyển dòng tiền.

| Nhóm nghề nghiệp | Phân vị p99 số tiền giao dịch (VND) |
| :---- | :---- |
| STUDENT | **257.551.350** |
| PENSIONER | **495.080.000** |
| UNEMPLOYED | **149.692.566** |
| COMMERCIAL ASSOCIATE | 188.000.000 |
| WORKING | 161.500.000 |
| BUSINESSMAN | 159.444.000 |
| STATE SERVANT | 140.124.000 |

**Phân tích theo nhóm tuổi:** 394 giao dịch có số tiền lớn hơn 38.000.000 VND được thực hiện bởi khách hàng dưới 18 tuổi hoặc trên 70 tuổi — hai nhóm tuổi có năng lực tài chính và mức độ giám sát tài khoản hạn chế.

**Phân tích theo thời gian hoạt động của tài khoản:** Trong 27.352 giao dịch phát sinh trong 7 ngày đầu sau khi mở tài khoản, 2.357 giao dịch (8,62%) có số tiền lớn hơn 50.000.000 VND — tỷ lệ này cao gấp nhiều lần so với tỷ lệ nền (~1%), có thể phản ánh mẫu hành vi của các nhóm nghi vấn gian lận có tổ chức: mở tài khoản mới, có khả năng nhận tiền không hợp lệ và rút cạn trước khi bị phát hiện. Ngoài ra, 2.201 khách hàng (4,2%) đã đăng ký nhưng bỏ trống tài khoản hơn 90 ngày trước khi đột ngột kích hoạt và có dấu hiệu nghi vấn trung chuyển tiền, có tài khoản ngưng tới 357 ngày.

> **Gợi ý biểu đồ:**
> - Bar chart: Phân vị p99 số tiền giao dịch theo từng nhóm nghề nghiệp, tô đậm STUDENT, UNEMPLOYED, PENSIONER.
> - Histogram: Phân bố độ tuổi khách hàng thực hiện giao dịch > 38.000.000 VND, đánh dấu hai vùng cực đoan (< 18 và > 70).
> - Scatter plot: `TENURE_DAYS` (số ngày tuổi tài khoản, trục X) × `TRANS_AMOUNT` (trục Y), zoom vào vùng ≤ 7 ngày.

### 2.4. Phân tích chuỗi hoạt động & sự kiện bảo mật

**Tần suất đổi mật khẩu/PIN:** Hệ thống theo dõi 111.835 sự kiện bảo mật (bao gồm đổi mật khẩu, thay đổi mã PIN, cập nhật sổ địa chỉ). Trong tổng số này, hệ thống phát hiện 14.172 lệnh rút tiền lớn (chiếm 1% tổng giao dịch) xảy ra ngay trong vòng 24 giờ sau sự kiện bảo mật. Đặc biệt đáng lưu ý là nhóm ~1.200 giao dịch diễn ra chớp nhoáng chỉ trong vòng chưa đầy 1 giờ sau khi đổi thông tin — có khả năng là dấu hiệu tài khoản bị chiếm quyền và bị rút tiền ngay lập tức.

| Chỉ số | Giá trị | % |
| :---- | :---- | :---- |
| Tổng sự kiện bảo mật | 111.835 | — |
| GD trong 24h sau sự kiện bảo mật | 14.172 | 1,00% |
| GD cửa sổ ≤ 1 giờ | ~1.200 | — |
| Login Drift alerts | 2.364 | 0,17% |

**Hạ cấp phương thức bảo mật:** 2.364 giao dịch (0,17%) cho thấy khách hàng vốn quen dùng Face ID hoặc vân tay (sử dụng cho trên 50% số lần đăng nhập) đột ngột chuyển sang mật khẩu tĩnh ngay trước khi thực hiện lệnh chuyển tiền.

**Phân bố hoạt động đăng nhập/chuyển tiền — cơ sở thiết kế feature:**

- *Giao dịch ban đêm bất thường:* Trong 46.449 giao dịch diễn ra vào ban đêm (00h – 05h), có 2.155 giao dịch (trị giá trên 5 triệu VND) đáng lưu ý vì xuất phát từ những khách hàng có tỷ lệ thức đêm hiếm khi vượt quá 5%. Có 601 khách hàng thực hiện 100% lệnh chuyển tiền chỉ vào giữa đêm khuya — đây có thể là dấu hiệu cần xem xét thêm.
- *Tốc độ giao dịch bất thường:* Khi một tài khoản chạm ngưỡng 3 lệnh/giờ hoặc 6 lệnh/giờ, 34 lệnh/ngày, đó là dấu hiệu bất thường cần lưu ý. Quy mô lệnh chuyển tiền có thể đột ngột vọt lên gấp 3,48 lần, 6,89 lần, thậm chí 82,65 lần so với thói quen thường ngày.
- *Thiết bị bất thường:* 8.227 giao dịch (0,58%) xảy ra khi tài khoản đột ngột thay đổi hệ điều hành thiết bị trong 24 giờ. 42.449 giao dịch (3%) có hiện tượng hai lệnh liên tiếp từ hai tỉnh/thành khác nhau trong chưa tới 1 giờ (Impossible Travel).

Các dấu hiệu trên (khoảng cách thời gian tới sự kiện bảo mật, tốc độ giao dịch dồn dập, độ dị biệt khung giờ giao dịch) chính là cơ sở thiết kế các đặc trưng `HOURS_SINCE_SEC_EVENT`, `SPIKE_*`, `TRANS_HOUR_PROB`, `ACTIVITY_SEQ_RARITY` ở Phase 1-2.

> **Gợi ý biểu đồ:**
> - Histogram: Phân bố `HOURS_SINCE_SEC_EVENT` cho các giao dịch xảy ra sau sự kiện bảo mật, đánh dấu ngưỡng 1 giờ và 24 giờ.
> - Stacked bar chart: Phân loại sự kiện bảo mật (CHANGE_PASSWORD, SET_PIN, ADDRESS_BOOK_UPDATE) theo số lượng, kèm tỷ lệ dẫn tới giao dịch bất thường trong 24h.
> - Heatmap giờ × ngày trong tuần: Mật độ giao dịch, tô đậm vùng 00h – 05h.
> - Histogram log-scale: Phân bố `COUNT_1H` và `COUNT_24H`, đánh dấu ngưỡng p99 và vùng bất thường.

### 2.5. Nhận định chung về tình hình hoạt động của ngân hàng

Xét tổng thể, bộ dữ liệu phản ánh một ngân hàng số bán lẻ ở trạng thái hoạt động tích cực và ổn định nhưng tiềm ẩn một số rủi ro cấu trúc cần giám sát chặt chẽ.

**Các chỉ số tích cực:**

- Nền tảng khách hàng đa dạng với 290.223 hồ sơ trải rộng nhiều phân khúc nghề nghiệp và độ tuổi, cho thấy khả năng thâm nhập thị trường tốt.
- Dòng tiền giao dịch dồi dào với hơn 1,4 triệu giao dịch, kênh P2P chiếm tỷ trọng chi phối (69,7%), phản ánh mức độ tin dùng dịch vụ chuyển tiền trực tuyến cao.
- Mức độ số hóa khả quan với 16 triệu bản ghi hoạt động, tỷ lệ áp dụng sinh trắc học đạt 22% tổng số lần đăng nhập, cho thấy khách hàng đã bắt đầu chuyển dịch sang các phương thức xác thực tiên tiến hơn.
- Phân bố địa lý cân đối giữa hai trung tâm kinh tế Hà Nội và TP. Hồ Chí Minh, đồng thời phủ sóng đến các đô thị vệ tinh, thể hiện quy mô vận hành toàn quốc.

**Các chỉ số cần cảnh báo:**

- *Tỷ lệ kích hoạt dịch vụ thấp:* Chỉ 52.488/290.223 khách hàng (18,1%) thực sự phát sinh giao dịch trong năm. Còn lại 81,9% ở trạng thái bất hoạt, vừa là cơ hội tăng trưởng, vừa là rủi ro nếu tài khoản ngủ đông có khả năng bị khai thác làm tài khoản rác (Mule Account).
- *Chất lượng tín dụng có dấu hiệu xuống cấp:* 17.665 khách hàng (6,1%) phát sinh nợ quá hạn, trong đó 2.593 khách hàng vừa nợ xấu vừa hoạt động trong mạng lưới P2P, có thể tạo nguy cơ lan truyền rủi ro tài chính qua mạng lưới giao dịch.
- *Tỷ lệ sinh trắc học còn thấp:* 78% khách hàng vẫn phụ thuộc hoàn toàn vào mật khẩu tĩnh, tiềm ẩn nguy cơ bị chiếm đoạt thông qua phishing hoặc mã độc.
- *Phân phối giao dịch lệch phải cực đoan:* Chênh lệch giữa trung vị (640.000 VND) và p99 (163 triệu VND) lên tới 255 lần, đòi hỏi mô hình phát hiện bất thường phải hoạt động theo cơ chế phân cụm (cohort) thay vì áp dụng ngưỡng chung.

> **Gợi ý biểu đồ:**
> - Biểu đồ radar (Spider chart): Tổng hợp 5 trục đánh giá (Quy mô khách hàng, Thanh khoản dòng tiền, Chất lượng tín dụng, Mức độ số hóa, Độ phủ địa lý) trên thang điểm chuẩn hóa.
> - Biểu đồ waterfall: Phân rã 290.223 khách hàng thành các nhóm: hoạt động bình thường → nợ quá hạn → ngủ đông → nghi vấn gian lận.

### 2.6. Nhận định về giới hạn của bộ dữ liệu

Quá trình khám phá dữ liệu đã bộc lộ một số giới hạn cấu trúc của bộ dữ liệu mẫu, ảnh hưởng trực tiếp đến độ tin cậy của các mô hình học máy nếu được huấn luyện trên dữ liệu này.

**1. Không có nhãn gian lận (Zero Fraud Labels):** Bộ dữ liệu không cung cấp bất kỳ nhãn giao dịch gian lận đã xác nhận nào (`confirmed_frauds.json` rỗng). Điều này có nghĩa:
- Không thể huấn luyện mô hình phân loại có giám sát (supervised learning) theo cách truyền thống.
- Việc áp dụng PU Learning (Positive-Unlabeled) buộc phải dựa vào nhãn proxy từ Isolation Forest — bản chất là dùng mô hình không giám sát để tạo nhãn cho mô hình có giám sát, tạo thành vòng lặp giả định không thể kiểm chứng với dữ liệu thực.
- Không có tập kiểm tra (test set) với nhãn thật để đo lường chính xác precision/recall của hệ thống.

**2. Toàn bộ dữ liệu chỉ trong 1 năm duy nhất (2019):** Tất cả các bảng (Customer, Transaction, Activity) đều nằm trong khung thời gian 2019-01 đến 2019-12:
- Không có dữ liệu lịch sử nhiều năm để xây dựng baseline hành vi dài hạn.
- Không thể so sánh seasonal patterns qua các năm.
- Tất cả 290.223 hồ sơ `CLIENT_CREATE_DATE` đều trong năm 2019, khiến biến `TENURE_DAYS` (tuổi tài khoản) bị nén trong khoảng 0–365 ngày. Trong thực tế ngân hàng, tài khoản có thể tồn tại 10–20 năm.

**3. Khối lượng giao dịch tăng trưởng bất thường trong năm:** Số lượng giao dịch tháng 1 (3.203) chỉ bằng 1% tháng 12 (323.689) — tăng 100 lần trong cùng một năm. Hiện tượng này có thể do:
- Dữ liệu được trích xuất theo cách tích lũy (chỉ lấy khách hàng bắt đầu giao dịch từ thời điểm nhất định).
- Survivorship bias — chỉ ghi nhận khách hàng còn hoạt động.
- Hệ quả: Các đặc trưng cửa sổ trượt (SUM_30D, COUNT_7D...) ở đầu năm có rất ít dữ liệu context, khiến velocity ratio bị sai lệch.

| Tháng | Số giao dịch | % so với tháng 12 |
| :---- | :---- | :---- |
| 01/2019 | 3.203 | 1,0% |
| 06/2019 | 74.970 | 23,2% |
| 09/2019 | 172.971 | 53,4% |
| 12/2019 | 323.689 | 100% |

**4. Thiếu hụt thông tin xác thực (45% null):** Hai trường quan trọng cho phát hiện gian lận bị thiếu gần một nửa:
- `IB_REGISTER_DATE`: 131.248/290.223 khách hàng (45,22%) không có ngày đăng ký ebank.
- `VERIFY_METHOD`: 131.276/290.223 (45,23%) không có phương thức xác thực.
- Việc thiếu thông tin xác thực làm giảm khả năng phát hiện dấu hiệu hạ cấp bảo mật (Login Drift) — một trong những chỉ báo quan trọng nhất cho Account Takeover.

**5. Phân phối giao dịch lệch phải cực đoan (Heavy-Tailed):** 54,2% giao dịch có giá trị dưới 1 triệu VND, trong khi chỉ 4% vượt 50 triệu VND. Chênh lệch mean (8,77 triệu) so với median (640.000) đạt 13,7 lần. Phân phối này khiến:
- Các mô hình ML dễ bị bias về phía giao dịch nhỏ lẻ (chiếm đa số).
- Các giao dịch lớn bất thường (chính là đối tượng cần phát hiện) bị coi là outlier ngay cả khi chúng hợp lệ.
- Z-score và các feature dựa trên khoảng cách thống kê mất độ phân giải ở vùng đuôi phân phối.

| Khoảng giá trị | Số giao dịch | Tỷ lệ |
| :---- | :---- | :---- |
| < 1 triệu VND | 768.629 | 54,2% |
| 1M – 10M VND | 455.093 | 32,1% |
| 10M – 50M VND | 137.243 | 9,7% |
| ≥ 50 triệu VND | 57.065 | 4,0% |

**6. Thiếu thông tin địa lý thực và thông tin thiết bị chi tiết:** Bộ dữ liệu chỉ cung cấp `IP_Address_Proxy` (đã mã hóa thành tỉnh/thành) và `Device_ID_Hash` (đã hash). Không có:
- Tọa độ GPS hoặc cell tower để tính Geovelocity chính xác.
- Thông tin device fingerprint chi tiết (phiên bản OS, trình duyệt, jailbreak status).
- Phân loại IP (VPN/Tor/Residential/Datacenter).

**Định hướng tiếp cận:** Với những giới hạn trên, đặc biệt là việc không có nhãn gian lận và phân phối dữ liệu bất cân bằng cực đoan, đề án nhận định rằng việc xây dựng mô hình ML thuần túy có thể không đảm bảo độ tin cậy cần thiết cho bài toán phát hiện gian lận trong trường hợp này. Do đó, đề án định hướng tập trung nhiều hơn vào hệ thống rule-based có cơ sở thống kê (được thiết kế dựa trên kết quả EDA ở các mục 2.1–2.4), kết hợp mô hình ML ở vai trò hỗ trợ và bổ sung — thay vì phụ thuộc hoàn toàn vào khả năng học tự động của mô hình.

> **Gợi ý biểu đồ:**
> - Histogram log-scale: Phân bố `TRANS_AMOUNT` với đánh dấu mean, median, p95, p99 — thể hiện heavy tail.
> - Bar chart: Khối lượng giao dịch theo tháng (01–12/2019), thể hiện sự tăng trưởng bất thường 100x.
> - Stacked bar: Tỷ lệ null/non-null của `IB_REGISTER_DATE` và `VERIFY_METHOD` trên tổng khách hàng.
> - Pie chart: Phân bố giao dịch theo khoảng giá trị (<1M, 1M–10M, 10M–50M, ≥50M).

---

## Phần III: Trích xuất & Kỹ thuật Đặc trưng (Phase 1-2)

Để chuyển hóa dữ liệu thô thành các tín hiệu rủi ro định lượng, hệ thống thực hiện quy trình trích xuất và kỹ thuật đặc trưng qua hai giai đoạn, tạo ra bộ đặc trưng số hóa tối ưu. 

### 3.1. Trích xuất dữ liệu thô (Phase 1 — Data Extraction)

Giai đoạn Data Extraction tập trung vào việc tính toán các thống kê tích lũy và kết nối dữ liệu từ 6 bảng cơ sở dữ liệu.

| Mục | Hạng mục Trích xuất | Đặc trưng / Tính toán | Ý nghĩa & Dấu hiệu Gian lận |
| :--- | :--- | :--- | :--- |
| 3.1.1 | Nối các nguồn dữ liệu | Nối `Data_Transaction` với `Data_Customer`, `Activity`, `Deposit` (theo `ts_dt`) | Tạo ra bức tranh toàn cảnh về hoạt động của khách hàng. |
| 3.1.2 | Tổng hợp cửa sổ trượt | `SUM_AMOUNT`, `COUNT` trên 6 cửa sổ: 1h, 3h, 24h, 48h, 7d, 30d | Bắt tín hiệu tiêu tiền bất thường, số lượng giao dịch dồn dập (Card testing, Bot). |
| 3.1.3 | Thống kê lịch sử khách hàng | `HIST_AVG_CA_BALANCE`, `HIST_AVG_TRANS_AMOUNT` | Làm baseline (cơ sở) để đánh giá độ lệch của giao dịch hiện tại. |
| 3.1.4 | Khoảng cách thời gian giao dịch | `DAYS_SINCE_LAST_TRANS` (số ngày từ giao dịch trước) | Nhận diện tài khoản "ngủ đông thức dậy". |
| 3.1.5 | Người thụ hưởng 24h | `UNIQUE_BENEFICIARIES_24H` (số lượng tài khoản đích) | Bắt tín hiệu phân tán dòng tiền nhanh (Mule Fan-out). |
| 3.1.6 | Thời gian tới sự kiện bảo mật | `HOURS_SINCE_SEC_EVENT` (từ lần đổi PIN/Pass gần nhất) | Khoảng thời gian rất ngắn (< 1h) cảnh báo Account Takeover (ATO). |
| 3.1.7 | Thống kê Sinh trắc học | `HIST_BIOMETRIC_RATIO` (tỷ lệ dùng FaceID/Vân tay) | Phát hiện sự hạ cấp phương thức bảo mật. |
| 3.1.8 | Phân tích Benford's Law | `BENFORD_DEV` (KL-Divergence, ngưỡng N ≥ 5) | Đánh giá độ phân kỳ của chữ số đầu tiên so với quy luật tự nhiên. |
| 3.1.9 | Chuỗi Markov bậc 2 | `ACTIVITY_SEQ_RARITY` (nội suy backoff trên chuỗi thao tác) | Tìm ra các hành vi điều hướng ứng dụng hiếm gặp hoặc bot tự động. |
| 3.1.10 | Xác suất giờ giao dịch | `TRANS_HOUR_PROB` (lịch sử khách hàng hoặc toàn hệ thống) | Xác định mức độ quen thuộc của khung giờ thực hiện giao dịch của khách hàng. Khung giờ lạ là chỉ báo rủi ro cao. |

### 3.2. Xây dựng bộ lọc rule-based (8 loại rule)

Dựa trên kết quả phân tích khám phá dữ liệu (EDA) về hành vi giao dịch và sự kiện bảo mật, hệ thống xây dựng 8 Rule nhằm giải quyết bài toán định tuyến phân tầng (Hierarchical Routing Pipeline) tại Tier 1. Mục tiêu của bộ lọc là **BLOCK** ngay lập tức các giao dịch có độ tin cậy rủi ro cực cao (Smoking gun), và **BYPASS** (cho qua) các giao dịch rủi ro cực thấp nhằm giảm tải tính toán cho mô hình ML ở Tier 2.

**1. DormancyWakeupRule (🔴 BLOCK)**
* **Nội dung rule**: `DAYS_SINCE_LAST_TRANS > 90` AND `TRANS_AMOUNT > 10,000,000` AND `TRANS_LV2 = 'Outside_bank'`
* **Cơ sở**: Tội phạm rửa tiền thường thu mua tài khoản (Mule Accounts), để "ngủ đông" từ 3-6 tháng nhằm trốn tránh hệ thống giám sát của ngân hàng. Sau đó, chúng đột ngột kích hoạt lại để chuyển dòng tiền bẩn với số lượng lớn ra bên ngoài.
* **EDA**: Phân tích trên tập 1.4 triệu giao dịch cho thấy chỉ có 867 giao dịch (0.06%) vi phạm điều kiện này. Tỷ lệ báo động giả (False Positive) là cực thấp vì người dùng thật rất hiếm khi bỏ quên tài khoản 3 tháng rồi bất ngờ chuyển ra ngoài hơn 10 triệu đồng.

**2. ATOPanicRule (🔴 BLOCK)**
* **Nội dung rule**: `HOURS_SINCE_SEC_EVENT <= 1.0` AND `TRANS_AMOUNT > 10,000,000` AND `TRANS_LV2 = 'Outside_bank'`. Chặn (Fraud) nếu customer tenure (tuổi tài khoản) $\ge$ 1 ngày; chuyển về diện Nghi vấn (Ambiguous -1) nếu tenure < 1 ngày.
* **Cơ sở**: Chặn hành vi chiếm đoạt tài khoản (ATO) kinh điển. Loại trừ tài khoản mới tạo hoạt động trong ngày đầu (tenure < 1 ngày) sang diện nghi vấn để xử lý mềm thay vì chặn cứng.
* **EDA**: Dữ liệu sự kiện bảo mật ghi nhận ~1.200 giao dịch chớp nhoáng trong cửa sổ 1 giờ sau khi đổi thông tin xác thực. Phân nhóm theo tenure giúp giảm thiểu ảnh hưởng đến hành trình đăng ký/kích hoạt của người dùng mới.

**3. HourlyAnomalyRule (🔴 BLOCK)**
* **Nội dung rule**: `TRANS_HOUR_PROB < 0.015` AND `TRANS_AMOUNT > 10,000,000`
* **Cơ sở**: Chặn các giao dịch phát sinh đột xuất vào khoảng thời gian mà lịch sử khách hàng rất ít hoạt động (xác suất < 1.5%), kết hợp số tiền lớn (> 10 triệu) - chỉ báo rất mạnh cho các đợt cash-out tốc độ của tội phạm chiếm quyền tài khoản (ATO).
* **EDA**: Rất hiếm khi khách hàng bình thường chuyển tiền lớn vào những khung giờ lạ của chính họ.

**4. CreditCardBustOutRule (🔴 BLOCK)**
* **Nội dung rule**: `LIMIT_UTILIZATION_VELOCITY >= 0.45` AND `TRANS_AMOUNT > 20,000,000` AND `BALANCE_COVERAGE_RATIO > 10.0`
* **Cơ sở**: Chặn hành vi vét hạn mức thẻ tín dụng tẩu tán tài sản đột biến (Bust-out Fraud). Kết hợp cả tốc độ tăng trưởng dư nợ (velocity MoM), số tiền lớn và số dư tài khoản thanh toán siêu thấp để bắt trúng các tài khoản bị chiếm đoạt hoặc mule.
* **EDA**: Chỉ kích hoạt chặn trên **282 giao dịch** trong toàn bộ 1.4 triệu dòng lịch sử (~0.0199%), đảm bảo độ chính xác (Precision) cực cao và giảm thiểu tối đa báo động giả.

**5. LowRiskChannelBypassRule (🟢 BYPASS)**
* **Nội dung rule**: `TRANS_LV2 IN ('Utilities_payment', 'Credit_card_repayment', 'Lending_repayment', 'Cable', 'Game', 'Lifestyle_payment', 'MCPP')` AND `TRANS_AMOUNT < 5,000,000`
* **Cơ sở**: Kẻ gian muốn chiếm đoạt tài sản sẽ không bao giờ dùng tiền ăn cắp để thanh toán hóa đơn điện/nước hay trả nợ thẻ tín dụng cho nạn nhân.
* **EDA**: Bypass này giúp lọc đi ~14.000 giao dịch/ngày. Ngưỡng 5 triệu VND được chọn (thay vì 10 triệu) nhằm đề phòng kỹ thuật Structuring Overpayment (Rửa tiền qua thanh toán thừa dư nợ thẻ tín dụng).

**6. SequenceRarityRule (🟢 BYPASS)**
* **Nội dung rule**: `ACTIVITY_SEQ_RARITY > -1.0` AND `TRANS_AMOUNT < 5,000,000`
* **Cơ sở**: Các chuỗi hành động (activity sequence) điển hình (có điểm độ hiếm > -1.0) thường phản ánh hành vi điều hướng, sử dụng bình thường, quen thuộc của người dùng. Kết hợp với lượng giao dịch trung bình nhỏ, mức độ rủi ro gian lận gần như không có.
* **EDA**: Mô hình Markov bậc 2 cho thấy đa phần giao dịch sinh hoạt hàng ngày đi theo các luồng thao tác quen thuộc. Việc nâng ngưỡng lên 5 triệu VND (thay vì 500.000 VND) giúp tăng độ phủ tự động cho các giao dịch chuyển khoản sinh hoạt thông thường mà vẫn đảm bảo an toàn vì chuỗi thao tác hoàn toàn chuẩn chỉ.

**7. VelocityBypassRule (🟢 BYPASS)**
* **Nội dung rule**: `TRANS_AMOUNT < 500,000` AND `COUNT_1H <= 1` AND `COUNT_24H <= 2`
* **Cơ sở**: Tần suất giao dịch ở mức thưa thớt bình thường (không dồn dập) kết hợp quy mô giao dịch nhỏ cho thấy đây không phải hành vi Card Testing (thử thẻ) hay Mule Fan-out (chuyển tiền phân tán).
* **EDA**: Tần suất giao dịch chuẩn ở mức thưa thớt, trung bình đạt 1.03 giao dịch/giờ và 99% khách hàng chỉ thực hiện tối đa 11 lệnh/ngày. Tốc độ giao dịch của kẻ gian thường đẩy lên 3-6 lệnh/giờ. Do đó rule Bypass này hoạt động vô cùng an toàn.

**8. SmallAmountBypassRule (🟢 BYPASS)**
* **Nội dung rule**: `TRANS_AMOUNT < 500,000`
* **Cơ sở**: Bỏ qua trực tiếp tất cả giao dịch có giá trị cực nhỏ (dưới 500.000 VND). Trong hệ thống ngân hàng số bán lẻ, các giao dịch dưới 500K thường là thanh toán sinh hoạt, ăn uống hoặc nạp tiền thẻ cào giá trị thấp, rủi ro gian lận chiếm đoạt diện rộng là vô cùng thấp.
* **EDA**: Phân loại giao dịch cho thấy hơn 35% giao dịch trong hệ thống thuộc phân khúc dưới 500.000 VND. Việc tự động bypass các giao dịch này giúp giảm hơn 1/3 tải lượng tính toán cho toàn bộ pipeline xử lý sâu ở Tier 2 và loại bỏ phần lớn cảnh báo giả ở phân khúc tiền nhỏ.

### 3.3. Kỹ thuật đặc trưng (Phase 2 — Feature Engineering)

Giai đoạn Feature Engineering (thực hiện bởi `NewFeaturesPreprocessor`) tổng hợp các thông tin đã trích xuất thành các đặc trưng rủi ro chất lượng cao (ratios, z-scores, spike indices). Sau quá trình sàng lọc loại bỏ các đặc trưng gây nhiễu và kém hiệu quả, hệ thống tối ưu hóa bộ đặc trưng còn lại **8 đặc trưng rủi ro cốt lõi** nạp trực tiếp vào mô hình học máy ở Tier 2, kết hợp với các đặc trưng phụ trợ dùng riêng cho bộ lọc Rule-based ở Tier 1.

#### 3.3.1. 8 đặc trưng rủi ro nạp vào mô hình ML (Tier 2)

##### Nhóm 1: Lệch chuẩn Số tiền (Amount Deviation)
Nhóm đặc trưng này cá nhân hóa rủi ro theo từng khách hàng, thay vì áp dụng ngưỡng tuyệt đối cứng nhắc — giải quyết bài toán chênh lệch thu nhập giữa các phân khúc khách hàng (sinh viên vs. doanh nhân).

| Tên Đặc trưng | Định nghĩa | Measurement | Ý nghĩa trong mô hình |
| :--- | :--- | :--- | :--- |
| `TRANS_AMOUNT_Z_SCORE` | Mức độ lệch chuẩn thống kê của số tiền giao dịch hiện tại so với lịch sử chi tiêu cá nhân của khách hàng. | `(TRANS_AMOUNT - HIST_AVG_TRANS_AMOUNT) / HIST_STD_TRANS_AMOUNT` (nếu std > 1e-5; ngược lại = 0.0) | Kẻ chiếm đoạt tài khoản (ATO) luôn muốn rút tối đa tiền, tạo ra độ lệch chuẩn Z-Score cực lớn. Công thức Z-score thống kê giúp loại bỏ nhiễu biên và chuẩn hóa chính xác mức độ bất thường. |
| `BALANCE_COVERAGE_RATIO` | Tỷ lệ giữa số tiền giao dịch và số dư trung bình lịch sử tài khoản. | `TRANS_AMOUNT / (HIST_AVG_CA_BALANCE + 1e-5)` | Dấu hiệu kinh điển của Money Mule: dòng tiền vừa vào lập tức bị chuyển đi hết, khiến số tiền giao dịch vượt xa số dư bình quân lâu dài. Tỷ lệ > 1.0 cho thấy dấu hiệu "rút cạn" hoặc trung chuyển tiền. |
| `TRANS_AMOUNT_VS_30D_AVG_RATIO` | So sánh số tiền giao dịch hiện tại với mức chi tiêu trung bình ngắn hạn 30 ngày gần nhất. | `TRANS_AMOUNT / (SUM_AMOUNT_30D / (COUNT_30D + 1e-5) + 1e-5)` | Hoạt động như "bộ lọc thích ứng": nếu khách hàng thực sự đã bắt đầu chi tiêu cao gần đây (nhờ tăng thu nhập), tỷ lệ này sẽ thấp, tránh cảnh báo sai. Ngược lại, đột biến gấp nhiều lần thói quen tháng sẽ bị phát hiện. |

##### Nhóm 2: Đột biến Dòng tiền & Tần suất (Spike Detection)
Hệ thống sử dụng các đặc trưng Spike (đột biến) đa tầng thay thế cho các tỷ lệ Velocity cũ nhằm bắt chính xác các hành vi dồn tiền dồn dập vào các khoảng thời gian cực ngắn so với thói quen nền dài hơn.

| Tên Đặc trưng | Định nghĩa | Measurement | Ý nghĩa trong mô hình |
| :--- | :--- | :--- | :--- |
| `SPIKE_1H_VS_24H` | Tỷ lệ bất thường kết hợp giữa số tiền và số lượng giao dịch phát sinh trong 1 giờ qua so với 24 giờ. | `(1.0 - v_amt_1h_24h) * (1.0 - v_cnt_1h_24h)` với `v_*` là tỷ lệ lượng/lượt giao dịch (1H / 24H) | Trị số tiến gần về 1.0 khi có một lượng giao dịch lớn và dồn dập xuất hiện trong 1 giờ qua mà trước đó 24 giờ hầu như không hoạt động (dấu hiệu botnet hoặc ATO vét tiền). |
| `SPIKE_24H_VS_7D` | Tỷ lệ bất thường kết hợp giữa số tiền và số lượng giao dịch trong 24 giờ qua so với 7 ngày. | `(1.0 - v_amt_24h_7d) * (1.0 - v_cnt_24h_7d)` với `v_*` là tỷ lệ lượng/lượt giao dịch (24H / 7D) | Chỉ ra hành vi đột biến tiêu dùng/rút tiền tích lũy trong vòng 1 ngày qua so với thói quen của cả tuần. |
| `SPIKE_7D_VS_30D` | Tỷ lệ bất thường kết hợp giữa số tiền và số lượng giao dịch trong 7 ngày qua so với 30 ngày. | `(1.0 - v_amt_7d_30d) * (1.0 - v_cnt_7d_30d)` với `v_*` là tỷ lệ lượng/lượt giao dịch (7D / 30D) | Phát hiện sự bất thường có tính chất chu kỳ ngắn hạn so với thói quen tháng. Rất hữu ích khi tội phạm chia nhỏ giao dịch ra vài ngày để tránh các rule 1h/24h. |

##### Nhóm 3: Phân tích Thống kê & Xác suất Chuỗi (Statistical & Sequence)
Nhóm đặc trưng phân tích sâu hành vi điều hướng ứng dụng và tính hợp lý của số tiền giao dịch dựa trên các quy luật toán học khách quan.

| Tên Đặc trưng | Định nghĩa | Measurement | Ý nghĩa trong mô hình |
| :--- | :--- | :--- | :--- |
| `BENFORD_DEV` | Độ lệch phân phối chữ số đầu tiên của các khoản tiền giao dịch so với định luật Benford. | KL-Divergence: `Σ p_d * ln(p_d / q_d)`, với `q_d = log10(1 + 1/d)` | Khi tội phạm chia nhỏ dòng tiền (structuring) để tránh ngưỡng báo động, phân bố chữ số đầu tiên sẽ lệch nghiêm trọng so với tự nhiên. Chỉ số cao (>0.15) cho thấy sự sắp đặt dòng tiền chủ quan. |
| `ACTIVITY_SEQ_RARITY` | Điểm số độ hiếm của chuỗi thao tác trên ứng dụng di động dựa trên mô hình Markov bậc 2. | Xác suất chuyển tiếp bậc 2 smoothed bằng nội suy backoff: `0.7*P_2nd + 0.2*P_1st + 0.1*P_global`. | Phát hiện các kịch bản bot tự động hoặc kẻ gian điều hướng nhanh để đổi mật khẩu rồi chuyển tiền ngay. Chuỗi thao tác bất thường sẽ tạo ra log-probability âm rất sâu. |

#### 3.3.2. Các đặc trưng phụ trợ phục vụ bộ lọc Rule-based (Tier 1)

Các đặc trưng này được nạp vào để chạy hệ thống luật cứng ở Tier 1, giúp đưa ra quyết định Block hoặc Bypass nhanh chóng trước khi dữ liệu đi vào mô hình ML:

*   `DAYS_SINCE_LAST_TRANS` (Đo khoảng thời gian im lặng ngày): Sử dụng trong `DormancyWakeupRule` để phát hiện tài khoản "ngủ đông" bị kích hoạt chuyển tiền lớn ra ngoài.
*   `HOURS_SINCE_SEC_EVENT` (Đo số giờ kể từ sự kiện bảo mật gần nhất): Sử dụng trong `ATOPanicRule` để phát hiện việc chuyển tiền ngay sau khi đổi mật khẩu/PIN.
*   `LIMIT_UTILIZATION_VELOCITY` (Tốc độ vét hạn mức tín dụng MoM): Sử dụng trong `CreditCardBustOutRule` để chặn vét thẻ tín dụng tẩu tán tài sản.
*   `TRANS_HOUR_PROB` (Xác suất giờ giao dịch cá nhân): Sử dụng trong `HourlyAnomalyRule` để phát hiện giao dịch phát sinh vào khung giờ lạ của khách hàng.
*   `COUNT_1H`, `COUNT_24H` (Lượt giao dịch trượt): Sử dụng trong `VelocityBypassRule` để bypass các giao dịch thưa thớt, an toàn.

#### 3.3.3. Tổng kết bộ đặc trưng
Bộ pipeline hoàn thiện bao gồm **8 đặc trưng rủi ro nạp trực tiếp vào mô hình ML (Tier 2)** và **5 đặc trưng bổ trợ dùng cho bộ lọc Rule-based (Tier 1)**. Sự phân chia này giúp hệ thống đạt độ chính xác cao, đẩy nhanh tốc độ suy luận của mô hình XGBoost và tối ưu hóa hiệu năng xử lý đặc trưng trên tập dữ liệu lớn.

---

## Phần IV: Huấn luyện Mô hình (Phase 3 — PU Learning)

Sau khi hoàn thành thiết lập bộ đặc trưng số hóa, hệ thống tiến hành huấn luyện mô hình phân loại giao dịch bất thường. Tuy nhiên, bộ dữ liệu mẫu không cung cấp bất kỳ nhãn gian lận đã xác nhận nào — đây là thách thức cốt lõi quyết định toàn bộ chiến lược huấn luyện.

### 4.1. Vấn đề: Không có nhãn gian lận

Trong thực tế vận hành ngân hàng, nhãn gian lận (fraud labels) là tài sản cực kỳ hiếm và tốn kém:

- **Chi phí gán nhãn cao:** Mỗi giao dịch cần chuyên gia kiểm soát rủi ro xác minh thủ công, đối chiếu với nhiều nguồn dữ liệu (lịch sử khách hàng, nhật ký sự kiện bảo mật, phản hồi khiếu nại). Chi phí trung bình để gán nhãn một giao dịch có thể tốn hàng chục phút công sức chuyên viên.
- **Tỷ lệ gian lận cực thấp:** Trong hệ thống thực tế, tỷ lệ giao dịch gian lận thường chỉ chiếm 0.1% – 3% tổng khối lượng giao dịch. Việc quét thủ công hàng triệu giao dịch để tìm vài nghìn ca gian lận là không khả thi.
- **Nhãn thiếu hoàn toàn:** Bộ dữ liệu mẫu cung cấp 1.418.030 giao dịch nhưng không có bất kỳ nhãn nào (`confirmed_frauds.json` rỗng). Không thể huấn luyện mô hình phân loại có giám sát (supervised learning) theo cách truyền thống.

**Lựa chọn giải pháp: Positive-Unlabeled (PU) Learning.** Thay vì yêu cầu nhãn đầy đủ (positive vs. negative), PU Learning chỉ cần hai tập dữ liệu:

- **Tập P (Positive):** Các mẫu được xác định là bất thường — trong trường hợp này, được khởi tạo bằng thuật toán phát hiện bất thường không giám sát (Isolation Forest).
- **Tập U (Unlabeled):** Tất cả các mẫu còn lại — có thể chứa lẫn cả giao dịch hợp lệ (true negative) và giao dịch gian lận chưa bị phát hiện (hidden positive).

Quy trình PU Learning sau đó sử dụng 3 lớp kiểm soát nhiễu (Spy Filtering, CVuO, Elkan-Noto Calibration) để dần dần tách tập U thành nhóm "chắc chắn an toàn" và nhóm "nghi vấn", giảm thiểu ảnh hưởng của nhiễu nhãn lên mô hình cuối cùng.

> **Gợi ý biểu đồ:**
> - Flowchart PU Learning: Luồng 5 bước từ Isolation Forest → Spy Filtering → CVuO → XGBoost → Elkan-Noto, thể hiện sự thu hẹp dần của tập U qua mỗi bước lọc.

### 4.2. Bước 1: Khởi tạo nhãn Proxy bằng Isolation Forest

Do không có nhãn gian lận thực, hệ thống sử dụng thuật toán **Isolation Forest** để tạo nhãn proxy (nhãn thay thế) ban đầu. Isolation Forest hoạt động trên nguyên lý: các điểm dữ liệu bất thường (anomaly) cần ít bước phân chia cây ngẫu nhiên hơn để bị cô lập khỏi phần còn lại, do chúng nằm ở vùng thưa thớt của không gian đặc trưng.

**Tham số chính:**
- **Contamination rate** `c = 0.03` (3%): Tỷ lệ giao dịch bất thường được giả định trong dữ liệu. Giá trị 3% được chọn dựa trên thống kê ngành tài chính (tỷ lệ gian lận phổ biến dao động 1-5%) và phân tích EDA (mục 2.1–2.4) cho thấy tỷ lệ giao dịch đáng ngờ nằm trong khoảng 2-4%.

**Công thức gán nhãn:**

$$s_i = \begin{cases} 1 & \text{nếu Isolation Forest phân loại } x_i \text{ là bất thường (anomaly)} \\ 0 & \text{còn lại (unlabeled)} \end{cases}$$

Kết quả thu được hai tập dữ liệu:

| Tập | Ký hiệu | Mô tả |
| :--- | :--- | :--- |
| Positive (nghi vấn bất thường) | $P = \{i : s_i = 1\}$ | Các mẫu được Isolation Forest đánh dấu là outlier. Đây là nhãn proxy, không phải nhãn gian lận xác nhận. |
| Unlabeled (chưa gán nhãn) | $U = \{i : s_i = 0\}$ | Tất cả mẫu còn lại — có thể chứa lẫn cả giao dịch hợp lệ và giao dịch gian lận chưa bị phát hiện. |

**Hạn chế cần xử lý:** Nhãn proxy từ Isolation Forest có hai dạng nhiễu:
1. **False Positive trong P:** Một số giao dịch hợp lệ nhưng có giá trị bất thường (VIP mua nhà, chuyển lương cuối năm) bị gán nhầm vào tập P.
2. **Hidden Positive trong U:** Một số giao dịch gian lận tinh vi "hòa nhập" đủ tốt vào dữ liệu bình thường, không bị Isolation Forest phát hiện. Các bước tiếp theo (Spy Filtering, CVuO) được thiết kế để giảm thiểu cả hai dạng nhiễu này.

### 4.3. Bước 2: Lọc dữ liệu gián điệp PAYN (Spy Filtering)

Mục tiêu của bước này là xác định một tập con **chắc chắn an toàn** ($N_{\text{confirmed}}$) từ trong tập $U$ bằng kỹ thuật "cấy gián điệp" (spy embedding).

**Quy trình thực hiện:**

**Bước 2a — Cấy gián điệp:** Chọn ngẫu nhiên 10% mẫu từ tập $P$ làm "gián điệp" (spies) và chuyển chúng sang tập $U$:

$$\text{Spies} \subset P, \quad |\text{Spies}| = \lfloor 0.10 \cdot |P| \rfloor$$

**Bước 2b — Huấn luyện mô hình sơ bộ:** Huấn luyện một XGBoost tạm thời với:
- Lớp Positive: $P \setminus \text{Spies}$ (các mẫu nghi vấn, trừ gián điệp)
- Lớp Negative: $U \cup \text{Spies}$ (toàn bộ mẫu chưa gán nhãn, bao gồm gián điệp)

**Bước 2c — Xác định ngưỡng gián điệp:** Dự đoán xác suất cho các mẫu gián điệp. Vì gián điệp là mẫu bất thường thật sự nhưng bị trộn vào lớp Negative, những mẫu gián điệp nào được mô hình dự đoán với xác suất thấp nhất chính là "ranh giới an toàn" — mọi mẫu trong $U$ có xác suất thấp hơn mức này gần như chắc chắn là giao dịch hợp lệ thật:

$$\tau_{\text{spy}} = \text{Percentile}_{5}\bigl(\{g(x_j)\}_{j \in \text{Spies}}\bigr)$$

Ngưỡng phân vị thứ 5 (thay vì 1 hay 10) được chọn để đảm bảo tính bảo thủ: chỉ những mẫu nào thật sự "không giống bất thường" mới được xác nhận là an toàn.

**Bước 2d — Phân tách tập U:**

$$N_{\text{confirmed}} = \{j \in U : g(x_j) < \tau_{\text{spy}}\}$$

$$U_{\text{remaining}} = U \setminus N_{\text{confirmed}}$$

Kết quả: tập $N_{\text{confirmed}}$ chứa các giao dịch có điểm rủi ro thấp hơn cả mẫu gián điệp yếu nhất — đây là nhóm "chắc chắn không phải gian lận". Phần còn lại $U_{\text{remaining}}$ vẫn nằm trong vùng mơ hồ, cần được xử lý tiếp ở bước CVuO.

### 4.4. Bước 3: Tối ưu hóa không gắn nhãn có kiểm chứng chéo (CVuO)

Mục tiêu của bước CVuO (Cross-Validated unlabeled Optimization) là lọc bỏ các mẫu gian lận ẩn (hidden positives) còn lẫn trong tập $U_{\text{remaining}}$ — những mẫu mà Isolation Forest bỏ sót nhưng gây nhiễu nếu được gán nhãn "an toàn" trong quá trình huấn luyện.

**Quy trình thực hiện:**

**Bước 3a — Kiểm chứng chéo 5-fold:** Chia $U_{\text{remaining}}$ thành 5 phần (folds) bằng nhau. Với mỗi fold:
- Huấn luyện một mô hình XGBoost tạm thời chỉ trên tập $P \cup N_{\text{confirmed}}$ (nhãn đã đáng tin cậy).
- Dự đoán xác suất cho các mẫu trong fold đang giữ lại (held-out fold).

**Bước 3b — Tính log-loss giả định:** Với mỗi mẫu trong $U_{\text{remaining}}$, tính log-loss giả định rằng nó là giao dịch hợp lệ (negative, $y = 0$):

$$\ell_j = -\ln(1 - g(x_j) + 10^{-15})$$

Nếu mô hình cho rằng mẫu đó có xác suất gian lận cao ($g(x_j) \approx 1$), log-loss sẽ rất lớn — phản ánh sự mâu thuẫn giữa giả định "an toàn" và thực tế dữ liệu.

**Bước 3c — Loại bỏ mẫu nhiễu:** Loại bỏ 10% mẫu có log-loss cao nhất — đây là những mẫu mà mô hình đánh giá không phù hợp với lớp negative, có khả năng cao là gian lận ẩn:

$$U_{\text{filtered}} = \{j \in U_{\text{remaining}} : \ell_j \leq \text{Percentile}_{90}(\{\ell_k\})\}$$

Kết quả: Tập $U_{\text{filtered}}$ đã được "khử nhiễu" — giảm đáng kể tỷ lệ hidden positives lẫn vào, tạo nền tảng sạch hơn cho bước huấn luyện cuối cùng.

### 4.5. Bước 4: Huấn luyện XGBoost cuối cùng

Sau 3 bước lọc (Isolation Forest → Spy Filtering → CVuO), hệ thống thu được bộ nhãn đã được kiểm soát nhiễu tối đa:

| Vai trò | Thành phần | Mô tả |
| :--- | :--- | :--- |
| Positive (gian lận nghi vấn) | Toàn bộ $P$ | Các mẫu được Isolation Forest đánh dấu ban đầu |
| Negative (an toàn xác nhận) | $N_{\text{confirmed}} \cup U_{\text{filtered}}$ | Mẫu đã qua 2 lớp lọc: spy filtering + CVuO |

Mô hình XGBoost cuối cùng được huấn luyện trên bộ nhãn này với các siêu tham số được thiết kế theo nguyên tắc **Rademacher Complexity Regularization** — kiểm soát chặt chẽ độ phức tạp mô hình để giảm thiểu overfitting trên nhãn proxy có nhiễu:

| Tham số | Giá trị | Vai trò |
| :--- | :--- | :--- |
| `n_estimators` | 100 | Số vòng boosting. Giới hạn ở mức vừa phải để tránh mô hình "ghi nhớ" nhiễu trong nhãn proxy. |
| `max_depth` | 3 | Độ sâu tối đa của mỗi cây quyết định. Giá trị thấp (3 tầng) buộc mô hình học các mô hình (patterns) tổng quát thay vì ghi nhớ từng mẫu. |
| `reg_alpha` ($\alpha$) | 1.0 | Chính quy hóa L1 (Lasso) — tạo tính thưa (sparsity), loại bỏ các feature không đóng góp ý nghĩa. |
| `reg_lambda` ($\lambda$) | 2.0 | Chính quy hóa L2 (Ridge) — kiểm soát biên độ trọng số lá (leaf weights), ngăn mô hình đưa ra dự đoán cực đoan trên các vùng dữ liệu thưa. |
| `learning_rate` ($\eta$) | 0.05 | Hệ số co rút (shrinkage). Giá trị thấp (0.05) buộc mô hình hội tụ chậm và ổn định hơn, giảm nhạy cảm với nhiễu nhãn. |

**Cơ sở lý thuyết — Rademacher Complexity:** Lý thuyết Rademacher Complexity (Bartlett & Mendelson, 2002) chứng minh rằng sai số tổng quát hóa (generalization error) của mô hình bị chặn trên bởi tổng của sai số huấn luyện và độ phức tạp Rademacher $\mathcal{R}_n(\mathcal{H})$ của lớp giả thuyết:

$$\text{Lỗi tổng quát} \leq \text{Lỗi huấn luyện} + 2\mathcal{R}_n(\mathcal{H}) + O\!\left(\sqrt{\frac{\ln(1/\delta)}{n}}\right)$$

Việc giới hạn `max_depth = 3` kết hợp chính quy hóa L1 + L2 mạnh (1.0 + 2.0) trực tiếp thu hẹp lớp giả thuyết $\mathcal{H}$, kéo giảm $\mathcal{R}_n(\mathcal{H})$. Điều này đặc biệt quan trọng trong bối cảnh PU Learning: khi nhãn huấn luyện có nhiễu, mô hình có độ phức tạp cao sẽ "ghi nhớ" cả nhiễu, dẫn đến generalization kém trên dữ liệu thực tế.

### 4.6. Bước 5: Hiệu chỉnh xác suất Elkan-Noto

Xác suất đầu ra $g(x)$ từ XGBoost bị thiên lệch (biased) vì mô hình được huấn luyện trên nhãn PU (noisy proxy labels), không phải nhãn gian lận thật. Cụ thể, mô hình chỉ phân biệt giữa "giống tập P" và "giống tập U", chứ không phải giữa "gian lận" và "hợp lệ".

Phương pháp hiệu chỉnh Elkan-Noto (Elkan & Noto, 2008) điều chỉnh xác suất bằng cách ước lượng tỷ lệ nhãn dương thực sự trong tập P:

**Bước 5a — Ước lượng hệ số hiệu chỉnh:** Tính xác suất trung bình mà mô hình gán cho các mẫu trong tập P:

$$\hat{c} = \frac{1}{|P|}\sum_{j \in P} g(x_j)$$

Trực giác: Nếu mô hình hoàn hảo, tất cả mẫu trong $P$ đều có $g(x) = 1.0$, nên $\hat{c} = 1.0$. Trong thực tế, một số mẫu trong $P$ là false positive (giao dịch hợp lệ bị đánh dấu nhầm), nên $\hat{c} < 1.0$.

**Bước 5b — Hiệu chỉnh xác suất:**

$$P(\text{fraud} | x) = \min\!\left(\frac{g(x)}{\hat{c}},\; 1.0\right)$$

Phép chia cho $\hat{c}$ "kéo giãn" phân bố xác suất, bù đắp cho sự thiên lệch do nhiễu nhãn. Hàm $\min(\cdot, 1.0)$ đảm bảo xác suất không vượt quá 1.

### 4.7. Ngưỡng quyết định

Sau khi hiệu chỉnh, hệ thống cần xác định ngưỡng quyết định $\tau$ để phân loại nhị phân: giao dịch nào bị gắn cờ gian lận, giao dịch nào được thông qua.

**Nguyên tắc thiết kế:** Ngưỡng $\tau$ được đặt sao cho tỷ lệ giao dịch bị gắn cờ trên tập huấn luyện khớp với contamination rate $c = 3\%$ ban đầu. Điều này đảm bảo tính nhất quán giữa giả định ở bước Isolation Forest và hành vi phân loại cuối cùng:

$$\tau = \text{Percentile}_{97}\!\bigl(\{P(\text{fraud}|x_i)\}_{i \in \text{training}}\bigr)$$

**Quy tắc phân loại:**

$$\hat{y} = \begin{cases} 1 \text{ (gắn cờ gian lận)} & \text{nếu } P(\text{fraud}|x) \geq \tau \\ 0 \text{ (thông qua)} & \text{nếu } P(\text{fraud}|x) < \tau \end{cases}$$

Giao dịch bị gắn cờ ($\hat{y} = 1$) sẽ được chuyển tiếp sang Tier 3 — Causal Explanation để tạo giải trình SHAP, phân tích tương tác và đề xuất phản biện (counterfactual recourse) phục vụ chuyên viên kiểm soát rủi ro.

---

## Phần V: Suy luận Phân tầng & Giải thích (Phase 4 — Tiered Inference)

### 5.1. Tổng quan kiến trúc 3 tầng
Hệ thống phát hiện gian lận vận hành theo kiến trúc 3 tầng (3-Tier Hierarchical Routing) nhằm giải quyết bài toán đánh đổi giữa chi phí tính toán, độ trễ (latency) và độ chính xác. Bằng cách sử dụng các luật cứng (rule-based) để xử lý nhanh phần lớn giao dịch cực đoan (trắng/đen), hệ thống chỉ dành nguồn lực tính toán học máy (ML) và giải thích nhân quả (xAI) cho vùng xám (ambiguous events) — nơi hành vi gian lận ẩn giấu tinh vi nhất.

### 5.2. Tầng 1: Bỏ qua Nhanh bằng Luật (High-Speed Rule Bypass)
Tất cả giao dịch trước tiên đi qua bộ lọc Deterministic Rules gồm 5 luật (đã trình bày chi tiết tại mục 3.2):
- **Cơ chế BLOCK (Chặn ngay lập tức):** Các giao dịch vi phạm `DormancyWakeupRule` hoặc `ATOPanicRule` mang dấu vết rõ ràng (Smoking gun) của gian lận (Account Takeover, Mule) sẽ bị gắn cờ ngay lập tức mà không cần gọi ML.
- **Cơ chế BYPASS (Cho qua an toàn):** Các giao dịch thỏa mãn các điều kiện rủi ro cực thấp sẽ được đánh dấu an toàn (score = 0.0) và bỏ qua toàn bộ pipeline phía sau. Các điều kiện BYPASS chính gồm:
  - **Điều kiện A (Sequence + Amount):** Chuỗi hành động bình thường (`ACTIVITY_SEQ_RARITY > -1.0`) VÀ số tiền nhỏ (`TRANS_AMOUNT < 500,000`).
  - **Điều kiện B (Velocity + Amount):** Tần suất thưa thớt (`COUNT_1H <= 1` và `COUNT_24H <= 2`) VÀ số tiền nhỏ (`TRANS_AMOUNT < 500,000`).
  - **Điều kiện C (Kênh rủi ro thấp):** Thanh toán hóa đơn, điện nước, trả nợ thẻ tín dụng với quy mô nhỏ (`LowRiskChannelBypassRule`).

**Kết quả:** Thực nghiệm trong hệ thống thực tế cho thấy Tầng 1 giúp lọc bỏ an toàn ~95% lưu lượng giao dịch hàng ngày (chỉ tính 2 điều kiện A và B), tiết kiệm khối lượng khổng lồ chi phí tính toán cho hệ thống.

### 5.3. Tầng 2: Phân loại ML (XGBoost + Elkan-Noto)
Chỉ những giao dịch không vượt qua được Tầng 1 (rơi vào vùng xám) mới được tính toán toàn bộ 25 đặc trưng số hóa (Phase 2) và được đưa vào mô hình XGBoost. 

Tại đây, mỗi giao dịch vùng xám nhận được:
- **Xác suất hiệu chỉnh:** $P(\text{fraud}|x)$ đã qua hiệu chỉnh Elkan-Noto bù trừ thiên lệch do PU Learning.
- **Phân loại nhị phân:** $\hat{y} = \mathbb{1}[P(\text{fraud}|x) \geq \tau]$. Nếu xác suất này bằng hoặc vượt ngưỡng $\tau$, giao dịch bị gắn cờ bất thường (Anomaly Score) và được chuyển sang Tầng 3.

### 5.4. Tầng 3: Giải thích Nhân quả (xAI)
Các mô hình ML truyền thống hoạt động như một "hộp đen". Để chuyên viên kiểm soát rủi ro có cơ sở đưa ra quyết định xử lý (đóng băng tài khoản, gọi điện xác minh khách hàng), hệ thống áp dụng Explainable AI (xAI) độc quyền chỉ dành riêng cho các giao dịch bị gắn cờ.

#### 5.4.1. SHAP Feature Contributions
Sử dụng thuật toán TreeSHAP để phân rã điểm số bất thường thành tổng đóng góp (additive contribution) của từng đặc trưng:

$$g(x) = \phi_0 + \sum_{j=1}^{F} \phi_j$$

Với $\phi_0$ là rủi ro nền, $\phi_j$ là giá trị đóng góp cận biên của đặc trưng $j$. Hệ thống tự động trích xuất Top 3 đặc trưng có $\phi_j$ dương cao nhất và chuyển đổi chúng thành văn bản ngôn ngữ tự nhiên thông qua một hệ thống template tất định. Ví dụ:
- `ACTIVITY_SEQ_RARITY`: "Chuỗi hành vi điều hướng ứng dụng cực kỳ hiếm gặp."
- `TRANS_AMOUNT_Z_SCORE`: "Số tiền giao dịch lớn gấp X lần mức chi tiêu trung bình của khách hàng."
- `NEW_DEVICE_FLAG`: "Giao dịch phát sinh trên thiết bị chưa từng được sử dụng trước đây."

#### 5.4.2. SHAP Interaction Values
Đối với các mô hình dựa trên cây (tree-based), hệ thống tính toán toàn bộ ma trận tương tác $F \times F$ ($\Phi_{ij}$) để tìm ra các hiệu ứng cộng hưởng phi tuyến giữa các cặp biến:

$$\text{Interaction}(i, j) = \Phi_{ij} + \Phi_{ji}$$

Các cặp tương tác có cường độ tác động cực mạnh (ví dụ: $|v| > 0.01$) được trích xuất. Điều này giúp chuyên viên phân tích các kịch bản tấn công kép thay vì chỉ nhìn vào từng đặc trưng đơn lẻ (ví dụ: tương tác độc hại giữa `NEW_DEVICE_FLAG` × `DAYS_AMOUNT_COMBINED` phản ánh kịch bản "Tài khoản ngủ đông đăng nhập trên máy lạ").

#### 5.4.3. Counterfactual Recourse
Hệ thống xác định "sự thay đổi tối thiểu" cần thiết để đưa giao dịch từ trạng thái "gian lận" về trạng thái "an toàn" ($P < \tau$) thông qua thuật toán tìm kiếm nhị phân (Binary Search). Quá trình này mô phỏng hành vi nhân quả chặt chẽ:
1. **Ràng buộc biến bất biến (Immutable features):** Khóa cứng các trường dữ liệu không thể thay đổi theo ý muốn (Tuổi khách hàng, thời gian tạo tài khoản, giới tính, giờ giao dịch, cờ thiết bị).
2. **Cơ chế lan truyền nhân quả (Causal Propagation):** Khi một đặc trưng gốc bị thay đổi để tìm kiếm phương án an toàn (ví dụ: giả lập giảm số tiền `TRANS_AMOUNT` xuống mức $a'$), toàn bộ các đặc trưng toán học phái sinh (như `TRANS_AMOUNT_Z_SCORE`, `BALANCE_COVERAGE_RATIO`, `DAYS_AMOUNT_COMBINED` và các tỷ lệ `VELOCITY_RATIO`) đều được tự động tính toán lại. Mô hình sau đó dự đoán lại rủi ro trên toàn bộ dải dữ liệu phái sinh mới này.
3. **Thuật toán tìm kiếm nhị phân:** Thực hiện lặp tối đa 20 vòng trong khoảng $[0, \text{original\_value}]$ để tìm ra ngưỡng giao dịch an toàn cao nhất có thể chấp nhận, từ đó xuất ra đề xuất phản biện (ví dụ: "Giao dịch sẽ an toàn nếu số tiền giảm xuống mức Y"). Điều này hỗ trợ ngân hàng trong việc tư vấn khách hàng tự giảm nhẹ hạn mức giao dịch nếu đó là giao dịch hợp lệ.

---

## Phần VI: Học liên tục & Chống Quên Thảm họa (Phase 5 — EWC)

### 6.1. Vấn đề Distribution Drift trong hệ thống ngân hàng số
Hệ thống ngân hàng luôn đối mặt với hiện tượng "Distribution Drift" (Dịch chuyển phân bố) — khi hành vi khách hàng thay đổi theo thời gian (ví dụ: bùng nổ mua sắm dịp lễ, lạm phát khiến mức chi tiêu trung bình tăng, hoặc các sản phẩm tín dụng mới ra đời). Khi đó, các mô hình học máy truyền thống thường gặp phải hiện tượng "Quên thảm họa" (Catastrophic Forgetting): nếu huấn luyện lại (retrain) trên dòng dữ liệu mới, mô hình sẽ quên đi các quy luật phân biệt gian lận cốt lõi đã học từ dữ liệu cũ, dẫn đến việc đánh giá sai lệch các giao dịch truyền thống.

Để giải quyết, hệ thống áp dụng kỹ thuật **Elastic Weight Consolidation (EWC)** nhằm bảo vệ những trọng số quan trọng nhất của mô hình không bị dịch chuyển quá xa khi học trên dữ liệu mới.

### 6.2. Kiến trúc Autoencoder
Giai đoạn này sử dụng một kiến trúc Autoencoder đối xứng học không giám sát để làm cơ sở đánh giá độ lệch chuẩn. Autoencoder thực hiện nén dữ liệu đầu vào thông qua một thắt nút (bottleneck) để học ra các biểu diễn cốt lõi (baseline representation) của dữ liệu giao dịch sạch:

- **Dữ liệu đầu vào:** Toàn bộ $D$ đặc trưng (sau quá trình mã hóa Phase 2) được chuẩn hóa theo z-score: $\tilde{x} = \frac{x - \mu}{\sigma + 10^{-5}}$.
- **Cơ chế nén (Encoder):** $\mathbb{R}^{D} \xrightarrow{\text{Linear}(D, 16)} \text{ReLU} \xrightarrow{\text{Linear}(16, 8)} \text{ReLU} \rightarrow \mathbb{R}^{8}$
- **Cơ chế giải nén (Decoder):** $\mathbb{R}^{8} \xrightarrow{\text{Linear}(8, 16)} \text{ReLU} \xrightarrow{\text{Linear}(16, D)} \mathbb{R}^{D}$

### 6.3. Huấn luyện cơ sở & Ngưỡng Anomaly
Autoencoder ban đầu được huấn luyện trên tập dữ liệu lịch sử bằng thuật toán Adam (Learning rate = 0.01, Batch size = 256, 5 epochs) nhằm tối thiểu hóa sai số tái tạo (Mean Squared Error — MSE):

$$\mathcal{L}_{\text{recon}} = \frac{1}{N}\sum_{i=1}^{N} \|x_i - \hat{x}_i\|^2$$

Sau khi huấn luyện cơ sở, hệ thống xác định "ngưỡng bất thường" (Anomaly Threshold) dựa trên phân vị thứ 97 (tương ứng chừa lại 3% là bất thường, $c = 0.03$) của các giá trị MSE trên tập huấn luyện:

$$\tau_{\text{AE}} = \text{Percentile}_{97}(\{\text{MSE}_i\}_{i \in \text{train}})$$

Khi đưa vào thực tế, điểm số bất thường của một giao dịch sẽ là tỷ lệ giữa MSE của nó và ngưỡng $\tau_{\text{AE}}$:

$$\text{score}(x) = \min\!\left(\frac{\text{MSE}(x)}{\tau_{\text{AE}}},\; 1.0\right)$$

Bất kỳ giao dịch nào có $\text{score} \geq 1.0$ (sai số tái tạo vượt ngưỡng) sẽ bị coi là giao dịch bất thường.

### 6.4. Ma trận Fisher Information (FIM)
Để chống lại sự lãng quên thảm họa, ngay sau khi hoàn thành huấn luyện cơ sở, hệ thống tính toán đường chéo của Ma trận Fisher Information (FIM) cho từng tham số $\theta_k$ dựa trên tập dữ liệu baseline:

$$F_k = \frac{1}{N}\sum_{i=1}^{N}\left(\frac{\partial \mathcal{L}(x_i)}{\partial \theta_k}\right)^2$$

Đại lượng $F_k$ định lượng "tầm quan trọng" của trọng số $\theta_k$ trong việc tái tạo phân bố dữ liệu gốc. Các trọng số có $F_k$ lớn là những trọng số "cốt lõi". Hệ thống sẽ lưu lại bộ trọng số cơ sở này dưới dạng $\theta^*$.

### 6.5. Huấn luyện lại với penalty EWC
Khi có dữ liệu mới (có khả năng mang theo distribution drift), mô hình được huấn luyện lại thông qua quá trình online retraining. Tuy nhiên, thay vì chỉ tối ưu MSE trên dữ liệu mới, hàm loss được cộng thêm một thành phần phạt (EWC penalty) mang tính đàn hồi:

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{recon}}^{\text{new}} + \frac{\lambda_{\text{EWC}}}{2}\sum_k F_k \cdot (\theta_k - \theta_k^*)^2$$

Tham số $\lambda_{\text{EWC}} = 50.0$ đóng vai trò kiểm soát cường độ phạt. Sự có mặt của hệ số $F_k$ khiến mô hình chịu tổn thất (loss) rất lớn nếu cố tình thay đổi các trọng số lõi (nơi $F_k$ cao). Do đó, để thích nghi với dữ liệu mới, mô hình buộc phải điều chỉnh các trọng số ít quan trọng ($F_k$ thấp) thay vì phá vỡ cấu trúc của các trọng số quan trọng.

### 6.6. Kết quả so sánh
Để chứng minh hiệu quả, một thử nghiệm giả lập drift được thực hiện bằng cách nhân toàn bộ số tiền giao dịch lên gấp 5 lần (mô phỏng lạm phát bất ngờ hoặc một kỳ nghỉ lễ). Hai mô hình được đem ra huấn luyện lại trên dữ liệu bị drift này và sau đó kiểm tra ngược lại trên dữ liệu baseline chuẩn:

1. **Mô hình Không EWC ($\lambda_{\text{EWC}} = 0$):** Học dữ liệu mới một cách tự do, phá vỡ hoàn toàn các trọng số cũ (Catastrophic Forgetting). Khi đánh giá lại trên tập baseline ban đầu, điểm số MSE bất thường vọt lên rất cao do mô hình đã "quên" cách xử lý các giao dịch quy mô bình thường.
2. **Mô hình Có EWC ($\lambda_{\text{EWC}} = 50.0$):** Nhờ cơ chế penalty FIM bảo vệ các trọng số lõi, mô hình này vẫn duy trì được sai số MSE thấp và ổn định trên dữ liệu chuẩn ban đầu dù đã được học qua tập dữ liệu bị drift.

Kết quả này khẳng định kiến trúc Autoencoder tích hợp EWC cho phép hệ thống ngân hàng dung nạp (accommodate) các xu hướng hành vi mới một cách liên tục mà không đánh mất trí nhớ về các mô hình gian lận cốt lõi đã được xác lập từ trước.

---

## Phần VII: Kết quả & Phân tích

Sau khi đưa toàn bộ **900.000 giao dịch** qua hệ thống phân tầng rủi ro tích hợp (Hierarchical Routing Pipeline) với bộ đặc trưng rủi ro tối ưu, hệ thống đã đem lại kết quả đo lường và phát hiện vượt trội, chứng minh hiệu quả thực tế của việc kết hợp giữa Rule-based và mô hình ML học máy có hiệu chỉnh (NNPU-C XGBoost).

### 7.1. Thống kê tổng quan (Kết quả Rule-based & ML)
Quá trình phân tầng định tuyến đã thể hiện hiệu suất sàng lọc rõ rệt trên quy mô dữ liệu lớn:
- **Tổng giao dịch đánh giá:** 900.000 giao dịch
- **Tier 1 (Safe Bypass):** Lọc bỏ an toàn **547.100 giao dịch (60,79%)** nhờ các quy tắc bypass tự động (LowRiskChannelBypassRule, SequenceRarityRule, VelocityBypassRule, SmallAmountBypassRule), tiết kiệm ngay lập tức hơn 60% chi phí tính toán cho mô hình máy học.
- **Tier 1 (Forced Fraud Block):** Ngăn chặn lập tức **2.719 giao dịch (0,30%)** có dấu hiệu gian lận rõ ràng (Smoking gun) thông qua các quy tắc chặn cứng (DormancyWakeupRule, ATOPanicRule, HourlyAnomalyRule, CreditCardBustOutRule).
- **Tier 2 (ML XGBoost):** **350.181 giao dịch vùng xám** còn lại được định tuyến vào mô hình ML để phân tích chuyên sâu với 8 đặc trưng cốt lõi.
- **Tier 3 (Flagged Anomaly Alerts):** Mô hình ML phát hiện và gắn cờ rủi ro thêm **4.288 giao dịch** (tương đương 1,22% phân khúc vùng xám).
- **Tổng số cảnh báo gian lận:** **7.007 giao dịch** bị chặn hoặc gắn cờ cảnh báo trên toàn hệ thống (tỷ lệ **0,78%** trên tổng số giao dịch), hoàn toàn phù hợp với phân bố rủi ro thực tế trong vận hành ngân hàng thương mại.

### 7.2. Phân bố rủi ro theo nhóm Feature
Dựa trên phân tích 7.007 giao dịch bất thường bị phát hiện, sự tập trung rủi ro lộ diện rất rõ ràng:
- **Về số tiền:** Giao dịch bất thường trung bình là **91.181.937 VND** (với trung vị là **33.000.000 VND**), cao hơn rất nhiều so với trung vị **640.000 VND** của hệ thống, phản ánh xu hướng tẩu tán tài sản lớn khẩn cấp của tội phạm.
- **Về kênh chuyển tiền:** Kênh **Outside_bank** (chuyển tiền ra ngoài hệ thống ngân hàng gốc) chiếm đến **77,79%** tổng số cảnh báo. Điều này phản ánh chính xác hành vi tẩu tán dòng tiền bất hợp pháp (Mule Account / ATO) để dòng tiền không thể thu hồi. Trong khi đó, các giao dịch nội bộ (Within_bank) chiếm **14,37%**.

### 7.3. Đóng góp Đặc trưng (Ranked SHAP Contributors)
Dựa trên giá trị giải thích TreeSHAP trung bình trên toàn bộ các cảnh báo bất thường, mức độ đóng góp của 8 đặc trưng ML được xếp hạng như sau:

| Hạng | Đặc trưng (Feature) | Trung bình SHAP Value | Tần suất xuất hiện ở Top 3 | Giải thích logic thực tế |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **TRANS_AMOUNT_Z_SCORE** | 5.802 | 4.244 cảnh báo (98,97%) | Mức độ lệch chuẩn chi tiêu cá nhân. Số tiền giao dịch vượt nhiều lần độ lệch chuẩn lịch sử cá nhân là chỉ báo rủi ro số 1. |
| 2 | **TRANS_AMOUNT_VS_30D_AVG_RATIO** | 3.976 | 4.061 cảnh báo (94,71%) | So sánh với thói quen chi tiêu trung bình ngắn hạn 30 ngày qua, vạch trần hành vi đột biến rút tiền khẩn cấp. |
| 3 | **BALANCE_COVERAGE_RATIO** | 0.764 | 2.044 cảnh báo (47,67%) | Số tiền giao dịch vượt nhiều lần số dư trung bình lịch sử tài khoản (tín hiệu tài khoản mule nhận tiền rồi chuyển đi ngay). |
| 4 | **BENFORD_DEV** | 0.322 | 991 cảnh báo (23,11%) | Độ lệch phân phối chữ số đầu tiên (Benford's Law) chỉ ra hành vi chia nhỏ số tiền (structuring) nhằm né các hạn mức giám sát. |
| 5 | **SPIKE_1H_VS_24H** | 0.104 | 653 cảnh báo (15,23%) | Đột biến giao dịch trong 1 giờ qua so với 24 giờ, bắt trúng hành vi tấn công botnet hoặc ATO tẩu tán dồn dập. |
| 6 | **SPIKE_24H_VS_7D** | 0.021 | 248 cảnh báo (5,78%) | Đột biến giao dịch trong 24 giờ qua so với 7 ngày qua, cảnh báo sự gia tăng tần suất giao dịch ngắn hạn đột xuất. |
| 7 | **ACTIVITY_SEQ_RARITY** | 0.014 | 295 cảnh báo (6,88%) | Độ hiếm chuỗi thao tác (Markov bậc 2), bắt bài các hành vi điều hướng ứng dụng bất thường hoặc tự động hóa. |
| 8 | **SPIKE_7D_VS_30D** | 0.014 | 328 cảnh báo (7,65%) | Đột biến giao dịch trong 7 ngày qua so với 30 ngày, phát hiện rủi ro phân tán tiền chu kỳ tuần. |

### 7.4. Tương tác Đặc trưng Độc hại (Toxic Feature Interactions)
Các kịch bản gian lận hiện đại rất hiếm khi bộc lộ qua một biến đơn lẻ. SHAP Interaction ghi nhận các cặp tương tác mạnh mẽ tạo ra hiệu ứng cộng hưởng rủi ro phi tuyến:
1. **TRANS_AMOUNT_Z_SCORE × TRANS_AMOUNT_VS_30D_AVG_RATIO (92,37% alerts):** Mức độ lệch chuẩn của giao dịch hiện tại kết hợp sự đột biến so với trung bình 30 ngày ngắn hạn (cảnh báo nguy cơ vét sạch tài khoản nhanh).
2. **TRANS_AMOUNT_Z_SCORE × BALANCE_COVERAGE_RATIO (53,99% alerts):** Sự kết hợp giữa số tiền giao dịch lệch chuẩn lớn và số tiền này chiếm phần lớn/vượt số dư trung bình tích lũy lịch sử (dấu vết tài khoản mule nhận tiền bẩn lớn rồi tẩu tán ngay).
3. **BALANCE_COVERAGE_RATIO × TRANS_AMOUNT_VS_30D_AVG_RATIO (48,76% alerts):** Số tiền giao dịch vượt nhiều lần số dư trung bình lịch sử cộng hưởng với việc vượt mức chi tiêu 30 ngày gần nhất.
4. **BENFORD_DEV × TRANS_AMOUNT_VS_30D_AVG_RATIO (31,30% alerts):** Độ lệch Benford cộng hưởng với đột biến giao dịch ngắn hạn 30 ngày, cho thấy hành vi chia nhỏ số tiền chuyển liên tục nhằm trốn tránh hệ thống cảnh báo.
5. **TRANS_AMOUNT_Z_SCORE × SPIKE_1H_VS_24H (26,42% alerts):** Tổ hợp số tiền giao dịch lệch chuẩn cực cao phát sinh ngay khi xuất hiện đột biến tần suất/lưu lượng trong vòng 1 giờ qua (dấu vết của các cuộc tấn công ATO vét tiền khẩn cấp).

### 7.5. Ví dụ Counterfactual Recourse
Explainable AI (xAI) giúp đề xuất hướng giải quyết (Recourse) tối thiểu để đưa giao dịch về trạng thái an toàn:
- Một khách hàng có mức chi tiêu bình quân `HIST_AVG_TRANS_AMOUNT` là 2,4 triệu VND, hôm nay khách hàng thực hiện lệnh chuyển đi **50 triệu VND** (Z-Score > 8). Hệ thống chấm điểm rủi ro $P(\text{fraud}|x) = 1.00$ (vượt ngưỡng).
- **Cơ chế lan truyền nhân quả (Causal Propagation):** Khi mô phỏng giảm thử `TRANS_AMOUNT`, thuật toán sẽ tự động tính toán lại sự sụt giảm của các biến phụ thuộc như `TRANS_AMOUNT_Z_SCORE`, `BALANCE_COVERAGE_RATIO`, `SPIKE_1H_VS_24H`, `TRANS_AMOUNT_VS_30D_AVG_RATIO` và tái đánh giá lại điểm số mô hình.
- **Đề xuất Counterfactual xAI:** *"Giao dịch sẽ chuyển về trạng thái an toàn nếu số tiền giảm xuống còn tối đa 14.500.000 VND."*
- **Quyết định nghiệp vụ:** Ngân hàng có thể tự động gửi thông báo yêu cầu khách hàng chia nhỏ mức thanh toán dưới 14.5 triệu, hoặc bắt buộc xác thực sinh trắc học FaceID tăng cường nếu muốn chuyển thẳng 50 triệu.

### 7.6. Hiệu suất xử lý thực tế
Một trong những điểm sáng nhất của kiến trúc Pipeline V3 là tốc độ vận hành thực tế. Tổng thời gian xử lý toàn bộ quá trình phân tầng cho 900.000 giao dịch chỉ mất **36.524 ms** (tương đương khoảng **~0,04 mili-giây cho một giao dịch**).
Tốc độ độ trễ cực thấp này cho phép hệ thống phòng vệ can thiệp vào giữa luồng thanh toán tại core-banking của ngân hàng để phân tích rủi ro thời gian thực (real-time) mà không gây ra bất kỳ sự suy giảm trải nghiệm nào của người dùng.

---

## Phần VIII: Giá trị Kinh doanh & Đề xuất

Một hệ thống phòng chống gian lận (Anti-Fraud) thành công luôn cân bằng hoàn hảo giữa rủi ro (Risk) và Tăng trưởng (Growth). Kiến trúc Pipeline 3 tầng kết hợp xAI này mang lại những giá trị chiến lược to lớn dưới góc độ vận hành của ngân hàng thương mại tại Việt Nam.

### 8.1. Bảo vệ uy tín ngân hàng và Tối ưu chi phí nguồn vốn
- **Giảm thiểu báo động giả (False Positives):** Việc tối ưu hóa mô hình ML giúp giảm tỷ lệ cảnh báo rủi ro (Anomaly Flagging Rate) xuống mức thực tế **0,78%** trên toàn hệ thống (7.007 cảnh báo / 900.000 giao dịch), hạn chế tối đa báo động giả làm phiền khách hàng.
- **Bảo vệ dòng vốn thất thoát:** Sự tập trung mũi nhọn vào kênh giao dịch rủi ro cao (**77,79%** cảnh báo thuộc về kênh chuyển ra ngoài - Outside_bank) giúp chặn đứng dòng tiền không thể thu hồi (irreversible), gia tăng uy tín của ngân hàng đối với người dùng.

### 8.2. Nâng cao trải nghiệm khách hàng (Frictionless Security)
- **Bảo mật không ma sát:** Nhờ bộ lọc Tier 1 Bypass, hệ thống tự động cho qua **60,79%** giao dịch (547.100 / 900.000) có mức độ rủi ro cực thấp mà không cần gọi đến mô hình phân tích nặng nề, đem lại trải nghiệm Zero-latency cho người dùng.
- **Phản ứng linh hoạt nhờ Counterfactual:** Thay vì tư duy khóa cứng tài khoản, sức mạnh của Counterfactual Recourse (xAI) cho phép ngân hàng đề xuất giải pháp xác thực FaceID tăng cường linh hoạt theo Quyết định 2345/QĐ-NHNN hoặc gợi ý chia nhỏ giao dịch.

### 8.3. Tăng hiệu suất của khối Tuân thủ & Kiểm soát rủi ro (Compliance & AML)
- Tính năng dịch các giá trị SHAP Value thành **narrative tự nhiên (Natural Language Explanations)** cung cấp cho Analyst một "hồ sơ tóm tắt tội phạm" ngay trên màn hình cảnh báo (Ví dụ: *"Giao dịch rủi ro do số tiền vượt 8.7 lần độ lệch chuẩn, lớn gấp 15.2 lần thói quen 30 ngày qua và gấp 19.3 lần số dư"*), giúp rút ngắn thời gian điều tra và ra quyết định nhanh gấp 3 đến 5 lần.

### 8.4. Giới hạn hiện tại & Hướng phát triển (Next Steps)
Mặc dù hệ thống đã đáp ứng tốt các yêu cầu phát hiện hành vi lừa đảo phức tạp (ATO, Mule Account, Structuring), cấu trúc hiện tại vẫn còn một số điểm cần tiếp tục hoàn thiện để đạt chuẩn hệ sinh thái tăng trưởng lõi:

1. **Xây dựng Vòng lặp Phản hồi (Active Feedback Loop):**
   - Tích hợp giao diện để Analyst của ngân hàng có thể bấm nút `[Xác nhận Gian Lận]` hoặc `[Báo cáo Nhầm lẫn]` trực tiếp trên màn hình Alert để đưa ngược trở lại vào cơ sở dữ liệu tái huấn luyện mô hình XGBoost.

2. **Nâng cấp kiến trúc Streaming thời gian thực (Real-time Stream Processing):**
   - Dịch chuyển việc tính toán đặc trưng sang kiến trúc Streaming (sử dụng Apache Kafka và Apache Flink) để đảm bảo thời gian truy xuất các biến số như `SPIKE_1H_VS_24H` đạt ngưỡng dưới 1 mili-giây dưới tải trọng hàng nghìn TPS.

3. **Mở rộng kịch bản phòng vệ thẻ tín dụng (Credit Shield):**
   - Bổ sung các nguồn dữ liệu về điểm tín dụng CIC và hành vi chi tiêu thẻ để tối ưu hóa khả năng phát hiện sớm ý định rửa tiền hoặc lạm dụng hạn mức.


