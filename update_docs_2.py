import re

def replace_section(text, start_marker, end_marker, new_content):
    start_idx = text.find(start_marker)
    if start_idx == -1:
        return text
    
    end_idx = text.find(end_marker, start_idx)
    if end_idx == -1:
        # If no end marker, just replace to the end
        return text[:start_idx] + new_content
    
    return text[:start_idx] + new_content + text[end_idx:]

def process_files():
    # File paths
    file_base = "d:/uni/gcontest v3/gcontest/feature_description_outcome.md"
    file_2026 = "d:/uni/gcontest v3/gcontest/feature_description_outcome_2026.md"
    
    # 1. Update BENFORD_DEV in both
    benford_start = "#### BENFORD_DEV\n"
    benford_end = "#### ACTIVITY_SEQ_RARITY\n"
    
    benford_new = """#### BENFORD_DEV
- **Nguồn dữ liệu:** Trích xuất chữ số đầu tiên (1-9) của tất cả số tiền `TRANS_AMOUNT` của một người dùng.
- **Công thức đo lường:** `KL-Divergence` giữa phân bố thực tế của chữ số đầu tiên và phân bố lý thuyết định luật Benford: `log10(1 + 1/d)`. Chỉ tính toán khi số lượng mẫu giao dịch (N) ≥ 50.
- **Vai trò:** **Biến độc lập** (Phát hiện gian lận cấu trúc).
- **Lý luận logic & Thực tế:** Định luật Benford rất nhạy cảm với kích thước mẫu. Việc tính toán trên lượng dữ liệu quá nhỏ (N < 50) sẽ tạo nhiễu (noise) và tỷ lệ Báo động giả (False Positive) cao đối với hành vi giao dịch cá nhân. Việc áp dụng ngưỡng N ≥ 50 là phương pháp luận chính xác theo nghiên cứu kiểm toán hiện đại. Khi tội phạm lách luật AML bằng cách chia nhỏ tiền có chủ đích (Structuring), sự sai lệch phân bố chữ số tự nhiên sẽ chỉ điểm chúng một cách chuẩn xác.

"""
    
    for path in [file_base, file_2026]:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
            
        text = replace_section(text, benford_start, benford_end, benford_new)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    # 2. Update Group 7 and Group 8 in 2026 file
    with open(file_2026, "r", encoding="utf-8") as f:
        text_2026 = f.read()
        
    group_7_8_start = "### 3.7 Nhóm 7: Mạng Lưới & Đồ Thị"
    group_7_8_end = "## 4. Kết quả Pipeline"
    
    group_7_8_new = """### 3.7 Nhóm 7: Mạng Lưới & Đồ Thị (Network & Graph Analytics - New 2026)

#### PAGERANK_SCORE & IN_DEGREE_CENTRALITY (Đặc trưng Mạng Nơ-ron Đồ thị - GNN)
- **Nguồn dữ liệu:** Xây dựng đồ thị có hướng (Directed Graph) từ `CUSTOMER_NUMBER` (Người gửi) đến `Beneficiary_CUSTOMER_NUMBER` (Người nhận) trong cửa sổ 30 ngày từ bảng `Data_Transaction`.
- **Công thức đo lường:** Sử dụng thư viện `networkx` để dựng đồ thị và tính toán điểm thuật toán PageRank cùng In-Degree Centrality.
- **Vai trò:** **Biến độc lập** (Khám phá cấu trúc tổ chức tội phạm).
- **Lý luận logic & Thực tế:** Quan sát giao dịch đơn lẻ (1-hop) là không đủ với mô hình rửa tiền tinh vi (như các vụ án thao túng kiểu SCB/Vạn Thịnh Phát). Tiền bẩn thường được phân lớp (Layering) qua nhiều tài khoản rác và gom về một tài khoản tổng (Hub). Đo lường Centrality và PageRank giúp đo lường mức độ "nút thắt" của một tài khoản nhận tiền, khoanh vùng chính xác các Money Mule Hub rửa tiền giữa hàng triệu người dùng.

---

### 3.8 Nhóm 8: Tín dụng & Chiêu trò tinh vi (Credit & Advanced Structuring - New 2026)

#### LIMIT_UTILIZATION_VELOCITY (Tốc độ sử dụng hạn mức Bust-out)
- **Nguồn dữ liệu:** Lấy thông tin hạn mức `LIMIT_AMT_CREDIT` và dư nợ `OUTSTANDING_BAL_CREDIT` từ `Data_Card`.
- **Công thức đo lường:** Do dữ liệu có độ phân giải theo tháng (không có snapshot ngày), áp dụng tính Tốc độ tăng trưởng sử dụng thẻ Tháng-qua-Tháng (Month-over-Month Velocity) của tỷ lệ `OUTSTANDING_BAL_CREDIT / LIMIT_AMT_CREDIT`.
- **Vai trò:** **Biến độc lập**.
- **Lý luận logic & Thực tế:** Chống gian lận lừa đảo danh tính (Synthetic Identity Fraud / Bust-Out): Kẻ lừa đảo dùng giấy tờ giả mở thẻ, nuôi lịch sử tín dụng vài tháng rồi đột nhiên rút/sử dụng kịch kim hạn mức tiệm cận 100% trước khi biến mất (bùng nợ). Tốc độ tăng trưởng tỷ lệ này càng cao, nguy cơ vỡ nợ gian lận càng rõ ràng.

#### STRUCTURING_OVERPAYMENT_FLAG
- **Nguồn dữ liệu:** Lọc các giao dịch trả nợ thẻ (`TRANS_LV2 = 'Credit_card_repayment'`) từ `Data_Transaction` ghép với Dư nợ (`OUTSTANDING_BAL_CREDIT`) từ `Data_Card`.
- **Công thức đo lường:** Gán cờ bằng `1` (True) NẾU Tổng số tiền nạp trong 30 ngày (`CUM_REPAYMENT_30D`) > Dư nợ thẻ VÀ Số lần nạp tiền trong 30 ngày (`REPAYMENT_COUNT_30D`) ≥ 2.
- **Vai trò:** **Biến độc lập**.
- **Lý luận logic & Thực tế:** Đây là mánh khóe rửa tiền tinh vi hiện đại: Tội phạm dùng tiền bẩn thanh toán dư nợ thẻ tín dụng vượt mức (Overpayment) qua nhiều lần nạp chia nhỏ. Sau đó, chúng gọi tổng đài yêu cầu hoàn phần tiền trả dư đó về một tài khoản ngân hàng sạch. Tiền hoàn lại lúc này đã được hợp thức hóa thành tiền sạch từ ngân hàng.

#### IP_HOPPING_VELOCITY
- **Nguồn dữ liệu:** Địa chỉ mạng/quốc gia `IP_Address_Proxy` và mã thiết bị `Device_ID_Hash` (`Data_Transaction`).
- **Công thức đo lường:** Đếm số lượng IP/Proxy (hoặc ASN) độc nhất mà một `Device_ID_Hash` sử dụng luân phiên trong khung cửa sổ trượt 3 giờ (rolling window).
- **Vai trò:** **Biến độc lập**.
- **Lý luận logic & Thực tế:** Tội phạm mạng và các mã độc di động (như GoldPickaxe) thường sử dụng công cụ tự động xoay vòng IP/Proxy liên tục để che giấu danh tính và lách các bộ quy tắc (rule) địa lý. Việc bắt số lượng dải mạng thay đổi liên tục trên cùng 1 thiết bị là chiến thuật xuất sắc để phát hiện bất thường thời gian thực.

#### AUTH_DOWNGRADE_RISK (Hạ cấp Xác thực)
- **Nguồn dữ liệu:** Lịch sử đăng nhập sinh trắc học (`LOGIN_FACEID`, `LOGIN_FINGER`) và `LOGIN` mật khẩu từ bảng `Data_Activity`, kết hợp thiết bị mới `Device_ID_Hash` từ `Data_Transaction`.
- **Công thức đo lường:** Gán cờ (Flag) nếu khách hàng vốn có lịch sử tỷ lệ dùng sinh trắc học rất cao (`IS_BIOMETRIC`), nhưng nay lại đăng nhập bằng `LOGIN` (mật khẩu tĩnh) trên một `Device_ID_Hash` MỚI (chưa từng ghi nhận trong lịch sử).
- **Vai trò:** **Biến độc lập**.
- **Lý luận logic & Thực tế:** Bảng `Data_Customer` thiếu lịch sử `VERIFY_METHOD`, nên đây là giải pháp thay thế (workaround) quan trọng để phát hiện hành vi Chiếm đoạt tài khoản (ATO). Kẻ gian khi chiếm được thiết bị mới thường không có dấu vân tay/khuôn mặt của nạn nhân, nên buộc phải thoái lui (downgrade) về dùng mật khẩu tĩnh để lách Quyết định 2345/QĐ-NHNN. Sự sụt giảm đột ngột sinh trắc học trên thiết bị mới là cờ đỏ ATO cực mạnh.

---

"""
    
    # We want to replace everything from group_7_8_start to group_7_8_end with our new content.
    # Note that `group_7_8_end` is "## 4. Kết quả Pipeline". We want to keep it!
    text_2026 = replace_section(text_2026, group_7_8_start, group_7_8_end, group_7_8_new)
    
    with open(file_2026, "w", encoding="utf-8") as f:
        f.write(text_2026)
        
    print("Files updated successfully!")

process_files()
