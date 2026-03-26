# FEATURE EXTRACTION FROM REAL DATA
**Converting Your Network PCAPs to ML-Ready Feature Vectors**

---

## 🎯 GOAL
Convert captured .pcap files into the 8-feature CSV format that trains your Isolation Forest + XGBoost models.

---

## THE 8 FEATURES EXPLAINED

Your models expect exactly these 8 features (no more, no less):

| Feature | Source | Calculation | Range | Why It Matters |
|---------|--------|-------------|-------|----------------|
| `flow_duration` | PCAP | Last pkt time - First pkt time | 0.001-300s | Anomaly: Burst attacks are short|
| `fwd_packet_rate` | PCAP | Forward packets / duration | 1-1000 pps | Anomaly: Floods are >500pps |
| `bwd_packet_rate` | PCAP | Backward packets / duration | 1-1000 pps | Anomaly: Response floods unusual |
| `byte_entropy` | Payload | Shannon entropy of bytes | 0.0-1.0 | Anomaly: Encrypted/compressed |
| `unique_dst_ports` | PCAP | Count of unique dest ports | 1-65535 | Anomaly: Scanners hit many |
| `tcp_flags_count` | TCP header | Count of unusual flags | 0-100 | Anomaly: Flags indicate probes |
| `inter_arrival_time_min` | PCAP | Minimum gap between pkts | 0.0001-1000ms | Anomaly: Bursty = small gaps |
| `inter_arrival_time_max` | PCAP | Maximum gap between pkts | 0.0001-1000ms | Anomaly: Very spaced = slow exfil |

---

## STEP 1: VERIFY YOUR pcap_to_csv.py (Already Provided)

**Location:** `training/pcap_to_csv.py`

**Check it has these functions:**

```python
def extract_flow_duration(flow):
    """Last packet time - First packet time"""
    return flow['last_timestamp'] - flow['first_timestamp']

def extract_packet_rates(flow):
    """Count packets per second in each direction"""
    fwd_pps = flow['fwd_packet_count'] / flow['duration'] if flow['duration'] > 0 else 0
    bwd_pps = flow['bwd_packet_count'] / flow['duration'] if flow['duration'] > 0 else 0
    return min(fwd_pps, 1000), min(bwd_pps, 1000)  # Cap at 1000pps

def extract_byte_entropy(payload):
    """Shannon entropy measure of randomness"""
    from collections import Counter
    import math
    
    counts = Counter(payload)
    entropy = 0
    for count in counts.values():
        p = count / len(payload)
        entropy -= p * math.log2(p)
    return entropy / 8.0  # Normalize to [0,1]

def extract_inter_arrival_times(flow):
    """Min/max time between consecutive packets"""
    times = sorted(flow['packet_timestamps'])
    gaps = [times[i+1] - times[i] for i in range(len(times)-1)]
    return min(gaps) if gaps else 0, max(gaps) if gaps else 0

def extract_tcp_flags(flow):
    """Count of unusual flag combinations"""
    # Normal: ACK, SYN+ACK, FIN+ACK
    # Anomaly: SYN+FIN, RST+ACK, many FINs, etc.
    return unusual_flag_count
```

---

## STEP 2: EXTRACT FEATURES FROM REAL PCAPS

### Quick Method: One PCAP at a Time

```bash
# Convert a single PCAP to CSV
cd /home/mahanth-s/sdnproject/SDN-Based\ Adaptive\ Zero-Trust\ Security\ for\ East–West\ Traffic

python training/pcap_to_csv.py \
  -i /data/pcaps/monday_business_hours.pcap \
  -o /data/training/monday_business_features.csv \
  -l 0  # 0 = normal traffic

echo "✅ Extracted features: /data/training/monday_business_features.csv"
```

### Batch Method: Extract All at Once

**Create extraction script:**

```bash
cat > /tmp/batch_extract.sh << 'EOF'
#!/bin/bash

# Input directories
PCAP_DIR="/data/pcaps"
CSV_OUTPUT_DIR="/data/training"

echo "🔄 Starting batch PCAP extraction..."

# Extract normall traffic (label=0)
for pcap in $PCAP_DIR/weekday_business_hours/*.pcap; do
    filename=$(basename "$pcap" .pcap)
    echo "Processing: $filename"
    
    python training/pcap_to_csv.py \
      -i "$pcap" \
      -o "$CSV_OUTPUT_DIR/${filename}_features.csv" \
      -l 0 \
      --verbose
    
    echo "✅ Extracted: ${filename}_features.csv"
done

# Extract attack traffic (label=1)
for pcap in $PCAP_DIR/attacks/*.pcap; do
    filename=$(basename "$pcap" .pcap)
    echo "Processing: $filename (ATTACK)"
    
    python training/pcap_to_csv.py \
      -i "$pcap" \
      -o "$CSV_OUTPUT_DIR/${filename}_attack_features.csv" \
      -l 1 \
      --verbose
    
    echo "✅ Extracted: ${filename}_attack_features.csv"
done

echo "🎉 All extractions complete!"
ls -lh $CSV_OUTPUT_DIR/*.csv | wc -l
echo "files generated"
EOF

chmod +x /tmp/batch_extract.sh
./tmp/batch_extract.sh
```

