import os
import sqlite3
import pandas as pd
import math
from collections import defaultdict
from typing import Optional, Generator, Dict
from src.pipeline.protocols import DataLoader

def calculate_benford_mapping(conn: sqlite3.Connection) -> Dict[int, float]:
    """Calculate KL-Divergence of transaction amount leading digits vs Benford's Law per customer."""
    cursor = conn.cursor()
    cursor.execute("SELECT CUSTOMER_NUMBER, TRANS_AMOUNT FROM Data_Transaction")
    
    cust_amounts = defaultdict(list)
    for cust, amt in cursor.fetchall():
        if amt and amt > 0:
            cust_amounts[cust].append(amt)
            
    benford_dist = [math.log10(1 + 1.0 / d) for d in range(1, 10)]
    mapping = {}
    
    for cust, amts in cust_amounts.items():
        if len(amts) < 5:
            mapping[cust] = 0.0
            continue
            
        digits = []
        for a in amts:
            s = str(a).lstrip('0.').replace('.', '')
            if s:
                d = int(s[0])
                if 1 <= d <= 9:
                    digits.append(d)
                    
        if len(digits) < 5:
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

def calculate_activity_seq_mapping(conn: sqlite3.Connection) -> Dict[int, float]:
    """Calculate sequential action rarity (Markov Chain Log-Likelihood) per customer based on their action paths."""
    cursor = conn.cursor()
    
    # Load activities for transacting customers (sample to optimize speed & RAM)
    cursor.execute("""
        SELECT CUSTOMER_NUMBER, ACTIVITY_NAME 
        FROM Data_Activity 
        WHERE CUSTOMER_NUMBER IN (SELECT DISTINCT CUSTOMER_NUMBER FROM Data_Transaction LIMIT 20000)
        ORDER BY CUSTOMER_NUMBER, ACTIVITY_DATE, ACTIVITY_HOUR
    """)
    
    cust_sequences = defaultdict(list)
    for cust, act in cursor.fetchall():
        if act:
            cust_sequences[cust].append(act.strip())
            
    # Calculate transition counts
    transition_counts = defaultdict(lambda: defaultdict(int))
    state_counts = defaultdict(int)
    
    for seq in cust_sequences.values():
        for i in range(len(seq) - 1):
            s1, s2 = seq[i], seq[i+1]
            transition_counts[s1][s2] += 1
            state_counts[s1] += 1
            
    # Normalize to probabilities
    transition_probs = defaultdict(dict)
    for s1, targets in transition_counts.items():
        total = state_counts[s1]
        for s2, count in targets.items():
            transition_probs[s1][s2] = count / total
            
    # Compute average transition log-probability per customer
    mapping = {}
    eps = 1e-5
    for cust, seq in cust_sequences.items():
        if len(seq) < 2:
            mapping[cust] = 0.0
            continue
            
        log_prob_sum = 0.0
        transitions_evaluated = 0
        for i in range(len(seq) - 1):
            s1, s2 = seq[i], seq[i+1]
            prob = transition_probs[s1].get(s2, 0.0)
            log_prob_sum += math.log(prob + eps)
            transitions_evaluated += 1
            
        mapping[cust] = log_prob_sum / transitions_evaluated if transitions_evaluated > 0 else 0.0
        
    return mapping

class SQLiteDataLoader(DataLoader):
    """DataLoader that extracts transactional data aggregated with rolling windows, Benford, and Markov sequence metrics."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.benford_mapping: Optional[Dict[int, float]] = None
        self.seq_mapping: Optional[Dict[int, float]] = None

    def _get_sql_query(self, limit: Optional[int] = None) -> str:
        query = """
            WITH trans_time_added AS (
                SELECT 
                    t.CUSTOMER_NUMBER,
                    t.TRANS_LV1,
                    t.TRANS_LV2,
                    t.TRANS_DATE,
                    t.DAY_OF_WEEK,
                    t.TRANS_HOUR,
                    t.TRANS_NO,
                    t.TRANS_AMOUNT,
                    (julianday(t.TRANS_DATE) + (t.TRANS_HOUR / 24.0)) as ts
                FROM Data_Transaction t
            ),
            rolling_metrics AS (
                SELECT 
                    CUSTOMER_NUMBER,
                    TRANS_LV1,
                    TRANS_LV2,
                    TRANS_DATE,
                    DAY_OF_WEEK,
                    TRANS_HOUR,
                    TRANS_NO,
                    TRANS_AMOUNT,
                    ts,
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
                        RANGE BETWEEN 7.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_7D,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 7.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_7D
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
                r.CUSTOMER_NUMBER,
                r.TRANS_LV1,
                r.TRANS_LV2,
                r.TRANS_DATE,
                r.DAY_OF_WEEK,
                r.TRANS_HOUR,
                r.TRANS_NO,
                r.TRANS_AMOUNT,
                c.CLIENT_SEX,
                c.CLIENT_CREATE_DATE,
                c.DATE_OF_BIRTH,
                c.STAFF,
                c.IB_REGISTER_DATE,
                c.EB_REGISTER_CHANNEL,
                c.SMS,
                c.VERIFY_METHOD,
                r.SUM_AMOUNT_24H,
                r.COUNT_24H,
                r.SUM_AMOUNT_7D,
                r.COUNT_7D,
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
        """Load fully aggregated dataset with Benford and Markov sequence metrics."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
            
        conn = sqlite3.connect(self.db_path)
        query = self._get_sql_query(limit=limit)
        df = pd.read_sql_query(query, conn)
        
        if self.benford_mapping is None:
            self.benford_mapping = calculate_benford_mapping(conn)
            
        if self.seq_mapping is None:
            self.seq_mapping = calculate_activity_seq_mapping(conn)
            
        df['BENFORD_DEV'] = df['CUSTOMER_NUMBER'].map(self.benford_mapping).fillna(0.0)
        df['ACTIVITY_SEQ_RARITY'] = df['CUSTOMER_NUMBER'].map(self.seq_mapping).fillna(0.0)
        
        conn.close()
        return df

    def stream_batches(self, batch_size: int = 1000) -> Generator[pd.DataFrame, None, None]:
        """Stream chunks of fully aggregated data with Benford and Markov sequence metrics."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
            
        conn = sqlite3.connect(self.db_path)
        
        if self.benford_mapping is None:
            self.benford_mapping = calculate_benford_mapping(conn)
            
        if self.seq_mapping is None:
            self.seq_mapping = calculate_activity_seq_mapping(conn)
            
        query = self._get_sql_query()
        for chunk in pd.read_sql_query(query, conn, chunksize=batch_size):
            chunk['BENFORD_DEV'] = chunk['CUSTOMER_NUMBER'].map(self.benford_mapping).fillna(0.0)
            chunk['ACTIVITY_SEQ_RARITY'] = chunk['CUSTOMER_NUMBER'].map(self.seq_mapping).fillna(0.0)
            yield chunk
            
        conn.close()
