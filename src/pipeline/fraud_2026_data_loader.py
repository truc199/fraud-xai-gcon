import os
import sqlite3
import pandas as pd
import numpy as np
import math
from collections import defaultdict
from typing import Optional, Generator, Dict
from src.pipeline.protocols import DataLoader
from src.pipeline.second_order_markov_loader import calculate_second_order_markov_mapping


# ---------------------------------------------------------------------------
# Standalone helper: rolling unique beneficiaries in 24h window
# (Copied from advanced_data_loader.py - no changes)
# ---------------------------------------------------------------------------
def compute_rolling_unique_beneficiaries(df):
    unique_counts = np.zeros(len(df), dtype=int)
    grouped = df.groupby('CUSTOMER_NUMBER')
    
    for cust, group in grouped:
        times = group['ts_dt'].values
        bens = group['Beneficiary_CUSTOMER_NUMBER'].fillna('UNKNOWN').astype(str).values
        indices = group.index.values
        
        start_idx = 0
        active_bens = {}
        
        for i in range(len(group)):
            current_time = times[i]
            b = bens[i]
            
            if b not in ['UNKNOWN', 'NaN', 'nan']:
                active_bens[b] = active_bens.get(b, 0) + 1
            
            limit_time = current_time - np.timedelta64(24, 'h')
            while times[start_idx] < limit_time:
                old_b = bens[start_idx]
                if old_b not in ['UNKNOWN', 'NaN', 'nan']:
                    active_bens[old_b] -= 1
                    if active_bens[old_b] == 0:
                        del active_bens[old_b]
                start_idx += 1
                
            unique_counts[indices[i]] = len(active_bens)
            
    return unique_counts


# ---------------------------------------------------------------------------
# NEW: Benford with strict N>=50 threshold
# ---------------------------------------------------------------------------
def calculate_benford_mapping_strict(conn: sqlite3.Connection) -> Dict[int, float]:
    """Calculate KL-Divergence of transaction amount leading digits vs Benford's Law per customer.
    
    Uses a strict minimum sample size of N >= 50 transactions to reduce false positives,
    per auditing research on small-sample Benford test unreliability.
    """
    MIN_SAMPLE_SIZE = 50

    cursor = conn.cursor()
    cursor.execute("SELECT CUSTOMER_NUMBER, TRANS_AMOUNT FROM Data_Transaction")
    
    cust_amounts = defaultdict(list)
    for cust, amt in cursor.fetchall():
        if amt and amt > 0:
            cust_amounts[cust].append(amt)
            
    benford_dist = [math.log10(1 + 1.0 / d) for d in range(1, 10)]
    mapping = {}
    
    for cust, amts in cust_amounts.items():
        if len(amts) < MIN_SAMPLE_SIZE:
            mapping[cust] = 0.0
            continue
            
        digits = []
        for a in amts:
            s = str(a).lstrip('0.').replace('.', '')
            if s:
                d = int(s[0])
                if 1 <= d <= 9:
                    digits.append(d)
                    
        if len(digits) < MIN_SAMPLE_SIZE:
            mapping[cust] = 0.0
            continue
            
        counts = [0] * 9
        for d in digits:
            counts[d - 1] += 1
            
        probs = [c / len(digits) for c in counts]
        
        kl = 0.0
        for p, q in zip(probs, benford_dist):
            if p > 0:
                kl += p * math.log(p / q)
        mapping[cust] = kl
        
    return mapping