---

## STEP 3: VERIFY FEATURE QUALITY

**Check that features are normalized correctly:**

```python
import pandas as pd

# Load one extracted CSV
df = pd.read_csv('/data/training/monday_business_features.csv')

print("=" * 60)
print("FEATURE EXTRACTION QUALITY CHECK")
print("=" * 60)

# Check 1: All features present
required_features = [
    'flow_duration', 'fwd_packet_rate', 'bwd_packet_rate',
    'byte_entropy', 'unique_dst_ports', 'tcp_flags_count',
    'inter_arrival_time_min', 'inter_arrival_time_max', 'label'
]

missing = [f for f in required_features if f not in df.columns]
if missing:
    print(f"❌ MISSING FEATURES: {missing}")
else:
    print(f"✅ All 9 columns present")

# Check 2: No NaN values
nans = df.isna().sum()
if nans.sum() > 0:
    print(f"⚠️  WARNING - NaN values detected:")
    print(nans[nans > 0])
else:
    print(f"✅ No NaN values (all flows valid)")

# Check 3: Values in expected ranges
print("\n📊 FEATURE DISTRIBUTIONS:")
print(f"flow_duration: min={df['flow_duration'].min():.4f}, max={df['flow_duration'].max():.4f}")
print(f"  → Should be 0.001-300s (normalized)")
print(f"fwd_packet_rate: min={df['fwd_packet_rate'].min():.1f}, max={df['fwd_packet_rate'].max():.1f}")
print(f"  → Should be 1-1000 pps (normalized)")
print(f"byte_entropy: min={df['byte_entropy'].min():.4f}, max={df['byte_entropy'].max():.4f}")
print(f"  → Should be 0.0-1.0 (normalized)")
print(f"unique_dst_ports: min={df['unique_dst_ports'].min()}, max={df['unique_dst_ports'].max()}")
print(f"  → Should be 1-65535")

# Check 4: Label distribution
labels = df['label'].value_counts()
print(f"\n📈 LABEL DISTRIBUTION:")
print(f"Normal (0): {labels.get(0, 0):,} flows")
print(f"Attack (1): {labels.get(1, 0):,} flows")
print(f"Ratio: {(labels.get(1, 0) / len(df) * 100):.1f}% attacks")

# Check 5: Outlier detection
print(f"\n⚠️  OUTLIER CHECK:")
for col in ['flow_duration', 'fwd_packet_rate', 'unique_dst_ports']:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    outliers = len(df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)])
    print(f"{col}: {outliers} outliers ({outliers/len(df)*100:.2f}%)")

print("=" * 60)
```

**Expected Output:**
```
✅ All 9 columns present
✅ No NaN values (all flows valid)

📊 FEATURE DISTRIBUTIONS:
flow_duration: min=0.0010, max=298.4567
  → Should be 0.001-300s (normalized)
fwd_packet_rate: min=1.2, max=987.3
  → Should be 1-1000 pps (normalized)
byte_entropy: min=0.0001, max=0.9876
  → Should be 0.0-1.0 (normalized)
unique_dst_ports: min=1, max=2043
  → Should be 1-65535

📈 LABEL DISTRIBUTION:
Normal (0): 440,021 flows
Attack (1): 89,979 flows
Ratio: 17.0% attacks

⚠️  OUTLIER CHECK:
flow_duration: 342 outliers (0.07%)
fwd_packet_rate: 18 outliers (0.00%)
unique_dst_ports: 5,431 outliers (1.13%)  ← Port scanners
```

---

## STEP 4: MERGE ALL EXTRACTED CSVs

**Combine baseline + attack features into single training set:**

```python
import pandas as pd
import glob
import os

# Find all extracted CSVs
csv_files = glob.glob('/data/training/*_features.csv')

print(f"📂 Found {len(csv_files)} CSV files to merge...")

# Read all CSVs
dfs = []
for csv_file in csv_files:
    print(f"  Loading: {os.path.basename(csv_file)}")
    df = pd.read_csv(csv_file)
    dfs.append(df)

# Combine
combined_df = pd.concat(dfs, ignore_index=True)
print(f"\n✅ Combined into {len(combined_df):,} total flows")

# Verify
print(f"Columns: {list(combined_df.columns)}")
print(f"Normal: {len(combined_df[combined_df['label']==0]):,}")
print(f"Attack: {len(combined_df[combined_df['label']==1]):,}")

# Shuffle (important!)
combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)

# Save
output_file = '/data/training_data/real_data_final.csv'
os.makedirs(os.path.dirname(output_file), exist_ok=True)
combined_df.to_csv(output_file, index=False)

print(f"\n📊 Saved to: {output_file}")
print(f"File size: {os.path.getsize(output_file) / 1024**2:.1f} MB")
```

