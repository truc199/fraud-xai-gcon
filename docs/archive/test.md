Searched for "TRANS_AMOUNT_VS_30D_AVG_RATIO"
Viewed new_features_preprocessor.py:195-220
Searched for "SUM_AMOUNT_30D"
Viewed fraud_2026_data_loader.py:490-520
Viewed fraud_2026_data_loader.py:450-490
Viewed fraud_2026_data_loader.py:420-450

Mức trung bình 30 ngày qua (`hist_avg_30d`) được tính dựa trên hai cột thô là `SUM_AMOUNT_30D` (tổng số tiền giao dịch trong 30 ngày qua) và `COUNT_30D` (số lượng giao dịch trong 30 ngày qua). 

Các thông số này được trích xuất trực tiếp từ Cơ sở dữ liệu SQLite (`data/gcontest.db`) thông qua SQL Window Functions của DataLoader. 

Chi tiết cách thức lấy và tính toán như sau:

---

### 1. Ở tầng Cơ sở dữ liệu (SQL Query)
Trong [fraud_2026_data_loader.py](file:///d:/uni/gcontest%20v3/gcontest/src/pipeline/fraud_2026_data_loader.py#L432-L510), thời gian giao dịch được chuẩn hóa sang đơn vị ngày (`ts` sử dụng hàm `julianday` trong SQLite):
```sql
(julianday(t.TRANS_DATE) + (t.TRANS_HOUR / 24.0)) as ts
```

Sau đó, hệ thống sử dụng các hàm cửa sổ trượt (Rolling Window Functions) phân nhóm theo từng khách hàng (`PARTITION BY CUSTOMER_NUMBER`) để tính toán trong phạm vi 30 ngày trước đó cho tới giao dịch hiện tại:
*   **Tổng số tiền giao dịch 30 ngày qua (`SUM_AMOUNT_30D`):**
    ```sql
    SUM(TRANS_AMOUNT) OVER (
        PARTITION BY CUSTOMER_NUMBER 
        ORDER BY ts
        RANGE BETWEEN 30.0 PRECEDING AND CURRENT ROW
    ) as SUM_AMOUNT_30D
    ```
*   **Tổng số lượng giao dịch 30 ngày qua (`COUNT_30D`):**
    ```sql
    COUNT(*) OVER (
        PARTITION BY CUSTOMER_NUMBER 
        ORDER BY ts
        RANGE BETWEEN 30.0 PRECEDING AND CURRENT ROW
    ) as COUNT_30D
    ```

---

### 2. Ở tầng Tiền xử lý (Python Preprocessor)
Khi các cột dữ liệu thô `SUM_AMOUNT_30D` và `COUNT_30D` được tải lên DataFrame, bộ tiền xử lý sẽ thực hiện phép chia để tìm ra số tiền giao dịch trung bình của 30 ngày qua:

*   Tại dòng 208-209 trong [new_features_preprocessor.py](file:///d:/uni/gcontest%20v3/gcontest/src/pipeline/new_features_preprocessor.py#L208-L209):
    ```python
    hist_avg_30d = sum_amount_30d / (count_30d + 1e-5)
    processed_df['TRANS_AMOUNT_VS_30D_AVG_RATIO'] = (trans_amount / (hist_avg_30d + 1e-5)).astype(float)
    ```

Tóm lại, **mức trung bình 30 ngày qua** của mỗi giao dịch chính là:
$$\text{Average 30D Amount} = \frac{\text{SUM\_AMOUNT\_30D}}{\text{COUNT\_30D} + 10^{-5}}$$
được truy vấn động theo thời gian thực (rolling window) từ bảng lịch sử giao dịch của chính khách hàng đó trong SQLite.