# ---------------------------------------------------------------------------
# NEW: IP Hopping Velocity (unique IPs per Device in 3h sliding window)
# ---------------------------------------------------------------------------
def compute_ip_hopping_velocity(df: pd.DataFrame) -> pd.Series:
    """Count number of unique IP_Address_Proxy values used by the same Device_ID_Hash
    within a rolling 3-hour window ending at each transaction.
    
    Rationale: Malware like GoldPickaxe rotates proxies to evade geolocation checks.
    A legitimate user rarely changes IP more than once per session.
    """
    result = np.ones(len(df), dtype=int)

    device_col = 'Device_ID_Hash' if 'Device_ID_Hash' in df.columns else None
    ip_col = 'IP_Address_Proxy' if 'IP_Address_Proxy' in df.columns else None

    if device_col is None or ip_col is None:
        return pd.Series(result, index=df.index)

    grouped = df.groupby(device_col)

    for device, group in grouped:
        if str(device) in ('UNKNOWN', 'nan', 'NaN', ''):
            continue

        times = group['ts_dt'].values
        ips = group[ip_col].fillna('UNKNOWN').astype(str).values
        indices = group.index.values

        start_idx = 0
        active_ips = {}

        for i in range(len(group)):
            current_time = times[i]
            ip = ips[i]

            if ip not in ('UNKNOWN', 'nan', 'NaN', ''):
                active_ips[ip] = active_ips.get(ip, 0) + 1

            limit_time = current_time - np.timedelta64(3, 'h')
            while start_idx < i and times[start_idx] < limit_time:
                old_ip = ips[start_idx]
                if old_ip not in ('UNKNOWN', 'nan', 'NaN', ''):
                    active_ips[old_ip] -= 1
                    if active_ips[old_ip] == 0:
                        del active_ips[old_ip]
                start_idx += 1

            result[indices[i]] = len(active_ips)

    return pd.Series(result, index=df.index)


# ---------------------------------------------------------------------------
# NEW: Graph-based features (PageRank + In-Degree Centrality)
# ---------------------------------------------------------------------------
def compute_graph_features(conn: sqlite3.Connection) -> Dict[int, Dict[str, float]]:
    """Build a directed graph from CUSTOMER_NUMBER -> Beneficiary_CUSTOMER_NUMBER
    and compute PageRank and In-Degree Centrality for each node.

    Rationale: Money mule accounts and shell companies act as 'hubs' that receive
    funds from many sources. PageRank and In-Degree Centrality quantify this
    hub-ness. Standard technique in AML graph analytics (FinCEN, Europol SIENA).
    """
    try:
        import networkx as nx
    except ImportError:
        print("WARNING: networkx not installed. GNN features will be zeroed.")
        return {}

    query = """
    SELECT CUSTOMER_NUMBER, Beneficiary_CUSTOMER_NUMBER
    FROM Data_Transaction
    WHERE Beneficiary_CUSTOMER_NUMBER IS NOT NULL
      AND Beneficiary_CUSTOMER_NUMBER != 'UNKNOWN'
      AND Beneficiary_CUSTOMER_NUMBER != ''
    """
    df_edges = pd.read_sql_query(query, conn)

    if df_edges.empty:
        return {}

    G = nx.DiGraph()
    for _, row in df_edges.iterrows():
        sender = row['CUSTOMER_NUMBER']
        receiver = row['Beneficiary_CUSTOMER_NUMBER']
        if G.has_edge(sender, receiver):
            G[sender][receiver]['weight'] += 1
        else:
            G.add_edge(sender, receiver, weight=1)

    print(f"Transaction graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")

    pagerank = nx.pagerank(G, weight='weight', max_iter=100)
    n = G.number_of_nodes()
    
    # IMPROVEMENT: Scale PageRank by N to avoid microscopic values (mean ~0.00001)
    # This ensures ML models (like Isolation Forest/XGBoost) can split on it without precision issues
    for node in pagerank:
        pagerank[node] = pagerank[node] * n

    in_degree_centrality = {}
    if n > 1:
        for node in G.nodes():
            in_degree_centrality[node] = G.in_degree(node) / (n - 1)
    else:
        for node in G.nodes():
            in_degree_centrality[node] = 0.0

    mapping = {}
    for node in G.nodes():
        try:
            node_key = int(node)
        except (ValueError, TypeError):
            node_key = node
        mapping[node_key] = {
            'PAGERANK_SCORE': pagerank.get(node, 0.0),
            'IN_DEGREE_CENTRALITY': in_degree_centrality.get(node, 0.0),
        }

    return mapping

