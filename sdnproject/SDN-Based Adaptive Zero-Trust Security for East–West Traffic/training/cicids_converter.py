#!/usr/bin/env python3
"""
CICIDS Dataset Converter to 8-Feature Format
Converts CICIDS2018/2019/2023 datasets to 8 optimized ML features
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

class CICIDSConverter:
    """Convert CICIDS datasets to 8-feature format"""
    
    # CICIDS feature mappings
    FEATURE_MAPPING = {
        'flow_duration': 'Flow Duration',  # or 'Duration'
        'fwd_packet_rate': 'Fwd Packets/s',
        'bwd_packet_rate': 'Bwd Packets/s',
        'byte_entropy': 'Fwd Header Len',  # Proxy for entropy
        'unique_dst_ports': 'Dst Port',
        'tcp_flags_count': 'Init_Win_bytes',  # Proxy for TCP flags
        'inter_arrival_time_min': 'Active Min',
        'inter_arrival_time_max': 'Active Max',
        'label': 'Label'  # or 'class' or 'attack'
    }
    
    def __init__(self, input_file, output_file='cicids_8features.csv'):
        """Initialize converter"""
        self.input_file = input_file
        self.output_file = output_file
        print(f"📂 Loading: {input_file}")
        
    def load_data(self):
        """Load CSV file"""
        try:
            self.df = pd.read_csv(self.input_file, low_memory=False)
            print(f"✓ Loaded {len(self.df)} rows, {len(self.df.columns)} features")
            print(f"Columns: {list(self.df.columns)[:5]}... (showing first 5)")
            return self
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return None
    
    def normalize_features(self, df):
        """Normalize all numeric features to [0, 1]"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val - min_val > 0:
                df[col] = (df[col] - min_val) / (max_val - min_val)
            else:
                df[col] = 0
        return df
    
    def extract_features(self):
        """Extract 8 features from CICIDS data"""
        print("\n📊 Extracting 8 features...")
        
        df = self.df.copy()
        
        # 1. Flow Duration (ms → seconds)
        if 'Flow Duration' in df.columns:
            df['flow_duration'] = pd.to_numeric(df['Flow Duration'], errors='coerce') / 1000
        elif 'Duration' in df.columns:
            df['flow_duration'] = pd.to_numeric(df['Duration'], errors='coerce')
        else:
            df['flow_duration'] = 30.0  # Default
        
        # 2. Forward Packet Rate
        if 'Fwd Packets/s' in df.columns:
            df['fwd_packet_rate'] = pd.to_numeric(df['Fwd Packets/s'], errors='coerce')
        elif 'Total Fwd Packets' in df.columns and 'Flow Duration' in df.columns:
            duration_s = pd.to_numeric(df['Flow Duration'], errors='coerce') / 1000
            df['fwd_packet_rate'] = pd.to_numeric(df['Total Fwd Packets'], errors='coerce') / (duration_s + 0.001)
        else:
            df['fwd_packet_rate'] = 10.0
        
        # 3. Backward Packet Rate
        if 'Bwd Packets/s' in df.columns:
            df['bwd_packet_rate'] = pd.to_numeric(df['Bwd Packets/s'], errors='coerce')
        elif 'Total Bwd Packets' in df.columns and 'Flow Duration' in df.columns:
            duration_s = pd.to_numeric(df['Flow Duration'], errors='coerce') / 1000
            df['bwd_packet_rate'] = pd.to_numeric(df['Total Bwd Packets'], errors='coerce') / (duration_s + 0.001)
        else:
            df['bwd_packet_rate'] = 8.0
        
        # 4. Byte Entropy (use Fwd Header Length as proxy)
        if 'Fwd Header Length' in df.columns:
            df['byte_entropy'] = pd.to_numeric(df['Fwd Header Length'], errors='coerce')
        elif 'Fwd Packets' in df.columns:
            df['byte_entropy'] = pd.to_numeric(df['Fwd Packets'], errors='coerce')
        else:
            df['byte_entropy'] = 5.0
        
        # 5. Unique Destination Ports
        if 'Dst Port' in df.columns:
            df['unique_dst_ports'] = pd.to_numeric(df['Dst Port'], errors='coerce')
        else:
            df['unique_dst_ports'] = 443  # Default HTTPS
        
        # 6. TCP Flags Count (use Init_Win_bytes as proxy)
        if 'Init_Win_bytes' in df.columns:
            df['tcp_flags_count'] = pd.to_numeric(df['Init_Win_bytes'], errors='coerce')
        else:
            df['tcp_flags_count'] = 65000
        
        # 7. Inter-arrival Time Min
        if 'Active Min' in df.columns:
            df['inter_arrival_time_min'] = pd.to_numeric(df['Active Min'], errors='coerce')
        else:
            df['inter_arrival_time_min'] = 0.001
        
        # 8. Inter-arrival Time Max
        if 'Active Max' in df.columns:
            df['inter_arrival_time_max'] = pd.to_numeric(df['Active Max'], errors='coerce')
        elif 'Flow Duration' in df.columns:
            df['inter_arrival_time_max'] = pd.to_numeric(df['Flow Duration'], errors='coerce') / 1000
        else:
            df['inter_arrival_time_max'] = 30.0
        
        # Extract label
        label_col = None
        for col in ['Label', 'label', 'class', 'Class', 'attack', 'Attack']:
            if col in df.columns:
                label_col = col
                break
        
        if label_col:
            # Convert labels: BENIGN=0, attack=1
            df['label'] = df[label_col].apply(lambda x: 0 if 'BENIGN' in str(x).upper() or x == 0 else 1)
        else:
            print("⚠️ Warning: Could not find label column. Using all as benign (0)")
            df['label'] = 0
        
        # Select only 8 features
        features = ['flow_duration', 'fwd_packet_rate', 'bwd_packet_rate', 'byte_entropy',
                   'unique_dst_ports', 'tcp_flags_count', 'inter_arrival_time_min', 
                   'inter_arrival_time_max', 'label']
        
        df_8feat = df[features].copy()
        
        # Handle missing values
        df_8feat = df_8feat.fillna(0)
        
        # Remove outliers (flow duration > 1 hour)
        df_8feat = df_8feat[df_8feat['flow_duration'] < 3600]
        
        print(f"✓ Extracted {len(df_8feat)} samples with 8 features")
        
        # Normalize
        print("📊 Normalizing features to [0, 1]...")
        df_8feat = self.normalize_features(df_8feat)
        
        self.df_processed = df_8feat
        return self
    
    def save(self):
        """Save processed data to CSV"""
        print(f"\n💾 Saving to {self.output_file}...")
        self.df_processed.to_csv(self.output_file, index=False)
        file_size = os.path.getsize(self.output_file) / (1024*1024)
        print(f"✓ Saved! Size: {file_size:.1f} MB")
        print(f"\n📊 Statistics:")
        print(f"  - Total flows: {len(self.df_processed)}")
        print(f"  - Normal: {len(self.df_processed[self.df_processed['label'] == 0])}")
        print(f"  - Attack: {len(self.df_processed[self.df_processed['label'] == 1])}")
        print(f"  - Features: {', '.join(self.df_processed.columns[:-1])}")
        return self

def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python3 cicids_converter.py <input.csv> [output.csv]")
        print("\nExample:")
        print("  python3 cicids_converter.py data/cicids2018.csv data/cicids2018_8features.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.csv', '_8features.csv')
    
    converter = CICIDSConverter(input_file, output_file)
    converter.load_data()
    if converter.df is not None:
        converter.extract_features()
        converter.save()
        print("\n✅ Conversion complete!")
    else:
        print("\n❌ Conversion failed!")

if __name__ == '__main__':
    main()
