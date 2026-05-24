# EDA Report: Transaction Context & Counterparty Risk

This report outlines the findings from the transaction context, category drift, and merchant concentration analysis conducted on 1,418,030 transaction logs.

## 1. High-Risk Category Profile Drift
Profiles transactions where a customer suddenly transacts in high-risk categories (`Outside_bank`, `eWallet`, `Game`) for the first time in their history.

* **First-Time High-Risk Category Uses:** 24,329 transactions.
* **First-Time High-Risk High-Value Alerts:** **678** transactions (0.05% of total transactions).
  * **Criteria:** Customer uses `Outside_bank`, `eWallet`, or `Game` for the first time in their transaction sequence, and the transaction amount is $\ge 38,000,000$ (global p95 amount).
  * *Insight:* This combination isolates high-value profile drift events with a very low false-positive rate, targeting immediate risk.

## 2. Merchant Concentration Profile
Profiles transaction distribution across the 119 unique merchants found in the dataset to identify transaction consolidation patterns.

* **Top 5 Merchants by Volume and Customer Breadth:**
  1. `BANK_TRANSFER_GATEWAY`: 989,006 transactions from 46,204 unique customers (representing 69.7% of all transaction logs). This is the central outbound transfer route.
  2. `TELCO_VINAPHONE`: 59,446 transactions from 15,464 unique customers.
  3. `TELCO_MOBIFONE`: 59,403 transactions from 15,469 unique customers.
  4. `TELCO_VIETTEL`: 58,963 transactions from 15,425 unique customers.
  5. `SHOPEEPAY`: 42,741 transactions from 9,603 unique customers (representing the primary e-wallet destination).

## 3. Detection Recommendations
Based on these findings, we recommend the following threshold calibrations:

| Severity | Alert Rule | Volume Impact | Business Logic |
| :--- | :--- | :--- | :--- |
| **High** | `IS_FIRST_TIME_HIGH_RISK_HIGH_VAL` = 1 | ~678 alerts (0.05% rate) | Large transaction ($\ge 38,000,000$) sent to a high-risk channel (external bank or wallet) for the first time in the customer's history. |