# ---------------------------------------------------------------------------
# NEW: Bust-Out Utilization (max credit utilization from Data_Card)
# ---------------------------------------------------------------------------
def compute_limit_utilization_velocity(conn: sqlite3.Connection) -> Dict[int, float]:
    """Compute the maximum Month-over-Month credit utilization velocity per customer.

    LIMIT_UTILIZATION_VELOCITY = max(utilization_t - utilization_{t-1}) across months.
    Rationale: Synthetic identity fraudsters build up credit over months at low
    utilization (~5-10%), then spike utilization by 50%+ in a single month before
    disappearing (bust-out pattern). The VELOCITY captures this spike, not the
    absolute level — distinguishing bust-out from legitimate high spenders.
    """
    query = """
    SELECT CUSTOMER_NUMBER, MONTH, LIMIT_AMT_CREDIT, OUTSTANDING_BAL_CREDIT
    FROM Data_Card
    WHERE LIMIT_AMT_CREDIT > 0
    ORDER BY CUSTOMER_NUMBER, MONTH
    """
    df_card = pd.read_sql_query(query, conn)

    if df_card.empty:
        return {}

    df_card['LIMIT_AMT_CREDIT'] = pd.to_numeric(df_card['LIMIT_AMT_CREDIT'], errors='coerce').fillna(0)
    df_card['OUTSTANDING_BAL_CREDIT'] = pd.to_numeric(df_card['OUTSTANDING_BAL_CREDIT'], errors='coerce').fillna(0)
    df_card = df_card[df_card['LIMIT_AMT_CREDIT'] > 0]

    if df_card.empty:
        return {}

    df_card['utilization'] = df_card['OUTSTANDING_BAL_CREDIT'] / df_card['LIMIT_AMT_CREDIT']
    df_card['prev_util'] = df_card.groupby('CUSTOMER_NUMBER')['utilization'].shift(1)
    df_card['util_velocity'] = df_card['utilization'] - df_card['prev_util']
    valid = df_card.dropna(subset=['util_velocity'])

    if valid.empty:
        return {}

    max_velocity = valid.groupby('CUSTOMER_NUMBER')['util_velocity'].max()
    return max_velocity.to_dict()


# ---------------------------------------------------------------------------
# NEW: Structuring Overpayment Flag
# ---------------------------------------------------------------------------
def compute_structuring_overpayment(conn: sqlite3.Connection, df: pd.DataFrame) -> pd.Series:
    """Detect structuring via credit card overpayment.

    Logic: Dirty money -> Split into small repayments -> Overpay credit card
    balance -> Request refund or spend -> Clean money.

    Flag = 1 when:
      - Cumulative repayment in 30 days > Outstanding balance (overpaying)
      - AND repayment count in 30 days >= 2 (splitting pattern)

    References: GAO-02-670 (2002), PwC Global Economic Crime Survey (2021).
    """
    # Get credit card outstanding balance per customer (latest month)
    card_query = """
    SELECT CUSTOMER_NUMBER, MAX(MONTH) as LATEST_MONTH, OUTSTANDING_BAL_CREDIT
    FROM Data_Card
    WHERE OUTSTANDING_BAL_CREDIT IS NOT NULL
    GROUP BY CUSTOMER_NUMBER
    """
    card_df = pd.read_sql_query(card_query, conn)
    card_df['OUTSTANDING_BAL_CREDIT'] = pd.to_numeric(card_df['OUTSTANDING_BAL_CREDIT'], errors='coerce').fillna(0)
    outstanding_map = dict(zip(card_df['CUSTOMER_NUMBER'], card_df['OUTSTANDING_BAL_CREDIT']))

    # Identify credit card repayment transactions
    repay_mask = df['TRANS_LV2'].str.contains('Credit_card', case=False, na=False)
    
    result = pd.Series(0, index=df.index, dtype=int)

    if repay_mask.sum() == 0:
        return result

    for cust, group in df.groupby('CUSTOMER_NUMBER'):
        outstanding = outstanding_map.get(cust, None)
        if outstanding is None or outstanding <= 0:
            continue

        cust_repays = group[repay_mask.loc[group.index]]
        if cust_repays.empty:
            continue

        times = cust_repays['ts_dt'].values
        amounts = cust_repays['TRANS_AMOUNT'].values
        indices = cust_repays.index.values

        start_idx = 0
        cum_amount = 0.0
        count = 0

        for i in range(len(cust_repays)):
            current_time = times[i]
            cum_amount += amounts[i]
            count += 1

            limit_time = current_time - np.timedelta64(30, 'D')
            while start_idx < i and times[start_idx] < limit_time:
                cum_amount -= amounts[start_idx]
                count -= 1
                start_idx += 1

            if cum_amount > outstanding and count >= 2:
                result.loc[indices[i]] = 1

    return result


