# Pipeline Feature Classification

This document classifies all features processed by `AdvancedPreprocessor` as either **Absolute** or **Relative** inputs for the fraud detection models.

---

## 1. Absolute Features

These features represent raw counts, absolute amounts, static customer demographics, or absolute timestamps.

### Amounts & Balances
*   `TRANS_AMOUNT`: The transaction value in local currency.
*   `HIST_AVG_CA_BALANCE`: The historical average current account balance for the customer.
*   `HIST_AVG_TRANS_AMOUNT`: The customer's average historical transaction amount.
*   `SUM_AMOUNT_1H`: Total money transferred by the customer in the last 1 hour.
*   `SUM_AMOUNT_3H`: Total money transferred by the customer in the last 3 hours.
*   `SUM_AMOUNT_24H`: Total money transferred by the customer in the last 24 hours.
*   `SUM_AMOUNT_48H`: Total money transferred by the customer in the last 48 hours.
*   `SUM_AMOUNT_7D`: Total money transferred by the customer in the last 7 days.
*   `SUM_AMOUNT_30D`: Total money transferred by the customer in the last 30 days.

### Counts & Frequencies
*   `TRANS_NO`: Transaction sequential sequence number.
*   `HIST_TRANS_COUNT`: Total historical transaction count for this customer.
*   `HIST_LOGIN_COUNT`: Cumulative count of historical logins prior to this transaction.
*   `COUNT_1H`: Transaction count in the last 1 hour.
*   `COUNT_3H`: Transaction count in the last 3 hours.
*   `COUNT_24H`: Transaction count in the last 24 hours.
*   `COUNT_48H`: Transaction count in the last 48 hours.
*   `COUNT_7D`: Transaction count in the last 7 days.
*   `COUNT_30D`: Transaction count in the last 30 days.
*   `UNIQUE_BENEFICIARIES_24H`: Unique outbound destination accounts targeted by the customer in the last 24 hours.

### Time & Tenure
*   `TRANS_HOUR`: The hour of the day (0-23) when the transaction took place.
*   `CUSTOMER_AGE`: Customer age at the time of the transaction (years).
*   `TENURE_DAYS`: Account age in days at the time of the transaction.
*   `DAYS_SINCE_LAST_TRANS`: Number of days elapsed since the customer's previous transaction.
*   `HOURS_SINCE_SEC_EVENT`: Hours since the last security-sensitive event (e.g. PIN/password reset).

### Categorical Profiles (Label Encoded)
*   `TRANS_LV1`: High-level transaction category (e.g. Transfer, Payment).
*   `TRANS_LV2`: Detailed transaction subtype (e.g. Within Bank, Outside Bank).
*   `DAY_OF_WEEK`: The day of the week (Mon-Sun).
*   `CLIENT_SEX`: Sex/Gender of the client.
*   `EB_REGISTER_CHANNEL`: Registration channel for online banking (e.g. Branch, Mobile).
*   `VERIFY_METHOD`: The authentication protocol used (e.g. SMS, Smart OTP).
*   `Occupation_Group`: Customer occupation category.
*   `STAFF`: Binary indicator flag if the customer is bank staff.
*   `SMS`: Binary indicator flag if SMS notification service is enabled.

---

## 2. Relative Features

These features compare current behavior against historical averages, balances, or evaluate proportional patterns and statistical deviations.

### Amount & Velocity Ratios
*   `TRANS_AMOUNT_Z_SCORE`: Ratio of the current transaction amount to the customer's historical average:
    $$\text{TRANS\_AMOUNT\_Z\_SCORE} = \frac{\text{TRANS\_AMOUNT}}{\text{HIST\_AVG\_TRANS\_AMOUNT} + 10^{-5}}$$
*   `BALANCE_COVERAGE_RATIO`: Ratio of the current transaction amount to the customer's historical monthly balance:
    $$\text{BALANCE\_COVERAGE\_RATIO} = \frac{\text{TRANS\_AMOUNT}}{\text{HIST\_AVG\_CA\_BALANCE} + 10^{-5}}$$
*   `TRANS_AMOUNT_VS_30D_AVG_RATIO`: Ratio of the current transaction amount to the 30-day average transaction amount:
    $$\text{TRANS\_AMOUNT\_VS\_30D\_AVG\_RATIO} = \frac{\text{TRANS\_AMOUNT}}{\text{SUM\_AMOUNT\_30D} / (\text{COUNT\_30D} + 10^{-5}) + 10^{-5}}$$
*   `VELOCITY_RATIO_AMOUNT_1H_VS_24H`: Proportion of 24h spending concentrated in the last 1 hour:
    $$\text{VELOCITY\_RATIO\_AMOUNT\_1H\_VS\_24H} = \frac{\text{SUM\_AMOUNT\_1H}}{\text{SUM\_AMOUNT\_24H} + 10^{-5}}$$
*   `VELOCITY_RATIO_AMOUNT_24H_VS_7D`: Proportion of 7d spending concentrated in the last 24 hours:
    $$\text{VELOCITY\_RATIO\_AMOUNT\_24H\_VS\_7D} = \frac{\text{SUM\_AMOUNT\_24H}}{\text{SUM\_AMOUNT\_7D} + 10^{-5}}$$
*   `VELOCITY_RATIO_AMOUNT_7D_VS_30D`: Proportion of 30d spending concentrated in the last 7 days:
    $$\text{VELOCITY\_RATIO\_AMOUNT\_7D\_VS\_30D} = \frac{\text{SUM\_AMOUNT\_7D}}{\text{SUM\_AMOUNT\_30D} + 10^{-5}}$$
*   `VELOCITY_RATIO_COUNT_1H_VS_24H`: Proportion of 24h transactions occurring in the last 1 hour:
    $$\text{VELOCITY\_RATIO\_COUNT\_1H\_VS\_24H} = \frac{\text{COUNT\_1H}}{\text{COUNT\_24H} + 10^{-5}}$$
*   `VELOCITY_RATIO_COUNT_24H_VS_7D`: Proportion of 7d transactions occurring in the last 24 hours:
    $$\text{VELOCITY\_RATIO\_COUNT\_24H\_VS\_7D} = \frac{\text{COUNT\_24H}}{\text{COUNT\_7D} + 10^{-5}}$$
*   `VELOCITY_RATIO_COUNT_7D_VS_30D`: Proportion of 30d transactions occurring in the last 7 days:
    $$\text{VELOCITY\_RATIO\_COUNT\_7D\_VS\_30D} = \frac{\text{COUNT\_7D}}{\text{COUNT\_30D} + 10^{-5}}$$

### Proportional Usage Metrics
*   `HIST_BIOMETRIC_RATIO`: The percentage of cumulative logins that were completed via biometrics (Fingerprint/FaceID):
    $$\text{HIST\_BIOMETRIC\_RATIO} = \frac{\text{Biometric Logins}}{\text{Total Logins} + 10^{-5}}$$
*   `HIST_NIGHT_RATIO`: The percentage of cumulative historical transactions that took place during night hours (00:00 - 05:00):
    $$\text{HIST\_NIGHT\_RATIO} = \frac{\text{Night Transactions}}{\text{Total Transactions} + 10^{-5}}$$

### Statistical Deviation & Likelihood Scores
*   `BENFORD_DEV`: Divergence score measuring how much the customer's transaction amount leading digits deviate from Benford's Law distribution.
*   `ACTIVITY_SEQ_RARITY`: The second-order Markov chain log-probability score of the customer's activity transition patterns.
