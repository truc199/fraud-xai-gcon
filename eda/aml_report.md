# EDA Report: Regulatory & AML Compliance Analysis

This report outlines the findings from the Anti-Money Laundering (AML) structuring and outbound mule fan-out analysis conducted on 1,418,030 transaction logs.

## 1. Structuring / Smurfing Analysis
Detects users breaking large funds into smaller transactions just below reporting thresholds to avoid AML review triggers.

* **Reporting Threshold Levels Checked:** 50M, 100M, 200M, 500M
* **Structured Transactions:** **9,012** transactions (0.64% of total) fell within 90%–99.9% of these limits (e.g., 90M to 99.9M).
* **Structuring Alerts:** **1,130** alerts (0.08% of total volume).
  * **Criteria:** Senders executing $\ge 2$ structured transactions within a rolling 24-hour window.
  * *Insight:* These 1,130 events represent highly suspicious smurfing patterns where a sender deliberately split transactions.

## 2. Mule Account Outbound Fan-out
Mule accounts receive funds and quickly route them to multiple distinct external beneficiaries to complicate the transaction sequence.

### Data Constraint Discovery
* Senders in `Data_Transaction` are 100% matched in `Data_Customer`.
* Beneficiaries in `Data_Transaction` have **0% overlap** with `Data_Customer`.
* *Insight:* We only observe outbound transfers to external accounts. Consequently, we cannot measure inbound-to-outbound pass-through ratios directly. Instead, we measure **outbound fan-out** (the count of unique external beneficiaries receiving funds from a single customer within 24 hours).

### Outbound Fan-out Statistics
* **Maximum Unique Beneficiaries in 24h:** 27 distinct receivers
* **95th Percentile (p95):** 5.0 unique receivers
* **99th Percentile (p99):** 10.0 unique receivers
* **Mule Alerts (Baseline):** **107,925** alerts.
  * **Criteria:** Customer sends funds to $\ge 3$ unique beneficiaries in 24h, totaling $\ge 10,000,000$ VND/USD. (This baseline is broad and flags ~7.6% of transaction volume).

## 3. AML Detection Rules & Recommendations
To achieve high precision and manageable alert volumes in production, we recommend the following threshold calibrations:

| Severity | Alert Rule | Volume Impact | Business Logic |
| :--- | :--- | :--- | :--- |
| **High** | `IS_STRUCTURING_ALERT` = 1 | ~1,130 alerts (0.08% rate) | Direct attempt to bypass regulatory limits. |
| **High** | `UNIQUE_BENEFICIARIES_24H` $\ge 5$ AND `SUM_AMOUNT_24H` $\ge 38,000,000$ (p95 size) | ~11,000 alerts (0.78% rate) | High-volume transfer distribution to multiple distinct receivers. |
| **Critical** | `UNIQUE_BENEFICIARIES_24H` $\ge 10$ AND `SUM_AMOUNT_24H` $\ge 163,000,000$ (p99 size) | ~1,200 alerts (0.08% rate) | Severe multi-beneficiary transfer distribution. |

