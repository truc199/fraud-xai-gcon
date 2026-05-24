# EDA Report: Behavioral Deviation Analysis

This report outlines the findings from the behavioral deviation and dormancy analysis conducted on 1,418,030 transaction logs.

## 1. Baseline Deviation (`BALANCE_COVERAGE_RATIO`)
Measures how much of the customer's average monthly current account balance is transferred out in a single transaction.
* **Median (p50):** 0.21 (21% of average balance)
* **90th Percentile (p90):** 3.63 (3.6x of average balance)
* **95th Percentile (p95):** 8.55 (8.5x of average balance)
* **99th Percentile (p99):** 67.74 (67.7x of average balance)
* *Insight:* A single transaction representing over 8.5x the typical monthly average balance is a significant outlier (top 5%). When it exceeds 67x, it represents extreme balance draining.

## 2. Dormancy Gap (`DAYS_SINCE_LAST_TRANS`)
Measures the time elapsed (in days) since the customer's previous transaction.
* **Median (p50):** 1.17 days
* **90th Percentile (p90):** 10.96 days
* **95th Percentile (p95):** 20.63 days
* **99th Percentile (p99):** 57.96 days
* **Max:** 357.63 days (almost 1 year of inactivity)

### Dormancy Wake-ups
* **Criteria:** Transaction amount $\ge 10,000,000$ after a dormancy period of $\ge 90$ days.
* **Alert Count:** **1,412** transactions (0.10% of total volume).
* *Insight:* These are high-value transactions on previously dormant accounts. They represent immediate risk, as account holders are unlikely to monitor these accounts actively.

## 3. Anomalous Transaction Times
We analyze whether transactions occur during high-risk sleep hours and whether they deviate from the customer's historical profile.

* **Late Night Transactions:** **46,449** transactions (3.28% of total volume) occurred globally between 12 AM and 5 AM.
* **Anomalous Time Alerts:** **2,155** transactions (0.15% of total volume).
  * **Criteria:** Transaction occurs between 12 AM – 5 AM, the customer has transacted $\ge 3$ times historically, their historical late-night transaction ratio is $< 5\%$, and the transaction is high-value ($\ge 5,000,000$).
  * *Insight:* These represent severe out-of-pattern access events where a customer who typically transacts during standard daytime hours suddenly attempts a large transfer in the middle of the night.

## 4. Anomaly Detection Rules & Impact
Based on these findings, we recommend incorporating the following logic into the main pipeline:

| Severity | Alert Rule | Volume Impact | Business Logic |
| :--- | :--- | :--- | :--- |
| **Critical** | `IS_DORMANT_WAKEUP` = 1 AND `BALANCE_COVERAGE_RATIO` $\ge 8.5$ | ~200 alerts | High-value drainage of long-silent accounts. |
| **High** | `IS_ANOMALOUS_TIME_ALERT` = 1 AND `BALANCE_COVERAGE_RATIO` $\ge 3.6$ | ~450 alerts | Out-of-pattern late-night access combined with above-average account balance draining. |