---

## STEP 5: HANDLE EDGE CASES

### Case 1: Some PCAPs Don't Extract Properly

**Problem:** pcap_to_csv.py fails on certain files

**Solution:**
```python
# Add error handling to extraction
import subprocess
import sys

for pcap_file in pcap_files:
    try:
        result = subprocess.run(
            ['python', 'training/pcap_to_csv.py', 
             '-i', pcap_file, '-o', output_csv],
            timeout=60,  # Max 60 seconds per PCAP
            capture_output=True
        )
        if result.returncode != 0:
            print(f"⚠️  Failed: {pcap_file}")
            print(result.stderr.decode())
            continue  # Skip this file
    except subprocess.TimeoutExpired:
        print(f"⏱️  Timeout: {pcap_file}")
        continue
```

### Case 2: PCAP Has Fragmented Packets

**Problem:** Some flows don't aggregate properly

**Solution:**
```bash
# Pre-process PCAP with tcpdump to remove fragments
tcpdump -r broken.pcap -w fixed.pcap '! ip[6:2] & 0x1fff'
# Now extract from fixed.pcap
```

### Case 3: Features Have All Zeros

**Problem:** Extraction creates rows with no data

**Solution:**
```python
# Remove zero-flow rows
df = df[(df['flow_duration'] > 0) & (df['fwd_packet_rate'] > 0)]
print(f"Removed {len(df) - len(df) // 20} bad rows")  # Example
```

---

## STEP 6: NORMALIZE FOR ML TRAINING

**Before training, normalize all features to [0,1]:**

```python
from sklearn.preprocessing import MinMaxScaler

# Load merged dataset
df = pd.read_csv('/data/training_data/real_data_final.csv')

# Keep label
labels = df['label'].copy()
features = df.drop('label', axis=1)

# Normalize features
scaler = MinMaxScaler()
features_normalized = scaler.fit_transform(features)

# Combine
df_normalized = pd.DataFrame(features_normalized, columns=features.columns)
df_normalized['label'] = labels.values

# Save normalized version
df_normalized.to_csv('/data/training_data/real_data_normalized.csv', index=False)

print(f"✅ Normalized and saved: real_data_normalized.csv")
print(f"   All features now in [0, 1] range")

# Save scaler for deployment
import joblib
joblib.dump(scaler, '/brain/models/feature_scaler.pkl')
print(f"✅ Scaler saved for API usage: feature_scaler.pkl")
```

---

## STEP 7: SPLIT FOR TRAINING vs VALIDATION

**Never train and test on same data:**

```python
from sklearn.model_selection import train_test_split

df = pd.read_csv('/data/training_data/real_data_normalized.csv')

# Split: 80% train, 20% test
X = df.drop('label', axis=1).values
y = df['label'].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.2, 
    random_state=42,
    stratify=y  # Keep label ratio same in both sets
)

# Save
import numpy as np
np.save('/data/training_data/X_train.npy', X_train)
np.save('/data/training_data/X_test.npy', X_test)
np.save('/data/training_data/y_train.npy', y_train)
np.save('/data/training_data/y_test.npy', y_test)

print(f"✅ Training set: {len(X_train):,} flows ({y_train.sum()} attacks)")
print(f"✅ Test set: {len(X_test):,} flows ({y_test.sum()} attacks)")
```

---

## ✅ EXTRACTION CHECKLIST

- [ ] All PCAPs collected from network
- [ ] pcap_to_csv.py configured with YOUR feature definitions
- [ ] Run extraction on baseline traffic
- [ ] Run extraction on attack traffic  
- [ ] Feature quality check passed (no NaNs, all in range)
- [ ] Merged all CSVs into single file
- [ ] Shuffled to avoid overfitting
- [ ] Normalized features to [0,1]
- [ ] Split 80% train / 20% test
- [ ] Ready for model training!

---

## 🚀 NEXT: Train Models

```bash
python training/train_models.py \
  --X-train /data/training_data/X_train.npy \
  --X-test /data/training_data/X_test.npy \
  --y-train /data/training_data/y_train.npy \
  --y-test /data/training_data/y_test.npy \
  --output-dir brain/models/
```

**This will generate:**
- `isolation_forest_model.pkl` (Anomaly detection)
- `xgboost_model.pkl` (Attack classification)
- `feature_scaler.pkl` (Feature normalization)

Your FastAPI Brain will automatically load these and use them for real-time inference!
