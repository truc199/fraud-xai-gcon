# OUTLINE BÁO CÁO KẾT QUẢ DỰ ÁN
## Hệ thống Cảnh báo Giao dịch Bất thường — Anomaly Alert System

---

### Phần I: Giới thiệu
*   **1.1. Bối cảnh & Vấn đề cần giải quyết**
    *   Thực trạng gian lận tài chính qua kênh ngân hàng số tại Việt Nam (tăng 65%/năm, thiệt hại >8.000 tỷ VND)
    *   Các hình thức gian lận chính: chiếm đoạt tài khoản (ATO), tài khoản trung chuyển (Money Mule), chia nhỏ giao dịch (Structuring)
    *   Hệ thống cảnh báo truyền thống (rule-based) gây báo động giả >95%, làm giảm trải nghiệm khách hàng
*   **1.2. Mục tiêu hệ thống**
    *   Phát hiện giao dịch nghi vấn gian lận với tỷ lệ cảnh báo chính xác
    *   Giảm báo động giả — không khóa nhầm tài khoản khách hàng hợp lệ
    *   Tự động giải thích lý do cảnh báo bằng ngôn ngữ tự nhiên cho nhân viên Compliance
    *   Đề xuất bước xác thực bổ sung tối thiểu thay vì chặn giao dịch
    *   Bảo mật không ma sát (Frictionless Security) — giữ chân khách hàng, tăng uy tín ngân hàng
*   **1.3. Phạm vi dự án**
    *   Lựa chọn Hướng 1: Fraud & Anomaly Detection
    *   Sơ đồ tổng quan kiến trúc hệ thống (5 module xử lý tuần tự)
*   **1.4. Dữ liệu sử dụng**
    *   6 bảng dữ liệu ngân hàng: Khách hàng, Giao dịch, Hoạt động số, Tiền gửi, Cho vay, Thẻ
    *   Quy mô: ~20 triệu bản ghi

---

### Phần II: Tổng quan Dữ liệu (EDA)
*   **2.1. Quy mô & cấu trúc dữ liệu**
    *   Tổng số khách hàng, giao dịch, hoạt động
    *   Phân bố giao dịch theo thời gian (ngày, giờ, ngày trong tuần)
*   **2.2. Phân bố giao dịch**
    *   Phân bố số tiền giao dịch (phần lớn nhỏ lẻ, thiểu số giá trị rất lớn)
    *   Tỷ trọng theo loại giao dịch (Transfer Outside, Within, eWallet...)
    *   Tỷ trọng theo thiết bị (iOS, Android, Web)
*   **2.3. Phân tích hành vi theo nhóm khách hàng**
    *   Khác biệt hành vi giao dịch giữa các nhóm tuổi, nghề nghiệp, thời gian sử dụng dịch vụ
    *   Nhận diện các nhóm có rủi ro cao hơn (sinh viên, tài khoản mới, tài khoản ngủ đông)
*   **2.4. Phân tích hoạt động bảo mật**
    *   Tần suất đổi mật khẩu/PIN và mối liên hệ với giao dịch sau đó
    *   Các insight định hướng thiết kế tín hiệu cảnh báo

---

### Phần III: Hệ thống Thu thập & Xử lý Tín hiệu Rủi ro
*   **3.1. Thu thập dữ liệu giao dịch thời gian thực**
    *   Nối và làm giàu dữ liệu từ 6 nguồn
    *   Tính toán tổng tiền & tần suất giao dịch theo 6 khung thời gian (1 giờ → 30 ngày)
    *   Số dư trung bình & mức chi tiêu lịch sử của từng khách hàng
*   **3.2. Các tín hiệu rủi ro được hệ thống theo dõi**
    *   **Tín hiệu số tiền:** Giao dịch lớn bất thường so với lịch sử cá nhân? So với số dư? So với 30 ngày gần nhất?
    *   **Tín hiệu tốc độ:** Tần suất và tổng tiền tập trung bất thường trong 1 giờ / 24 giờ gần nhất?
    *   **Tín hiệu thời gian:** Tài khoản im lặng lâu rồi đột ngột giao dịch lớn? Giao dịch đêm bất thường so với thói quen?
    *   **Tín hiệu bảo mật:** Giao dịch xảy ra ngay sau khi đổi mật khẩu/PIN? Phương thức đăng nhập khác thường (không dùng sinh trắc học)?
    *   **Tín hiệu thống kê:** Phân bố số tiền vi phạm Định luật Benford (dấu hiệu chia nhỏ có chủ đích)?
    *   **Tín hiệu hành vi:** Chuỗi thao tác trên app bất thường so với hàng triệu phiên giao dịch bình thường?
    *   **Bối cảnh khách hàng:** Nhóm tuổi, nghề nghiệp, loại giao dịch — để cá nhân hóa ngưỡng rủi ro thay vì áp dụng một ngưỡng cứng cho tất cả
