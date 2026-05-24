# Pipeline Enhancement Proposal: Advanced Behavioral Features & Hierarchical Optimization

Based on the Exploratory Data Analysis (EDA) conducted across 1,418,030 transaction records, this document outlines the technical proposal to improve the precision, recall, and reliability of the fraud detection pipeline.

---

## 1. Continuous Feature Engineering (StandardPreprocessor)
To improve the machine learning model's capability to learn non-linear and context-aware boundaries, we recommend replacing simple binary indicators with continuous variables.

### A. Velocity (Spike & Speed)
* **`SUM_1H` & `COUNT_1H`:** Continuous sum and count of transactions in the last 1 hour.
* **`SUM_3H` & `COUNT_3H`:** Continuous sum and count of transactions in the last 3 hours.
* **`SUM_48H` & `COUNT_48H`:** Continuous sum and count of transactions in the last 48 hours.
* **`VELOCITY_RATIO_AMOUNT_1H_VS_24H`:** Ratio of 1-hour transaction volume to 24-hour volume.
* **`TRANS_AMOUNT_VS_30D_AVG_RATIO`:** Ratio of the current transaction amount to the customer's historical 30-day average transaction size.

### B. Behavioral Deviations & Dormancy
* **`DAYS_SINCE_LAST_TRANS`:** Continuous count of days since the previous transaction (filled with days since registration for the first transaction).
* **`HIST_NIGHT_RATIO`:** Cumulative ratio of late-night transactions (12 AM – 5 AM) executed by the customer prior to the current transaction.
* **`BALANCE_COVERAGE_RATIO`:** Ratio of the transaction amount to the monthly average balance.

### C. Outbound Dispersion (Mule Behavior)
* **`UNIQUE_BENEFICIARIES_24H`:** Continuous count of unique external destination accounts receiving funds from the customer within a 24-hour window.

### D. Digital Channel Behavior
* **`HOURS_SINCE_SEC_EVENT`:** Continuous count of hours elapsed since the customer's last security-sensitive modification (password reset, PIN change, address book update).
* **`HIST_BIOMETRIC_RATIO`:** Cumulative ratio of biometric logins (`LOGIN_FINGER` / `LOGIN_FACEID`) executed by the customer prior to the transaction.

### E. Early Lifecycle & Demographics
* **`TENURE_DAYS`:** Account age in days at the time of the transaction.
* **`CUSTOMER_AGE`:** Customer age in years at the time of the transaction.

---

## 2. High-Speed Route Optimization (HierarchicalMLPipeline)
To improve latency and reduce model execution costs for safe transactions:
* **Current state:** Tier 1 only filters based on activity sequence rarity and transaction amount.
* **Proposal:** Integrate the new 1-hour and 24-hour transaction count velocity metrics into the Tier 1 safety router. If a transaction is low-value and falls within normal velocity parameters (e.g. `COUNT_1H` = 1, `COUNT_24H` $\le 2$), mark it as safe immediately, bypassing the XGBoost model.

---

## 3. Causal Propagation Updates (BRACEExplainer)
When new features are added to the model, the Explainable AI (xAI) recourse search must be updated to maintain causal consistency:
* **Action:** If the explainer recommends reducing `TRANS_AMOUNT` to clear an alert, propagate this reduction mathematically to all dependent features:
  * `TRANS_AMOUNT_VS_30D_AVG_RATIO`
  * `VELOCITY_RATIO_AMOUNT_1H_VS_24H`
  * `BALANCE_COVERAGE_RATIO`
  * `SUM_AMOUNT_1H` and `SUM_AMOUNT_3H`
  This ensures that the generated counterfactual recommendations are mathematically correct and actionable.

---

## 4. Exclusion of Volatile Location Features
* **Insight:** Location profile shifts (`IP_Address_Proxy`) occur in 96.2% of normal customer transactions due to dynamic IP address allocation.
* **Action:** Exclude absolute "new location" flags from the model features to prevent high false-positive rates. Focus instead on relative geospatial anomalies (`IS_IMPOSSIBLE_TRAVEL` within 1 hour) and operating system changes (`Device_OS` shifts within 24 hours).
