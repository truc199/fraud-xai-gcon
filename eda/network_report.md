# EDA Report: Entity Resolution & Network Linkage Analysis

This report outlines the insights from the shared hardware and beneficiary network analysis conducted on 1,418,030 transaction logs.

## 1. Shared Hardware Insights (Device Linkage)
We analyzed the distribution of unique customer accounts per device identifier (`Device_ID_Hash`).

* **Maximum Customers per Device:** 1 unique customer.
* **Percentiles (p90, p95, p99):** 1.0 unique customer.
* *Insight:* There is **zero device sharing** across distinct customer numbers in this dataset. Every `Device_ID_Hash` is uniquely linked to a single `CUSTOMER_NUMBER`. Consequently, hardware sharing analysis is not a feasible vector for identifying fraud rings in this dataset.

## 2. Common Receiver Insights (Beneficiary Consolidation Nodes)
We analyzed how many distinct customer accounts sent funds to each individual beneficiary identifier (`Beneficiary_CUSTOMER_NUMBER`).

* **Maximum Senders per Beneficiary:** 736 unique customers.
* **90th Percentile (p90):** 664 unique customers.
* **95th Percentile (p95):** 676 unique customers.
* **99th Percentile (p99):** 695 unique customers.
* *Insight:* The distribution is highly concentrated. A small set of beneficiary accounts receive transfers from hundreds of distinct customer accounts.
* *Interpretation:* These highly-shared receivers represent **high-traffic collection nodes**. In a banking system, these nodes are typically:
  1. Legitimate commercial merchants (e.g., e-commerce platforms, utility companies, mobile top-up providers).
  2. Main consolidation accounts used by illicit networks.

## 3. Recommended Analysis Profile
Because the high-traffic nodes are dominated by legitimate utility and merchant payments, network alerts must distinguish transfer categories. We recommend profiling these nodes as follows:

| Receiver Category | Sender Count | Typical Transaction Types | Risk Profile |
| :--- | :--- | :--- | :--- |
| **Commercial Portal** | High ($\ge 500$) | Bill payments, utility services, card payments | Low Risk (Legitimate business transactions) |
| **Consolidation Node** | Moderate-to-High ($\ge 5$) | Peer-to-peer transfers, direct bank transfers | High Risk (Suspicious fund aggregation) |