*   **3.3. Tổng kết: ~46 tín hiệu rủi ro được tổng hợp cho mỗi giao dịch**

---

### Phần IV: Cơ chế Huấn luyện Mô hình
*   **4.1. Thách thức: Không có dữ liệu gian lận được gắn nhãn sẵn**
    *   Trong thực tế ngân hàng, không tồn tại nhãn "giao dịch gian lận" xác nhận → hệ thống phải tự học từ dữ liệu chưa gắn nhãn
*   **4.2. Quy trình tự tạo nhãn và lọc nhiễu (3 bước)**
    *   **Bước 1 — Sàng lọc ban đầu:** Dùng thuật toán phát hiện bất thường (Isolation Forest) để đánh dấu ~3% giao dịch nghi vấn nhất
    *   **Bước 2 — Xác minh chéo:** "Cài gián điệp" vào nhóm bình thường để kiểm tra độ tin cậy → tách ra nhóm giao dịch bình thường đáng tin
    *   **Bước 3 — Loại bỏ nhiễu:** Kiểm chứng chéo 5 lần trên nhóm chưa rõ ràng, loại bỏ 10% mẫu có xác suất sai nhãn cao nhất
*   **4.3. Huấn luyện bộ phân loại**
    *   Thuật toán XGBoost với cấu hình chống quá khớp (overfitting)
    *   Hiệu chỉnh xác suất đầu ra (Elkan-Noto) cho ra điểm rủi ro chính xác
*   **4.4. Ngưỡng quyết định**
    *   Top 3% giao dịch có điểm rủi ro cao nhất được gắn cờ cảnh báo

---

### Phần V: Cơ chế Xử lý Giao dịch 3 Tầng (Tiered Inference)
> *Đây là kiến trúc cốt lõi của hệ thống — phân luồng thông minh để vừa nhanh, vừa chính xác, vừa giải thích được.*

*   **5.1. Tổng quan: Tại sao cần 3 tầng?**
    *   Không phải mọi giao dịch đều cần qua mô hình AI → lãng phí tài nguyên, tăng độ trễ
    *   Hệ thống 3 tầng: giao dịch rõ ràng an toàn → bỏ qua ngay; giao dịch mơ hồ → AI đánh giá; giao dịch bị gắn cờ → giải thích chi tiết
*   **5.2. Tầng 1 — Bỏ qua Nhanh (Rule-Based Bypass)**
    *   Giao dịch nhỏ (<500.000 VND) + tần suất thấp + hành vi bình thường → xử lý tức thì, không qua AI
    *   Kết quả: **~95% giao dịch được xử lý trong <1ms** → không gây trễ cho khách hàng
*   **5.3. Tầng 2 — Đánh giá bằng AI (ML Classification)**
    *   ~5% giao dịch còn lại được chấm điểm rủi ro bằng mô hình XGBoost
    *   Output: Điểm rủi ro (0-100%) + quyết định gắn cờ/không gắn cờ
*   **5.4. Tầng 3 — Giải thích Tự động (xAI Engine)**
    *   Chỉ kích hoạt cho các giao dịch bị gắn cờ bất thường
    *   **5.4.1. Lý do cảnh báo bằng ngôn ngữ tự nhiên**
        *   Hệ thống tự sinh câu giải thích, ví dụ: *"Số tiền gấp 15 lần mức giao dịch trung bình của khách hàng"*, *"Giao dịch xảy ra 20 phút sau khi đổi mật khẩu"*
    *   **5.4.2. Phân tích tổ hợp rủi ro**
        *   Phát hiện các cặp tín hiệu kết hợp nguy hiểm, ví dụ: *"Số tiền lớn bất thường + tài khoản ngủ đông lâu"*
    *   **5.4.3. Đề xuất hành động khắc phục (Counterfactual Recourse)**
        *   Thay vì chặn cứng, hệ thống đề xuất: *"Giảm số tiền xuống 45 triệu"* hoặc *"Xác minh FaceID để tiếp tục"*
        *   Tự động tính toán mức thay đổi tối thiểu để giao dịch thoát ngưỡng cảnh báo

---

