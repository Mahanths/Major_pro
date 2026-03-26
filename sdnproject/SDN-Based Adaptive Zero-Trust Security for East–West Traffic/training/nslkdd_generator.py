#!/usr/bin/env python3
"""
Generate NSL-KDD-like realistic dataset for model retraining
This mimics real network intrusion detection data
"""

import pandas as pd
import numpy as np
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Attack types that appear in NSL-KDD
ATTACK_TYPES = [
    'normal', 'back', 'buffer_overflow', 'ftp_write', 'guess_passwd', 'imap',
    'ipsweep', 'land', 'loadmodule', 'multihop', 'neptune', 'nmap', 'perl',
    'phf', 'port_scan', 'rootkit', 'satan', 'smurf', 'spy', 'teardrop', 'warezclient',
    'warezmaster', 'xlock', 'xsnoop', 'dos', 'probe', 'u2r', 'r2l'
]

def generate_normal_flow():
    """Generate realistic normal network flow"""
    duration = random.uniform(0.01, 300)  # Connection duration
    src_bytes = random.randint(100, 100000)  # Data sent from source
    dst_bytes = random.randint(100, 100000)  # Data received from destination
    
    return {
        'duration': duration,
        'protocol_type': random.choice(['tcp', 'tcp', 'tcp', 'udp', 'icmp']),
        'service': random.choice(['http', 'https', 'ftp', 'ssh', 'smtp', 'dns', 'imap']),
        'flag': random.choice(['SF', 'S0', 'RSTO', 'RSTR', 'SH', 'S1', 'S2', 'S3']),
        'src_bytes': src_bytes,
        'dst_bytes': dst_bytes,
        'land': 0,
        'wrong_fragment': random.randint(0, 3),
        'urgent': random.randint(0, 1),
        'hot': random.randint(0, 20),
        'num_failed_logins': 0,
        'logged_in': 1,
        'num_compromised': 0,
        'root_shell': 0,
        'su_attempted': 0,
        'num_root': 0,
        'num_file_creations': random.randint(0, 5),
        'num_shells': 0,
        'num_access_files': 0,
        'num_outbound_cmds': 0,
        'is_host_login': 0,
        'is_guest_login': 0,
        'count': random.randint(1, 100),
        'srv_count': random.randint(1, 100),
        'serror_rate': random.uniform(0, 0.1),
        'srv_serror_rate': random.uniform(0, 0.1),
        'rerror_rate': random.uniform(0, 0.1),
        'srv_rerror_rate': random.uniform(0, 0.1),
        'same_srv_rate': random.uniform(0.7, 1.0),
        'diff_srv_rate': random.uniform(0, 0.3),
        'srv_diff_host_rate': random.uniform(0, 0.2),
        'dst_host_count': random.randint(1, 255),
        'dst_host_srv_count': random.randint(1, 200),
        'dst_host_same_srv_rate': random.uniform(0.7, 1.0),
        'dst_host_diff_srv_rate': random.uniform(0, 0.3),
        'dst_host_same_src_port_rate': random.uniform(0.5, 1.0),
        'dst_host_srv_diff_host_rate': random.uniform(0, 0.2),
        'dst_host_serror_rate': random.uniform(0, 0.1),
        'dst_host_srv_serror_rate': random.uniform(0, 0.1),
        'dst_host_rerror_rate': random.uniform(0, 0.1),
        'dst_host_srv_rerror_rate': random.uniform(0, 0.1),
        'label': 'normal'
    }

