#!/usr/bin/env python3
"""
Convert NSL-KDD dataset to 8-feature format compatible with training pipeline
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# NSL-KDD column names
NSLKDD_COLUMNS = [
    'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
    'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
    'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
    'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
    'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
    'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
    'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
    'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
    'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
    'dst_host_rerror_rate', 'dst_host_srv_rerror_rate', 'label'
]

def load_nslkdd(file_path):
    """Load NSL-KDD CSV file"""
    logger.info(f"Loading NSL-KDD from {file_path}...")
    df = pd.read_csv(file_path, header=None, names=NSLKDD_COLUMNS)
    # Skip header row if it exists (check if first row contains 'duration')
    if df['duration'].iloc[0] == 'duration':
        df = df.iloc[1:].reset_index(drop=True)
        logger.info(f"Skipped header row")
    
    # Convert numeric columns to float
    numeric_cols = ['duration', 'src_bytes', 'dst_bytes', 'land', 'wrong_fragment', 
                   'urgent', 'hot', 'num_failed_logins', 'logged_in', 'num_compromised',
                   'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
                   'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
                   'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
                   'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
                   'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
                   'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
                   'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
                   'dst_host_rerror_rate', 'dst_host_srv_rerror_rate']
    
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    logger.info(f"Loaded {len(df)} records")
    return df

def convert_to_8_features(df):
    """
    Convert NSL-KDD 41-feature format to 8-feature format
    """
    logger.info("Converting NSL-KDD to 8-feature format...")
    
    # Create 8-feature dataframe
    features_df = pd.DataFrame()
    
    # Feature 1: flow_duration (duration column, convert to seconds if needed)
    features_df['flow_duration'] = df['duration'].astype(float) / 60.0  # Convert to seconds
    
    # Feature 2: fwd_packet_rate (src_bytes / duration for forward rate)
    features_df['fwd_packet_rate'] = np.where(
        df['duration'] > 0,
        df['src_bytes'].astype(float) / (df['duration'].astype(float) + 0.001),
        0
    )
    
    # Feature 3: bwd_packet_rate (dst_bytes / duration for backward rate)
    features_df['bwd_packet_rate'] = np.where(
        df['duration'] > 0,
        df['dst_bytes'].astype(float) / (df['duration'].astype(float) + 0.001),
        0
    )
    
    # Feature 4: byte_entropy (approximated from count and srv_count - flow diversity)
    total_bytes = df['src_bytes'].astype(float) + df['dst_bytes'].astype(float)
    features_df['byte_entropy'] = np.where(
        total_bytes > 0,
        df['count'].astype(float) / (total_bytes.astype(float) + 1),
        0
    )
    
    # Feature 5: unique_dst_ports (count of connections - approximation)
    features_df['unique_dst_ports'] = df['count'].astype(float)
    
    # Feature 6: tcp_flags_count (flag diversity - convert protocol to numeric)
    protocol_map = {'tcp': 1, 'udp': 0, 'icmp': 0}
    features_df['tcp_flags_count'] = df['protocol_type'].map(protocol_map).fillna(0)
    
    # Feature 7 & 8: inter_arrival_time_min and max (use diff_srv_rate and same_srv_rate)
    features_df['inter_arrival_time_min'] = df['diff_srv_rate'].astype(float) * 100
    features_df['inter_arrival_time_max'] = df['same_srv_rate'].astype(float) * 100
    
    # Labels: 0 = normal, 1 = attack
    # In NSL-KDD, 'normal' is benign, everything else is attack
    features_df['label'] = (df['label'].str.strip() != 'normal').astype(int)
    
    logger.info(f"Converted {len(features_df)} records")
    logger.info(f"Label distribution: Normal={len(features_df[features_df['label']==0])}, "
                f"Attacks={len(features_df[features_df['label']==1])}")
    
    return features_df

def normalize_features(df):
    """Normalize features to reasonable ranges"""
    logger.info("Normalizing features...")
    
    scaler = MinMaxScaler(feature_range=(0, 1))
    features = df.iloc[:, :-1]  # All except label
    
    normalized = scaler.fit_transform(features)
    
    df_normalized = pd.DataFrame(
        normalized,
        columns=features.columns
    )
    df_normalized['label'] = df['label'].values
    
    logger.info("Features normalized to [0, 1] range")
    return df_normalized

def validate_data(df):
    """Validate dataset before saving"""
    logger.info("Validating dataset...")
    
    # Check columns
    expected_cols = ['flow_duration', 'fwd_packet_rate', 'bwd_packet_rate', 'byte_entropy',
                    'unique_dst_ports', 'tcp_flags_count', 'inter_arrival_time_min',
                    'inter_arrival_time_max', 'label']
    
    if list(df.columns) != expected_cols:
        logger.warning(f"Column order mismatch: {list(df.columns)}")
    
    # Check for NaN values
    nan_count = df.isna().sum().sum()
    if nan_count > 0:
        logger.warning(f"Found {nan_count} NaN values. Filling with 0...")
        df = df.fillna(0)
    
    # Check label values
    unique_labels = df['label'].unique()
    if not set(unique_labels).issubset({0, 1}):
        logger.warning(f"Unexpected label values: {unique_labels}")
    
    logger.info(f"✓ Dataset validation complete: {len(df)} records")
    return df

def process_nslkdd(input_file, output_file):
    """Main processing pipeline"""
    try:
        df = load_nslkdd(input_file)
        df = convert_to_8_features(df)
        df = normalize_features(df)
        df = validate_data(df)
        
        df.to_csv(output_file, index=False)
        logger.info(f"✓ Saved to {output_file}")
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"\nFirst few rows:")
        logger.info(df.head())
        
    except Exception as e:
        logger.error(f"Error processing NSL-KDD: {e}")
        raise

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python nslkdd_converter.py <input_file> <output_file>")
        print("Example: python nslkdd_converter.py NSL_KDD_Train+.csv nslkdd_training.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    process_nslkdd(input_file, output_file)