### Phần VI: Khả năng Tự cập nhật (Continuous Learning)
*   **6.1. Vấn đề: Hành vi giao dịch thay đổi theo thời gian**
    *   Khách hàng thay đổi thói quen chi tiêu, mùa lễ Tết tăng giao dịch → mô hình cần thích ứng mà không "quên" kiến thức cũ
*   **6.2. Giải pháp: Cơ chế bảo vệ trí nhớ (EWC)**
    *   Mô hình tự cập nhật khi có dữ liệu mới nhưng vẫn giữ được khả năng phát hiện các mẫu gian lận đã học
*   **6.3. Kết quả kiểm chứng**
    *   So sánh mô hình Có/Không có cơ chế bảo vệ khi dữ liệu thay đổi mạnh (x5 số tiền)
    *   Mô hình được bảo vệ duy trì hiệu quả phát hiện trên dữ liệu gốc

---

### Phần VII: Kết quả Hệ thống
*   **7.1. Hiệu quả phát hiện**
    *   Tổng giao dịch đánh giá: 5.000
    *   Giao dịch bị gắn cờ: 121 (2,42%) — thấp hơn đáng kể so với 5-10% báo động giả của hệ thống cũ
    *   66 khách hàng bị ảnh hưởng, cao nhất 9 cảnh báo/1 khách hàng
    *   Giá trị trung bình giao dịch nghi vấn: 42 triệu VND (trung vị: 21 triệu VND)
*   **7.2. Phân bố rủi ro — Hệ thống nhắm đúng mục tiêu**
    *   **57,85% cảnh báo là chuyển tiền ra ngoài ngân hàng** — đúng nhóm rủi ro cao nhất, khó thu hồi nhất
    *   Thiết bị: iOS (50,4%), Android (47,9%), Web (1,7%)
*   **7.3. Các tín hiệu rủi ro quan trọng nhất (Top SHAP Contributors)**
    *   Bảng top 10 tín hiệu xuất hiện nhiều nhất trong 121 cảnh báo
    *   Phân tích: *"Giao dịch chiếm tỷ trọng lớn so với số dư"* xuất hiện trong 80% cảnh báo — khớp với mô hình tài khoản trung chuyển (Money Mule)
*   **7.4. Các tổ hợp rủi ro nguy hiểm nhất**
    *   Top 5 cặp tín hiệu kết hợp và ý nghĩa thực tế, ví dụ: *"Số tiền lớn bất thường + giao dịch lớn so với cả thu nhập lẫn số dư"* (50,4% cảnh báo)
*   **7.5. Ví dụ Đề xuất Khắc phục (Counterfactual Recourse)**
    *   Case study cụ thể: giao dịch bị cờ → hệ thống đề xuất giảm số tiền hoặc xác minh sinh trắc học
*   **7.6. Hiệu suất xử lý**
    *   Tầng 1 (Rule Bypass): **0,83 ms** — tức thì
    *   Tầng 2 (AI Classification): **39,86 ms** — gần real-time
    *   Tầng 3 (Giải thích xAI): **8,86 giây** — chỉ cho giao dịch bị cờ
    *   → Đủ nhanh cho hệ thống cảnh báo thời gian thực

---

### Phần VIII: Giá trị Kinh doanh & Đề xuất Triển khai
*   **8.1. Bảo vệ uy tín ngân hàng**
    *   Tỷ lệ cảnh báo 2,42% vs 5-10% báo động giả của hệ thống rule-based cũ
    *   Tập trung đúng vào giao dịch rủi ro cao (chuyển tiền ra ngoài chiếm 57,85% cảnh báo)
*   **8.2. Nâng cao trải nghiệm khách hàng**
    *   95% giao dịch xử lý tức thì không qua AI → khách hàng bình thường không bị ảnh hưởng
    *   Đề xuất xác thực bổ sung (FaceID/OTP) thay vì chặn cứng → giảm ma sát, giữ chân khách hàng
*   **8.3. Tăng hiệu suất đội ngũ Compliance**
    *   Mỗi cảnh báo đi kèm giải thích tự động bằng ngôn ngữ tự nhiên → Analyst duyệt nhanh gấp 3-5 lần
    *   Phân tích tổ hợp rủi ro cho biết chính xác sự kết hợp yếu tố nào gây ra cảnh báo → không cần phỏng đoán
*   **8.4. Khả năng mở rộng & Hướng phát triển**
    *   Tích hợp feedback loop từ Analyst để mô hình tự cải thiện
    *   Nâng cấp lên pipeline streaming thời gian thực (Kafka)
    *   Bổ sung phân tích mạng lưới giao dịch (Graph-based detection) để phát hiện vòng rửa tiền

---

### Phần IX: Tài liệu Tham khảo
