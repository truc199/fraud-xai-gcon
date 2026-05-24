# EDA Report: Geographic & Spatial Anomalies

This report outlines the findings from the geographic and spatial anomaly analysis conducted on 1,418,030 transaction logs.

## 1. Impossible Travel Detection
Measures consecutive transactions for a customer where the transaction location (`IP_Address_Proxy`) changed within a time window of less than 1 hour.

* **Impossible Travel Alerts:** **42,449** transactions (3.00% of total transactions).
* *Insight:* A 3% occurrence rate indicates that geographic location shifts within 1 hour are rare but present. These events represent potential remote access abuse or credential sharing.

## 2. Location Volatility Analysis (First-Time Location Outliers)
Analyzes how often a customer initiates a transaction from a location profile (`IP_Address_Proxy`) that they have never accessed before.

* **New Location Uses:** **1,364,199** transactions.
* **New Location High-Value Alerts:** **67,310** transactions.
* *Insight:* Almost all transactions (96.2% of total volume) qualify as "first-time location" uses for their respective customers. This indicates that `IP_Address_Proxy` is highly volatile (e.g., dynamically assigned IP addresses or shifting mobile tower connections). 
* *Conclusion:* A "first-time location" check is not a viable anomaly indicator because it triggers on almost every transaction. It should be excluded from the alert rules to prevent false-positive alarms.

## 3. Detection Recommendations
Based on these findings, we recommend the following threshold calibrations:

| Severity | Alert Rule | Volume Impact | Business Logic |
| :--- | :--- | :--- | :--- |
| **High** | `IS_IMPOSSIBLE_TRAVEL` = 1 AND `TRANS_AMOUNT` $\ge 38,000,000$ (p95 size) | ~1,800 alerts | Out-of-state location changes within 1 hour involving high-value transactions. |