def generate_attack_flow():
    """Generate realistic attack network flow"""
    attack_type = random.choice(ATTACK_TYPES[1:])  # Exclude 'normal'
    
    # Different attack characteristics
    if 'dos' in attack_type.lower() or 'smurf' in attack_type.lower():
        duration = random.uniform(1, 60)  # Usually short bursts
        src_bytes = random.randint(1000, 1000000)
        dst_bytes = random.randint(1000, 1000000)
        count = random.randint(100, 10000)  # Many packets
        serror_rate = random.uniform(0.3, 0.9)
    elif 'port' in attack_type.lower() or 'nmap' in attack_type.lower():
        duration = random.uniform(5, 300)
        src_bytes = random.randint(100, 10000)
        dst_bytes = random.randint(100, 10000)
        count = random.randint(50, 1000)
        serror_rate = random.uniform(0.5, 0.95)
    elif 'scan' in attack_type.lower():
        duration = random.uniform(10, 300)
        src_bytes = random.randint(100, 50000)
        dst_bytes = random.randint(100, 50000)
        count = random.randint(50, 500)
        serror_rate = random.uniform(0.6, 0.9)
    else:  # Other attacks
        duration = random.uniform(0.5, 300)
        src_bytes = random.randint(100, 50000)
        dst_bytes = random.randint(100, 50000)
        count = random.randint(10, 500)
        serror_rate = random.uniform(0.1, 0.7)
    
    return {
        'duration': duration,
        'protocol_type': random.choice(['tcp', 'udp', 'icmp']),
        'service': random.choice(['http', 'https', 'ftp', 'ssh', 'smtp', 'dns', 'imap', 'other']),
        'flag': random.choice(['S0', 'S1', 'SF', 'SH', 'RSTR', 'RSTO', 'REJ']),
        'src_bytes': src_bytes,
        'dst_bytes': dst_bytes,
        'land': random.randint(0, 1) if 'land' in attack_type else 0,
        'wrong_fragment': random.randint(0, 10) if 'frag' in attack_type else random.randint(0, 1),
        'urgent': random.randint(0, 20),
        'hot': random.randint(0, 100),
        'num_failed_logins': random.randint(0, 50) if 'passwd' in attack_type else 0,
        'logged_in': 0,
        'num_compromised': random.randint(0, 20),
        'root_shell': random.randint(0, 1),
        'su_attempted': random.randint(0, 1),
        'num_root': random.randint(0, 100),
        'num_file_creations': random.randint(0, 50),
        'num_shells': random.randint(0, 5),
        'num_access_files': random.randint(0, 20),
        'num_outbound_cmds': random.randint(0, 10),
        'is_host_login': 0,
        'is_guest_login': random.randint(0, 1),
        'count': count,
        'srv_count': random.randint(5, min(count, 500)),
        'serror_rate': serror_rate,
        'srv_serror_rate': serror_rate,
        'rerror_rate': random.uniform(0, 0.5),
        'srv_rerror_rate': random.uniform(0, 0.5),
        'same_srv_rate': random.uniform(0.3, 1.0),
        'diff_srv_rate': random.uniform(0.1, 1.0),
        'srv_diff_host_rate': random.uniform(0, 1.0),
        'dst_host_count': random.randint(50, 255),
        'dst_host_srv_count': random.randint(20, 200),
        'dst_host_same_srv_rate': random.uniform(0.2, 0.8),
        'dst_host_diff_srv_rate': random.uniform(0.2, 1.0),
        'dst_host_same_src_port_rate': random.uniform(0, 1.0),
        'dst_host_srv_diff_host_rate': random.uniform(0.2, 1.0),
        'dst_host_serror_rate': random.uniform(0.1, 0.8),
        'dst_host_srv_serror_rate': random.uniform(0.1, 0.8),
        'dst_host_rerror_rate': random.uniform(0, 0.5),
        'dst_host_srv_rerror_rate': random.uniform(0, 0.5),
        'label': attack_type
    }

def generate_nslkdd_dataset(num_normal=50000, num_attacks=20000, output_file='nslkdd_generated.csv'):
    """Generate NSL-KDD-like dataset"""
    logger.info(f"Generating NSL-KDD-like dataset: {num_normal} normal + {num_attacks} attacks")
    
    data = []
    
    # Generate normal flows
    for i in range(num_normal):
        if (i + 1) % 10000 == 0:
            logger.info(f"Generated {i + 1} normal flows")
        data.append(generate_normal_flow())
    
    # Generate attack flows
    for i in range(num_attacks):
        if (i + 1) % 5000 == 0:
            logger.info(f"Generated {i + 1} attack flows")
        data.append(generate_attack_flow())
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    logger.info(f"✓ Saved {len(df)} flows to {output_file}")
    logger.info(f"File size: {df.memory_usage().sum() / 1024 / 1024:.2f} MB")
    logger.info(f"\nLabel distribution:")
    logger.info(df['label'].value_counts())
    
    return output_file

if __name__ == '__main__':
    import sys
    
    output = sys.argv[1] if len(sys.argv) > 1 else 'nslkdd_generated.csv'
    num_normal = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
    num_attacks = int(sys.argv[3]) if len(sys.argv) > 3 else 20000
    
    generate_nslkdd_dataset(num_normal, num_attacks, output)
