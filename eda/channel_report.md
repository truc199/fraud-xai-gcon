# EDA Report: Digital Channel Behavior Analysis

This report outlines the findings from the digital channel activity and authentication method analysis conducted on 1,418,030 transaction logs.

## 1. Security Event to Transaction Gap (Account Takeover Checks)
Measures the time elapsed (in hours) between a customer's sensitive security change and their subsequent transaction.

* **Security Events Evaluated:** `CHANGE_PASSWORD`, `SET_PASSWORD`, `MB_SET_PIN`, `MB_CHANGE_PIN`, `MB_RESET_PIN`, `ACCOUNT_ADDRESS_BOOK_UPDATE`.
* **Total Security Events Found:** 111,835
* **Account Takeover Alerts:** **14,172** transactions (1.00% of total transactions) occurred within 24 hours of a customer security change.
* *Insight:* Executing transactions immediately after changing account passwords or PINs is highly anomalous and correlates with unauthorized access.

## 2. Login Channel Drift
Analyzes changes in authentication habits, specifically comparing biometric mobile logins against standard password logins.

* **Baseline Biometric Usage:** Biometric mobile logins (`LOGIN_FINGER` / `LOGIN_FACEID`) account for ~22% of total logins. On average, customers use biometrics for 15% of their logins.
* **Calibrated Preferred Biometric User:** A user who has transacted at least 3 times and uses biometric logins $\ge 50\%$ of the time. (A threshold of 80% biometric usage is too restrictive, as it only covers a tiny fraction of the active customer base).
* **Login Drift Alerts:** **2,364** transactions (0.17% of total transactions).
  * **Criteria:** Last login before the transaction was standard password (`LOGIN`), but the customer's historical biometric login ratio was $\ge 50\%$.
  * *Insight:* These 2,364 cases represent sudden shifts from typical biometric device usage to password login, representing potential credential exposure.

## 3. Detection Recommendations
We recommend incorporating the following logic into the main pipeline:

| Severity | Alert Rule | Volume Impact | Business Logic |
| :--- | :--- | :--- | :--- |
| **High** | `IS_ATO_ALERT` = 1 AND `HOURS_SINCE_SEC_EVENT` $\le 1.0$ | ~1,200 alerts | Transactions initiated within 1 hour of a password/PIN change. |
| **High** | `IS_LOGIN_DRIFT_ALERT` = 1 AND `TRANS_AMOUNT` $\ge 38,000,000$ (p95 size) | ~800 alerts | Biometric-to-password login drift combined with high transaction amounts. |
