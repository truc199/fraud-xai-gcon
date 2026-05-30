import os
import pickle
import pandas as pd
from typing import Optional, List, Callable

def load_dataloader_cache(
    own_cache_filename: str,
    global_cache_filename: str,
    required_columns: List[str],
    calculate_fn: Callable[[], pd.DataFrame],
    limit: Optional[int] = None
) -> pd.DataFrame:
    """Generic hierarchical cache loader for DataLoaders.
    1. Try to load own_cache_filename.
    2. If miss, try to load global_cache_filename and verify required_columns.
    3. If miss/invalid, run calculate_fn(), save to own cache, and update/merge into global cache.
    """
    own_cache_filename = os.path.abspath(own_cache_filename)
    global_cache_filename = os.path.abspath(global_cache_filename)

    # 1. Try class-specific local cache
    if os.path.exists(own_cache_filename):
        print(f"[Cache Helper] Loading local class-specific cache from {own_cache_filename}...")
        try:
            df = pd.read_pickle(own_cache_filename)
            # Make sure it's valid
            if all(col in df.columns for col in required_columns):
                return df.head(limit) if limit is not None else df
            else:
                print(f"[Cache Helper] Local cache missing some required columns. Falling back...")
        except Exception as e:
            print(f"[Cache Helper] Warning: Failed to load local cache: {e}")

    # 2. Try global cache
    if os.path.exists(global_cache_filename):
        print(f"[Cache Helper] Checking global cache at {global_cache_filename}...")
        try:
            global_df = pd.read_pickle(global_cache_filename)
            # Check if all required columns are in global_df
            if all(col in global_df.columns for col in required_columns):
                print(f"[Cache Helper] Global cache hit! Saving full dataframe to local cache.")
                os.makedirs(os.path.dirname(own_cache_filename), exist_ok=True)
                global_df.to_pickle(own_cache_filename)
                return global_df.head(limit) if limit is not None else global_df
            else:
                print(f"[Cache Helper] Global cache exists but is missing required columns. Falling back to calculation...")
        except Exception as e:
            print(f"[Cache Helper] Warning: Failed to load global cache: {e}")

    # 3. Cache miss: compute from scratch
    print(f"[Cache Helper] Cache miss. Computing features using calculate_fn...")
    df = calculate_fn()

    # Save to local cache
    try:
        os.makedirs(os.path.dirname(own_cache_filename), exist_ok=True)
        df.to_pickle(own_cache_filename)
        print(f"[Cache Helper] Saved calculated features to local cache {own_cache_filename}.")
    except Exception as e:
        print(f"[Cache Helper] Warning: Failed to save local cache: {e}")

    # Update global cache (merging columns)
    try:
        os.makedirs(os.path.dirname(global_cache_filename), exist_ok=True)
        if os.path.exists(global_cache_filename):
            print(f"[Cache Helper] Updating global cache at {global_cache_filename}...")
            global_df = pd.read_pickle(global_cache_filename)
            # Merge columns
            cols_to_add = [c for c in df.columns if c not in global_df.columns]
            if cols_to_add:
                global_df = global_df.join(df[cols_to_add], how='left')
            # For columns that already exist, update them
            cols_to_update = [c for c in df.columns if c in global_df.columns]
            if cols_to_update:
                global_df.update(df[cols_to_update])
        else:
            print(f"[Cache Helper] Creating new global cache at {global_cache_filename}...")
            global_df = df.copy()
        global_df.to_pickle(global_cache_filename)
    except Exception as e:
        print(f"[Cache Helper] Warning: Failed to update global cache: {e}")

    return df.head(limit) if limit is not None else df


def transform_preprocessor_cache(
    own_cache_filename: str,
    global_cache_filename: str,
    df_hash: str,
    required_columns: List[str],
    transform_fn: Callable[[], pd.DataFrame]
) -> pd.DataFrame:
    """Generic hierarchical cache loader for Preprocessors transform step.
    1. Try to load from class-specific local cache dictionary.
    2. If miss, try to load from global cache dictionary and verify required columns.
    3. If miss/invalid, run transform_fn(), save to local, and update/merge into global.
    """
    own_cache_filename = os.path.abspath(own_cache_filename)
    global_cache_filename = os.path.abspath(global_cache_filename)

    # 1. Try local cache
    own_cache = {}
    if os.path.exists(own_cache_filename):
        try:
            with open(own_cache_filename, "rb") as f:
                own_cache = pickle.load(f)
            if df_hash in own_cache:
                v = own_cache[df_hash]
                if all(col in v.columns for col in required_columns):
                    return v[required_columns]
        except Exception as e:
            print(f"[Cache Helper] Warning: Failed to load local preprocessor cache: {e}")

    # 2. Try global cache
    global_cache = {}
    if os.path.exists(global_cache_filename):
        print(f"[Cache Helper] Checking global preprocessor cache at {global_cache_filename}...")
        try:
            with open(global_cache_filename, "rb") as f:
                global_cache = pickle.load(f)
            if df_hash in global_cache:
                v = global_cache[df_hash]
                if all(col in v.columns for col in required_columns):
                    print(f"[Cache Helper] Global preprocessor cache hit! Saving to local cache.")
                    own_df = v[required_columns]
                    own_cache[df_hash] = own_df
                    os.makedirs(os.path.dirname(own_cache_filename), exist_ok=True)
                    with open(own_cache_filename, "wb") as f:
                        pickle.dump(own_cache, f)
                    return own_df
        except Exception as e:
            print(f"[Cache Helper] Warning: Failed to load global preprocessor cache: {e}")

    # 3. Transform from scratch
    print(f"[Cache Helper] Transform cache miss. Processing data...")
    processed_df = transform_fn()

    # Save to local cache
    own_cache[df_hash] = processed_df
    try:
        os.makedirs(os.path.dirname(own_cache_filename), exist_ok=True)
        with open(own_cache_filename, "wb") as f:
            pickle.dump(own_cache, f)
    except Exception as e:
        print(f"[Cache Helper] Warning: Failed to save local preprocessor cache: {e}")

    # Update/merge global cache
    try:
        os.makedirs(os.path.dirname(global_cache_filename), exist_ok=True)
        if os.path.exists(global_cache_filename):
            with open(global_cache_filename, "rb") as f:
                global_cache = pickle.load(f)
        
        if df_hash in global_cache:
            existing_df = global_cache[df_hash]
            cols_to_add = [c for c in processed_df.columns if c not in existing_df.columns]
            if cols_to_add:
                existing_df = existing_df.join(processed_df[cols_to_add], how='left')
            cols_to_update = [c for c in processed_df.columns if c in existing_df.columns]
            if cols_to_update:
                existing_df.update(processed_df[cols_to_update])
            global_cache[df_hash] = existing_df
        else:
            global_cache[df_hash] = processed_df.copy()

        with open(global_cache_filename, "wb") as f:
            pickle.dump(global_cache, f)
        print(f"[Cache Helper] Updated global preprocessor cache for hash {df_hash}.")
    except Exception as e:
        print(f"[Cache Helper] Warning: Failed to update global preprocessor cache: {e}")

    return processed_df
