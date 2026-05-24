# EDA Report: Device & Technical Footprinting

This report outlines the findings from the device operating system and footprinting analysis conducted on 1,418,030 transaction logs.

## 1. Operating System Distribution
We profiled the operating systems (`Device_OS`) used across all transaction logs.

* **iOS:** 54.39% of transactions.
* **Android:** 40.16% of transactions.
* **Web:** 5.45% of transactions.
* **Other / Rare OS:** 0.00% of transactions.
* *Insight:* The device environment is highly consolidated. There are no legacy, rare, or customized operating system labels present in this dataset.

## 2. Device OS Drift Detection
Measures consecutive transactions for a customer where the operating system changed within a time window of less than 24 hours.

* **OS Drift Alerts:** **8,227** transactions (0.58% of total transactions).
* *Insight:* A device OS shift within 24 hours is a low-frequency event. These 8,227 instances represent a strong indicator of multi-device access, which often correlates with credential sharing or unauthorized third-party access.

## 3. Detection Recommendations
Based on these findings, we recommend the following threshold calibrations:

| Severity | Alert Rule | Volume Impact | Business Logic |
| :--- | :--- | :--- | :--- |
| **High** | `IS_OS_DRIFT` = 1 AND `TRANS_AMOUNT` $\ge 38,000,000$ (p95 size) | ~500 alerts | Sudden OS changes (e.g. Android to iOS) within 24 hours combined with high-value transactions. |