# ---------------------------------------------------------------------------
# NEW: Auth Downgrade Risk
# ---------------------------------------------------------------------------
def compute_auth_downgrade_risk(df: pd.DataFrame, conn: sqlite3.Connection) -> pd.Series:
    """Detect authentication downgrade: a customer who historically uses biometric
    login (FaceID/Fingerprint) suddenly performs transactions from a new device
    using password-only login.

    Rationale: Account takeover (ATO) attackers register new devices and cannot
    use the victim's biometrics. Per Decision 2345/QD-NHNN (July 2024), large
    transactions require facial authentication. Downgrading is a red flag.
    """
    result = pd.Series(0.0, index=df.index, dtype=float)

    if 'HIST_BIOMETRIC_RATIO' not in df.columns or 'LAST_LOGIN_METHOD' not in df.columns:
        return result

    has_device = 'Device_ID_Hash' in df.columns
    
    # To track seen devices chronologically per customer
    # We will build a rolling set of seen devices.
    seen_devices = defaultdict(set)

    for idx in df.index:
        bio_ratio = df.at[idx, 'HIST_BIOMETRIC_RATIO']
        last_login = df.at[idx, 'LAST_LOGIN_METHOD']
        cust = df.at[idx, 'CUSTOMER_NUMBER']
        
        # Track device
        is_new_device = False
        if has_device:
            current_device = df.at[idx, 'Device_ID_Hash']
            if current_device not in ('UNKNOWN', 'nan', 'NaN', ''):
                if current_device not in seen_devices[cust]:
                    is_new_device = True
                    seen_devices[cust].add(current_device)

        # IMPROVEMENT: Lower biometric threshold (0.6 is too strict, EDA shows only 1 user hits it)
        # We just need to know they *use* biometrics occasionally (> 0.05)
        if bio_ratio < 0.05:
            continue

        # Condition 2: Last login was non-biometric (password only)
        if last_login in ('LOGIN_FINGER', 'LOGIN_FACEID'):
            continue

        # Condition 3: Transaction is on a completely NEW device
        if has_device and is_new_device:
            # High risk: Uses biometrics historically, but password today on a brand new device
            result.at[idx] = 1.0
        elif has_device and not is_new_device:
            # Normal: Password on a known device
            result.at[idx] = 0.0
        else:
            result.at[idx] = bio_ratio * 0.5

    return result

