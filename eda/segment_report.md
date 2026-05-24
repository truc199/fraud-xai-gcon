# EDA Report: High-Risk Segments & Demographic Analysis

This report outlines the findings from the new account early lifecycle and demographic outlier analysis conducted on 1,418,030 transaction logs.

## 1. New Account Early Lifecycle Abuse
Analyzes transaction activity occurring within the first 7 days of account creation (CIF opening).

* **Transactions on New Accounts:** 27,352 transactions occurred within the first 7 days of account creation.
* **Early Lifecycle Abuse Alerts:** **2,357** transactions (8.62% of new account transactions).
  * **Criteria:** Transaction occurs within 7 days of account creation, and the transaction amount is $\ge 50,000,000$.
  * *Insight:* Initiating high-value transfers immediately after opening an account is a strong indicator of early lifecycle abuse, typical of organized fraud groups.

## 2. Demographic Risk Factors (Age & Occupation Outliers)
Profiles transaction sizes across age extremes and occupational categories to detect anomalies.

### Age Extreme Alerts
* **Criteria:** Transaction amount $\ge 38,000,000$ (global p95 amount) executed by customers under 18 years old or over 70 years old.
* **Alert Count:** **394** transactions.
  * *Insight:* High-value transactions are rare for minors and seniors. These 394 transactions represent potential account exploitation or card theft.

### Occupation Outliers & Low-Income Alerts
* **Low-Income High-Value Alerts:** **3,463** transactions.
  * **Criteria:** Transaction amount $\ge 38,000,000$ executed by customers registered as Students, Unemployed, or Retired (Pensioners).
  * *Insight:* Large transfers from low-income segments deviate from expected financial profiles.
* **99th Percentile Transaction Sizes by Occupation Group:**
  * `BUSINESSMAN`: 159,444,000
  * `COMMERCIAL ASSOCIATE`: 188,000,000
  * `WORKING`: 161,500,000
  * `STATE SERVANT`: 140,124,000
  * `UNEMPLOYED`: 149,692,566
  * `STUDENT`: 257,551,350
  * `PENSIONER`: 495,080,000
  * *Insight:* The 99th percentile transaction size for Students (257.6M) and Unemployed (149.7M) is extremely high. This confirms that these demographics are highly exposed to anomalous high-value transactions, which often correlate with third-party account usage.

## 3. Detection Recommendations
We recommend incorporating the following logic into the main pipeline:

| Severity | Alert Rule | Volume Impact | Business Logic |
| :--- | :--- | :--- | :--- |
| **High** | `IS_EARLY_ABUSE_ALERT` = 1 | ~2,357 alerts | Transactions $\ge 50,000,000$ within the first 7 days of account opening. |
| **Medium** | `IS_LOW_INCOME_HIGH_VALUE_ALERT` = 1 AND `IS_OCCUPATION_OUTLIER` = 1 | ~1,100 alerts | Student/Unemployed/Retired transfers exceeding their specific 99th percentile threshold. |
| **High** | `IS_AGE_EXTREME` = 1 | ~394 alerts | Minor/Senior transfers exceeding 38,000,000. |
