# EDA Report: Velocity (Spike & Speed) Analysis

This report outlines the findings from the transaction velocity analysis conducted on 1,418,030 transaction logs.

## 1. Transaction Frequency (Counts)
Normal banking behavior is highly sparse. Most accounts transact only a few times per week/month. High frequency indicates automation, scripting, or rapid-fire checkout abuse.

* **1-Hour Window (`COUNT_1H`):**
  * **Mean:** 1.03 transactions
  * **99th Percentile (p99):** 2 transactions
  * **Max:** 6 transactions
  * *Insight:* More than 1 transaction per hour is anomalous (top 1%). Any count $\ge 3$ represents a massive outlier.
* **3-Hour Window (`COUNT_3H`):**
  * **p95:** 2 transactions
  * **p99:** 3 transactions
  * **Max:** 9 transactions
* **24-Hour Window (`COUNT_24H`):**
  * **p95:** 5 transactions
  * **p99:** 11 transactions
  * **Max:** 34 transactions

## 2. Transaction Amounts & Spikes
* **Transaction Size (`TRANS_AMOUNT`):**
  * **Median (p50):** 640,000
  * **95th Percentile (p95):** 38,000,000
  * **99th Percentile (p99):** 163,236,758
  * **Max:** 2,458,000,000
* **30-Day Volume (`SUM_30D`):**
  * **Median (p50):** 17,900,000
  * **95th Percentile (p95):** 977,744,950
  * **Max:** 20,662,345,413

## 3. Velocity Ratios (Spike Detectors)
Ratios compare short-term volume against longer-term context. A ratio near 1.0 indicates that all weekly or monthly volume was spent in a single day or hour.

* **`VELOCITY_RATIO_AMOUNT_1H_VS_24H`:**
  * **Median (p50):** 1.0
  * *Insight:* It is highly common for a transaction to be isolated within 24 hours. However, when combined with high amounts (e.g. `SUM_1H` > p95), it indicates sudden massive single transfers.
* **Transaction Size Deviation (`TRANS_AMOUNT_VS_30D_AVG_RATIO`):**
  * **Median (p50):** 0.55
  * **90th Percentile (p90):** 2.37
  * **95th Percentile (p95):** 3.48
  * **99th Percentile (p99):** 6.89
  * **99.9th Percentile (p99.9):** 14.20
  * **Max:** 82.65
  * *Insight:* Transactions exceeding 3.5x of the customer's typical monthly average transaction size represent the top 5% of anomalies. Transactions exceeding 7x are in the top 1% of anomalies.

## 4. Anomaly Detection Threshold Recommendations
Based on the distributions, we define the following rules for alerting on velocity anomalies:

| Severity | Alert Conditions | Action / Impact |
| :--- | :--- | :--- |
| **High** | `COUNT_1H` $\ge 3$ OR `COUNT_24H` $\ge 11$ | Flag for potential automated abuse / script-based card testing. |
| **High** | `TRANS_AMOUNT_VS_30D_AVG_RATIO` $\ge 7.0$ AND `TRANS_AMOUNT` > p95 (38M) | Flag for sudden massive single funds drain (Account Takeover indicator). |
| **Medium** | `VELOCITY_RATIO_AMOUNT_24H_VS_7D` $\ge 0.8$ AND `SUM_24H` > p95 (85M) and `COUNT_24H` > 2 | Flag for rapid multi-transaction daily cash-out. |
