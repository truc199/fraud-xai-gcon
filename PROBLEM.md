**Bài toán** và **Yêu cầu** của vòng thi:

### I. BÀI TOÁN (ĐỀ BÀI)
**1. Đề bài cốt lõi:**
Ứng dụng Data Analytics nhằm xây dựng giải pháp phân tích hành vi khách hàng, phát hiện rủi ro và cá nhân hóa dịch vụ trong lĩnh vực ngân hàng số.

**2. Bối cảnh:**
Trong bối cảnh chuyển đổi số diễn ra mạnh mẽ trong ngành tài chính – ngân hàng, các tổ chức tài chính không chỉ cần đảm bảo an toàn giao dịch mà còn phải tối ưu trải nghiệm khách hàng và nâng cao hiệu quả tăng trưởng thông qua khai thác dữ liệu. Bạn là một Data Analyst làm việc tại một ngân hàng số, có nhiệm vụ sử dụng dữ liệu khách hàng và giao dịch để xây dựng các mô hình phân tích phục vụ hoạt động kinh doanh và quản trị rủi ro.

**3. Mục tiêu của đề án:**
Khai thác dữ liệu khách hàng, lịch sử giao dịch, hành vi sử dụng dịch vụ số và dữ liệu sản phẩm tài chính nhằm:
*   Phát hiện các hành vi bất thường hoặc giao dịch có dấu hiệu gian lận.
*   Dự đoán nhu cầu sử dụng sản phẩm tài chính của khách hàng nhằm tối ưu hoạt động cross-selling.
*   Xây dựng chân dung khách hàng dựa trên hành vi để phục vụ cá nhân hóa trải nghiệm số.

---

### II. YÊU CẦU ĐỀ ÁN (CÁC HƯỚNG PHÂN TÍCH)

Từ bộ dữ liệu được cung cấp, các đội thi có thể **lựa chọn thực hiện một trong ba hướng phân tích dưới đây** hoặc **xây dựng mô hình tích hợp bao phủ nhiều hướng tiếp cận**:

**Hướng 1: Fraud & Anomaly Detection – Phát hiện gian lận và bất thường**
*   Xây dựng mô hình hoặc framework nhằm phát hiện các hành vi giao dịch bất thường và giảm thiểu rủi ro bảo mật (như: chiếm đoạt tài khoản, chuyển khoản trái phép, hoạt động rửa tiền).
*   Được tự do lựa chọn supervised learning, unsupervised learning hoặc rule-based framework tuỳ theo cách tiếp cận dữ liệu.
*   Phân tích hành vi giao dịch theo thời gian nhằm xác định các dấu hiệu bất thường (giao dịch ngoài khung giờ, dòng tiền ra bất thường, tần suất giao dịch không hợp lý).
*   Đề xuất cơ chế giải thích kết quả mô hình theo hướng dễ hiểu và có tính ứng dụng thực tế.

**Hướng 2: Next Best Financial Offer (NBFO) – Đề xuất sản phẩm tài chính phù hợp**
*   Xây dựng mô hình dự đoán khả năng khách hàng sử dụng thêm sản phẩm tài chính mới trong chu kỳ tiếp theo.
*   Tự xác định target adoption phù hợp dựa trên cấu trúc dữ liệu và business logic.
*   Phân tích xu hướng biến động về: tiền gửi, dư nợ tín dụng, hành vi sử dụng thẻ nhằm xác định nhu cầu tài chính tiềm ẩn của khách hàng.
*   Đề xuất chiến lược hỗ trợ hoạt động: Cross-selling, Marketing cá nhân hóa, Quản trị quan hệ khách hàng.

**Hướng 3: Persona-Based Digital Personalization – Cá nhân hóa số dựa trên chân dung khách hàng**
*   Ứng dụng các kỹ thuật phân cụm và học không giám sát nhằm xây dựng các nhóm khách hàng theo hành vi.
*   Phân tích các yếu tố: Tần suất đăng nhập, Hành vi sử dụng dịch vụ số, Khối lượng giao dịch, Mức độ đa dạng giao dịch.
*   Xây dựng các nhóm persona khách hàng phục vụ: Cá nhân hóa trải nghiệm, Tăng mức độ gắn kết khách hàng, Tối ưu hóa chiến lược giữ chân khách hàng và phát triển sản phẩm số.

---

### III. YÊU CẦU ĐỐI VỚI THÍ SINH (HÌNH THỨC & NỘP BÀI)

**1. Các thành phần khuyến khích (Điểm cộng):**
*   **xAI Engine (Explainable AI):** Đặc biệt đối với hướng Fraud & Anomaly Detection, mô hình cần có khả năng giải thích trực quan, đưa ra lý do cụ thể cho các giao dịch bị đánh dấu bất thường (VD: "Tài khoản xuất hiện dòng tiền ra bất thường so với lịch sử").
*   **Demo trực tiếp:** Xây dựng demo minh họa khả năng hoạt động của mô hình hoặc framework trên dữ liệu khách hàng mẫu.