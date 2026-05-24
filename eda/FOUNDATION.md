# EDA Foundation: Financial Fraud Detection

This document outlines the core business risk vectors and metrics of concern for financial fraud detection EDA.

## 1. Velocity (Spike & Speed)
* **Outbound Volume Spikes:** Sudden rapid depletion of funds (cash-outs) in short windows (e.g., 10 minutes, 24 hours).
* **High Frequency:** Multiple rapid micro-transactions (card testing or automation/bot activity).

## 2. Behavioral Deviations
* **Baseline Deviation:** Transactions exceeding historical mean amounts (Z-Score) or average monthly balances.
* **Dormancy Wake-up:** Sudden large transactions on long-inactive accounts.
* **Anomalous Times:** High-value transactions outside user’s normal active hours (e.g., late night).

## 3. Regulatory & Anti-Money Laundering (AML) Compliance
* **Structuring (Smurfing):** Repeated transactions kept just below regulatory reporting thresholds (e.g., $9,900 vs. $10,000 trigger).
* **Mule Accounts:** High incoming volume followed by immediate external transfers to multiple distinct accounts.

## 4. Digital Channel Behavior
* **Profile Changes:** Sensitive settings modifications (password reset, email change) followed by immediate transfers (Account Takeover).
* **Channel Drift:** Sudden shift from typical web login to api/automated channels.

## 5. High-Risk Segments
* **New Accounts:** High transaction volume shortly after creation.
* **Demographics:** Age groups or location profiles exhibiting sudden unusual patterns.

## 6. Entity Resolution & Network Linkage (Fraud Rings)
* **Shared Hardware (FEASIBLE):** Multiple distinct `CUSTOMER_NUMBER` accounts logging in or executing transactions from the same `Device_ID_Hash`.
* **Circular Money Flow / Transaction Graphs (FEASIBLE):** Funds moving in closed loops (e.g., A -> B -> C -> A) or many-to-one/one-to-many paths using `CUSTOMER_NUMBER` and `Beneficiary_CUSTOMER_NUMBER`.
* *Not Feasible:* Shared PII (phone number, physical address, email are not present in the dataset).

## 7. Geographic & Spatial Anomalies
* **Impossible Travel (FEASIBLE):** A user initiating transactions from different locations within an impossible time window (e.g., different `IP_Address_Proxy` values within 30 minutes).
* *Not Feasible:* IP to Billing Mismatch (no customer billing address field is available in the customer profile).
* *Not Feasible:* High-Risk VPN/Tor node flags (no network IP categorization tags are provided in the data).

## 8. Device & Technical Footprinting
* **Device OS Anomaly & Drift (FEASIBLE):** Sudden change in `Device_OS` (e.g., switching from iOS to Android for the same user) or use of rare/unusual OS variants.
* *Not Feasible:* Device Emulators/Jailbreaks (no device security status logs exist).
* *Not Feasible:* Sensory/Biometric/Copy-Paste telemetry (no mouse movement, keyboard, or sensory telemetry is available).

## 9. Transaction Context & Counterparty Risk
* **Merchant & Category Risk Profiling (FEASIBLE):** Sudden spike in spending at high-risk transaction types (`TRANS_LV1`, `TRANS_LV2`) or specific receiver merchant IDs (`Merchant_ID_Masked`).
* **Cross-Border Outflow (FEASIBLE):** Sudden shift to international wire transfers or foreign currency conversions using transaction groups (`TRANS_LV1` / `TRANS_LV2`).