# ===========================================================================
# Main DataLoader class
# ===========================================================================
class Fraud2026DataLoader(DataLoader):
    """DataLoader that extends AdvancedDataLoader with 6 additional features
    targeting modern fraud patterns (2020-2026):

    1. BENFORD_DEV         - Upgraded with N>=50 threshold
    2. IP_HOPPING_VELOCITY - Unique IPs per device in 3h window
    3. PAGERANK_SCORE      - Graph centrality (money mule detection)
    4. IN_DEGREE_CENTRALITY - Inbound connection count (hub detection)
    5. BUST_OUT_UTILIZATION - Max credit card utilization ratio
    6. STRUCTURING_OVERPAYMENT_FLAG - Split repayment overpayment detection
    7. AUTH_DOWNGRADE_RISK  - Biometric-to-password downgrade on new device
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.benford_mapping: Optional[Dict[int, float]] = None
        self.seq_mapping: Optional[Dict[int, float]] = None
        self.graph_mapping: Optional[Dict[int, Dict[str, float]]] = None
        self.limit_util_velocity_mapping: Optional[Dict[int, float]] = None
        self.cached_df: Optional[pd.DataFrame] = None

    def _get_sql_query(self, limit: Optional[int] = None) -> str:
        query = """
            WITH trans_time_added AS (
                SELECT 
                    t.col_0 as TRANSACTION_ID,
                    t.CUSTOMER_NUMBER,
                    t.TRANS_LV1,
                    t.TRANS_LV2,
                    t.TRANS_DATE,
                    t.DAY_OF_WEEK,
                    t.TRANS_HOUR,
                    t.TRANS_NO,
                    t.TRANS_AMOUNT,
                    t.Beneficiary_CUSTOMER_NUMBER,
                    t.Device_ID_Hash,
                    t.Device_OS,
                    t.IP_Address_Proxy,
                    (julianday(t.TRANS_DATE) + (t.TRANS_HOUR / 24.0)) as ts
                FROM Data_Transaction t
            ),
            rolling_metrics AS (
                SELECT 
                    TRANSACTION_ID,
                    CUSTOMER_NUMBER,
                    TRANS_LV1,
                    TRANS_LV2,
                    TRANS_DATE,
                    DAY_OF_WEEK,
                    TRANS_HOUR,
                    TRANS_NO,
                    TRANS_AMOUNT,
                    Beneficiary_CUSTOMER_NUMBER,
                    Device_ID_Hash,
                    Device_OS,
                    IP_Address_Proxy,
                    ts,
                    SUM(TRANS_AMOUNT) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 1.0/24.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_1H,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 1.0/24.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_1H,
                    SUM(TRANS_AMOUNT) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 3.0/24.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_3H,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 3.0/24.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_3H,
                    SUM(TRANS_AMOUNT) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 1.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_24H,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 1.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_24H,
                    SUM(TRANS_AMOUNT) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 2.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_48H,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 2.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_48H,
                    SUM(TRANS_AMOUNT) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 7.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_7D,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 7.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_7D,
                    SUM(TRANS_AMOUNT) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 30.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_30D,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 30.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_30D
                FROM trans_time_added
            ),
            deposit_agg AS (
                SELECT CUSTOMER_NUMBER, AVG(AVG_CA_BALANCE) as HIST_AVG_CA_BALANCE 
                FROM Data_Deposit GROUP BY CUSTOMER_NUMBER
            ),
            trans_agg AS (
                SELECT CUSTOMER_NUMBER, AVG(TRANS_AMOUNT) as HIST_AVG_TRANS_AMOUNT, COUNT(*) as HIST_TRANS_COUNT
                FROM Data_Transaction GROUP BY CUSTOMER_NUMBER
            )
            SELECT 
                r.TRANSACTION_ID,
                r.CUSTOMER_NUMBER,
                r.TRANS_LV1,
                r.TRANS_LV2,
                r.TRANS_DATE,
                r.DAY_OF_WEEK,
                r.TRANS_HOUR,
                r.TRANS_NO,
                r.TRANS_AMOUNT,
                r.Beneficiary_CUSTOMER_NUMBER,
                r.Device_ID_Hash,
                r.Device_OS,
                r.IP_Address_Proxy,
                c.CLIENT_SEX,
                c.CLIENT_CREATE_DATE,
                c.DATE_OF_BIRTH,
                c.STAFF,
                c.IB_REGISTER_DATE,
                c.EB_REGISTER_CHANNEL,
                c.SMS,
                c.VERIFY_METHOD,
                c.Occupation_Group,
                r.SUM_AMOUNT_1H,
                r.COUNT_1H,
                r.SUM_AMOUNT_3H,
                r.COUNT_3H,
                r.SUM_AMOUNT_24H,
                r.COUNT_24H,
                r.SUM_AMOUNT_48H,
                r.COUNT_48H,
                r.SUM_AMOUNT_7D,
                r.COUNT_7D,
                r.SUM_AMOUNT_30D,
                r.COUNT_30D,
                COALESCE(d.HIST_AVG_CA_BALANCE, 0.0) as HIST_AVG_CA_BALANCE,
                COALESCE(ta.HIST_AVG_TRANS_AMOUNT, 0.0) as HIST_AVG_TRANS_AMOUNT,
                COALESCE(ta.HIST_TRANS_COUNT, 0) as HIST_TRANS_COUNT
            FROM rolling_metrics r
            LEFT JOIN Data_Customer c ON r.CUSTOMER_NUMBER = c.CUSTOMER_NUMBER
            LEFT JOIN deposit_agg d ON r.CUSTOMER_NUMBER = d.CUSTOMER_NUMBER
            LEFT JOIN trans_agg ta ON r.CUSTOMER_NUMBER = ta.CUSTOMER_NUMBER
        """
        if limit:
            query += f" LIMIT {limit}"
        return query

    def load_training_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Load fully aggregated dataset with advanced continuous features
        plus 2026 fraud detection features."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
            
        print("Extracting transaction logs and rolling window aggregates...")
        conn = sqlite3.connect(self.db_path)
        query = self._get_sql_query(limit=limit)
        df = pd.read_sql_query(query, conn)
        
        # ---------------------------------------------------------------
        # BASE FEATURES (copied from AdvancedDataLoader)
        # ---------------------------------------------------------------

        # 1. Processing timestamps and sorting sequentially
        df['ts_dt'] = pd.to_datetime(df['TRANS_DATE']) + pd.to_timedelta(df['TRANS_HOUR'], unit='h')
        df['CLIENT_CREATE_DATE'] = pd.to_datetime(df['CLIENT_CREATE_DATE'], errors='coerce')
        df['DATE_OF_BIRTH'] = pd.to_datetime(df['DATE_OF_BIRTH'], errors='coerce')
        df['IB_REGISTER_DATE'] = pd.to_datetime(df['IB_REGISTER_DATE'], errors='coerce')
        
        df = df.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
        df['tx_id'] = df.index
        
        # 2. Compute Days Since Last Transaction
        print("Computing transaction time gaps...")
        grouped = df.groupby('CUSTOMER_NUMBER')
        df['DAYS_SINCE_LAST_TRANS'] = grouped['ts_dt'].diff().dt.total_seconds() / (24 * 3600)
        reg_date = df['IB_REGISTER_DATE'].fillna(df['CLIENT_CREATE_DATE'])
        days_since_reg = (df['ts_dt'] - reg_date).dt.total_seconds() / (24 * 3600)
        df['DAYS_SINCE_LAST_TRANS'] = df['DAYS_SINCE_LAST_TRANS'].fillna(days_since_reg).fillna(999.0)
        
        # 3. Compute Outbound unique beneficiaries in 24 hours
        df['UNIQUE_BENEFICIARIES_24H'] = compute_rolling_unique_beneficiaries(df)
        
        # 4. Integrate Security Event to Transaction Gaps
        print("Loading customer activity logs for security event mapping...")
        act_query = """
            SELECT 
                CUSTOMER_NUMBER,
                ACTIVITY_DATE,
                ACTIVITY_HOUR,
                ACTIVITY_NAME
            FROM Data_Activity
            WHERE ACTIVITY_NAME IN (
                'LOGIN', 'LOGIN_FINGER', 'LOGIN_FACEID',
                'CHANGE_PASSWORD', 'SET_PASSWORD', 
                'MB_SET_PIN', 'MB_CHANGE_PIN', 'MB_RESET_PIN',
                'ACCOUNT_ADDRESS_BOOK_UPDATE'
            )
        """
        act_df = pd.read_sql_query(act_query, conn)
        act_df['ts_dt'] = pd.to_datetime(act_df['ACTIVITY_DATE']) + pd.to_timedelta(act_df['ACTIVITY_HOUR'], unit='h')
        
        security_names = [
            'CHANGE_PASSWORD', 'SET_PASSWORD', 
            'MB_SET_PIN', 'MB_CHANGE_PIN', 'MB_RESET_PIN',
            'ACCOUNT_ADDRESS_BOOK_UPDATE'
        ]
        sec_df = act_df[act_df['ACTIVITY_NAME'].isin(security_names)].copy()
        login_df = act_df[~act_df['ACTIVITY_NAME'].isin(security_names)].copy()
        
        # Sort and merge security events
        tx_df_sorted = df.sort_values('ts_dt').reset_index(drop=True)
        sec_df = sec_df.sort_values('ts_dt').reset_index(drop=True)
        sec_df['sec_event_ts'] = sec_df['ts_dt']
        
        merged_sec = pd.merge_asof(
            tx_df_sorted,
            sec_df[['CUSTOMER_NUMBER', 'ts_dt', 'sec_event_ts']],
            on='ts_dt',
            by='CUSTOMER_NUMBER',
            direction='backward'
        )
        
        # Align back to df
        merged_sec = merged_sec.sort_values('tx_id').reset_index(drop=True)
        df['LAST_SEC_EVENT_TS'] = merged_sec['sec_event_ts']
        df['HOURS_SINCE_SEC_EVENT'] = (df['ts_dt'] - df['LAST_SEC_EVENT_TS']).dt.total_seconds() / 3600
        df['HOURS_SINCE_SEC_EVENT'] = df['HOURS_SINCE_SEC_EVENT'].fillna(999.0)
        
        # 5. Integrate Login Channel Statistics
        print("Mapping login events and computing biometric usage ratio...")
        login_df = login_df.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
        login_df['IS_BIOMETRIC'] = login_df['ACTIVITY_NAME'].isin(['LOGIN_FINGER', 'LOGIN_FACEID']).astype(int)
        
        grouped_logins = login_df.groupby('CUSTOMER_NUMBER')
        login_df['cum_login_count'] = grouped_logins.cumcount()
        login_df['cum_biometric_count'] = grouped_logins['IS_BIOMETRIC'].cumsum() - login_df['IS_BIOMETRIC']
        login_df['cum_biometric_ratio'] = login_df['cum_biometric_count'] / (login_df['cum_login_count'] + 1e-5)
        
        login_df['login_ts'] = login_df['ts_dt']
        login_df = login_df.sort_values('ts_dt').reset_index(drop=True)
        
        merged_login = pd.merge_asof(
            tx_df_sorted,
            login_df[['CUSTOMER_NUMBER', 'ts_dt', 'login_ts', 'ACTIVITY_NAME', 'cum_biometric_ratio', 'cum_login_count']],
            on='ts_dt',
            by='CUSTOMER_NUMBER',
            direction='backward'
        )
        
        # Align back to df
        merged_login = merged_login.sort_values('tx_id').reset_index(drop=True)
        df['LAST_LOGIN_METHOD'] = merged_login['ACTIVITY_NAME'].fillna('UNKNOWN')
        df['HIST_BIOMETRIC_RATIO'] = merged_login['cum_biometric_ratio'].fillna(0.0)
        df['HIST_LOGIN_COUNT'] = merged_login['cum_login_count'].fillna(0)
        
        # 6. Map Benford (UPGRADED: N>=50) & Markov Sequence Rarity
        print("Mapping Benford (N>=50) and Markov sequence rarity scores...")
        if self.benford_mapping is None:
            self.benford_mapping = calculate_benford_mapping_strict(conn)
        if self.seq_mapping is None:
            self.seq_mapping = calculate_second_order_markov_mapping(conn)
            
        df['BENFORD_DEV'] = df['CUSTOMER_NUMBER'].map(self.benford_mapping).fillna(0.0)
        df['ACTIVITY_SEQ_RARITY'] = df['CUSTOMER_NUMBER'].map(self.seq_mapping).fillna(0.0)

        # ---------------------------------------------------------------
        # NEW 2026 FEATURES
        # ---------------------------------------------------------------

        # 6.5. New Device Flag
        print("Computing NEW_DEVICE_FLAG...")
        df['device_seen_before'] = df.groupby(['CUSTOMER_NUMBER', 'Device_ID_Hash']).cumcount()
        df['NEW_DEVICE_FLAG'] = (df['device_seen_before'] == 0).astype(float)
        df = df.drop(columns=['device_seen_before'])

        # 7. IP Hopping Velocity
        print("Computing IP Hopping Velocity (3h sliding window)...")
        df['IP_HOPPING_VELOCITY'] = compute_ip_hopping_velocity(df)

        # 8. Graph features (PageRank + In-Degree Centrality)
        print("Building transaction graph and computing PageRank / In-Degree...")
        if self.graph_mapping is None:
            self.graph_mapping = compute_graph_features(conn)
        
        if self.graph_mapping:
            df['PAGERANK_SCORE'] = df['CUSTOMER_NUMBER'].map(
                lambda c: self.graph_mapping.get(c, {}).get('PAGERANK_SCORE', 0.0)
            )
            df['IN_DEGREE_CENTRALITY'] = df['CUSTOMER_NUMBER'].map(
                lambda c: self.graph_mapping.get(c, {}).get('IN_DEGREE_CENTRALITY', 0.0)
            )
        else:
            df['PAGERANK_SCORE'] = 0.0
            df['IN_DEGREE_CENTRALITY'] = 0.0

        # 9. Limit Utilization Velocity (MoM)
        print("Computing Limit Utilization Velocity from Data_Card...")
        if self.limit_util_velocity_mapping is None:
            self.limit_util_velocity_mapping = compute_limit_utilization_velocity(conn)
        
        df['LIMIT_UTILIZATION_VELOCITY'] = df['CUSTOMER_NUMBER'].map(self.limit_util_velocity_mapping).fillna(0.0)

        # 10. Structuring Overpayment Flag
        print("Computing Structuring Overpayment Flag...")
        df['STRUCTURING_OVERPAYMENT_FLAG'] = compute_structuring_overpayment(conn, df)

        # 11. Auth Downgrade Risk
        print("Computing Auth Downgrade Risk...")
        df['AUTH_DOWNGRADE_RISK'] = compute_auth_downgrade_risk(df, conn)

        conn.close()
        
        # Drop temporary columns
        df = df.drop(columns=['tx_id', 'LAST_SEC_EVENT_TS', 'ts_dt'], errors='ignore')
        if 'TRANSACTION_ID' in df.columns:
            df['TRANSACTION_ID'] = df['TRANSACTION_ID'].astype(str)
            df = df.set_index('TRANSACTION_ID', drop=False)

        print("Fraud2026DataLoader: All features computed successfully.")
        return df

    def stream_batches(self, batch_size: int = 1000) -> Generator[pd.DataFrame, None, None]:
        """Stream data in chunks by caching the processed dataset first."""
        if self.cached_df is None:
            self.cached_df = self.load_training_data()
            
        n_rows = len(self.cached_df)
        for i in range(0, n_rows, batch_size):
            yield self.cached_df.iloc[i : i + batch_size].copy()
