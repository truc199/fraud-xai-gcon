import os

file_path = "d:/uni/gcontest v3/gcontest/src/pipeline/fraud_2026_data_loader.py"

with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace compute_graph_features
old_graph_start = "def compute_graph_features(conn: sqlite3.Connection) -> Dict[int, Dict[str, float]]:"
old_graph_end = "# ---------------------------------------------------------------------------"

graph_start_idx = text.find(old_graph_start)
graph_end_idx = text.find(old_graph_end, graph_start_idx + len(old_graph_start))

new_graph_func = """def compute_graph_features(conn: sqlite3.Connection) -> Dict[int, Dict[str, float]]:
    \"\"\"Build a directed graph from CUSTOMER_NUMBER -> Beneficiary_CUSTOMER_NUMBER
    and compute PageRank and In-Degree Centrality for each node.

    Rationale: Money mule accounts and shell companies act as 'hubs' that receive
    funds from many sources. PageRank and In-Degree Centrality quantify this
    hub-ness. Standard technique in AML graph analytics (FinCEN, Europol SIENA).
    \"\"\"
    try:
        import networkx as nx
    except ImportError:
        print("WARNING: networkx not installed. GNN features will be zeroed.")
        return {}

    query = \"\"\"
    SELECT CUSTOMER_NUMBER, Beneficiary_CUSTOMER_NUMBER
    FROM Data_Transaction
    WHERE Beneficiary_CUSTOMER_NUMBER IS NOT NULL
      AND Beneficiary_CUSTOMER_NUMBER != 'UNKNOWN'
      AND Beneficiary_CUSTOMER_NUMBER != ''
    \"\"\"
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

"""

text = text[:graph_start_idx] + new_graph_func + text[graph_end_idx:]


# Replace compute_auth_downgrade_risk
old_auth_start = "def compute_auth_downgrade_risk(df: pd.DataFrame, conn: sqlite3.Connection) -> pd.Series:"
old_auth_end = "# ==========================================================================="

auth_start_idx = text.find(old_auth_start)
auth_end_idx = text.find(old_auth_end, auth_start_idx + len(old_auth_start))

new_auth_func = """def compute_auth_downgrade_risk(df: pd.DataFrame, conn: sqlite3.Connection) -> pd.Series:
    \"\"\"Detect authentication downgrade: a customer who historically uses biometric
    login (FaceID/Fingerprint) suddenly performs transactions from a new device
    using password-only login.

    Rationale: Account takeover (ATO) attackers register new devices and cannot
    use the victim's biometrics. Per Decision 2345/QD-NHNN (July 2024), large
    transactions require facial authentication. Downgrading is a red flag.
    \"\"\"
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

"""

text = text[:auth_start_idx] + new_auth_func + text[auth_end_idx:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Patched fraud_2026_data_loader.py successfully.")
